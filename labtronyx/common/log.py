import logging
from logging.handlers import BufferingHandler

__all__ = ['RotatingMemoryHandler', 'CallbackLogHandler']


class RotatingMemoryHandler(BufferingHandler):
    def emit(self, record):
        self.buffer.append(record)
        if len(self.buffer) > self.capacity:
            del self.buffer[0]

    def getBuffer(self):
        return [self.format(record) for record in self.buffer]


class CallbackLogHandler(logging.Handler):
    def __init__(self, callback):
        logging.Handler.__init__(self)
        self._callback = callback

    def emit(self, record):
        self._callback(self.format(record))
