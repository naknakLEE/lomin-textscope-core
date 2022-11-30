import os
import tifffile
import pdf2image
import base64
import shutil

from httpx import Client
from PIL import Image
from PIL.Image import DecompressionBombError
from io import BytesIO
from pathlib import Path
from functools import lru_cache
from typing import Tuple, List
from fastapi.encoders import jsonable_encoder
from starlette.responses import JSONResponse

from app import hydra_cfg
from app.utils.logging import logger
from app.common.const import get_settings
from app.utils.minio import MinioService
from app.utils.image import read_image_from_bytes
from app.schemas import error_models as ErrorResponse
from app.middlewares.exception_handler import CoreCustomException
from app.wrapper import pipeline, pp
from app.database import query

from concurrent import futures
from itertools import repeat
from app.utils.utils import get_ts_uuid
from app.utils.ocr_to_pdf import Word, PdfParser
from app.utils import pdf_converter
from app.utils.pdf2txt import get_pdf_text_info
import copy
from sqlalchemy.orm import Session
from app.database.schema import InferenceInfo
import socket
from datetime import date
from minio.commonconfig import Tags
from typing import Optional

settings = get_settings()
minio_client = MinioService()
pdf_parser = PdfParser()
pdf2pdfa_convertor = pdf_converter.PDF2PDFAConvertor(libreoffice="soffice")
support_file_extension_list = {
    "image": [".jpg", ".jpeg", ".jp2", ".png", ".bmp"],
    "tif": [".tif", ".tiff"],
    "pdf": [".pdf"]
}

multipage_file_format = ['.pdf','.tif','.tiff']


def get_file_extension(document_filename: str = "x.xxx") -> str:
    return Path(document_filename).suffix.lower()


def get_stored_file_extension(document_path: str) -> str:
    stored_ext = Path(document_path).suffix
    doc_ext = stored_ext
    
    if doc_ext.lower() in settings.MULTI_PAGE_DOCUMENT:
        stored_ext = settings.MULTI_PAGE_SEPARATE_EXTENSION
    
    return stored_ext


@lru_cache(maxsize=15)
def get_page_count(document_data: str, document_filename: str) -> int:
    document_bytes = base64.b64decode(document_data)
    file_extension = get_file_extension(document_filename)
    total_pages = 1
    
    if file_extension in support_file_extension_list.get("image"):
        total_pages = 1
        
    elif file_extension in support_file_extension_list.get("tif"):
        try:
            with tifffile.TiffFile(BytesIO(document_bytes)) as tif:
                total_pages = len(tif.pages)
        except:
            logger.exception("read pillow")
            logger.error(f"Cannot load {document_filename}")
            total_pages = 0
            
    elif file_extension in support_file_extension_list.get("pdf"):
        pages = pdf2image.convert_from_bytes(document_bytes)
        total_pages = len(pages)
        
    else:
        logger.error(f"{document_filename} is not supported!")
        total_pages = 0
    
    return total_pages

# A1 (1684, 2384 pts), 300dpi
MAX_IMAGE_PIXEL_SIZE = (7016, 9933)
def is_support_image(document_name: str, document_bytes: bytes) -> bool:
    support = True
    
    file_extension = get_file_extension(document_name)
    if file_extension in support_file_extension_list.get("image"):
        try:
            image = Image.open(BytesIO(document_bytes))
            if image is None or image.size[0] > MAX_IMAGE_PIXEL_SIZE[0] or image.size[1] > MAX_IMAGE_PIXEL_SIZE[1]:
                support = False
        except DecompressionBombError:
            support = False
        
    elif file_extension in support_file_extension_list.get("tif"):
        try:
            with tifffile.TiffFile(BytesIO(document_bytes)) as tifs:
                if len(tifs.pages) > hydra_cfg.document.multi_page_limit:
                    raise CoreCustomException("C01.002.2003")
                
                for tif in tifs.pages:
                    # tif: tifffile.TiffPage = tif
                    if tif.shaped[3] > MAX_IMAGE_PIXEL_SIZE[0] or tif.shaped[4] > MAX_IMAGE_PIXEL_SIZE[1]:
                        support = False
        except:
            support = False
        
    elif file_extension in support_file_extension_list.get("pdf"):
        pdf_info = pdf2image.pdfinfo_from_bytes(document_bytes)
        
        if pdf_info.get("Pages", hydra_cfg.document.multi_page_limit+1) > hydra_cfg.document.multi_page_limit:
            raise CoreCustomException("C01.002.2003")
        
        page_size = pdf_info.get("Page size", "2000.0 x 3000.0 pts")
        page_size = page_size.split(" ")
        if float(page_size[0]) > 1684 or float(page_size[2]) > 2384:
            support = False
        
    else:
        logger.error(f"{document_name} is not supported!")
        support = False
    
    return support


# 파일 확장자 제한
def is_support_file_format(document_filename: str) -> bool:
    file_extension = get_file_extension(document_filename)
    support = False
    
    for support_list in support_file_extension_list.values():
        if file_extension in support_list:
            support = True
    
    return support

# 파일 용량 제한 ( 300MB )
def is_support_file_size(document_bytes: bytes) -> bool:
    return len(document_bytes) < 300 * 1048576


def is_support_file(document_filename: str, document_bytes: bytes) -> bool:
    return True \
        & is_support_file_format(document_filename) \
        & is_support_file_size(document_bytes)


def save_upload_document(
    documnet_id: str, documnet_name: str, documnet_base64: str, /,  new_document: bool = True
) -> Tuple[bool, Path, int]:
    
    document_extension = Path(documnet_name).suffix
    
    save_document_dict = dict()
    decoded_image_data = base64.b64decode(documnet_base64)
    
    # 원본 파일
    save_document_dict.update({'/'.join([documnet_id, documnet_name]): decoded_image_data})
    
    # pdf나 tif, tiff 일 경우 장 단위 분리
    if document_extension.lower() in settings.MULTI_PAGE_DOCUMENT:
        buffered = BytesIO()
        
        try:
            document_pages: List[Image.Image] = read_image_from_bytes(decoded_image_data, documnet_name, 0.0, 1, separate=True)
        except DecompressionBombError:
            raise CoreCustomException("C01.003.2001")
        
        for page, document_page in enumerate(document_pages):
            document_page.save(buffered, settings.MULTI_PAGE_SEPARATE_EXTENSION[1:])
            save_document_dict.update({'/'.join([documnet_id, str(page+1)+settings.MULTI_PAGE_SEPARATE_EXTENSION]): buffered.getvalue()})
            buffered.seek(0)
    elif new_document:
        save_document_dict.update({'/'.join([documnet_id, "1" + document_extension]): decoded_image_data})
    
    success = True
    save_path = ""
    if settings.USE_MINIO:
        for object_name, data in save_document_dict.items():
            success &= minio_client.put(
                bucket_name=settings.MINIO_IMAGE_BUCKET,
                object_name=object_name,
                data=data,
            )
        save_path = "minio/" + documnet_name
        
    else:
        root_path = Path(settings.IMG_PATH)
        base_path = root_path.joinpath(documnet_id)
        base_path.mkdir(parents=True, exist_ok=True)
        
        for object_name, data in save_document_dict.items():
            save_path = base_path.joinpath(object_name)
            
            with save_path.open("wb") as file:
                file.write(data)
        
        success = True
    
    return success, save_path, (len(save_document_dict) - 1)


def get_document_bytes(document_id: str, document_path: Path) -> str:
    document_bytes = None
    
    if settings.USE_MINIO:
        image_minio_path = "/".join([document_id, document_path.name])
        document_bytes = minio_client.get(image_minio_path, settings.MINIO_IMAGE_BUCKET)
    else:
        with document_path.open("rb") as f:
            document_bytes = f.read()
    
    return document_bytes

def is_support_format(document_filename: str) -> bool:
    file_extension = get_file_extension(document_filename)
    support = False
    
    for support_list in support_file_extension_list.values():
        if file_extension in support_list:
            support = True
    
    return support    

def create_socket_msg(pdf_file_nm:str, status_code:int, gubun:str, **kwargs) -> bytes:
    """
        socket 통신용 msg 만드는 function
    """
    pdf_file_nm_msg = f"pdf_file_nm:{pdf_file_nm}"
    status_code_msg = f"result_code:{status_code}"
    msg_array = [pdf_file_nm_msg, status_code_msg]

    err_info:dict = kwargs.get('err_info', None)
    if status_code != 200 and err_info: 
        msg_array.append(f"error_code:{err_info.get('error_code')}")
        msg_array.append(f"error_message:{err_info.get('error_message')}")
    msg_array.append(f"gubun:{gubun}")
    return ",".join(msg_array).encode('utf-8')    

def multiple_request_ocr(
    inputs: dict 
):
    """
        다중 문서 ocr 요청
    """
    document_dir_path = inputs.get('document_dir')
    file_list = os.listdir(document_dir_path)
    file_list.sort()
    
    inference_result_list = list()
    document_data_list = list()

    document_cnt = 0
    pdf_file_name = inputs.get('pdf_file_name')
    try:
        # dir안에 있는 file들을 읽어서 list로 변환하기
        for file_name in file_list: document_cnt = generate_document_list(document_dir_path, file_name, document_data_list, document_cnt)

        # MultiThread로 ocr결과 담기
        # TODO: 멀티쓰레드, 멀티프로세싱, async 속도 비교        
        with futures.ThreadPoolExecutor(max_workers=hydra_cfg.document.thread_max_works) as executor:
            future = executor.map(request_ocr,document_data_list,repeat(inputs))
            inference_result_list = list(future)

            # ocr_result list sorting
            sorted(inference_result_list, key=lambda k: k['cnt'])

            # sorting된 값을 가지고 pdf생성하기
            inputs.update(
                inference_result_list=inference_result_list
            )
            generate_searchalbe_pdf(inputs)        
            socket_msg: bytes = create_socket_msg(pdf_file_name, 200, 'C')

    except Exception as exc:
        logger.error(exc, exc_info=True)
        err_code: int = exc.__getattribute__('context') if hasattr(exc,'context') else 3501
        status_code, error = ErrorResponse.ErrorCode.get(err_code)
        socket_msg: bytes = create_socket_msg(pdf_file_name, status_code, 'C', error=error)
        # return JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))                                      
        
    # hydra config를 이용하여 소켓정보 가져오기
    socket_server_ip:str = hydra_cfg.route.socket_server_ip
    socket_server_port:int = hydra_cfg.route.socket_server_port
        
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((socket_server_ip, socket_server_port))
        client_socket.send(socket_msg)    

def request_ocr(
    document_info: dict, inputs: dict
):
    """
        문서 하나당 ocr 요청
    """
    document_data:bytes = document_info.get('data')
    document_cnt: int   = document_info.get('cnt')
    document_name: str  = document_info.get('name')
    target_page: int    = 0

    new_inputs = copy.deepcopy(inputs)
    new_inputs.update(
        image_bytes=document_data,
        image_path=document_name,
        document_cnt=document_cnt,
        page=target_page,
        doc_type=None,        
    )
    response_log = dict()
    with Client() as client:
        # Inference
        status_code, inference_results, response_log = pipeline.single(
            client=client,
            inputs=new_inputs,
            response_log=response_log,
            route_name='gocr',
        )
        if isinstance(status_code, int) and (status_code < 200 or status_code >= 400):
            logger.error(inference_results, exc_info=True)
            exec = Exception()
            exec.__setattr__('context', 3501)
            raise exec

        # convert preds to texts
        if (
            "texts" not in inference_results
        ):
            status_code, texts = pp.convert_preds_to_texts(
                client=client,
                rec_preds=inference_results.get("rec_preds", []),
            )
            if status_code < 200 or status_code >= 400:
                exec = Exception()
                exec.__setattr__('context', 3503)
                raise exec

            inference_results["texts"] = texts             

        doc_type_code = inference_results.get("doc_type")
        inference_results.update(doc_type=doc_type_code)

        # Post processing -> Searchable_pp일경우 line_word
        status_code, post_processing_results, response_log = pp.post_processing(
            client=client,
            task_id="",
            response_log=response_log,
            inputs=inference_results,
            post_processing_type='line_word',
        )
        if status_code < 200 or status_code >= 400:
            exec = Exception()
            exec.__setattr__('context', 3502)
            raise exec             
        logger.debug(post_processing_results.get('result'))
        inference_results.update(
            post_processing_results.get('result'),
            base64_encode_file=document_data,
            cnt = document_cnt
        )                   

    return inference_results

def generate_document_list(
    document_dir_path: str, file_name: str, document_data_list: list, document_cnt: int
):
    """
        request로 입력받은 경로를 통해 documnet_list 생성
    """
    file_path = os.path.join(document_dir_path, file_name)
    with Path(file_path).open('rb') as file:
        document_data = file.read()
        # 업로드된 파일 포맷(확장자) 확인
        is_support = is_support_format(file_name)

        # TODO: 지원하지 않는 파일은 따로 txt 파일 생성 필요 할듯?
        if is_support is False:
            exec = Exception()
            exec.__setattr__('context', 2105)
            raise exec
        
        # 멀티페이지 파일 포맷(pdf, tif, tiff)일 경우 한장씩 분리하기
        if(Path(file_name).suffix.lower() in multipage_file_format):
            buffered = BytesIO()
            try:
                document_pages: List[Image.Image] = read_image_from_bytes(document_data, file_name, 0.0, 1, separate=True)
            except DecompressionBombError:
                raise CoreCustomException("C01.003.2001")
            
            for page, document_page in enumerate(document_pages):
                document_page.save(buffered, settings.MULTI_PAGE_SEPARATE_EXTENSION[1:])
                document_data_list.append(dict(
                    cnt=document_cnt,
                    data=base64.b64encode(buffered.getvalue()),
                    name=f"{document_cnt}.jpeg"
                ))
                document_cnt += 1
                buffered.seek(0)
        else:
            document_data_list.append(dict(
                cnt=document_cnt,
                data=base64.b64encode(document_data),
                name=file_name
            ))
            document_cnt +=1
            
        return document_cnt
        
def generate_searchalbe_pdf(
    inputs: dict
):
    """
        request param으로 받은 경로에 searchable pdf생성
    """
    try:
        pdf_parser = PdfParser()
        wordss: list[List[Word]] = list()
        images: List[Image.Image] = list()

        inference_result_list = inputs.get('inference_result_list')
        pdf_file_name = inputs.get('pdf_file_name')

        for inference_result in inference_result_list:    

            angle = inference_result.get("angle", 0)
            words: List[Word] = list()
        
            textss: List[List[str]] = inference_result.get("texts", [])
            boxess: List[List[List[float]]] = inference_result.get("boxes", [])
            
            for texts, boxs in zip(textss, boxess):
                
                i_s = 0
                i_e = 0
                
                for i in range(len(texts)):
                    # 다음이 있을때 
                    if i + 1 < len(texts):
                        x_dis = boxs[i+1][0] - boxs[i][2]
                        
                        # 바로 옆일때 
                        if x_dis < (boxs[0][3] - boxs[0][1]) * 0.3:
                            
                            # 다왔다
                            if i + 1 == len(texts) - 1:
                                
                                t_ = " ".join(texts[i_s:])
                                x_min, y_min, x_max, y_max = (100000, 100000, -1, -1)
                                for b in boxs[i_s:]:
                                    if x_min > b[0]: x_min = b[0]
                                    if y_min > b[1]: y_min = b[1]
                                    if x_max < b[2]: x_max = b[2]
                                    if y_max < b[3]: y_max = b[3]
                                
                                b_ = [ x_min, y_min, x_max, y_max ]
                                words.append(Word(text=t_, bbox=b_))
                                continue
                                
                            else:
                                continue
                            
                        else:
                            t_ = " ".join(texts[i_s:i + 1])
                            x_min, y_min, x_max, y_max = (100000, 100000, -1, -1)
                            for b in boxs[i_s:i + 1]:
                                if x_min > b[0]: x_min = b[0]
                                if y_min > b[1]: y_min = b[1]
                                if x_max < b[2]: x_max = b[2]
                                if y_max < b[3]: y_max = b[3]
                            
                            b_ = [ x_min, y_min, x_max, y_max ]
                            words.append(Word(text=t_, bbox=b_))
                            i_s = i + 1
                            continue
                        
                    # 다음이 업을때 
                    elif i + 1 == len(texts):
                        t_ = " ".join(texts[i_s:])
                        x_min, y_min, x_max, y_max = (100000, 100000, -1, -1)
                        for b in boxs[i_s:]:
                            if x_min > b[0]: x_min = b[0]
                            if y_min > b[1]: y_min = b[1]
                            if x_max < b[2]: x_max = b[2]
                            if y_max < b[3]: y_max = b[3]
                        
                        b_ = [ x_min, y_min, x_max, y_max ]
                        words.append(Word(text=t_, bbox=b_))
                        continue
                        
                    # 하나 또는 마지막 
                    elif i == len(texts) -1:
                        words.append(Word(text=texts[0], bbox=boxs[0]))
                        continue

            wordss.append(words)

            document_path_copy = Path(f"{pdf_file_name}.jpeg")
            document_bytes = base64.b64decode(inference_result.get("base64_encode_file"))
            images.append(read_image_from_bytes(document_bytes, document_path_copy.name, angle, 0))
        
        pdf_file_save_path: str = os.path.dirname(pdf_file_name)
        pdf_file_save_name = os.path.basename(pdf_file_name)
        
        # # 임시 저장 위치 (PDF)
        # pdf_file_save_dir_temp = Path(pdf_file_save_path + "/.tmp")
        # pdf_file_save_dir_temp.mkdir(parents=True, exist_ok=True)
        
        # # PDF 저장
        # pdf_save_path = pdf_file_save_dir_temp.joinpath(pdf_file_save_name)
        # pdf_parser.export_pdf(pdf_save_path.as_posix(), wordss, images, True)
        
        # # 실제 저장 위치 (PDF/A-1a)
        # pdf_file_save_dir = Path(pdf_file_save_path)
        # pdf_file_save_dir.mkdir(parents=True, exist_ok=True)
        
        # # PDF/A-1a 변환
        # pdf2pdfa_convertor.convert(outputPath=pdf_file_save_dir.as_posix(), inputPath=pdf_save_path.as_posix())

        if hydra_cfg.document.use_pdf_a1:
            pdf_convert(pdf_file_save_name, pdf_file_save_path, wordss, images)
        else:
            Path(pdf_file_save_path).mkdir(parents=True, exist_ok=True)
            pdf_parser.export_pdf(Path(pdf_file_name).as_posix(), wordss, images, True)
        

        # pdf생성이 성공하면 이미지 폴더 지우기
        document_dir: str = inputs.get("document_dir")
        if os.path.exists(document_dir):
            shutil.rmtree(document_dir)        
        
        

    except Exception as exc:    
        logger.error(exc)
        exc.__setattr__('context', "C01.006.5003")
        raise exc        

def generate_searchable_pdf_2(
    inputs: dict
):
    """
        request param으로 받은 경로에 searchable pdf생성
    """
    default_pdf_save_path = hydra_cfg.document.put_directory

    try:
        pdf_parser = PdfParser()
        wordss: list[List[Word]] = list()
        images: List[Image.Image] = inputs.get("pil_image_list", [])

        pdf_file_name = inputs.get('pdf_file_name')
        inspect_result = inputs.get('inspect_result_list', {})
        # pdf_save_path = inputs.get('pdf_save_path', default_pdf_save_path)
        pdf_save_path = default_pdf_save_path

        words: List[Word] = list()
        for page, result in enumerate(inspect_result):
            words = []
            texts = result.get("texts", [])
            boxes = result.get("boxes", [])
            for text, box in zip(texts, boxes):
                words.append(Word(text=text, bbox=box))
            wordss.append(words)
        
        
        pdf_file_save_name = os.path.basename(pdf_file_name)

        if hydra_cfg.document.use_pdf_a1:
            pdf_convert(pdf_file_save_name, pdf_save_path, wordss, images)
        else:
            Path(pdf_save_path).mkdir(parents=True, exist_ok=True)
            file_name = os.path.basename(pdf_file_name)
            file_name = "/".join([pdf_save_path, file_name])
            pdf_parser.export_pdf(Path(file_name).as_posix(), wordss, images, True)
            end_file_path = file_name.replace(".pdf", ".end")
            Path(end_file_path).touch()             


        # pdf_file_save_path = pdf_file_save_path.replace('minio', '/workspace')
        
        # # 임시 저장 위치 (PDF)
        # pdf_file_save_dir_temp = Path(pdf_save_path + "/tmp")
        # pdf_file_save_dir_temp.mkdir(parents=True, exist_ok=True)
        
        # # PDF 저장
        # pdf_save_path = pdf_file_save_dir_temp.joinpath(pdf_file_save_name)
        # pdf_parser.export_pdf(pdf_save_path.as_posix(), wordss, images, True)
        
        # # 실제 저장 위치 (PDF/A-1a)
        # # pdf_file_save_dir = Path(default_pdf_save_path).joinpath(pdf_file_save_name)
        # pdf_file_save_dir = Path(default_pdf_save_path)
        # pdf_file_save_dir.mkdir(parents=True, exist_ok=True)
        
        # # PDF/A-1a 변환
        # pdf2pdfa_convertor.convert(outputPath=pdf_file_save_dir.as_posix(), inputPath=pdf_save_path.as_posix())
               
    except Exception as exc:    
        logger.error(exc)
        exc.__setattr__('context', "C01.006.5003")
        raise exc    

def document_dir_verify(document_path: str):
    if not os.path.isdir(document_path):
        status_code, error = ErrorResponse.ErrorCode.get(2508)
        return JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    return True        

def save_minio_pdf_convert_img(
    inputs: dict,
    session: Session
) -> Tuple[int, str, str]:
    """
        pdf 파일을 img로 쪼개어 Minio 저장(local pc에는 저장X -> 요구사항)
    """
    pdf_dir = inputs.get('pdf_dir')
    pdf_list = os.listdir(pdf_dir)
    
    pdf_list = list(filter(lambda x: Path(x).suffix.lower() == '.pdf', pdf_list))
    pdf_file_name = pdf_list[0]

    file_path = os.path.join(pdf_dir, pdf_file_name)
    document_id = get_ts_uuid("document")
    pdf_len = 0
    origin_object_name = ""
    today = date.today().isoformat()

    with Path(file_path).open('rb') as file:
        pdf_data = file.read()
        buffered = BytesIO()
        try:        
            document_pages: List[Image.Image] = read_image_from_bytes(pdf_data, pdf_file_name, 0.0, 1, separate=True)
            pdf_len = len(document_pages)
            if(not pdf_len):
                status_code, error = ErrorResponse.ErrorCode.get(2103)
                return JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))                         
            success = False            
            # 원본 파일 집어 넣기
            origin_object_name = '/'.join([today, document_id, pdf_file_name])
            success = minio_client.put(
                bucket_name=settings.MINIO_IMAGE_BUCKET,
                object_name=origin_object_name,
                data=pdf_data,
            )                    

            if(not success): raise DecompressionBombError            

            # pdf 파일을 쪼개어 jpeg로 변환후 한장씩 저장
            for page, document_page in enumerate(document_pages):
                document_page.save(buffered, settings.MULTI_PAGE_SEPARATE_EXTENSION[1:])
                object_name = '/'.join([today, document_id, str(page+1)+settings.MULTI_PAGE_SEPARATE_EXTENSION])
                data = buffered.getvalue()

                success &= minio_client.put(
                    bucket_name=settings.MINIO_IMAGE_BUCKET,
                    object_name=object_name,
                    data=data,
                )                    
                if(not success): raise DecompressionBombError
                buffered.seek(0)            
        except DecompressionBombError:
            raise CoreCustomException("C01.003.2001")

    doc_type_idx = [0] * pdf_len
    doc_type_code = ["GOCR"] * pdf_len
    # save_path = "minio/" + pdf_file_name
    save_path = '/'.join([today, pdf_file_name])
    dao_document_params = {
        "document_id": document_id,
        "user_email": inputs.get('user_email'),
        "user_team": inputs.get('user_team'),
        "document_path": save_path,
        "document_pages": pdf_len,
        "doc_type_idx": doc_type_idx,
        "doc_type_code": doc_type_code,
        "cls_type_idx": 5
    }
    query.insert_document(session, **dao_document_params)                

    return [pdf_len, document_id, origin_object_name]

def get_inference_result_to_pdf(
    inputs: dict,
    # pdf_extract_inputs: dict,
    session: Session,
    # user_info: dict,
):
    """
        PDF 저장 및 Inference_result DB Insert
    """
    try:
        # 1. Minio 이미지 저장
        pdf_len, document_id, origin_object_name = save_minio_pdf_convert_img(inputs, session)
        # 2. 저장된 pdf파일로 inference_result 추출   
        get_pdf_text_info_inputs = dict(
            image_id = document_id,
            image_path = origin_object_name,
        )
        inference_results_list = list()
        
        logger.debug("=====================> Start Inference Result Extract To PDF File")
        parsed_text_info, image_size, parsed_text_list = get_pdf_text_info(get_pdf_text_info_inputs)
        logger.debug("=====================> Finish Inference Result Extract To PDF File")
        for idx, parsed_text_info in enumerate(parsed_text_list):
            if len(parsed_text_info) > 0:
                inference_id = get_ts_uuid("inference")
                inference_info = dict(
                    inference_id=inference_id,
                    document_id=document_id, 
                    user_email=inputs.get('user_email'),
                    user_team=inputs.get('user_team'),
                    inference_result=parsed_text_info,
                    inference_type="gocr",
                    page_num=parsed_text_info.get("page", idx+1),
                    doc_type_idx=0,
                    response_log=parsed_text_info.get("response_log", {})
                )           
                inference_results_list.append(inference_info)        

        session.bulk_insert_mappings(InferenceInfo,inference_results_list)
        session.commit()
        session.flush()

        # DB 인서트에 성공하면
        pdf_dir = inputs.get('pdf_dir')
        if os.path.exists(pdf_dir):
            shutil.rmtree(pdf_dir)          

        socket_msg: bytes = create_socket_msg(origin_object_name, 200, 'U')            
    except Exception as exc:
        logger.error(exc, exc_info=True)
        err_code: int = exc.__getattribute__('context') if hasattr(exc,'context') else 3503
        status_code, error = ErrorResponse.ErrorCode.get(err_code)
        socket_msg: bytes = create_socket_msg(origin_object_name, status_code, 'U', error=error)            

    # hydra config를 이용하여 소켓정보 가져오기
    socket_server_ip:str = hydra_cfg.route.socket_server_ip
    socket_server_port:int = hydra_cfg.route.socket_server_port
        
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((socket_server_ip, socket_server_port))
        client_socket.send(socket_msg)    

def pdf_convert(
    pdf_file_name: str,
    pdf_save_path: str,
    wordss: list,
    images: list,
    pdf_select_version: Optional[str]="1"
):
    """
        PDF Conver Function
        ex) PDF -> PDF/A1-a | PDF/A1-a -> PDF
    """
    # 임시 저장 위치 (PDF)
    pdf_file_save_dir_temp = Path(pdf_save_path + "/tmp")
    pdf_file_save_dir_temp.mkdir(parents=True, exist_ok=True)
    
    # PDF 저장
    pdf_temp_save_path = pdf_file_save_dir_temp.joinpath(pdf_file_name)
    pdf_parser.export_pdf(pdf_temp_save_path.as_posix(), wordss, images, True)
    
    # 실제 저장 위치 (PDF/A-1a)
    # pdf_file_save_dir = Path(default_pdf_save_path).joinpath(pdf_file_save_name)
    pdf_file_save_dir = Path(pdf_save_path)
    pdf_file_save_dir.mkdir(parents=True, exist_ok=True)
    
    # PDF/A-1a 변환
    pdf2pdfa_convertor.convert(outputPath=pdf_file_save_dir.as_posix(), inputPath=pdf_temp_save_path.as_posix(), pdf_select_version=pdf_select_version)