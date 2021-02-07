from urllib.error import HTTPError

import gmplot
import os
import sys
import zlib
import urllib
from car.track import read_tracks, TrackLocation, Target


# utility to generate maps of all the tracks, indicating
# where the start/finish and pit in coordinates are

def _calc_mid(track:TrackLocation):
    sum_lat = 0
    sum_long = 0
    count = 0
    for t in [track.pit_in, track.start_finish]:
        if t:
            count += 2
            sum_lat += t.lat_long1[0] + t.lat_long2[0]
            sum_long += t.lat_long1[1] + t.lat_long2[1]
    return sum_lat / count, sum_long / count

def run():
    tracks = read_tracks()

    for track in tracks:
        mid_lat, mid_long = _calc_mid(track)
        gmap = gmplot.GoogleMapPlotter(mid_lat, mid_long, 16,
                                       map_type="satellite",
                                       title=track.name)
        gmap.apikey = os.environ["GMAP_APIKEY"]
        start_finish = zip(*[
            track.start_finish.lat_long1,
            track.start_finish.lat_long2,
        ])
        gmap.polygon(*start_finish, color='white', edge_width=20)
        gmap.text(*track.start_finish.lat_long1, '   start/finish')

        if track.is_pit_defined():
            pit_in = zip(*[
                track.pit_in.lat_long1,
                track.pit_in.lat_long2
            ])
            gmap.polygon(*pit_in, color='blue', edge_width=20)
            gmap.text(*track.pit_in.lat_long1, '   pit in')

        if track.is_radio_sync_defined():
            radio = zip(*[
                track.radio_sync.lat_long1,
                track.radio_sync.lat_long2
            ])
            gmap.polygon(*radio, color='purple', edge_width=20)
            gmap.text(*track.radio_sync.lat_long1, '   radio')

        gmap.draw("tracks/{}.html".format(track.name.lower().replace(' ', '-')))

if __name__ == "__main__":
    if not os.environ["GMAP_APIKEY"]:
        print("no GMAP_APIKEY specified")
        sys.exit(1)

    # is tracks different to published tracks
    tracks = open("resources/tracks.yaml")
    check = zlib.crc32(tracks.read().encode("utf-8"))

    # calc the crc23 of the published tracks
    check2 = 0
    url = "https://storage.googleapis.com/perplexus/public/tracks.yaml"
    try:
        file = urllib.request.urlopen(url)
        check2 = zlib.crc32(file.read())
    except HTTPError:
        pass

    force = len(sys.argv) == 2 and sys.argv[1] == '-f'

    # don't do anything if the files are the same
    if check == check2 and not force:
        print("no update needed")
        sys.exit(1)

    # generate new maps
    if not os.path.isdir("tracks"):
        os.mkdir("tracks")

    run()
    print("new track maps generated")


