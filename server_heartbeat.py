import time
import threading

from bottle import route

@route('/heartbeat')
def do_heartbeat():
    heartbeat.beat()

class Heartbeat(object):
    def __init__(self):
        self._heartbeat = time.time()

    def beat(self):
        self._heartbeat = time.time()

    def seconds_since_last_beat(self):
        return time.time() - self._heartbeat

class HeartbeatMonitor(object):
    def __init__(self, hb, timeout, on_timeout_f):
        self._heartbeat = hb
        self._timeout = timeout
        self._on_timeout_f = on_timeout_f

        self._stop_evt = threading.Event()
        self._thread = threading.Thread(target=self._monitor, args=(self._stop_evt,))

    def monitor(self):
        self._thread.start()

    def stop(self):
        self._stop_evt.set()

    def _monitor(self, evt):
        while not evt.is_set():
            if self._heartbeat.seconds_since_last_beat() > self._timeout:
                self._on_timeout_f()
            time.sleep(2)
