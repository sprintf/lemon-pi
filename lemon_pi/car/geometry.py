from numpy import *
from haversine import haversine

def __perp_xy(a):
    b = empty_like(a)
    b[0] = -a[1]
    b[1] = a[0]
    return b

# caldulate the heading in degrees from north to go from one lat long to another
def heading_between_lat_long(from_ll, to_ll):
    x_diff = haversine(to_ll, (to_ll[0], from_ll[1]))
    y_diff = haversine(to_ll, (from_ll[0], to_ll[1]))
    # haversine distance is always positive, so we crudely set the sign
    if (to_ll[1] < from_ll[1]):
        x_diff = -x_diff
    if to_ll[0] < from_ll[0]:
        y_diff = -y_diff
    angle_radians = math.atan2(x_diff, y_diff)
    return (degrees(angle_radians) + 360) % 360

def seg_intersect_lat_long(a1, a2, b1, b2):
    result = seg_intersect_xy(
        array([a1[1], a1[0]]),
        array([a2[1], a2[0]]),
        array([b1[1], b1[0]]),
        array([b2[1], b2[0]])
    )
    return (result[1], result[0])

def seg_intersect_xy(a1, a2, b1, b2):
    da = a2 - a1
    db = b2 - b1
    dp = a1 - b1
    dap = __perp_xy(da)
    denom = dot(dap, db)
    num = dot(dap, dp)
    return (num / denom.astype(float))*db + b1

# is a point p1 between lat/long points a1 and a2
def is_between(a1, a2, p1):
    xy1 = (a1[1], a1[0])
    xy2 = (a2[1], a2[0])
    pxy = (p1[1], p1[0])

    minxy = (min(xy1[0], xy2[0]), min(xy1[1], xy2[1]))
    maxxy = (max(xy1[0], xy2[0]), max(xy1[1], xy2[1]))
    return pxy[0] >= minxy[0] and pxy[0] <= maxxy[0] \
            and pxy[1] >= minxy[1] and pxy[1] <= maxxy[1]

# get a point on the given heading
#  point is a (lat, long) tuple
# return a (lat, long) tuple
def get_point_on_heading(point, heading:float):
    a1 = array([point[1], point[0]])
    R = 6378.1  # radius of earth
    brg = math.radians(heading)
    d = 0.05 # 50 feet?

    lat1 = math.radians(a1[1])  # its the y axis
    lon1 = math.radians(a1[0])  # its the x axis

    lat2 = math.asin(math.sin(lat1) * math.cos(d/R) + \
              math.cos(lat1) * math.sin(d/R) * math.cos(brg))
    lon2 = lon1 + math.atan2(math.sin(brg) * math.sin(d/R) * math.cos(lat1),
                             math.cos(d/R) - math.sin(lat1) * math.sin(lat2))

    return math.degrees(lat2), math.degrees(lon2)


DirectionMap = {
    "N" : 0,
    "NE" : 45,
    "E" : 90,
    "SE" : 135,
    "S" : 180,
    "SW" : 225,
    "W" : 270,
    "NW" : 315
}


def calc_intersect_heading(lat_long1, lat_long2, direction):
    a = lat_long1
    b = lat_long2
    lat = 0
    lon = 1

    dL = b[lon] - a[lon]
    X = cos(b[lat]) * sin(dL)
    Y = cos(a[lat]) * sin(b[lat]) - sin(a[lat]) * cos(b[lat]) * cos(dL)
    line_heading = degrees(arctan2(X, Y))

    # print("got line_heading = {} want {}".format(line_heading, direction))

    line_heading += 360
    choice1 = (line_heading + 90)
    choice2 = (line_heading - 90)
    suggestion = DirectionMap[direction]

    # print("suggested angle is close to {}".format(suggestion))
    # print("choices are {} or {}".format(choice1 % 360, choice2 % 360))

    # print("diff 1 / 2 = {} {}".format(abs(suggestion - choice1), abs(suggestion - choice2)))

    if abs(suggestion - choice1 % 360)  < abs(suggestion - choice2 % 360):
        # print("choosing 1")
        return choice1 % 360
    else:
        # print("choosing 2")
        return choice2 % 360


if __name__ == "__main__":

    print("testing")
    # 37.928344,-122.299246,37.928311,-122.299114
    a1 = (37.928344, -122.299246)
    a2 = (37.928311, -122.299114)
    b1 = (37.929216, -122.298691)
    b2 = (37.928889, -122.298868)

    result = seg_intersect_lat_long(a1, a2, b1, b2)
    print(result)

    print(is_between(a1, a2, result))

    b2 = (37.928854, -122.298830)
    result = seg_intersect_lat_long(a1, a2, b1, b2)
    print(result)

    print(is_between(a1, a2, result))

    import gmplot
    from secrets import gmap_apikey

    gmap = gmplot.GoogleMapPlotter(37.928, -122.299, 16)
    gmap.apikey = gmap_apikey

    gmap.marker(a1[0], a1[1])
    gmap.marker(a2[0], a2[1])
    gmap.marker(b1[0], b1[1])


    for x in range(200, 210, 2):
        print(x)

        b3 = get_point_on_heading(b1, x)

        print("heading is : {}".format(heading_between_lat_long(b1, b3)))

        gmap.marker(b3[0], b3[1])
        print(b3)
        result = seg_intersect_lat_long(a1, a2, b1, b3)
        print(result)

        print(is_between(a1, a2, result))

    gmap.draw("mymap.html")


