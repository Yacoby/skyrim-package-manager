import requests
import tempfile
import os

DOMAIN = 'http://nmm.nexusmods.com'

#This is used as the user agent as the web service seems to care
NEXUS_CLIENT_VERSION = 'Nexus Client v0.46.0'

class memoize(dict):
    def __init__(self, func):
        self.func = func

    def __call__(self, *args):
        return self[args]

    def __missing__(self, key):
        result = self[key] = self.func(*key)
        return result

def _as_json(get_str, sid=None, headers=None):
    if not headers:
        headers = {'User-Agent':NEXUS_CLIENT_VERSION}
    r = requests.get('%s%s' % (DOMAIN, get_str), headers=headers)
    return r.json()

@memoize
def req_file_details(game, game_id, file_id):
    uri = '/%s/Files/%s/?game_id=%s' % (game, file_id, game_id)
    return _as_json(uri)

@memoize
def req_servers(game, game_id, download_id):
    uri = '/%s/Files/download/%s/?game_id=%s' % (game, download_id, game_id)
    return _as_json(uri)

def is_session_id_valid(session_id):
    get_str = '/Sessions/?Validate'
    cookies = {'sid':session_id}
    r = requests.post('%s%s' % (DOMAIN, get_str), cookies=cookies)
    return r.text != 'null'

def session_id(user, passwd):
    get_str = '/Sessions/?Login&username=%s&password=%s' % (user, passwd)
    r = requests.get('%s%s' % (DOMAIN, get_str))
    try:
        return r.cookies['sid']
    except KeyError:
        return None

def _download_to_stream(sid, url, fp, update_function):
    headers = {'User-Agent':NEXUS_CLIENT_VERSION}
    cookies = None
    if sid:
        cookies = {'sid':sid}
    r = requests.get(url, stream=True, cookies=cookies, headers=headers)
    total_written = 0
    for chunk in r.iter_content():
        if chunk:
            fp.write(chunk)
            total_written += len(chunk)
            update_function(total_written)

def download(sid, url, update_function):
    (os_level_fp, pathname) = tempfile.mkstemp()
    try:
        with os.fdopen(os_level_fp, 'w') as fp:
            _download_to_stream(sid, url, fp, update_function)
    except:
        os.unlink(pathname)
        raise
    return pathname
