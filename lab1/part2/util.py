import logging

LOG_TO_FILE = False

# config logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(message)s')
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

if LOG_TO_FILE:
    file_handler = logging.FileHandler('server-log.txt')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

# logs the given string with a timestamp
def log(s):
    logger.info(s)