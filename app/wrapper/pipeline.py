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
    route_name: str = "ocr",
) -> Tuple[int, Dict, Dict]:
    """doc type hint를 적용하고 inference 요청"""
    # Apply doc type hint
    hint = inputs.get("hint")
    if hint and hint.get("doc_type"):
        doc_type_hint = DocTypeHint(**hint.get("doc_type"))
        if doc_type_hint.use:
            cls_hint_result = apply_cls_hint(doc_type_hint=doc_type_hint, cls_result=inputs.get('cls_result', {}))
            response_log.update(apply_cls_hint_result=cls_hint_result)
            inputs["doc_type"] = cls_hint_result.get("doc_type")

    inference_start_time = datetime.now()
    response_log.update(inference_start_time=inference_start_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3])

    doc_type = inputs.get('doc_type', '')
    
    # input custom doc type convert lomin doc type
    reverse_doc_type: Dict = kdt_custom_mapping.get('REVERSE_DOC_TYPE')
    if reverse_doc_type.get(doc_type): 
        doc_type = reverse_doc_type.get(doc_type)
        inputs.update(doc_type=doc_type)

    # inferecne_server endpoint set
    custom_inference_endpoint: Dict = kdt_custom_mapping.get('KDT_ENDPOINT').get('SERVING')
    convert_route_name = custom_inference_endpoint.get(doc_type) if custom_inference_endpoint.get(doc_type) else route_name
    
    # endpoint가 tocr일경우 tocr에 맞는 input 만들기
    if convert_route_name == 'tocr':
        tocr_inputs: Dict = kdt_custom_mapping.get('KDT_TOCR').get(doc_type, "")
        
        # 1. template 이미지 setting
        template_images: Dict = tocr_inputs.get("template_images")
        for v in template_images.values():
            if v.get('is_apply'): continue
            image_name = v.get('image_path')
            file_path = Path(f"/workspace/app/assets/template_image/{image_name}")
            with file_path.open('rb') as file:
                image_data = file.read()
                image_data = base64.b64encode(image_data)
                success = save_upload_document(v.get('image_id'),image_name, image_data)
                if success: v.update(is_apply=True)                        
        # 2. test 이미지 setting                 
        tocr_inputs.update(test_image_id=inputs.get('image_id', ''))
        tocr_inputs.update(test_image_path=inputs.get('image_path', ''))

        # 3. inputs.update(tocr_inputs)             
        inputs = tocr_inputs 

    ocr_response = client.post(
        f"{model_server_url}/{convert_route_name}",
        json=inputs,
        timeout=settings.TIMEOUT_SECOND,
        headers={"User-Agent": "textscope core"},
    )
    
    inference_end_time = datetime.now()
    response_log.update(
        inference_end_time=inference_end_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
        inference_total_time=(inference_end_time - inference_start_time).total_seconds(),
    )
    logger.info(
        f"Inference time: {str((inference_end_time - inference_end_time).total_seconds())}"
    )
    return (ocr_response.status_code, ocr_response.json(), response_log)


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
