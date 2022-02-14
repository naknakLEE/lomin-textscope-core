from typing import Dict

from app.utils.logging import logger
from app.common.const import get_settings


settings = get_settings()
kv_hint_cer_threshold = settings.KV_HINT_CER_THRESHOLD
cls_hint_score_threshold = settings.CLS_HINT_SCORE_THRESHOLD


def apply_cls_hint(doc_type_hint: Dict, cls_result: Dict = {}) -> Dict:
    logger.info("Start apply cls hint")
    is_hint_used = False
    is_hint_trust = doc_type_hint.get("trust", False)
    if doc_type_hint is None:
        logger.info("Doc type hint is None")
    else:
        score = cls_result.get("score", 0.0)
        use = doc_type_hint.get("use", False)
        trust = doc_type_hint.get("trust", False)
        if (use and trust) or (use and score < cls_hint_score_threshold):
            hint_doc_type = doc_type_hint.get("doc_type")
            logger.info(
                "Change doc type from {} to {}",
                cls_result.get("doc_type", "None"),
                hint_doc_type,
            )
            cls_result["doc_type"] = hint_doc_type
            is_hint_used = True
    logger.info("End apply cls hint")
    return {
        "doc_type": cls_result.get("doc_type", "None"),
        "is_hint_used": is_hint_used,
        "is_hint_trusted": is_hint_trust,
    }
