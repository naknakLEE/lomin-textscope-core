import asyncio
import typing

from queue import SimpleQueue
from starlette.concurrency import run_in_threadpool
from app import hydra_cfg
from app.utils.logging import logger


bg_tasks_queue = SimpleQueue()
bg_progress_cnt = 0

class CustomBackgroundTask:
    def __init__(
        self, func: typing.Callable, *args: typing.Any, **kwargs: typing.Any
    ) -> None:
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.is_async = asyncio.iscoroutinefunction(func)

    async def __call__(self) -> None:
        bg_progress_task:CustomBackgroundTask = bg_tasks_queue.get_nowait()

        global bg_progress_cnt  
        bg_progress_cnt += 1        
        if bg_progress_task.is_async:
            await bg_progress_task.func(*bg_progress_task.args, **bg_progress_task.kwargs)
        else:
            await run_in_threadpool(bg_progress_task.func, *bg_progress_task.args, **bg_progress_task.kwargs)        
        bg_progress_cnt -= 1     
        
        if bg_tasks_queue.empty(): return
        asyncio.create_task(self())       


class CustomBackgroundTaskList(CustomBackgroundTask):
    def __init__(self):
        logger.info(f"==================> CustomQueueSize initialization")

    def add_task(
        self, func: typing.Callable, *args: typing.Any, **kwargs: typing.Any
    ) -> None:
        task = CustomBackgroundTask(func, *args, **kwargs)
        bg_tasks_queue.put_nowait(task)
        logger.info(f"==================> Current QueueSize:{bg_tasks_queue.qsize()} & Processing Task Size:{bg_progress_cnt}")
        if bg_progress_cnt >= hydra_cfg.document.bg_limit_task: return
        asyncio.create_task(task())                

