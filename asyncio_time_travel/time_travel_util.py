import collections
import heapq
import selectors
from asyncio import base_events, events


# A class to manage set of next events:
class NextTimers:
    def __init__(self):
        # Timers set. Used to check uniqueness:
        self._timers_set = set()
        # Timers heap. Used to get the closest timer event:
        self._timers_heap = []

    def add(self, when):
        """
        Add a timer (Future event).
        """
        # We don't add a time twice:
        if when in self._timers_set:
            return

        # Add to set:
        self._timers_set.add(when)
        # Add to heap:
        heapq.heappush(self._timers_heap, when)

    def is_empty(self):
        return len(self._timers_set) == 0

    def pop_closest(self):
        """
        Get closest event timer. (The one that will happen the soonest).
        """
        if self.is_empty():
            raise IndexError("NextTimers is empty")

        when = heapq.heappop(self._timers_heap)
        self._timers_set.remove(when)

        return when


# Based on TestSelector from asyncio.test_utils:
class TestSelector(selectors.BaseSelector):
    def __init__(self):
        self.keys = {}

    def register(self, fileobj, events, data=None):
        key = selectors.SelectorKey(fileobj, 0, events, data)
        self.keys[fileobj] = key
        return key

    def unregister(self, fileobj):
        return self.keys.pop(fileobj)

    def select(self, timeout=None):
        return []

    def get_map(self):
        return self.keys


# Based on TestLoop from asyncio.test_utils:
class TimeTravelLoop(base_events.BaseEventLoop):
    """
    Loop for unittests. Passes time without waiting, but makes sure events
    happen in the correct order.
    """

    def __init__(self):
        super().__init__()

        self._time = 0
        self._clock_resolution = 1e-9
        self._timers = NextTimers()
        self._selector = TestSelector()

        self.readers = {}
        self.writers = {}
        self.reset_counters()

    def time(self):
        return self._time

    def advance_time(self, advance):
        """Move test time forward."""
        if advance:
            self._time += advance

    def add_reader(self, fd, callback, *args):
        self.readers[fd] = events.Handle(callback, args, self)

    def remove_reader(self, fd):
        self.remove_reader_count[fd] += 1
        if fd in self.readers:
            del self.readers[fd]
            return True
        else:
            return False

    def assert_reader(self, fd, callback, *args):
        assert fd in self.readers, "fd {} is not registered".format(fd)
        handle = self.readers[fd]
        assert handle._callback == callback, "{!r} != {!r}".format(
            handle._callback, callback
        )
        assert handle._args == args, "{!r} != {!r}".format(handle._args, args)

    def add_writer(self, fd, callback, *args):
        self.writers[fd] = events.Handle(callback, args, self)

    def remove_writer(self, fd):
        self.remove_writer_count[fd] += 1
        if fd in self.writers:
            del self.writers[fd]
            return True
        else:
            return False

    def assert_writer(self, fd, callback, *args):
        assert fd in self.writers, "fd {} is not registered".format(fd)
        handle = self.writers[fd]
        assert handle._callback == callback, "{!r} != {!r}".format(
            handle._callback, callback
        )
        assert handle._args == args, "{!r} != {!r}".format(handle._args, args)

    def reset_counters(self):
        self.remove_reader_count = collections.defaultdict(int)
        self.remove_writer_count = collections.defaultdict(int)

    def _run_once(self):
        super()._run_once()
        # Advance time only when we finished everything at the present:
        if len(self._ready) == 0:
            if not self._timers.is_empty():
                self._time = self._timers.pop_closest()
                # print('time:',self._time,'timers:',self._timers._timers_set)

    def call_at(self, when, callback, *args, **kwargs):
        self._timers.add(when)
        return super().call_at(when, callback, *args, **kwargs)

    def _process_events(self, event_list):
        return

    def _write_to_self(self):
        pass
