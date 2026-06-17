import sys
from pathlib import Path

import logging
import sys
import os
from datetime import datetime
from pathlib import Path

def setup_logger(
    name: str = 'cspm-misconfiguration-management',
    level: str = 'INFO',
    log_to_file: bool = True,
    log_to_console: bool = True,
    log_dir: str = 'logs',
    max_file_size: int = 10 * 1024 * 1024,
    backup_count: int = 5
) -> logging.Logger:
    
    logger = logging.getLogger(name)
    
    if logger.handlers:
        return logger
    
    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f'Invalid log level: {level}')
    logger.setLevel(numeric_level)
    
    detailed_format = '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s() - %(message)s'
    simple_format = '%(levelname)s - %(filename)s:%(lineno)d - %(message)s'
    
    detailed_formatter = logging.Formatter(
        detailed_format,
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    simple_formatter = logging.Formatter(
        simple_format,
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(simple_formatter)
        logger.addHandler(console_handler)
    
    if log_to_file:
        from logging.handlers import RotatingFileHandler
        
        log_path = Path(log_dir)
        log_path.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d')
        log_file = log_path / f'{name}_{timestamp}.log'
        
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        logger.addHandler(file_handler)
    
    logger.propagate = False
    
    return logger


def get_logger(name: str = None) -> logging.Logger:
    if name is None:
        frame = sys._getframe(1)
        name = frame.f_globals.get('__name__', 'unknown')
    
    return logging.getLogger(name)


def create_class_logger(
    class_name: str,
    level: str = 'INFO',
    log_to_file: bool = True,
    log_to_console: bool = True,
    log_dir: str = 'logs'
) -> logging.Logger:
    """
    Create a dedicated logger for a specific class with its own log file.
    
    Args:
        class_name: Name of the class (will be used in log file name)
        level: Log level (default: INFO)
        log_to_file: Whether to log to file
        log_to_console: Whether to log to console
        log_dir: Directory for log files
    
    Returns:
        Logger instance configured for the specific class
    """
    return setup_logger(
        name=class_name,
        level=level,
        log_to_file=log_to_file,
        log_to_console=log_to_console,
        log_dir=log_dir
    )


LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_TO_FILE = os.getenv('LOG_TO_FILE', 'false').lower() == 'true'  # Changed default to 'false'
LOG_TO_CONSOLE = os.getenv('LOG_TO_CONSOLE', 'true').lower() == 'true'
LOG_DIR = os.getenv('LOG_DIR', 'logs')


log = setup_logger(
    name='csmp-misconfiguration-management',
    level=LOG_LEVEL,
    log_to_file=LOG_TO_FILE,
    log_to_console=LOG_TO_CONSOLE,
    log_dir=LOG_DIR
)

def debug(msg: str, *args, **kwargs):
    log.debug(msg, *args, **kwargs)

def info(msg: str, *args, **kwargs):
    log.info(msg, *args, **kwargs)

def warning(msg: str, *args, **kwargs):
    log.warning(msg, *args, **kwargs)

def error(msg: str, *args, **kwargs):
    log.error(msg, *args, **kwargs)

def critical(msg: str, *args, **kwargs):
    log.critical(msg, *args, **kwargs)

def exception(msg: str, *args, **kwargs):
    log.exception(msg, *args, **kwargs)