from struct import pack, unpack
import logging

# takes in header
def validate_header(header, silent=False):
    payload_len, psecret, step, num = unpack('!IIHH', header)
    if step != 2:
        if not silent:
            print("bad response:", payload_len, psecret, step, num)
        return False
    else:
        if not silent:
            print("response validated")
        return True



LOG_TO_FILE = False

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(message)s')

# Create a console handler and set level to INFO
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Check if flag is set to log to a file
if LOG_TO_FILE:
    # Create a file handler and set level to INFO
    file_handler = logging.FileHandler('log.txt')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

def log(s):
    logger.info(s)