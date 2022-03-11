from app.common import settings

pp_server_url = f"http://{settings.PP_IP_ADDR}"

from app.wrapper import classification
from app.wrapper import detection
from app.wrapper import pp
from app.wrapper import recognition
from app.wrapper import rotate
from app.wrapper import pipeline


__all__ = ["classification", "detection", "pp", "recognition", "rotate", "pipeline"]
