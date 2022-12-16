import typing
import asyncio
from queue import SimpleQueue
from app import hydra_cfg
from app.utils.logging import logger
from starlette.concurrency import run_in_threadpool


class CustomTask: 
    def __init__(
        self, func: typing.Callable, *args: typing.Any, **kwargs: typing.Any
    ) -> None:
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.is_async = asyncio.iscoroutinefunction(func)
    
class QueueBackGroundTask:
    def __init__(
        self
    ) -> None:
        self.bg_tasks_queue = SimpleQueue()
        self.bg_progress_cnt = 0
        logger.info(f"==================> CustomQueueSize initialization")

    def add_task(
        self, func: typing.Callable, *args: typing.Any, **kwargs: typing.Any
    ) -> None:
        task = CustomTask(func, *args, **kwargs)
        self.bg_tasks_queue.put_nowait(task)
        logger.info(f"==================> Current QueueSize:{self.bg_tasks_queue.qsize()} & Processing Task Size:{self.bg_progress_cnt}")
        if self.bg_progress_cnt >= hydra_cfg.document.bg_limit_task: return

        asyncio.create_task(self.__do_task())
    
    async def __do_task(
        self
    ) -> None:
        bg_progress_task = self.bg_tasks_queue.get_nowait()        
        self.bg_progress_cnt += 1

        logger.debug(f"==================> Background Task Start") 
        try:
            if bg_progress_task.is_async:
                await bg_progress_task.func(*bg_progress_task.args, **bg_progress_task.kwargs)
            else:
                await run_in_threadpool(bg_progress_task.func, *bg_progress_task.args, **bg_progress_task.kwargs)     
        except Exception as exc:       
            logger.error(exc, exc_info=True)
        logger.debug(f"==================> Background Task Finish")                              

        self.bg_progress_cnt -= 1
        if self.bg_tasks_queue.empty(): return

        asyncio.create_task(self.__do_task())

