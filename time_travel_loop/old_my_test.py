import asyncio
from time_travel_util import TimeTravelLoop

SLEEP_TIME = 1000

tloop = TimeTravelLoop()

@asyncio.coroutine
def inner_cor():
    # Sleep for a long time:
    yield from asyncio.sleep(SLEEP_TIME,loop=tloop)

tloop.run_until_complete(inner_cor())
