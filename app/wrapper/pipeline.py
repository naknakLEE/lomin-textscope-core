import json
from copy import deepcopy
from datetime import datetime
from operator import attrgetter
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from fastapi.responses import JSONResponse
from httpx import Client
from requests import Session

from app import wrapper
from app.common import settings
from app.database import query, schema
from app.models import DocTypeHint
from app.utils.hint import apply_cls_hint
from app.utils.image import get_image_bytes
from app.utils.inference import get_removed_text_inference_result
from app.utils.logging import logger
from app.utils.utils import (get_pp_api_name, get_ts_uuid, pretty_dict,
                             set_ocr_response, substitute_spchar_to_alpha)
from app.wrapper import pp

model_server_url = f"http://{settings.SERVING_IP_ADDR}:{settings.SERVING_IP_PORT}"
gocr_route = "gocr"
cls_route = "cls"

# TODO: move to json file
inference_pipeline_list = {
    "heungkuk": {
        "general_detection": {
            "model_name": "agamotto",
            "route_name": "agamotto",
            "module_name": "detection",
        },
        "kv_detection": {
            "model_name": None,
            "route_name": "duriel",
            "module_name": "detection",
        },
        "classification": {
            "model_name": "duriel",
            "route_name": "duriel",
            "module_name": "classification",
        },
        "recognition": {
            "model_name": "tiamo",
            "route_name": "tiamo",
            "module_name": "recognition",
        },
        "sequence": {
            "kv": ["general_detection", "recognition", "classification", "kv_detection"]
        },
    },
    "lomin": {
        "general_detection": {
            "model_name": "detection",
            "route_name": "detection",
            "module_name": "detection",
        },
        "classification": {
            "model_name": "classification",
            "route_name": "classification",
            "module_name": "classification",
        },
        "recognition": {
            "model_name": "recognition",
            "route_name": "recognition",
            "module_name": "recognition",
        },
        "sequence": {"kv": ["classification", "general_detection", "recognition"]},
    },
    "kbcard": {
        "general_detection": {
            "model_name": "general",
            "route_name": "detection",
            "module_name": "detection",
        },
        "classification": {
            "model_name": "longinus",
            "route_name": "classification",
            "module_name": "classification",
        },
        "recognition": {
            "model_name": "tiamo",
            "route_name": "recognition",
            "module_name": "recognition",
        },
        "sequence": {"kv": ["classification", "general_detection", "recognition"]},
    },
}
model_mapping_table = {"보험금청구서": "agammoto", "처방전": "duriel"}
route_mapping_table = {"보험금청구서": "agammoto", "처방전": "duriel"}


inference_pipeline: Dict[str, Dict] = inference_pipeline_list.get(settings.CUSTOMER)  # type: ignore


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
    # Apply doc type hint
    hint = inputs.get("hint", {})
    if hint is not None and hint.get("doc_type") is not None:
        doc_type_hint = hint.get("doc_type", {})
        doc_type_hint = DocTypeHint(**doc_type_hint)
        cls_hint_result = apply_cls_hint(doc_type_hint=doc_type_hint)
        response_log.update(apply_cls_hint_result=cls_hint_result)
        inputs["doc_type"] = cls_hint_result.get("doc_type")

    inference_start_time = datetime.now()
    response_log.update(inference_start_time=inference_start_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3])
    
    # TODO 추후 doc_type : route_name 매핑 정보 추가
    print(type(inputs["doc_type"]))
    # 고객사 doc_type -> 로민 doc_type
    lomin_doc_type = inputs["doc_type"]
    if lomin_doc_type != None and lomin_doc_type != "None":
        route_name = get_route_name(lomin_doc_type)
    # if inputs["doc_type"] == "FN-CB":
    #     route_name = "bill_enterprise"
    # # 처방전
    # if inputs["doc_type"] == "MD-PRS":
    #     route_name = "el"
    
    if route_name == "tocr":
        if lomin_doc_type == "KBL1-IC":
            inputs["template_json"] = settings.KBL1_IC_TEMPLATE_JSON
            
            inputs["template_images"] = {
                "0": {
                    "image_id": "template",
                    "image_path": "보험금청구서_template_1.png",
                    "image_bytes": settings.KBL1_IC_TEMPLATE_IMAGE_BASE64
                }
            }
            inputs["test_image_id"] = inputs.get("document_id")
            inputs["test_image_path"] = inputs.get("document_path")
        elif lomin_doc_type == "KBL1-PIC":
            inputs["template_json"] = settings.KBL1_PIC_TEMPLATE_JSON
            inputs["template_images"] = {
                "0": {
                    "image_id": "template_1",
                    "image_path": "개인정보동의서_템플릿_1.png",
                    "image_bytes": settings.KBL1_PIC_TEMPLATE_IMAGE_P1_BASE64
                },
                "1": {
                    "image_id": "template_2",
                    "image_path": "개인정보동의서_템플릿_2.png",
                    "image_bytes": settings.KBL1_PIC_TEMPLATE_IMAGE_P2_BASE64
                },
                "2": {
                    "image_id": "template_3",
                    "image_path": "개인정보동의서_템플릿_3.png",
                    "image_bytes": settings.KBL1_PIC_TEMPLATE_IMAGE_P3_BASE64
                }
            }
            
            inputs["test_image_id"] = inputs.get("document_id")
            inputs["test_image_path"] = inputs.get("document_path")

    ocr_response = client.post(
        f"{model_server_url}/{route_name}",
        json=inputs,
        timeout=settings.TIMEOUT_SECOND,
        headers={"User-Agent": "textscope core"},
    )
    
    ocr_response_json = ocr_response.json()
    if route_name == "tocr":
        ocr_response_json["kv"] = ocr_response_json.pop("result")
    
    inference_end_time = datetime.now()
    response_log.update(
        inference_end_time=inference_end_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
        inference_total_time=(inference_end_time - inference_start_time).total_seconds(),
    )
    logger.info(
        f"Inference time: {str((inference_end_time - inference_end_time).total_seconds())}"
    )
    return (ocr_response.status_code, ocr_response_json, response_log)


def gocr(
    client: Client,
    inputs: Dict,
    response_log: Dict,
    route_name: str = gocr_route,
) -> Tuple[int, Dict, Dict]:
    """gocr inference 요청"""
    
    inference_start_time = datetime.now()
    response_log.update(inference_start_time=inference_start_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3])

    # inputs["image_bytes"] = f"{get_image_bytes(inputs['image_id'], Path(inputs['image_path']))}"
    # inputs["image_bytes"] = get_image_bytes(inputs['document_id'], Path(inputs['document_path']))
    
    ocr_response = client.post(
        f"{model_server_url}/{gocr_route}",
        json=inputs,
        timeout=settings.TIMEOUT_SECOND,
        headers={"User-Agent": "textscope core"},
    )
    
    ocr_response_json = ocr_response.json()
    inference_end_time = datetime.now()
    response_log.update(
        inference_end_time=inference_end_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
        inference_total_time=(inference_end_time - inference_start_time).total_seconds(),
    )
    logger.info(
        f"Gocr Inference time: {str((inference_end_time - inference_end_time).total_seconds())}"
    )
    return (ocr_response.status_code, ocr_response_json, response_log)

def tensorrt(
    client: Client,
    inputs: Dict,
    response_log: Dict,
    task_id: str,
    route_name: str = gocr_route,
) -> Tuple[int, Dict, Dict]:
    """
        tensorrt 요청, 현재 rotate, detection, recognition가 통합되어있는 하나의 API로 요청을 날립니다.
        TODO로 나중에 rotate, detection, recognition이 분리 되면 이 부분도 분리 필요
    """
    
    inference_start_time = datetime.now()
    response_log.update(inference_start_time=inference_start_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3])

    # inputs["image_bytes"] = f"{get_image_bytes(inputs['image_id'], Path(inputs['image_path']))}"
    # inputs["image_bytes"] = get_image_bytes(inputs['document_id'], Path(inputs['document_path']))
    
    trt_response = client.post(
        f"{model_server_url}/{route_name}",
        json=inputs,
        timeout=settings.TIMEOUT_SECOND,
        headers={"User-Agent": "textscope core"},
    )
    
    trt_response_json = trt_response.json()
    inference_end_time = datetime.now()
    response_log.update(
        inference_end_time=inference_end_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
        inference_total_time=(inference_end_time - inference_start_time).total_seconds(),
    )
    logger.info(
        f"Gocr Inference time: {str((inference_end_time - inference_end_time).total_seconds())}"
    )
    return (trt_response.status_code, trt_response_json, response_log)

def cls(
    client: Client,
    inputs: Dict,
    response_log: Dict,
    task_id: str,
    route_name: str = cls_route,
) -> Tuple[int, Dict, Dict]:
    """cls 요청에 대해 inference와 pp를 수행한 결과를 return 합니다."""
    
    inference_start_time = datetime.now()
    response_log.update(inference_start_time=inference_start_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3])

    # cls inference 요청
    cls_inference_response = client.post(
        f"{model_server_url}/{route_name}",
        json=inputs,
        timeout=settings.TIMEOUT_SECOND,
        headers={"User-Agent": "textscope core"},
    )
    
    ocr_response_json = cls_inference_response.json()
    
    inference_end_time = datetime.now()
    response_log.update(
        inference_end_time=inference_end_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
        inference_total_time=(inference_end_time - inference_start_time).total_seconds(),
    )
    logger.info(
        f"Cls Inference time: {str((inference_end_time - inference_end_time).total_seconds())}"
    )
    # cls inference server error check
    if cls_inference_response.status_code != 200:
        logger.error(f"Cls Inference error: {ocr_response_json}")
        status_code = 3501
        return (status_code, ocr_response_json, response_log)

    # TODO : pp input 데이터 가공
    
    # - convert preds to texts
    if (
        inputs.get("convert_preds_to_texts") is not None
        and "texts" not in ocr_response_json
    ):
        status_code, texts = pp.convert_preds_to_texts(
            client=client,
            rec_preds=ocr_response_json.get("rec_preds", []),
        )
        # pp 가공 에러케이스
        if status_code < 200 or status_code >= 400:
            status_code = 3503
            logger.error(f"pp.convert_preds_to_texts / error: {status_code}")
            return (status_code, ocr_response_json, response_log)
        ocr_response_json["texts"] = texts

    # get pp route
    post_processing_type = get_pp_api_name(cls_route)

    if post_processing_type is not None:
        logger.info(f"{task_id}-pp type:{post_processing_type}")

        text_list = ocr_response_json.get("texts", [])
        box_list = ocr_response_json.get("boxes", [])
        score_list = ocr_response_json.get("scores", [])
        class_list = ocr_response_json.get("classes", [])
        
        score_list = score_list if len(score_list) > 0 else [ 0.0 for i in range(len(text_list)) ]
        class_list = class_list if len(class_list) > 0 else [ "" for i in range(len(text_list)) ]

        pp_inputs = dict(
            texts=text_list,
            boxes=box_list,
            scores=score_list,
            classes=class_list,
            rec_preds=ocr_response_json.get("rec_preds"),
            id_type=ocr_response_json.get("id_type"),
            doc_type=ocr_response_json.get("doc_type"),
            image_height=ocr_response_json.get("image_height"),
            image_width=ocr_response_json.get("image_width"),
            relations=ocr_response_json.get("relations"),
            cls_score=ocr_response_json.get("cls_score"),
            task_id=task_id,
        )
        status_code, post_processing_results, response_log = pp.post_processing(
            client=client,
            task_id=task_id,
            response_log=response_log,
            inputs=pp_inputs,
            post_processing_type=post_processing_type,
        )
        if status_code < 200 or status_code >= 400:
            status_code = 3502
            logger.error(f"pp inference error / error: {status_code}")
            return status_code
        # logger.info(
        #     f'{task_id}-post-processed kv result:\n{pretty_dict(inference_results.get("kv", {}))}'
        # )
        if "texts" not in ocr_response_json:
            ocr_response_json["texts"] = post_processing_results["texts"]

    return (status_code, ocr_response_json, response_log)

ONLY_PP_TYPE= [
"GV-BC",
"GV-CFR",
"GV-ARR"
]


def kv(
    client: Client,
    inputs: Dict,
    hint : Dict,
    response_log: Dict,
    task_id: str,
    route_name: str,
) -> Tuple[int, Dict, Dict]:
    """kv 요청에 대해 inference와 pp를 수행한 결과를 return 합니다."""


    inference_start_time = datetime.now()
    response_log.update(inference_start_time=inference_start_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3])

    origin_doc_type = deepcopy(inputs["doc_type"])
    lomin_doc_type = inputs["doc_type"].doc_type_code
    if lomin_doc_type != None and lomin_doc_type != "None":
        route_name = get_route_name(lomin_doc_type)
        inputs["doc_type"] = lomin_doc_type
        
    # TODO: inference 여부 체크
    if lomin_doc_type not in ONLY_PP_TYPE:
        # get kv route
        if route_name != 'ocr_for_pp':
            """doc type hint를 적용하고 inference 요청"""
            # Apply doc type hint
            # if hint is not None and hint.get("doc_type") is not None and hint.get("doc_type")["use"]:
            #     doc_type_hint = hint.get("doc_type", {})
            #     doc_type_hint = DocTypeHint(**doc_type_hint)
            #     cls_hint_result = apply_cls_hint(doc_type_hint=doc_type_hint)
            #     response_log.update(apply_cls_hint_result=cls_hint_result)
            #     inputs["doc_type"] = cls_hint_result.get("doc_type")
            
            if route_name == "tocr":
                inputs["image_id"] = inputs.get("document_id")
                inputs["image_path"] = inputs.get("document_path")
                inputs["pp_end_point"] = 'kbl1_tocr'
                inputs['template'] = {}

                if lomin_doc_type == "KBL1-IC":
                    inputs['template']["template_json"] = settings.KBL1_IC_TEMPLATE_JSON
                    
                    inputs['template']["template_images"] = {
                        "0": {
                            "image_id": "template",
                            "image_path": "보험금청구서_template_1.png",
                            "image_bytes": settings.KBL1_IC_TEMPLATE_IMAGE_BASE64
                        }
                    }
                elif lomin_doc_type == "KBL1-PIC":
                    inputs['template']["template_json"] = settings.KBL1_PIC_TEMPLATE_JSON
                    inputs['template']["template_images"] = {
                        "0": {
                            "image_id": "template_1",
                            "image_path": "개인정보동의서_템플릿_1.png",
                            "image_bytes": settings.KBL1_PIC_TEMPLATE_IMAGE_P1_BASE64
                        },
                        "1": {
                            "image_id": "template_2",
                            "image_path": "개인정보동의서_템플릿_2.png",
                            "image_bytes": settings.KBL1_PIC_TEMPLATE_IMAGE_P2_BASE64
                        },
                        "2": {
                            "image_id": "template_3",
                            "image_path": "개인정보동의서_템플릿_3.png",
                            "image_bytes": settings.KBL1_PIC_TEMPLATE_IMAGE_P3_BASE64
                        }
                    }


            # kv inference 요청
            kv_inference_response = client.post(
                f"{model_server_url}/{route_name}",
                json=inputs,
                timeout=settings.TIMEOUT_SECOND,
                headers={"User-Agent": "textscope core"},
            )
            inference_end_time = datetime.now()

            logger.info(
                f"Kv Inference time: {str((inference_end_time - inference_end_time).total_seconds())}"
            )

            # kv inference server error check
            if kv_inference_response.status_code != 200 or type(kv_inference_response.json()) == str:
                logger.error(f"Kv Inference error: {kv_inference_response}")
                status_code = 3501
                return (status_code, kv_inference_response, response_log)
            
            inputs = kv_inference_response.json()
            
            if route_name == "tocr":
                inputs["kv"] = inputs.pop("result")
            
            response_log.update(
                inference_end_time=inference_end_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
                inference_total_time=(inference_end_time - inference_start_time).total_seconds(),
            )
            
            # TODO : tocr 케이스는 pp 없이 return
            if route_name == "tocr":
                return (kv_inference_response.status_code, inputs, response_log)

        # TODO : pp input 데이터 가공
    
        # - convert preds to texts
        if (
            inputs.get("convert_preds_to_texts") is not None
            and "texts" not in inputs
        ):
            status_code, texts = pp.convert_preds_to_texts(
                client=client,
                rec_preds=inputs.get("rec_preds", []),
            )
            # pp 가공 에러케이스
            if status_code < 200 or status_code >= 400:
                status_code = 3503
                logger.error(f"pp.convert_preds_to_texts / error: {status_code}")
                return (status_code, inputs, response_log)
            inputs["texts"] = texts

    # get pp route
    post_processing_type = get_pp_api_name(lomin_doc_type)

    if post_processing_type is not None:
        logger.info(f"{task_id}-pp type:{post_processing_type}")

        text_list = inputs.get("texts", [])
        box_list = inputs.get("boxes", [])
        score_list = inputs.get("scores", [])
        class_list = inputs.get("classes", [])
        
        score_list = score_list if len(score_list) > 0 else [ 0.0 for i in range(len(text_list)) ]
        class_list = class_list if len(class_list) > 0 else [ "" for i in range(len(text_list)) ]

        pp_inputs = dict(
            texts=text_list,
            boxes=box_list,
            scores=score_list,
            classes=class_list,
            rec_preds=inputs.get("rec_preds"),
            id_type=inputs.get("id_type"),
            doc_type=inputs.get("doc_type"),
            image_height=inputs.get("image_height"),
            image_width=inputs.get("image_width"),
            relations=inputs.get("relations"),
            cls_score=inputs.get("cls_score"),
            task_id=task_id,
        )
        status_code, post_processing_results, response_log = pp.post_processing(
            client=client,
            task_id=task_id,
            response_log=response_log,
            inputs=pp_inputs,
            post_processing_type=post_processing_type,
        )
        if status_code < 200 or status_code >= 400:
            status_code = 3502
            logger.error(f"pp server error / error: {status_code}")
            return (status_code, inputs, response_log)
        # logger.info(
        #     f'{task_id}-post-processed kv result:\n{pretty_dict(inference_results.get("kv", {}))}'
        # )
        if "texts" not in inputs:
            inputs["texts"] = post_processing_results["texts"]
        if inputs.get("route_name", None) != 'cls' and "tables" not in inputs and "tables" in post_processing_results:
            inputs["tables"] = post_processing_results["tables"]
        if inputs.get("route_name", None) != 'cls' and "result" not in inputs and "result" in post_processing_results:
            inputs["kv"] = post_processing_results.pop("result")

        inputs["doc_type"] = origin_doc_type

    return (status_code, inputs, response_log)



# TODO: multiple 함수 사용하도록 수정
def heungkuk_life(
    client: Client,
    inputs: Dict,
    response_log: Dict,
    route_name: str = "ocr",
) -> Tuple[int, Dict, Dict]:
    inference_start_time = datetime.now()
    task_id = inputs.get("task_id")
    logger.debug(f"{task_id}-inference pipeline start:\n{pretty_dict(inputs)}")

    # Rotate
    rectify = inputs.get("rectify", {})
    if rectify.get("rotation_90n", False) or rectify.get("rotation_fine", False):
        rotate_result = wrapper.rotate.longinus(client, inputs).get("response", {})
        inputs["angle"] = rotate_result.get("angle")
        logger.debug(f"{task_id}-rotate result:\n{pretty_dict(rotate_result)}")

    # General detection
    agamotto_result = wrapper.detection.agamotto(client, inputs).get("response", {})
    logger.debug(f"{task_id}-general detection result:\n{pretty_dict(agamotto_result)}")
    response_log.update(agamotto_result.get("response_log", {}))
    original_image_size = (
        agamotto_result.get("image_width"),
        agamotto_result.get("image_height"),
    )
    response_log.update(original_image_size=original_image_size)

    # Recognition
    tiamo_result = wrapper.recognition.tiamo(client, inputs, agamotto_result).get(
        "response", {}
    )
    response_log.update(tiamo_result.get("response_log", {}))
    if settings.SUBSTITUTE_SPCHAR_TO_ALPHA:
        removed_spchar_texts = substitute_spchar_to_alpha(tiamo_result["texts"])
        pred_encode_status, encoded_texts = pp.convert_texts_to_preds(
            client=client, texts=removed_spchar_texts
        )
        tiamo_result["texts"] = removed_spchar_texts
        tiamo_result["rec_preds"] = encoded_texts
    duriel_inputs = {**agamotto_result, "texts": tiamo_result["texts"]}

    # Classification
    duriel_classification_result = wrapper.classification.duriel(
        client, inputs, duriel_inputs
    ).get("response", {})
    logger.debug(
        f"{task_id}-classification result:\n{pretty_dict(duriel_classification_result)}"
    )
    response_log.update(duriel_classification_result.get("response_log", {}))

    doc_type = duriel_classification_result.get("doc_type")
    score_result = duriel_classification_result.get("scores")
    duriel_classification_result["score"] = score_result.get(doc_type)

    # Apply doc type hint
    hint = inputs.get("hint", {})
    if "doc_type" in hint:
        doc_type_hint = hint.get("doc_type", {})
        doc_type_hint = DocTypeHint(**doc_type_hint)
        cls_hint_result = apply_cls_hint(
            cls_result=duriel_classification_result, doc_type_hint=doc_type_hint
        )
        response_log.update(apply_cls_hint_result=cls_hint_result)
        doc_type = cls_hint_result.get("doc_type")
        logger.info(f"{task_id}-apply doc type hint: {cls_hint_result}")

    # Apply static doc type
    if inputs.get("static_doc_type", None) is not None:
        doc_type = inputs.get("static_doc_type", None)
    score_result = duriel_classification_result.get("scores")
    duriel_classification_result["score"] = score_result.get(doc_type)
    inputs["doc_type"] = doc_type

    # Kv detection
    kv_result: Dict = dict()
    if doc_type in settings.DURIEL_SUPPORT_DOCUMENT:
        kv_result = wrapper.detection.duriel(
            client, inputs, duriel_inputs, doc_type
        ).get("response", {})
        response_log.update(kv_result.get("response_log", {}))
        try:
            if doc_type == "HKL01-DT-PRS" and settings.FORCE_MERGE_DCC_BOX:
                status_code, post_processing_results, response_log = pp.post_processing(
                    client=client,
                    task_id=inputs.get("request_id", ""),
                    response_log=response_log,
                    inputs={
                        **kv_result,
                        "image_width": agamotto_result.get("image_width", 2000),
                        "image_height": agamotto_result.get("image_height", 2000),
                    },
                    post_processing_type="diseases_box",
                )
                tiamo_inputs = {
                    "image_path": inputs.get("image_path"),
                    "image_id": inputs.get("image_id"),
                    "page": inputs.get("page"),
                    "request_id": inputs.get("request_id"),
                }
                is_diseases_box = post_processing_results.get("result", {}).get(
                    "preds", {}
                )
                if is_diseases_box:
                    dcc_texts = (
                        wrapper.recognition.tiamo(client, tiamo_inputs, is_diseases_box)
                        .get("response", {})
                        .get("texts")
                    )
                    print("dcc texts: ", dcc_texts)
                    if (
                        status_code < 200
                        or status_code >= 400
                        or post_processing_results is None
                    ):
                        logger.info(
                            "Diseases box pp 과정에서 문제 발생, {}", post_processing_results
                        )
                    else:
                        classes = kv_result.get("classes", [])
                        dcc_indexes = list()
                        for i in range(len(classes)):
                            if "HKL01-KV-DCC" == classes[i]:
                                dcc_indexes.append(i)
                        for index in sorted(dcc_indexes, reverse=True):
                            del kv_result["classes"][index]
                            del kv_result["scores"][index]
                            del kv_result["texts"][index]
                            del kv_result["boxes"][index]

                        post_processed_results = post_processing_results.get(
                            "result", {}
                        ).get("preds")
                        kv_result["classes"].extend(
                            post_processed_results.get("classes")
                        )
                        kv_result["scores"].extend(post_processed_results.get("scores"))
                        kv_result["texts"].extend(dcc_texts)
                        kv_result["boxes"].extend(post_processed_results.get("boxes"))
                        logger.info("Diseases pp result, {}", post_processing_results)
        except Exception:
            logger.exception("DCC pp")

    elif doc_type in settings.INSURANCE_SUPPORT_DOCUMENT:
        kv_result = wrapper.detection.agamotto(client, inputs).get("response", {})
        response_log.update(kv_result.get("response_log", {}))
        texts = (
            wrapper.recognition.tiamo(client, inputs, kv_result)
            .get("response", {})
            .get("texts")
        )
        kv_result["texts"] = texts
    if kv_result:
        kv_result["rec_preds"] = tiamo_result["rec_preds"]
        if "status_code" not in kv_result:
            kv_result["status_code"] = 200
    logger.info(f"{task_id}-kv result:\n{pretty_dict(kv_result)}")
    ocr_response = dict(
        boxes=agamotto_result.get("boxes"),
        scores=agamotto_result.get("scores"),
        classes=agamotto_result.get("classes"),
        angle=inputs.get("angle", 0.0),
        texts=tiamo_result.get("texts"),
        rec_preds=tiamo_result.get("rec_preds"),
        kv_result=kv_result,
        recognition_result=tiamo_result,
        classification_result=duriel_classification_result,
        class_score=duriel_classification_result.get("score", 0.0),
        image_height=agamotto_result.get("image_height"),
        image_width=agamotto_result.get("image_width"),
        id_type=kv_result.get("id_type", None),
        doc_type=doc_type,
        apply_cls_hint_result=cls_hint_result,
    )

    inference_end_time = datetime.now()
    logger.info(
        f"Inference time: {str((inference_end_time - inference_start_time).total_seconds())}"
    )
    response_log.update(
        dict(
            inference_request_start_time=inference_start_time.strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            inference_request_end_time=inference_end_time.strftime("%Y-%m-%d %H:%M:%S"),
            inference_request_time=inference_end_time - inference_start_time,
        )
    )
    logger.debug(f"{task_id}-output:\n{pretty_dict(ocr_response)}")
    kv_result_status_code: int = kv_result.get("status_code", 400)
    return (kv_result_status_code, ocr_response, response_log)

def get_route_name(doc_type: str):
    '''
    doc_type에 따라 inference 서버의 어떤 api를 call할지 return 합니다. 
    '''
    if doc_type == "FN-CB":
        return "bill_enterprise"
    for model in MODEL_DOC_TYPE_LIST.keys():
        if doc_type in get_model_doc_type_list(model):
            return model
    return None    

    # elif doc_type in get_model_doc_type_list("el"):
    #     return "el"
    # elif doc_type in get_model_doc_type_list("kv"):
    #     return "kv"
    # elif doc_type in get_model_doc_type_list("ocr_for_pp"):
    #     return "ocr_for_pp"
    # return doc_type

MODEL_DOC_TYPE_LIST = {
    "el" : ["MD-PRS", "MD-MED", "MD-MB", "MD-CPE", "KBL-10", "KBL1-11", "KBL1-12", "KBL1-13"],
    "kv" : [    "MD-CS", "MD-DN", "MD-CMT", "MD-CAD", "MD-MC", "MD-COT", 
                "KBL1-04", "KBL1-05", "KBL1-06", "KBL1-07", "KBL1-08", "KBL1-09"],
    "ocr_for_pp" : ["GV-CFR","GV-BC", "GV-ARR", "KBL1-01", "KBL1-02", "KBL1-03"],
    "tocr": ["KBL1-IC", "KBL1-PIC"]
}

# 모델에 해당하는 doc_type_list를 반환합니다. 
def get_model_doc_type_list(model: str):
    return MODEL_DOC_TYPE_LIST[model]

