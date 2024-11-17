

### Logger

# The `Logger` provides a simple logging functionality to help in debugging and tracking the analysis process.


# filename: aitools_autogen/coding/logger.py

import logging

def setup_logger(name: str, level=logging.INFO) -> logging.Logger:
    """
    Set up a logger with the specified name and level.

    Args:
        name (str): The name of the logger.
        level (int): The logging level.

    Returns:
        logging.Logger: The configured logger.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(level)

    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Add formatter to ch
    ch.setFormatter(formatter)

    # Add ch to logger
    logger.addHandler(ch)

    return logger