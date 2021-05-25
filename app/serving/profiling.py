import numpy as np
import cv2
import cProfile, pstats
import sys 
sys.path.append("/workspace/app")

from pyinstrument import Profiler

from common.const import get_settings
from serving.generate_bentoml_multiple_model import multi_model_service

settings = get_settings()
if settings.PROFILING is not None:
    img = np.expand_dims(cv2.imread("/workspace/others/000000000000000IMG_4831.jpg"), axis=0)
    multi_model_service.inference(img)
if settings.PROFILING == 'cProfile':
    profiler = cProfile.Profile()
    profiler.enable()
    multi_model_service.inference(img)
    profiler.disable()
    stats = pstats.Stats(profiler).sort_stats("tottime")
    stats.strip_dirs()
    stats.print_stats()
elif settings.PROFILING == 'pyinstrument':
    profiler = Profiler()
    profiler.start()
    multi_model_service.inference(img)
    profiler.stop()
    print(profiler.output_text(unicode=True, color=True, show_all=True))

    # visualize in jupyter notebook
    # %load_ext snakeviz
    # %snakeviz multi_model_service.inference(img)