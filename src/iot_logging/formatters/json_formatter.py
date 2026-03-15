"""JSON formatter that excludes None values from output."""

from pythonjsonlogger.json import JsonFormatter
from iot_logging.context import context


class StructuredJsonFormatter(JsonFormatter):
    """
    Structured JSON formatter that excludes None values from output.

    Automatically injects context variables (request_id, request_method,
    request_path, task_id, task_name) into every log record so all services
    produce consistent structured logs without manual extra= passing.
    """

    def add_fields(self, log_record, record, message_dict):
        """Add fields to log record, injecting context and excluding None values."""
        super().add_fields(log_record, record, message_dict)

        # Inject context variables (only if not already set by explicit extra={})
        for key, value in context.get_all_non_null().items():
            if key not in log_record:
                log_record[key] = value

        # Remove None values from the log record by iterating over a copy of keys
        for key in list(log_record.keys()):
            if log_record[key] is None:
                del log_record[key]
