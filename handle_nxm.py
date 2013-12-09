import sys
import re
import logging

import requests

def parse_nxm(nxm_str):
    data = sys.argv[1]
    data = re.sub(r'^nxm:', '', data)
    data = data.strip('/ ')
    _, _, mod_id, _, file_id = data.split('/')
    return mod_id, file_id

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    if len(sys.argv) > 1:
        mod_id, file_id = parse_nxm(sys.argv[1])

        game = 'skyrim'
        game_id = '101'

        addr = 'http://%s:%d' % ('localhost', 8080)
        try:
            req = requests.get('%s/status' % addr)
            req = requests.post('%s/download/%s/%s/%s' % (addr, game, game_id, file_id))
        except requests.exceptions.ConnectionError:
            pass
    else

        pass
