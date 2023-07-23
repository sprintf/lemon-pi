
import time
import os
import logging
import urllib.request
import urllib.error

import yaml

logger = logging.getLogger(__name__)


class TrackUpdater:

    def update(self):
        TrackUpdater._make_tmp_dir()
        track_file, mtime = self.get_track_file()
        gmt_time_str = time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime(mtime))
        r = urllib.request.Request("https://storage.googleapis.com/perplexus/public/tracks.yaml",
                                    headers={
                                        'If-Modified-Since':gmt_time_str
                                    })
        try:
            logger.info("checking for updated track info...")
            resp = urllib.request.urlopen(r)
            with open("tmp/tmp-tracks.yaml", "w") as f:
                f.write(resp.read().decode("UTF-8"))
            logger.info("track file updated in tmp/tmp-tracks.yaml")
            if self.valid_yaml("tmp/tmp-tracks.yaml"):
                os.rename("tmp/tmp-tracks.yaml", "tmp/tracks.yaml")
                logger.info("local track cache updated")
        except urllib.error.HTTPError as e:
            # we expect a HTTP 304 error if the file is no newer than
            # the passed up date
            if e.code == 304:
                logger.info("track up to date")
            else:
                logger.warning("track data unavailable/forbidden : {}".format(e.code))
        except urllib.error.URLError as e:
            logger.info("no wifi. no tracks updated")

    @classmethod
    def get_track_file(self):
        mtime1 = os.path.getmtime("resources/tracks.yaml")
        if os.path.exists("tmp/tracks.yaml"):
            mtime2 = os.path.getmtime("tmp/tracks.yaml")
            if mtime2 > mtime1:
                return "tmp/tracks.yaml", mtime2
        return "resources/tracks.yaml", mtime1

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


# used for manual testing
if __name__ == "__main__":

    logging.basicConfig(format='%(asctime)s %(name)s %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        level=logging.INFO)

    tu = TrackUpdater()
    tu.update()