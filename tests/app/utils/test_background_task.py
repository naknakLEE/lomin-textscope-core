import sys
from tests.resource import config
from tests.resource.common import logging
sys.modules['app.config'] = config
sys.modules['app.utils.logging'] = logging

from app.utils.background_task import QueueBackGroundTask
import pytest

import asyncio

@pytest.fixture(scope="session")
def init_queue():
    yield QueueBackGroundTask()

def test_queue_init(init_queue: QueueBackGroundTask):
    assert init_queue.bg_progress_cnt == 0
    assert init_queue.bg_tasks_queue.qsize() == 0

# def async_func():
#     asyncio.sleep(5.0)
#     return 3

# async def create_event_loop():
#     tasks = list()
#     tasks.append(asyncio.create_task(async_func(1,2)))
#     tasks.append(asyncio.create_task(async_func(3,4)))
#     tasks.append(asyncio.create_task(async_func(5,6)))
#     await asyncio.wait(tasks)

# @pytest.mark.asyncio
# def test_queue_add_task(init_queue: QueueBackGroundTask):
#     # asyncio.new_event_loop()
#     # init_queue.add_task(print_sum, 1, 2)
    
#     # init_queue.add_task(async_func, 1, 2)
#     # init_queue.add_task(async_func, 3, 4)
#     # init_queue.add_task(async_func, 5, 6)
#     # init_queue.add_task(create_event_loop)

#     # init_queue.add_task(asyncio.create_task(async_func(1,2)))
#     # init_queue.add_task(asyncio.create_task(async_func(3,4)))
#     # init_queue.add_task(asyncio.create_task(async_func(5,6)))
#     # init_queue.add_task(async_func,3,4)
#     # init_queue.add_task(async_func,5,6)
#     init_queue.add_task(async_func)
#     init_queue.add_task(async_func)
#     init_queue.add_task(async_func)


#     assert init_queue.bg_progress_cnt == 2
#     assert init_queue.bg_tasks_queue.qsize() == 3


