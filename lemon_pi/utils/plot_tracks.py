from urllib.error import HTTPError

import gmplot
import os
import sys
import zlib
import urllib

from lemon_pi.car.drs_controller import DrsDataLoader, DrsGate
from lemon_pi.car.track import read_tracks, TrackLocation


# utility to generate maps of all the tracks, indicating
# where the start/finish and pit in coordinates are

def _calc_mid(track:TrackLocation):
    sum_lat = 0
    sum_long = 0
    count = 0
    for t in [track.get_pit_in_target(), track.get_start_finish_target()]:
        if t:
            count += 2
            sum_lat += t.lat_long1[0] + t.lat_long2[0]
            sum_long += t.lat_long1[1] + t.lat_long2[1]
    return sum_lat / count, sum_long / count

def run():
    tracks = read_tracks()
    loader = DrsDataLoader()
    loader.read_file("resources/drs_zones.json")

    for track in tracks:
        if track.hidden:
            continue
        mid_lat, mid_long = _calc_mid(track)
        gmap = gmplot.GoogleMapPlotter(mid_lat, mid_long, 17,
                                       map_type="satellite",
                                       title=track.get_display_name())
        gmap.apikey = os.environ["GMAP_APIKEY"]
        sf = track.get_start_finish_target()
        start_finish = zip(*[
            sf.lat_long1,
            sf.lat_long2,
        ])
        gmap.polygon(*start_finish, color='white', edge_width=20)
        gmap.text(*sf.lat_long1, '   start/finish')

        if track.is_pit_defined():
            pi = track.get_pit_in_target()
            pit_in = zip(*[
                pi.lat_long1,
                pi.lat_long2
            ])
            gmap.polygon(*pit_in, color='blue', edge_width=20)
            gmap.text(*pi.lat_long1, '   pit in')

        if track.is_pit_out_defined():
            po = track.get_pit_out_target()
            pit_out = zip(*[
                po.lat_long1,
                po.lat_long2
            ])
            gmap.polygon(*pit_out, color='blue', edge_width=20)
            gmap.text(*po.lat_long1, '   pit out')

        drs_zones: [DrsGate] = loader.get_drs_activation_zones(track.code)
        if drs_zones:
            for gate in drs_zones:
                message = "on" if gate.activation else "off"
                drs_gate_lat_longs = zip(*[gate.target.lat_long1, gate.target.lat_long2])
                gmap.polygon(*drs_gate_lat_longs, color='yellow', edge_width=6)
                gmap.text(gate.target.lat_long1[0], gate.target.lat_long1[1], f'DRS {message}')

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

    drs_zones = open("resources/drs_zones.json")
    drs_check = zlib.crc32(drs_zones.read().encode("utf-8"))

    drs_check2 = 0
    url = "https://storage.googleapis.com/perplexus/public/drs_zones.json"
    try:
        file = urllib.request.urlopen(url)
        drs_check2 = zlib.crc32(file.read())
    except HTTPError:
        pass

    force = len(sys.argv) == 2 and sys.argv[1] == '-f'

    # don't do anything if the files are the same
    if check == check2 and drs_check == drs_check2 and not force:
        print("no update needed")
        sys.exit(1)

    # generate new maps
    if not os.path.isdir("tracks"):
        os.mkdir("tracks")

    run()
    print("new track maps generated")


