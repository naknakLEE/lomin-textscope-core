from typing import Dict, Optional, Any

from app.utils.logging import logger
from app.models import DocTypeHint
from app.common.const import get_settings


settings = get_settings()
kv_hint_cer_threshold = settings.KV_HINT_CER_THRESHOLD
cls_hint_score_threshold = settings.CLS_HINT_SCORE_THRESHOLD


def apply_cls_hint(
    doc_type_hint: Optional[DocTypeHint],
    cls_result: Dict = {},
    hint_threshold: float = cls_hint_score_threshold,
) -> Dict:
    score = cls_result.get("score", 0.0)
    result: Dict[str, Any] = {
        "doc_type": "None",
        "confidence": score,
        "is_hint_used": False,
        "is_hint_trusted": False,
    }
    if doc_type_hint is None:
        logger.info("Doc type hint is None")
        return result
    logger.debug("Start apply cls hint")
    hint_doc_type = doc_type_hint.doc_type
    # use = doc_type_hint.use
    trust = doc_type_hint.trust
    # if not use:
    #     logger.info("hint use is False")
    if not cls_result and not trust:
        logger.info("classification result is not exist and hint trust is False")
    elif trust:  # trust=True, cls_result is exist | trust=True, cls_result is not exist
        result["confidence"] = 1.0
        logger.debug(f"Change doc type to reliable {hint_doc_type}")
        result.update(doc_type=hint_doc_type, is_hint_used=True, is_hint_trusted=True)
    elif score < hint_threshold:  # trust=False, cls_result is not exist
        logger.debug(
            "Change doc type from {} to {}".format(
                cls_result.get("doc_type", "None"),
                hint_doc_type,
            )
        )
        result["doc_type"] = hint_doc_type
        result["is_hint_used"] = True
    else:
        result["doc_type"] = cls_result.get("doc_type", None)
    logger.debug("End apply cls hint")
    logger.debug(result)
    return result
