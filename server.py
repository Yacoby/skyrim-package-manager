from bottle import route, post, run, static_file, install
import logging
import json
import os

from functools import partial

from downloader import DownloadManager
from nxm_register import register_nxm_handler, is_nxm_registered
from server_adapter import StoppableWSGIRefServer
from server_heartbeat import HeartbeatMonitor, Heartbeat

ROOT_PATH = os.path.dirname(__file__)
GUI_DATA_PATH = os.path.join(ROOT_PATH, 'gui')

@route('/downloading')
def downloading():
    data = []
    for dl in download_manager.get_downloading():
        data.append(dl.raw_data())
    return {'active_downloads':data}

@route('/cancel_download/<dl_id>')
def cancel_download(dl_id):
    download_manager.stop_download(int(dl_id))

@post('/download/<game>/<game_id>/<mod_id>/<file_id>')
def download(game, game_id, mod_id, file_id):
    download_manager.download(server._on_dl_finished,
                              game,
                              game_id,
                              mod_id,
                              file_id)

@route('/status')
def status():
    return {
        'running':True,
        'username_set':cfg.get('user', '') != '',
        'password_set':cfg.get('password', '') != '',
        'save_location':cfg['download_location'],
    }

@route('/shutdown')
def shutdown():
    server.stop()

@route('/nxm')
def nxm_details():
    return {'registered':is_nxm_registered()}

@route('/nxm/register')
def nxm_register():
    register_nxm_handler()
    return nxm_details()

@route('/')
def index():
    return static_file('index.html', root=GUI_DATA_PATH)

@route('/static/<filepath:path>')
def server_static(filepath):
    return static_file(filepath, root=GUI_DATA_PATH)

def local_variable_plugin(to_inject, callback):
    def wrapper(*args, **kwargs):
        f_globals = callback.func_globals
        old_values = {}

        for name, var in to_inject.iteritems():
            try:
                old_values[name] = f_globals[name]
            except KeyError:
                pass
            f_globals[name] = var

        result = callback(*args, **kwargs)

        for key, value in old_values.iteritems():
            f_globals[key] = value

        return result

    return wrapper

def _path_to_abs(path):
    '''
    >>> p = _path_to_abs('~')
    >>> os.path.relpath(p, os.path.expanduser('~'))
    '.'

    >>> p = _path_to_abs('')
    >>> os.path.relpath(p, os.path.expanduser('~'))
    '.'

    >>> _path_to_abs('/home/yacoby')
    '/home/yacoby'

    >>> p = _path_to_abs('~/mods')
    >>> os.path.relpath(p, os.path.expanduser('~'))
    'mods'
    '''
    
    if not os.path.isabs(path):
        path = os.path.expanduser(path)
        if not os.path.isabs(path):
            path = os.path.join(os.path.expanduser('~'), path)
    return path

class Server(object):
    SHUTDOWN_TIMEOUT = 60

    def __init__(self):
        try:
            with open(os.path.join(ROOT_PATH, 'cfg.json')) as json_fp:
                self._cfg = json.load(json_fp)
        except IOError:
            logging.warning('No user config')
            self._cfg = {
                    'download_location' : '',
                    'user' : '',
                    'password' : '',
            }
        self._cfg['download_location'] = _path_to_abs(self._cfg.get('download_location', ''))

        try:
            with open(os.path.join(ROOT_PATH, 'data.json')) as json_fp:
                user_data = json.load(json_fp)
        except IOError:
            logging.warning('No user data')
            user_data = {}

        self._download_manager = DownloadManager(self._cfg['user'],
                                                 self._cfg['password'],
                                                 user_data.get('session_id'))

    def stop(self):
        self._bottle_server.stop()

    def _on_heartbeat_timeout(self, heartbeat):
        '''
        Called if we haven't had a heartbeat in a while
        '''
        if any(self._download_manager.get_downloading()):
            logging.debug('No heartbeat but downloading.... Still alive')
            heartbeat.beat()
        else:
            logging.debug('No heartbeat, no downloads. Stopping...')
            self._bottle_server.stop()

    def _on_dl_finished(self, path, file_name):
        '''
        TODO this needs sorting
        '''
        import shutil
        save_path = os.path.join(self._cfg['download_location'], file_name)
        logging.debug('Moving <%s> to <%s>' % (path, save_path,))
        shutil.move(path, save_path)

    def start_download(self, game, game_id, mod_id, file_id):
        self._download_manager.download(self._on_dl_finished,
                                        game,
                                        game_id,
                                        mod_id,
                                        file_id)

    def start_server(self, host, port):
        self._bottle_server = StoppableWSGIRefServer(host=host, port=port)

        hb = Heartbeat()
        install(partial(local_variable_plugin, {
            'cfg':self._cfg,
            'heartbeat': hb,
            'server' : self,
            'download_manager' : self._download_manager,
        }))

        hb_monitor = HeartbeatMonitor(hb, self.SHUTDOWN_TIMEOUT, self._on_heartbeat_timeout)
        hb_monitor.monitor()

        run(server=self._bottle_server)

        self._download_manager.stop()
        hb_monitor.stop()

if __name__ == "__main__":
    import doctest
    doctest.testmod()
