import pytest
import asyncio

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

    @asyncio.coroutine
    def inner_cor():
        for i in range(NUM_SLEEPS):
            yield from asyncio.sleep(SLEEP_TIME,loop=tloop)

    # Expected time for running:
    total_time = SLEEP_TIME * NUM_SLEEPS

    # This should work correctly:
    tloop.run_until_complete(asyncio.wait_for(\
            inner_cor(),timeout=total_time + 1,loop=tloop))

    run_until_timeout(\
            inner_cor(),loop=tloop,timeout=total_time + 1)

    with pytest.raises(asyncio.futures.TimeoutError):
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

    @asyncio.coroutine
    def inner_cor():
        # Add result 0:
        add_res(0)

        task1 = asyncio.async(asyncio.sleep(delay=SLEEP_TIME*3,loop=tloop),loop=tloop)
        task2 = asyncio.async(asyncio.sleep(delay=SLEEP_TIME*1,loop=tloop),loop=tloop)
        task3 = asyncio.async(asyncio.sleep(delay=SLEEP_TIME*4,loop=tloop),loop=tloop)
        task4 = asyncio.async(asyncio.sleep(delay=SLEEP_TIME*2,loop=tloop),loop=tloop)

        task1.add_done_callback(lambda x:add_res(1))
        task2.add_done_callback(lambda x:add_res(2))
        task3.add_done_callback(lambda x:add_res(3))
        task4.add_done_callback(lambda x:add_res(4))

        tasks = [task1,task2,task3,task4]

        # Wait for all the tasks to complete:
        yield from asyncio.wait(tasks,loop=tloop,timeout=None)

    # Expected time for running:
    total_time = (SLEEP_TIME * 4) + 1

    run_until_timeout(inner_cor(),loop=tloop,timeout=total_time)
    tloop.close()

    assert res_list == [0,2,4,1,3]

