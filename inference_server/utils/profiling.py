import numpy as np
import cv2

from inference_server.common.const import get_settings
from inference_server.generate_idcard_model_service import multi_model_service

settings = get_settings()
if settings.PROFILING_TOOL is not None:
    img = np.expand_dims(cv2.imread("test.jpg"), axis=0)
    multi_model_service.inference(img)

if settings.PROFILING_TOOL == "cProfile":
    import cProfile
    import pstats

    profiler = cProfile.Profile()
    profiler.enable()
    multi_model_service.inference(img)
    profiler.disable()
    stats = pstats.Stats(profiler).sort_stats("tottime")
    stats.strip_dirs()
    stats.print_stats()
elif settings.PROFILING_TOOL == "pyinstrument":
    from pyinstrument import Profiler

    profiler = Profiler()
    profiler.start()
    multi_model_service.inference(img)
    profiler.stop()
    print(profiler.output_text(unicode=True, color=True, show_all=True))
