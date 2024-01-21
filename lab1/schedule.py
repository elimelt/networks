from util import test_and_record_if_server_running
import time

attu2 = "attu2.cs.washington.edu"
attu3 = "attu3.cs.washington.edu"
ping_interval = 60

def test():
    test_and_record_if_server_running(attu2)
    test_and_record_if_server_running(attu3)

if __name__ == "__main__":
    while True:
        test()
        time.sleep(ping_interval)
