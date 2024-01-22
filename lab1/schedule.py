from util import test_and_record_if_server_running
from visualize import to_html
from datetime import datetime
import time
import os

attu2 = "attu2.cs.washington.edu"
attu3 = "attu3.cs.washington.edu"
ping_interval = 120

def test():
    test_and_record_if_server_running(attu2)
    test_and_record_if_server_running(attu3)

if __name__ == "__main__":
    i = 0
    while True:
        test()
        timestamp = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
        print(f'{timestamp} - pinged servers')

        if i % 5 == 0:
            if os.path.exists('./index.html'):
                os.remove('./index.html')

            with open('./index.html', 'w') as f:
                f.write(to_html())
                print(f'{timestamp} - wrote to index.html')

        time.sleep(ping_interval)
        i += 1
        if i == 100:
            i = 0