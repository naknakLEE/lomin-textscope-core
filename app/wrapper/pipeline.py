import base64
import json
from pathlib import Path

from httpx import Client

from typing import Dict, Tuple, List, Optional
from operator import attrgetter
from datetime import datetime

from app import wrapper
from app.models import DocTypeHint
from app.utils.document import save_upload_document
from app.wrapper import pp
from app.common import settings
from app.utils.hint import apply_cls_hint
from app.utils.logging import logger

from app.utils.utils import (
    pretty_dict,
    substitute_spchar_to_alpha,
    set_ocr_response,
)

model_server_url = f"http://{settings.SERVING_IP_ADDR}:{settings.SERVING_IP_PORT}"
# TODO: move to json file
inference_pipeline_list = {}
model_mapping_table = {"보험금청구서": "agammoto", "처방전": "duriel"}
route_mapping_table = {"보험금청구서": "agammoto", "처방전": "duriel"}

inference_pipeline: Dict[str, Dict] = inference_pipeline_list.get(settings.CUSTOMER)  # type: ignore

kdt_custom_mapping: Dict = settings.KDT_CUSTOM_MAPPING 

# TODO: raise not e~xist method name in pipeline
def get_model_info(
    method_name: str,
    result_set: Dict,
    inference_pipeline: Dict,
    route_mapping_table: Dict,
    model_mapping_table: Dict,
) -> Tuple[str, str, str]:
    model_info = inference_pipeline.get(method_name, {})
    model_name = model_info.get("model_name", "None")
    route_name = model_info.get("route_name", "None")
    module_name = model_info.get("module_name", "None")
    if route_name is None or method_name is None:
        doc_class = result_set.get("classification", {}).get("doc_class", "")
        if route_name is None:
            route_name = route_mapping_table.get(doc_class)
        if method_name is None:
            model_name = model_mapping_table.get(doc_class)
    return (model_name, route_name, module_name)


# TODO: hint 사용
# TODO: pipeline 상에서 각 모델의 inference 끝났을 때 결과를 출력하도록 구성
def multiple(
    client: Client,
    inputs: Dict,
    sequence_type: str,
    response_log: Dict,
    hint: Optional[Dict] = None,
) -> Tuple[int, Dict, Dict]:
    inference_start_time = datetime.now()
    response_log["inference_start_time"] = inference_start_time.strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    sequence_list = inference_pipeline.get("sequence", {})
    result_set: Dict = dict()
    latest_result: Dict = dict()
    sequence_type_list: List = []
    if isinstance(sequence_list, dict):
        sequence_type_list = sequence_list.get(sequence_type, [])
    for method_name in sequence_type_list:
        inference_start_time = datetime.now()
        response_log[f"{method_name}_start_time"] = inference_start_time.strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        model_info = get_model_info(
            method_name=method_name,
            result_set=result_set,
            inference_pipeline=inference_pipeline,
            route_mapping_table=route_mapping_table,
            model_mapping_table=model_mapping_table,
        )
        inputs["model_name"], inputs["route_name"], module_name = model_info
        func_name = inputs["model_name"]

        call_func = attrgetter(f"{module_name}.{func_name}")(wrapper)
        result = call_func(client, inputs, latest_result, hint)
        latest_result = result_set[method_name] = result.get("response")

        inference_end_time = datetime.now()
        response_log[f"{method_name}_end_time"] = inference_end_time.strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        response_log[f"{method_name}_inference_time"] = (
            inference_end_time - inference_start_time
        ).total_seconds()

        if method_name == "classification" and result.get("is_supported_type") == True:
            break
    inference_end_time = datetime.now()
    response_log.update(
        {
            "inference_end_time": inference_end_time.strftime("%Y-%m-%d %H:%M:%S"),
            "inference_total_time": (
                inference_end_time - inference_start_time
            ).total_seconds(),
        }
    )
    logger.info("inference log: {}", json.dumps(response_log, indent=4, sort_keys=True))

    result = set_ocr_response(
        inputs=inputs,
        sequence_list=sequence_type_list,
        result_set=result_set,
    )
    return (result.get("status_code"), result, response_log)


# TODO: pipeline 상에서 각 모델의 inference 끝났을 때 결과를 출력하도록 구성
def single(
    client: Client,
    inputs: Dict,
    response_log: Dict,
    route_name: str = "gocr",
) -> Tuple[int, Dict, Dict]:
    """doc type hint를 적용하고 inference 요청"""
    inference_start_time = datetime.now()
    response_log.update(inference_start_time=inference_start_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3])

    # Apply doc type hint
    doc_type = ""
    doc_type_hint = None
    hint = inputs.get("hint")
    if hint and hint.get("doc_type").get('doc_type'):
        doc_type_hint = DocTypeHint(**hint.get("doc_type"))
        if(doc_type_hint.use and doc_type_hint.trust): doc_type = doc_type_hint.doc_type

    # gocr
    inferecne_response = client.post(
        f"{model_server_url}/gocr",
        json=inputs,
        timeout=settings.TIMEOUT_SECOND,
        headers={"User-Agent": "textscope core"},
    )    
    gocr_result = inferecne_response.json()
    
    inputs = gocr_result
    # only cls 
    if route_name == 'cls':
        # gocr 실행 결과를 cls로 보내기
        inferecne_response = client.post(
            f"{model_server_url}/cls",
            json=inputs,
            timeout=settings.TIMEOUT_SECOND,
            headers={"User-Agent": "textscope core"},
        )
        doc_type = inferecne_response.json().get('doc_type')
        if doc_type_hint and doc_type_hint.use:
            cls_hint_result = apply_cls_hint(doc_type_hint=doc_type_hint, cls_result=inferecne_response.json().get('cls_result', {}))
            response_log.update(apply_cls_hint_result=cls_hint_result)
            inputs["doc_type"] = cls_hint_result.get("doc_type")
        
        # 감사보고서, 재무재표(기타) 케이스는 재무제표로 분류
        if doc_type in ['CP-FNS-ETC', 'CP-AR']:
            doc_type = 'CP-FNS'
        
    # kv 
    elif route_name == 'kv':
        reverse_doc_type: Dict = kdt_custom_mapping.get('REVERSE_DOC_TYPE')
        # doctype을 입력받지 않은 경우에는 cls 먼저 실행
        if not doc_type:
            inferecne_response = client.post(
                f"{model_server_url}/cls",
                json=inputs,
                timeout=settings.TIMEOUT_SECOND,
                headers={"User-Agent": "textscope core"},
            )
            inputs = inferecne_response.json()
            if doc_type_hint and doc_type_hint.use:
                cls_hint_result = apply_cls_hint(doc_type_hint=doc_type_hint, cls_result=inputs)
                response_log.update(apply_cls_hint_result=cls_hint_result)
                inputs["doc_type"] = cls_hint_result.get("doc_type")            
            doc_type = inputs.get('doc_type')
        # input custom doc type convert lomin doc type
        elif reverse_doc_type.get(doc_type): 
            doc_type = reverse_doc_type.get(doc_type)
        
        if doc_type not in ['CP-FNS-ETC', "CP-AR"]:
            inputs.update(doc_type=doc_type)                         

            custom_inference_endpoint: Dict = kdt_custom_mapping.get('KDT_ENDPOINT').get('SERVING')
            convert_route_name = custom_inference_endpoint.get(doc_type) if custom_inference_endpoint.get(doc_type) else "kv"
            # endpoint가 tocr일경우 tocr에 맞는 input 만들기
            if convert_route_name == 'tocr_legacy':
                tocr_inputs: Dict = dict(
                    template=kdt_custom_mapping.get('KDT_TOCR').get(doc_type, "")
                )
                
                # 1. template 이미지 setting
                template_images: Dict = tocr_inputs.get("template").get("template_images")
                for v in template_images.values():
                    if v.get('is_apply'): continue
                    image_name = v.get('image_path')
                    file_path = Path(f"/workspace/app/assets/template_image/{image_name}")
                    with file_path.open('rb') as file:
                        image_data = file.read()
                        image_data = base64.b64encode(image_data)
                        success = save_upload_document(v.get('image_id'),image_name, image_data)
                        if success: v.update(is_apply=True)                        
                # # 2. test 이미지 setting                 
                # tocr_inputs.update(test_image_id=inputs.get('image_id', ''))
                # tocr_inputs.update(test_image_path=inputs.get('image_path', ''))

                # 3. inputs.update(tocr_inputs)             
                gocr_result.update(
                    tocr_inputs,
                    pp_end_point="kdt1_tocr"
                )
                inputs = gocr_result

            inferecne_response = client.post(
                f"{model_server_url}/{convert_route_name}",
                json=inputs,
                timeout=settings.TIMEOUT_SECOND,
                headers={"User-Agent": "textscope core"},
            )
    inferecne_response_json = inferecne_response.json()
    inferecne_response_json.update({
        "doc_type": doc_type
    })
    inference_end_time = datetime.now()
    response_log.update(
        inference_end_time=inference_end_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
        inference_total_time=(inference_end_time - inference_start_time).total_seconds(),
    )
    logger.info(
        f"Inference time: {str((inference_end_time - inference_end_time).total_seconds())}"
    )

   

    return (inferecne_response.status_code, inferecne_response_json, response_log)                                     

    # input custom doc type convert lomin doc type
    # reverse_doc_type: Dict = kdt_custom_mapping.get('REVERSE_DOC_TYPE')
    # if reverse_doc_type.get(doc_type): 
    #     doc_type = reverse_doc_type.get(doc_type)
    #     inputs.update(doc_type=doc_type)

    # # inferecne_server endpoint set
    # custom_inference_endpoint: Dict = kdt_custom_mapping.get('KDT_ENDPOINT').get('SERVING')
    # convert_route_name = custom_inference_endpoint.get(doc_type) if custom_inference_endpoint.get(doc_type) else route_name
    
    # # endpoint가 tocr일경우 tocr에 맞는 input 만들기
    # if convert_route_name == 'tocr':
    #     tocr_inputs: Dict = kdt_custom_mapping.get('KDT_TOCR').get(doc_type, "")
        
    #     # 1. template 이미지 setting
    #     template_images: Dict = tocr_inputs.get("template_images")
    #     for v in template_images.values():
    #         if v.get('is_apply'): continue
    #         image_name = v.get('image_path')
    #         file_path = Path(f"/workspace/app/assets/template_image/{image_name}")
    #         with file_path.open('rb') as file:
    #             image_data = file.read()
    #             image_data = base64.b64encode(image_data)
    #             success = save_upload_document(v.get('image_id'),image_name, image_data)
    #             if success: v.update(is_apply=True)                        
    #     # 2. test 이미지 setting                 
    #     tocr_inputs.update(test_image_id=inputs.get('image_id', ''))
    #     tocr_inputs.update(test_image_path=inputs.get('image_path', ''))

    #     # 3. inputs.update(tocr_inputs)             
    #     inputs = tocr_inputs 

    # ocr_response = client.post(
    #     f"{model_server_url}/{convert_route_name}",
    #     json=inputs,
    #     timeout=settings.TIMEOUT_SECOND,
    #     headers={"User-Agent": "textscope core"},
    # )
    
    # inference_end_time = datetime.now()
    # response_log.update(
    #     inference_end_time=inference_end_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
    #     inference_total_time=(inference_end_time - inference_start_time).total_seconds(),
    # )
    # logger.info(
    #     f"Inference time: {str((inference_end_time - inference_end_time).total_seconds())}"
    # )
    # return (ocr_response.status_code, ocr_response.json(), response_log)
