Asyncio Time Travel Loop
========================

Intro
-----

Asyncio Time Travel Loop allows you to test asyncio code that waits or sleeps,
without actually waiting or sleeping.

At the same time, you don't have to bother thinking about how the time
advances. Your code should work exactly the same with TimeTravelLoop as it works
with a normal asyncio events loop.


Example. Assume that you have a code that waits 1000 seconds, and you want to
tests that code. Instead of actually waiting 1000 seconds, you could use
TimeTravelLoop:

```python
import asyncio
from time_travel_util import TimeTravelLoop

SLEEP_TIME = 1000

tloop = TimeTravelLoop()

@asyncio.coroutine
def inner_cor():
        # Sleep for a long time:
        yield from asyncio.sleep(SLEEP_TIME,loop=tloop)

tloop.run_until_complete(inner_cor())
```


This code completes immediately.

A more advanced example (From the tests):

```python
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
```

Tests
-----

Run: 
```bash
py.test
```

How does this work?
-------------------

TimeTravelLoop source is based on the source code of
asyncio.test_utils.TestLoop.

For each _run_once iteration of the loop, the following is done:
- Loop events are executed.
- Time is advanced to the closest scheduled event.

Using this method your code never waits, and at the same time the events
execute in the correct order.


Limitations
-----------

TimeTravelLoop is meant to be used with your tests, not for production code. In
particular, if your loop interacts with external events, bending time is not a
good idea (Time will advance differently outside of your loop).


Further work
------------

- The code might have bugs. If you find any issues, don't hesitate to fork or
open an issue. 

- It might also be possible to integrate this code into asyncio.test_utils in
  some way.
