'''
Wrapper around the API provided by Nexus mods
'''
import requests

DOMAIN = 'http://nmm.nexusmods.com'

#This is used as the user agent as the web service seems to care
NEXUS_CLIENT_VERSION = 'Nexus Client v0.46.0'

def _as_json(get_str, sid=None, headers=None):
    if not headers:
        headers = {'User-Agent':NEXUS_CLIENT_VERSION}
    r = requests.get('%s%s' % (DOMAIN, get_str), headers=headers)
    return r.json()

def get_file_details(game, game_id, file_id):
    uri = '/%s/Files/%s/?game_id=%s' % (game, file_id, game_id)
    return _as_json(uri)

def get_servers(game, game_id, file_id):
    uri = '/%s/Files/download/%s/?game_id=%s' % (game, file_id, game_id)
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

def get_download_url_headers(game, game_id, file_id, bad_urls = []):
    headers = {'User-Agent':NEXUS_CLIENT_VERSION}

    server_listing = get_servers(game, game_id, file_id)
    valid_servers = (server for server in server_listing
                     if server['IsPremium'] == False and
                        server['URI'] not in bad_urls)

    try:
        min_user_server = min(valid_servers, key=lambda s:s['ConnectedUsers'])
        return min_user_server['URI'], headers
    except ValueError:
        raise ValueError("No servers available")
