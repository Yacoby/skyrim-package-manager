import sys
import logging
import json
import os
from functools import partial

from bottle import route, post, run, static_file, install, request, response

from downloader import DownloadManager
from nxm_register import register_nxm_handler, is_nxm_registered
from server_adapter import StoppableWSGIRefServer
from server_heartbeat import HeartbeatMonitor, Heartbeat

if getattr(sys, 'frozen', False):
    APP_PATH = os.path.dirname(sys.executable)
elif __file__:
    APP_PATH = os.path.dirname(__file__)
GUI_DATA_PATH = os.path.join(APP_PATH, 'gui')

@post('/set_cfg')
def set_cfg():
    for k, v in request.json.items():
        cfg[k] = v
    return {}

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
        'user':cfg.get('user', ''),
        'username_set':cfg.get('user', '') != '',
        'password_set':cfg.get('password', '') != '',
        'save_location':cfg['save_location'],
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
    response.set_header('Cache-Control', 'no-cache, no-store, must-revalidate')
    response.set_header('Pragma', 'no-cache')
    response.set_header('Expires', '0')

    return static_file('index.html', root=GUI_DATA_PATH)

@route('/static/<filepath:path>')
def server_static(filepath):
    response.set_header('Cache-Control', 'no-cache, no-store, must-revalidate')
    response.set_header('Pragma', 'no-cache')
    response.set_header('Expires', '0')

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

def _cfg_path():
    return os.path.join(APP_PATH, 'cfg.json')

def _save_cfg(cfg):
    with open(_cfg_path(), 'w') as json_fp:
        json.dump(cfg, json_fp)

def _load_cfg():
    try:
        with open(_cfg_path()) as json_fp:
            cfg = json.load(json_fp)
    except IOError:
        logging.warning('No user config')
        cfg = {
                'save_location' : '',
                'user' : '',
                'password' : '',
        }
    cfg['save_location'] = _path_to_abs(cfg.get('save_location', ''))
    return cfg

class Server(object):
    SHUTDOWN_TIMEOUT = 60

    def __init__(self):

        self._cfg = _load_cfg()

        try:
            with open(os.path.join(APP_PATH, 'data.json')) as json_fp:
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
        save_path = os.path.join(self._cfg['save_location'], file_name)
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
        _save_cfg(self._cfg)

if __name__ == "__main__":
    import doctest
    doctest.testmod()
