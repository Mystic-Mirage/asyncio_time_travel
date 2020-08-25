import pytest
import asyncio

try:
    from asyncio.exceptions import TimeoutError
except ImportError:
    from asyncio.futures import TimeoutError

from ..time_travel_util import TimeTravelLoop


def run_until_timeout(cor,loop,timeout=None):
    """
    Run a given coroutine with timeout.
    """
    task_with_timeout = asyncio.wait_for(cor,timeout,loop=loop)
    loop.run_until_complete(task_with_timeout)


def test_time_travel_loop_basic_timeout():
    """
    Sleep a for a long time. Expect timeout when not enough time is given for
    the coroutine.
    """

    SLEEP_TIME = 0x1000
    NUM_SLEEPS = 5

    tloop = TimeTravelLoop()

    async def inner_cor():
        for i in range(NUM_SLEEPS):
            await asyncio.sleep(SLEEP_TIME,loop=tloop)

    # Expected time for running:
    total_time = SLEEP_TIME * NUM_SLEEPS

    # This should work correctly:
    tloop.run_until_complete(asyncio.wait_for(\
            inner_cor(),timeout=total_time + 1,loop=tloop))

    run_until_timeout(\
            inner_cor(),loop=tloop,timeout=total_time + 1)

    with pytest.raises(TimeoutError):
        run_until_timeout(inner_cor(),loop=tloop,timeout=total_time - 1)
    tloop.close()


def test_time_travel_loop_concurrent_sleep():
    """
    Create a few tasks that finish at different times.
    Expect the finish times to be of specific order.
    """

    # A long sleeping time:
    SLEEP_TIME = 0x1000

    # results list:
    res_list = []

    def add_res(res):
        """Add a result"""
        res_list.append(res)

    tloop = TimeTravelLoop()

    async def inner_cor():
        # Add result 0:
        add_res(0)

        task1 = asyncio.ensure_future(asyncio.sleep(delay=SLEEP_TIME*3,loop=tloop),loop=tloop)
        task2 = asyncio.ensure_future(asyncio.sleep(delay=SLEEP_TIME*1,loop=tloop),loop=tloop)
        task3 = asyncio.ensure_future(asyncio.sleep(delay=SLEEP_TIME*4,loop=tloop),loop=tloop)
        task4 = asyncio.ensure_future(asyncio.sleep(delay=SLEEP_TIME*2,loop=tloop),loop=tloop)

        task1.add_done_callback(lambda x:add_res(1))
        task2.add_done_callback(lambda x:add_res(2))
        task3.add_done_callback(lambda x:add_res(3))
        task4.add_done_callback(lambda x:add_res(4))

        tasks = [task1,task2,task3,task4]

        # Wait for all the tasks to complete:
        await asyncio.wait(tasks,loop=tloop,timeout=None)

    # Expected time for running:
    total_time = (SLEEP_TIME * 4) + 1

    run_until_timeout(inner_cor(),loop=tloop,timeout=total_time)
    tloop.close()

    assert res_list == [0,2,4,1,3]


def test_time_travel_loop_complex_order():
    """
    Build different points in time using coroutines that yield to other
    coroutines and asyncio.sleep. Make sure that the events are in the expected
    order.
    """

    # results list:
    res_list = []

    # List of async_tasks to wait for.
    async_tasks = []

    def add_res(res):
        """Add a result"""
        res_list.append(res)

    tloop = TimeTravelLoop()

    async def inner_cor():
        add_res(0)

        # Start cor_a:
        task = asyncio.ensure_future(cor_a(),loop=tloop)        # time=0

        asyncio.ensure_future(asyncio.sleep(delay=500,loop=tloop),loop=tloop)\
            .add_done_callback(lambda x:add_res(2))     # time=0 --> 500

        asyncio.ensure_future(asyncio.sleep(delay=1500,loop=tloop),loop=tloop)\
            .add_done_callback(lambda x:add_res(4))     # time=0  --> 1500

        # Wait for the longest task to complete:
        await asyncio.wait_for(task,timeout=None,loop=tloop)


    async def cor_a():
        add_res(1)                          # time=0
        await asyncio.sleep(1000,loop=tloop)      
        await cor_b()                  # time=1000

    async def cor_b():
        add_res(3)                          # time=1000
        await asyncio.sleep(1000,loop=tloop)
        add_res(5)                          # time=2000
        asyncio.ensure_future(asyncio.sleep(delay=500,loop=tloop),loop=tloop)\
            .add_done_callback(lambda x:add_res(8))     # time=2000 --> 2500
        await cor_c()


    async def cor_c():
        add_res(6)                          # time=2000
        await cor_d()
        await asyncio.sleep(1000,loop=tloop)      
        add_res(9)                          # time=3000

    async def cor_d():
        add_res(7)                          # time=2000

    # Expected time for running:
    total_time = (3000) + 1

    run_until_timeout(inner_cor(),loop=tloop,timeout=total_time)
    tloop.close()

    assert res_list == [0,1,2,3,4,5,6,7,8,9]
