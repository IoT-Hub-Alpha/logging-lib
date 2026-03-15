"""JSON formatter that excludes None values from output."""

from pythonjsonlogger import jsonlogger


class StructuredJsonFormatter(jsonlogger.JsonFormatter):
    """
    Structured JSON formatter that excludes None values from output.

    Produces clean, structured JSON logs with only relevant fields:
    - Request logs don't have task_id/task_name
    - Task logs don't have request_method/request_path
    - No wasteful null fields in JSON
    """

    def add_fields(self, log_record, record, message_dict):
        """Add fields to log record, excluding None values."""
        super().add_fields(log_record, record, message_dict)

        # Remove None values from the log record by iterating over a copy of keys
        for key in list(log_record.keys()):
            if log_record[key] is None:
                del log_record[key]
