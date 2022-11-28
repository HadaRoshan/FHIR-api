import sys
from loguru import logger


def patch(logger_method):
    """
    function extends loguru internal function to bind kwargs to extra parameter
    kwargs   :   key word args passed at the time of logging , all parameters except message
    """

    def patched(self, message, *args, **kwargs):
        self = self.opt(depth=1).bind(**kwargs)
        logger_method(self, message, *args, **kwargs)

    return patched


for log_method in ("trace", "debug", "info", "error", "warning", "critical"):
    method = getattr(logger.__class__, log_method)
    setattr(logger.__class__, log_method, patch(method))


def log_format(record):
    """format the log message with the string 'format_'"""
    format_ = 'time={time}   loglevel={level}   filename={name}   line={line}   message="{message}"  '
    if "action" in record["extra"].keys():
        format_ += 'action="{extra[action]}"  '
    if "status" in record["extra"].keys():
        format_ += 'status="{extra[status]}"  '
    if "detail" in record["extra"].keys():
        format_ += 'detail="{extra[detail]}"  '
    if "exception" in record["extra"].keys():
        format_ += 'exception="{extra[exception]}"  '
    if "tracing" in record["extra"].keys() and record["extra"]["tracing"]:
        record["extra"]["span_id"] = hex(record["extra"]["tracing"].span_id).lstrip("0x")
        record["extra"]["trace_id"] = hex(record["extra"]["tracing"].trace_id).lstrip("0x")
        format_ += 'span_id="{extra[span_id]}  trace_id="{extra[trace_id]}"  '
    for keys in record["extra"].keys():
        if keys not in {"action", "status", "detail", "exception", "tracing", "span_id", "trace_id"}:
            format_ += f'{keys}="{{extra[{keys}]}}"   '
    return format_ + "\n"


logger.remove()
logger.add(sys.stderr, format=log_format)


def setup_logging(log_file_path: str):
    """
    log file handler to the sink location
    rotation   :  time of new file creation
    format     :  format of the log message
    log_file_path: path of the log file to be stored
    """
    logger.add(sink=log_file_path, rotation="00:00", format=log_format)
