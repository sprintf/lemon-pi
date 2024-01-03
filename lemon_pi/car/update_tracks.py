import json
import time
import os
import logging
import urllib.request
import urllib.error

import yaml

logger = logging.getLogger(__name__)


class TrackUpdater:

    def update(self):
        self._do_update("tracks.yaml")
        self._do_update("drs_zones.json")

    def _do_update(self, filename):
        TrackUpdater._make_tmp_dir()
        track_file, mtime = self.get_track_file()
        gmt_time_str = time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime(mtime))
        r = urllib.request.Request(f"https://storage.googleapis.com/perplexus/public/{filename}",
                                    headers={
                                        'If-Modified-Since':gmt_time_str
                                    })
        try:
            logger.info(f"checking for updated {filename}...")
            resp = urllib.request.urlopen(r)
            with open(f"tmp/tmp-{filename}", "w") as f:
                f.write(resp.read().decode("UTF-8"))
            logger.info(f"{filename} updated in tmp/tmp-{filename}")
            if filename.endswith(".yaml") and self.valid_yaml(f"tmp/tmp-{filename}"):
                os.rename(f"tmp/tmp-{filename}", f"tmp/{filename}")
                logger.info(f"local {filename} cache updated")
            if filename.endswith(".json") and self.valid_json(f"tmp/tmp-{filename}"):
                os.rename(f"tmp/tmp-{filename}", f"tmp/{filename}")
                logger.info(f"local {filename} cache updated")
        except urllib.error.HTTPError as e:
            # we expect a HTTP 304 error if the file is no newer than
            # the passed up date
            if e.code == 304:
                logger.info(f"{filename} up to date")
            else:
                logger.warning(f"{filename} unavailable/forbidden : {e.code}")
        except urllib.error.URLError as e:
            logger.info(f"no wifi. {filename} not updated")

    @classmethod
    def get_track_file(cls):
        return TrackUpdater._get_best_file("tracks.yaml")

    @classmethod
    def get_drs_file(cls):
        return TrackUpdater._get_best_file("drs_zones.json")

    @staticmethod
    def _get_best_file(filename):
        mtime1 = os.path.getmtime(f"resources/{filename}")
        if os.path.exists(f"tmp/{filename}"):
            mtime2 = os.path.getmtime(f"tmp/{filename}")
            if mtime2 > mtime1:
                return f"tmp/{filename}", mtime2
        return f"resources/{filename}", mtime1

    @classmethod
    def _make_tmp_dir(self):
        if not os.path.isdir("tmp"):
            logger.info("creating tmp/ dir for updated tracks")
            os.mkdir("tmp")

    def valid_yaml(self, file):
        try:
            with open(file) as yamlfile:
                tracks = yaml.load(yamlfile, Loader=yaml.FullLoader)
                return "tracks" in tracks
        except Exception:
            return False

    def valid_json(self, file):
        try:
            with open(file) as jsonfile:
                json.load(jsonfile)
                return True
        except Exception:
            return False


# used for manual testing
if __name__ == "__main__":

    logging.basicConfig(format='%(asctime)s %(name)s %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        level=logging.INFO)

    tu = TrackUpdater()
    tu.update()