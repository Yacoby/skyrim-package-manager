import time
import logging
import threading
import tempfile
import requests
import os

import nxm_api

MAX_BACKOFF_SECONDS = 120
DOWNLOAD_TIMEOUT = 5
MAX_ATTEMPTS = 20
DOWNLOAD_CHUNK_SIZE = 8192

class Download(object):
    '''
    Yay. This seems to do all the things
    '''
    def __init__(self, details, game, game_id, file_id, cookies):
        self._details = details

        self._game = game
        self._game_id = game_id
        self._file_id = file_id

        self._cookies = cookies
        self._expected_size_kb = int(self._details['size'])

        self._current_downloaded = 0
        self._finished = False

        self._attempts = 0
        self._max_attempts = MAX_ATTEMPTS
        self._login_requried = False

        self._bad_urls = set()

        self._url, self._headers = self._get_download_url_headers()

    def _get_download_url_headers(self):
        return nxm_api.get_download_url_headers(self._game,
                                                self._game_id,
                                                self._file_id,
                                                self._bad_urls)

    def finished(self):
        return self._finished

    def login_required(self):
        return self._login_requried

    def set_login_required(self, val):
        self._login_requried = val

    def cookies(self, cookies):
        self._cookies = cookies

    def download(self):
        backoff = 2
        while self._attempts < self._max_attempts and not self.finished():

            if self.login_required():
                logging.debug('Waiting for login')

                time.sleep(backoff)
                continue

            self._attempts += 1
            try:
                download_path = self._download_to_tmp()
            except (requests.ConnectionError, requests.Timeout,):
                logging.debug('Connection error. Sleeping for <%s>' % backoff)
                self._bad_urls.add(self._url)
                self._url, _ = self._get_download_url_headers()
                time.sleep(backoff)
                backoff = min(backoff * 2, MAX_BACKOFF_SECONDS)
                continue

            download_size_bytes = os.path.getsize(download_path)

            #The +1 is as I think the rounding is different on the nexus (ceiling?).
            #It may be worth looking into if I can calculate this better
            upper_bound_expected_kb = int(download_size_bytes/1024 + 1)

            if download_size_bytes == 0:
                logging.debug('Zero file size. Backoff is <%d>' % backoff)
                time.sleep(backoff)
                backoff = min(backoff * 2, MAX_BACKOFF_SECONDS)
                continue
            elif upper_bound_expected_kb < self._expected_size_kb:
                logging.debug('Low file size. Got <%d>, expected <%d>. Login required?' %
                              (upper_bound_expected_kb, self._expected_size_kb,))
                self._login_requried = True
                continue

            #TODO
            #look at output and check it is as expected. Basically that it doesn't
            #have html in it... as this seems to be the case if there is errors

            logging.debug('Downloaded a file')
            self._finished = True

    def _download_to_tmp(self):
        logging.debug('Downloading to temp file')
        req = requests.get(self._url,
                           headers=self._headers,
                           cookies=self._cookies,
                           stream=True,
                           timeout=DOWNLOAD_TIMEOUT)
        logging.debug('Connection made...')

        (os_level_fp, pathname) = tempfile.mkstemp()
        try:
            with os.fdopen(os_level_fp, 'w') as fp:
                self._download_to_stream(req, fp)
        except:
            os.unlink(pathname)
            raise
        return pathname

    def _download_to_stream(self, request, fp):
        self._current_downloaded = 0
        for chunk in request.iter_content(DOWNLOAD_CHUNK_SIZE):
            if chunk:
                fp.write(chunk)
                self._current_downloaded += len(chunk)

    def raw_data(self):
        return {
                'file_name': self._details['name'],
                'url': self._url,
                'file_size_kb': self._details['size'],
                'total_downloaded_kb': self._current_downloaded/1024,
        }


class DownloadManager(object):
    def __init__(self, user, passwd, session_id):
        self._user = user
        self._passwd = passwd
        self._session_id = session_id
        self._downloads = []

        self._stop_event = threading.Event()
        threading.Thread(target=self.login_monitor, args=(self._stop_event,)).start()

    def stop(self):
        self._stop_event.set()

    def download(self, game, game_id, mod_id, file_id):
        logging.debug('Request to download file <%s> from mod <%s>' % (file_id, mod_id))
        file_details = nxm_api.get_file_details(game, game_id, file_id)
        print file_details

        dl = Download(file_details,
                      game,
                      game_id,
                      file_id,
                      {'sid':self._session_id})
        thread = threading.Thread(target=dl.download)
        thread.start()
        self._downloads.append(dl)

    def login_monitor(self, stop_event):
        while not stop_event.is_set():
            time.sleep(0.5)

            login_req = any(dl for dl in self._downloads if dl.login_required())
            if not login_req:
                continue
            logging.debug('Thread with login required flag set')

            if not nxm_api.is_session_id_valid(self._session_id):
                logging.debug('Session id is invalid, logging in')
                self._session_id = nxm_api.session_id(self._user, self._passwd)
                #TODO it isn't clear if login fails

            for dl in self.get_downloading():
                dl.cookies({'sid':self._session_id})
                dl.set_login_required(False)

    def get_downloading(self):
        return (dl for dl in self._downloads if not dl.finished())

    def get_done(self):
        return (dl for dl in self._downloads if dl.finished())
