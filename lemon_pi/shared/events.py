import logging
import time

logger = logging.getLogger(__name__)


class EventHandler:

    def handle_event(self, event, **kwargs):
        pass


class Event:

    # stop the logs getting too full : suppress repeat events in info log
    last_event = None
    last_event_count = 0
    instances = []

    def __init__(self, name="", suppress_logs=False, debounce_time=0):
        self.name = name
        for e in Event.instances:
            if e.name == name:
                raise Exception(f"redefinition of event {name}")
        Event.instances.append(self)
        # some events emit all the time so we suppress logging them consecutively
        self.suppress_logs = suppress_logs
        # some events prevent re-issue of the same event in a short space ot time
        self.debounce_time = debounce_time
        self.last_event_time = 0
        self.handlers = []

    def register_handler(self, handler:EventHandler):
        if handler not in self.handlers:
            self.handlers.append(handler)
        else:
            logger.error("{} attempted to register same handler twice {}", self.name, handler.__class__)

    def emit(self, **kwargs):
        if self == Event.last_event and self.suppress_logs:
            Event.last_event_count += 1
        else:
            if Event.last_event_count > 0:
                logger.info("suppressed ({}) {}".format(Event.last_event_count, Event.last_event.name))
            logger.info("emitting {}".format(self.name))
            Event.last_event_count = 0
        # prevent repeat emitting events if they have just happened
        now = time.time()
        if now - self.last_event_time > self.debounce_time:
            self.last_event_time = now
            Event.last_event = self
            # call all the registered handlers
            for handler in self.handlers:
                handler.handle_event(self, **kwargs)

    @classmethod
    def instance_iterator(cls):
        return Event.instances.__iter__()