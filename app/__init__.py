import ray
from psutil import cpu_count
if not ray.is_initialized():
    ray.init(num_cpus=cpu_count(logical=True), dashboard_host="0.0.0.0")
