import threading

from bottle import ServerAdapter
from wsgiref.simple_server import make_server, WSGIRequestHandler

class StoppableWSGIRefServer(ServerAdapter):
    server = None

    def run(self, handler):
        if self.quiet:
            class QuietHandler(WSGIRequestHandler):
                def log_request(*args, **kw):
                    pass
            self.options['handler_class'] = QuietHandler
        self.server = make_server(self.host, self.port, handler, **self.options)
        self.server.serve_forever()

    def stop(self):
        '''
        Using threading allows this method to be called from a request
        '''
        threading.Thread(target=self.server.shutdown).start()
