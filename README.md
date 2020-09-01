Asyncio Time Travel Loop
========================

Intro
-----

Asyncio Time Travel Loop allows you to test asyncio code that waits or sleeps,
without actually waiting or sleeping.

At the same time, you don't have to bother thinking about how the time
advances. Your code should work exactly the same with TimeTravelLoop as it works
with a normal asyncio events loop.

Example: Assume that you have a code that waits 1000 seconds, and you want to
tests that code. Instead of actually waiting 1000 seconds, you could use
TimeTravelLoop:

```python
import asyncio
from asyncio_time_travel import TimeTravelLoop

SLEEP_TIME = 1000

tloop = TimeTravelLoop()

async def inner_coro():
    # Sleep for a long time:
    await asyncio.sleep(SLEEP_TIME, loop=tloop)

tloop.run_until_complete(inner_coro())
```

This code completes immediately.

See some of the [tests](https://github.com/realcr/asyncio_time_travel/blob/master/asyncio_time_travel/tests/test_time_travel_loop.py) for more advanced examples of what TimeTravelLoop can do.

Installation
------------
Run:
```bash
pip install asyncio-time-travel
```
You can also find the package at https://pypi.python.org/pypi/asyncio-time-travel .

Tests
-----

Run (Inside asyncio_time_travel dir):
```bash
pytest
```

If you haven't yet heard of [pytest](http://pytest.org), it's your lucky day :)


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

- It might be possible to integrate this code into asyncio.test_utils in some
  way.
