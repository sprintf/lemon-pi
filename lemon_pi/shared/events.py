import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


class EventHandler:

    def handle_event(self, event, **kwargs):
        pass


class Event:

    # stop the logs getting too full : suppress repeat events in info log
    last_event = None
    last_event_count = 0

    def __init__(self, name="", suppress_logs=False):
        self.name = name
        # some events emit all the time so we suppress logging them consecutively
        self.suppress_logs = suppress_logs
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
        Event.last_event = self
        # call all the registered handlers
        for handler in self.handlers:
            handler.handle_event(self, **kwargs)