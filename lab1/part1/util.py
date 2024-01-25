from struct import pack, unpack
import logging

# takes in header and checks that the step is as expected.
def validate_header(header, expected_step):
    _, _, step, _ = unpack('!IIHH', header)
    if step != expected_step:
        return False
    else:
        return True


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
    file_handler = logging.FileHandler('client-log.txt')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

# logs the given string with a timestamp
def log(s):
    logger.info(s)