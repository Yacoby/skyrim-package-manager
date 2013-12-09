import sys
import logging

import requests

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    data = sys.argv[1]
    data = data.strip('/')
    _, _, mod_id, _, file_id = data.split('/')

    game = 'skyrim'
    game_id = '101'

    addr = 'http://%s:%d' % ('localhost', 8080)

    try:
        req = requests.get('%s/status')
        req = requests.post('%s/download/%s/%s/%s' % (addr, game, game_id, file_id))
    except requests.exceptions.ConnectionError:
        server.run()
