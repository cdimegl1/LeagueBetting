import logging
import logging.handlers

class _ColourFormatter(logging.Formatter):

    LEVEL_COLOURS = [
        (logging.DEBUG, '\x1b[32;1m'),
        (logging.INFO, '\x1b[34;1m'),
        (logging.WARNING, '\x1b[33;1m'),
        (logging.ERROR, '\x1b[31;1m'),
        (logging.CRITICAL, '\x1b[41;1m'),
    ]

    FORMATS = {
        level: logging.Formatter(
            f'\x1b[36;1m%(asctime)s\x1b[0m {colour}%(levelname)-8s\x1b[0m \x1b[35m%(pathname)s\x1b[0m %(message)s',
            '%m-%d %H:%M:%S',
        )
        for level, colour in LEVEL_COLOURS
    }

    def format(self, record):
        formatter = self.FORMATS.get(record.levelno)
        if formatter is None:
            formatter = self.FORMATS[logging.DEBUG]

        # Override the traceback to always print in red
        if record.exc_info:
            text = formatter.formatException(record.exc_info)
            record.exc_text = f'\x1b[31m{text}\x1b[0m'

        output = formatter.format(record)
        first_slash = output.find('/')
        py = output.find('.py')
        first_letter = output[first_slash:py].rfind('/') + first_slash + 1
        output = output[:first_slash] + output[first_letter:]

        # Remove the cache layer
        record.exc_text = None
        return output

handler = logging.StreamHandler()
formatter = _ColourFormatter()
handler.setFormatter(formatter)
handler.setLevel(logging.INFO)
_log = logging.getLogger('main')
_log.addHandler(handler)
_log.setLevel(logging.DEBUG)
file_handler = logging.handlers.RotatingFileHandler('../betting.log', maxBytes=10000000)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
_log.addHandler(file_handler)

