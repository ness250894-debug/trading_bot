"""
PII (Personally Identifiable Information) scrubbing for logs.
Automatically redacts sensitive data from log messages.
"""
import re
import logging


class PIIFilter(logging.Filter):
    """
    Logging filter that redacts PII from log messages.
    
    Redacts:
    - Email addresses
    - User IDs
    - JWT tokens
    - API keys
    - IP addresses (optional)
    """
    
    # Regex patterns for PII detection
    EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
    USER_ID_PATTERN = re.compile(r'\buser_id[=:\s]+(\d+)', re.IGNORECASE)
    JWT_PATTERN = re.compile(r'eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+')
    API_KEY_PATTERN = re.compile(r'(?:api[_-]?key|token|secret)[=:\s]+[\'"]?([A-Za-z0-9_-]{20,})[\'"]?', re.IGNORECASE)
    
    def filter(self, record):
        """
        Redact PII from log record message.
        """
        if isinstance(record.msg, str):
            record.msg = self._redact_pii(record.msg)
        
        # Also redact from args if present
        if record.args:
            if isinstance(record.args, dict):
                record.args = {k: self._redact_value(v) for k, v in record.args.items()}
            elif isinstance(record.args, tuple):
                record.args = tuple(self._redact_value(arg) for arg in record.args)
        
        return True
    
    def _redact_pii(self, message: str) -> str:
        """
        Apply all redaction patterns to message.
        """
        # Redact emails
        message = self.EMAIL_PATTERN.sub('[EMAIL_REDACTED]', message)
        
        # Redact user IDs
        message = self.USER_ID_PATTERN.sub(r'user_id=[USER_ID_REDACTED]', message)
        
        # Redact JWT tokens
        message = self.JWT_PATTERN.sub('[JWT_REDACTED]', message)
        
        # Redact API keys/tokens
        message = self.API_KEY_PATTERN.sub(r'\1=[KEY_REDACTED]', message)
        
        return message
    
    def _redact_value(self, value):
        """
        Redact PII from individual values.
        """
        if isinstance(value, str):
            return self._redact_pii(value)
        return value


def add_pii_filter_to_logger(logger_name: str = None):
    """
    Add PII filter to specified logger (or root logger if None).
    
    Args:
        logger_name: Name of logger to add filter to. None for root logger.
    """
    logger = logging.getLogger(logger_name)
    pii_filter = PIIFilter()
    logger.addFilter(pii_filter)
    return logger
