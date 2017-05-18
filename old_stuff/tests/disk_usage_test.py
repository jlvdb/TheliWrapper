import sys
import threading
from time import sleep


class ThreadingExample(threading.Thread):
    disk_quota = 0

    def __init__(self, interval=1):
        self.interval = interval
        thread = threading.Thread(target=self.run, args=())
        thread.daemon = True
        thread.start()

    def run(self):
        while True:
            self.disk_quota += 1
            if self.disk_quota > 1:
                self.leave()
            print('Doing something imporant in the background')
            sleep(self.interval)

    def leave(self):
        sys.exit()


example = ThreadingExample()
sleep(3)
print(example.disk_quota)
sleep(2)
print(example.disk_quota)
