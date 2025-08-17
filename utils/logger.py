import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional
import os

class Logger:
    """
    A centralized logger utility for the application.
    Supports console and file logging with different levels.
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls, name: str = "AIEduHackerton"):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
        return cls._instance
    
    def __init__(self, name: str = "AIEduHackerton"):
        if self._initialized:
            return
            
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Prevent duplicate handlers
        if not self.logger.handlers:
            self._setup_handlers()
        
        self._initialized = True
    
    def _setup_handlers(self):
        """Setup console and file handlers with appropriate formatters"""
        
        # Create logs directory if it doesn't exist
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        
        # File handler for all logs
        file_handler = logging.FileHandler(
            log_dir / f"app_{datetime.now().strftime('%Y%m%d')}.log",
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        
        # Error file handler
        error_handler = logging.FileHandler(
            log_dir / f"error_{datetime.now().strftime('%Y%m%d')}.log",
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)
        
        # Add handlers to logger
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(error_handler)
    
    def debug(self, message: str, extra: Optional[dict] = None):
        """Log debug message"""
        self.logger.debug(message, extra=extra)
    
    def info(self, message: str, extra: Optional[dict] = None):
        """Log info message"""
        self.logger.info(message, extra=extra)
    
    def warning(self, message: str, extra: Optional[dict] = None):
        """Log warning message"""
        self.logger.warning(message, extra=extra)
    
    def error(self, message: str, exc_info: bool = False, extra: Optional[dict] = None):
        """Log error message"""
        self.logger.error(message, exc_info=exc_info, extra=extra)
    
    def critical(self, message: str, exc_info: bool = False, extra: Optional[dict] = None):
        """Log critical message"""
        self.logger.critical(message, exc_info=exc_info, extra=extra)
    
    def exception(self, message: str, extra: Optional[dict] = None):
        """Log exception with traceback"""
        self.logger.exception(message, extra=extra)
    
    def set_level(self, level: str):
        """Set logging level dynamically"""
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        if level.upper() in level_map:
            self.logger.setLevel(level_map[level.upper()])
        else:
            self.warning(f"Invalid log level: {level}")

# Convenience functions for easy usage
def get_logger(name: str = "AIEduHackerton") -> Logger:
    """Get logger instance"""
    return Logger(name)

def debug(message: str, extra: Optional[dict] = None):
    """Log debug message using default logger"""
    get_logger().debug(message, extra)

def info(message: str, extra: Optional[dict] = None):
    """Log info message using default logger"""
    get_logger().info(message, extra)

def warning(message: str, extra: Optional[dict] = None):
    """Log warning message using default logger"""
    get_logger().warning(message, extra)

def error(message: str, exc_info: bool = False, extra: Optional[dict] = None):
    """Log error message using default logger"""
    get_logger().error(message, exc_info, extra)

def critical(message: str, exc_info: bool = False, extra: Optional[dict] = None):
    """Log critical message using default logger"""
    get_logger().critical(message, exc_info, extra)

def exception(message: str, extra: Optional[dict] = None):
    """Log exception with traceback using default logger"""
    get_logger().exception(message, extra)

# Context manager for logging function execution
class LogExecutionTime:
    """Context manager to log function execution time"""
    
    def __init__(self, operation_name: str, logger_instance: Optional[Logger] = None):
        self.operation_name = operation_name
        self.logger = logger_instance or get_logger()
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.now()
        self.logger.debug(f"Starting operation: {self.operation_name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        if exc_type is None:
            self.logger.info(f"Operation '{self.operation_name}' completed in {duration:.2f}s")
        else:
            self.logger.error(f"Operation '{self.operation_name}' failed after {duration:.2f}s: {exc_val}")
        
        return False  # Don't suppress exceptions

# Decorator for logging function calls
def log_function_call(logger_instance: Optional[Logger] = None):
    """Decorator to log function calls with parameters and execution time"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger = logger_instance or get_logger()
            func_name = func.__name__
            
            # Log function call
            logger.debug(f"Calling function: {func_name}")
            
            try:
                with LogExecutionTime(f"function {func_name}", logger):
                    result = func(*args, **kwargs)
                logger.debug(f"Function {func_name} completed successfully")
                return result
            except Exception as e:
                logger.exception(f"Function {func_name} raised an exception: {str(e)}")
                raise
        
        return wrapper
    return decorator