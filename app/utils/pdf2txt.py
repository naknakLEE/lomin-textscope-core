import os
import glob
import copy
import argparse
import uuid
import re
import pdf2image
import numpy as np
import xml.etree.ElementTree as ET

from PIL import Image
from typing import Optional, Dict, Tuple, List, Any
from pathlib import PurePath, Path
from functools import lru_cache

from pdfminer.layout import LAParams
from pdfminer.cmapdb import CMapDB
from pdfminer.pdfpage import PDFPage
from pdfminer.converter import XMLConverter
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfdocument import PDFDocument

from app.wrapper import settings
from app.utils.minio import MinioService


minio_client = MinioService()


def cid_to_char(cidx: str):
    '''
        pdf내에 text가 cid번호로 구성되어있는 경우 
        char로 번환하여 return 합니다.
    '''
    return chr(int(re.findall(r'\(cid\:(\d+)\)',cidx)[0]) + 29)

def convert_cid_to_str(input: str):
    res = input
    if input != "" and input != '(cid:3)':
        cids = re.findall(r'\(cid\:\d+\)',input)
        if len(cids) > 0:
            for cid in cids: res=res.replace(cid, cid_to_char(cid))
            return res
    return res

class Pdf2Image:
    def __init__(self, data_dir: Optional[str] = None):
        if data_dir is None:
            data_dir = PurePath("/workspace", "assets").as_posix()
        self.data_dir = data_dir
        self.load_lexicon()

    @lru_cache(maxsize=10)
    def save_xml(
        self,
        fname: str,
        xml_path: str,
        maxpages: int = 0,
        caching: bool = True,
        debug: int = 0,
    ) -> None:
        PDFDocument.debug = debug
        PDFParser.debug = debug
        CMapDB.debug = debug
        PDFPageInterpreter.debug = debug

        rsrcmgr = PDFResourceManager(caching=caching)
        outfp = open(xml_path, "w", encoding="utf-8")
        device = XMLConverter(
            rsrcmgr, outfp, laparams=LAParams(), imagewriter=None, stripcontrol=False
        )

        with open(fname, "rb") as fp:
            interpreter = PDFPageInterpreter(rsrcmgr, device)
            for page in PDFPage.get_pages(
                fp,
                set(),
                maxpages=maxpages,
                password=b"",
                caching=caching,
                check_extractable=True,
            ):
                page.rotate = (page.rotate + 0) % 360
                interpreter.process_page(page)
        device.close()
        outfp.close()

    def load_lexicon(self) -> None:
        self.lexicon_dict = dict()

        for idx, lexicon in enumerate(
            glob.glob(os.path.join(self.data_dir, "lexicons", "*.txt"))
        ):
            all_texts = list()
            with open(lexicon) as f:
                all_texts.extend(f.read().splitlines())
            self.lexicon_dict[idx] = all_texts

    def parse_coordinate(self, bbox: str) -> Tuple[int, ...]:
        x0, y0, x1, y1 = map(float, bbox.split(","))
        x0 = round(x0)
        y0 = round(y0)
        x1 = round(x1)
        y1 = round(y1)

        return (x0, y0, x1, y1)

    def get_integrated_box(self, boxes: np.ndarray) -> List[int]:
        return [
            np.min(boxes[:, 0]),
            np.min(boxes[:, 1]),
            np.max(boxes[:, 2]),
            np.max(boxes[:, 3]),
        ]

    def parse_texts(self, texts: List[ET.Element], height: int) -> Tuple[List, List]:
        box_list: List[List[int]] = list()
        text_list: List[str] = list()
        textline_box_list: List[List[int]] = list()
        textline_char: str = ""
        for text in texts:
            if len(text.attrib) == 0: continue
            char_attr = text.attrib

            bbox = char_attr["bbox"]
            x0, _y0, x1, _y1 = self.parse_coordinate(bbox)
            y1 = height - _y0
            y0 = height - _y1

            textline_box_list.append([x0, y0, x1, y1])
            char: Optional[str] = text.text
            if char is None:
                char = ""
            textline_char += char
        if len(textline_char.strip()) != 0:
            textline_box_array = np.array(textline_box_list)
            box_list.append(self.get_integrated_box(textline_box_array))
            textline_char = convert_cid_to_str(textline_char.strip())
            text_list.append(textline_char)
        return box_list, text_list

    def resize_bbox(self, bbox: np.ndarray, w_ratio: float, h_ratio: float) -> List:
        resized = copy.deepcopy(bbox)
        resized[:, 0] = resized[:, 0] * w_ratio
        resized[:, 1] = resized[:, 1] * h_ratio
        resized[:, 2] = resized[:, 2] * w_ratio
        resized[:, 3] = resized[:, 3] * h_ratio
        return resized.tolist()

    def read_xml(self, xml_path: str, page_num: int, page_size: List) -> Dict:
        bboxes = list()
        texts = list()

        doc = ET.parse(xml_path)
        pages = doc.findall("page")
        page = pages[page_num]
        page_attr = page.attrib
        width = round(float(page_attr["bbox"].split(",")[2]))
        height = round(float(page_attr["bbox"].split(",")[3]))
        _text_boxes = page.findall("textbox")

        for _text_box in _text_boxes:
            _text_lines = _text_box.findall("textline")
            for _text_line in _text_lines:
                _texts = _text_line.findall("text")
                _bboxes, _texts = self.parse_texts(_texts, height)
                bboxes.extend(_bboxes)
                texts.extend(_texts)

        bboxes = np.array(bboxes)
        bboxes = self.resize_bbox(
            bboxes, w_ratio=page_size[0] / width, h_ratio=page_size[1] / height
        )
        return {"boxes": bboxes, "texts": texts}

    def __call__(
        self, pages: List, page_num: int, pdf_path: Any, xml_path: str
    ) -> Image:
        page = pages[page_num]
        text_info = self.read_xml(
            xml_path=xml_path, page_num=page_num, page_size=page.size
        )
        return text_info


def parse_pdf_text(text_info: Dict) -> Dict:
    return {
        "rec_preds": [[]],
        "scores": [1.0] * len(text_info.get("texts", [])),
        "boxes": text_info.get("boxes"),
        "classes": ["text"] * len(text_info.get("texts", [])),
        "texts": text_info.get("texts")
    }


@lru_cache(maxsize=10)
def convert_path_to_image(pdf_path: str) -> List:
    pages = pdf2image.convert_from_path(pdf_path=pdf_path)
    return pages


def get_pdf_text_info(inputs: Dict) -> Tuple[Dict, Tuple[int, int]]:
    xml_path = PurePath("/tmp", str(uuid.uuid4()) + ".xml").as_posix()
    
    pdf_path = None
    if settings.USE_MINIO:
        image_minio_path = "/".join([inputs.get("image_id"), Path(inputs.get("image_path", "")).name])
        image_bytes = minio_client.get(image_minio_path, settings.MINIO_IMAGE_BUCKET)
        pdf_path = save_pdf(image_bytes)
        
    else:
        pdf_path = inputs.get("image_path")
    
    page_num = inputs.get("page", 1) - 1
    pdf2txt.save_xml(fname=pdf_path, xml_path=xml_path, maxpages=inputs.get("page"))
    
    doc = ET.parse(xml_path)
    pages = doc.findall("page")
    
    if 0 > page_num or page_num > (len(pages) - 1):
        page_num = 0
    
    page = pages[page_num]
    textbox = page.findall("textbox")
    
    parsed_text_info = {}
    image_size = (0, 0)
    if len(textbox) > 0:
        pages = convert_path_to_image(pdf_path=pdf_path)
        text_info = pdf2txt(
            pages=pages, page_num=page_num, pdf_path=pdf_path, xml_path=xml_path
        )
        image_size = pages[page_num].size
        
        parsed_text_info.update(parse_pdf_text(text_info))
        parsed_text_info.update(dict({
            "image_width": image_size[0],
            "image_height": image_size[1],
            "image_width_origin": image_size[0],
            "image_height_origin": image_size[1],
            "request_id": inputs.get("request_id", ""),
            "angle": 0,
            "id_type": "",
        }))
    
    return parsed_text_info, image_size


def save_pdf(file_bytes: str) -> str:
    pdf_dir = "/".join(["/tmp", str(uuid.uuid4()) + ".pdf"])
    
    with open(pdf_dir, "wb") as pdf:
        pdf.write(file_bytes)
    pdf.close()
    
    return pdf_dir


pdf2txt = Pdf2Image("/workspace/assets")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf_path", required=True, type=str)
    parser.add_argument("--page_num", required=False, type=str, default=0)
    parser.add_argument("--xml_path", required=False, type=str, default="/tmp/temp.xml")
    parser.add_argument(
        "--save_path", required=False, type=str, default="/tmp/temp.jpg"
    )
    args = parser.parse_args()

    from pyinstrument import Profiler

    profiler = Profiler()
    profiler.start()

    pdf2txt.save_xml(fname=args.pdf_path, xml_path=args.xml_path)
    pages = pdf2image.convert_from_path(pdf_path=args.pdf_path)
    text_info = pdf2txt(
        pages=pages,
        page_num=args.page_num,
        pdf_path=args.pdf_path,
        xml_path=args.xml_path,
    )
    texts = text_info.get("texts")
    boxes = text_info.get("boxes")
    image_array = np.array(pages[args.page_num])

    profiler.stop()
    print(profiler.output_text(unicode=True, color=True, show_all=True))
