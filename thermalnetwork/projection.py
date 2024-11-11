"""Utilities for converting (longitude, latitude) to (X, Y) coordinates in meters."""
import math


def meters_to_long_lat_factors(origin_lon_lat=(0, 0)):
    """
    Get conversion factors for translating between meters and (longitude, latitude).

    The resulting factors obey the WSG84 assumptions for the radius of the earth
    at the equator relative to the poles.

    :param origin_long_lat: An array of two numbers in degrees. The first value
        represents the longitude of the scene origin in degrees (between -180
        and +180). The second value represents latitude of the scene origin
        in degrees (between -90 and +90). Default: (0, 0).
    :return meters_to_lon: The conversion factor for meters to degrees longitude.
    :return meters_to_lat: The conversion factor for meters to degrees latitude.
    """
    # constants of the WSG84 system
    equator_rad = 6378137.0  # radius of the earth at the equator (meters)
    pole_rad = 6356752.314  # radius of the earth at the poles (meters)

    # convert everything to radians
    lat = math.radians(origin_lon_lat[1])

    # compute the conversion values
    d = math.sqrt(
        (equator_rad ** 2 * math.sin(lat) ** 2) + (pole_rad ** 2 * math.cos(lat) ** 2)
    )
    r = (equator_rad * pole_rad) / d  # radius of the earth at the latitude
    meters_to_lat = (math.pi * r * 2) / 360.0  # meters in one degree of latitude
    meters_to_lon = meters_to_lat * math.cos(lat)  # meters in one degree of longitude

    return meters_to_lon, meters_to_lat


def lon_lat_to_polygon(polygon_lon_lat_coords, origin_lon_lat=None,
                       conversion_factors=None):
    """
    Convert an array of (longitude, latitude) to (X, Y) coordinates in meters.

    Note that this function uses a single conversion factor for translating all
    coordinates in the polygon, which provides reasonably accurate conversions for
    polygons up to 100 kilometers long. Beyond that some distortion is expected.

    :param polygon_lon_lat_coords: A nested array with each sub-array having 2 values
        for the (longitude, latitude) of a polygon.
    :param origin_lon_lat: An array of two numbers in degrees. The first value
        represents the longitude of the scene origin in degrees (between -180
        and +180). The second value represents latitude of the scene origin
        in degrees (between -90 and +90). Note that the "scene origin" is the
        (0, 0) coordinate in the 2D space of the input polygon. If None,
        the scene origin will automatically be set to the lower left corner
        around the polygon.
    :param conversion_factors: A tuple with two values used to translate between
        longitude, latitude and meters. If None, these values will be automatically
        calculated from the meters_to_long_lat_factors method.
    :return: A nested array with each sub-array having 2 values for the
        (X, Y) coordinates of each polygon vertex in meters.
    """
    # set the origin_lon_lat if it is not specified
    if origin_lon_lat is None:
        origin_lon_lat = lower_left_point(polygon_lon_lat_coords)

    # Unpack or auto-calculate the conversion factors
    if not conversion_factors:
        meters_to_lon, meters_to_lat = meters_to_long_lat_factors(origin_lon_lat)
        lon_to_meters, lat_to_meters = 1.0 / meters_to_lon, 1.0 / meters_to_lat
    else:
        lon_to_meters, lat_to_meters = conversion_factors

    # Get the (X, Y) values for the polygon in meters
    return [((pt[0] - origin_lon_lat[0]) / lon_to_meters,
             (pt[1] - origin_lon_lat[1]) / lat_to_meters)
            for pt in polygon_lon_lat_coords]


def polygon_to_lon_lat(polygon, origin_lon_lat=(0, 0), conversion_factors=None):
    """
    Convert an array of (longitude, latitude) from an array of (X, Y) values in meters.

    Note that this function uses a single conversion factor for translating all
    coordinates in the polygon, which provides reasonably accurate conversions for
    polygons up to 100 kilometers long. Beyond that some distortion is expected.

    :param polygon: An array of (X, Y) values for coordinates in meters.
    :param origin_lon_lat: An array of two numbers in degrees. The first value
        represents the longitude of the scene origin in degrees (between -180
        and +180). The second value represents latitude of the scene origin
        in degrees (between -90 and +90). Note that the "scene origin" is the
        (0, 0) coordinate in the 2D space of the input polygon. By default,
        the polygon is placed assuming the scene origin is the equator (0, 0).
    :param conversion_factors: A tuple with two values used to translate between
        meters and longitude, latitude respectively. If None, these values will
        be automatically calculated using the meters_to_long_lat_factors method.
    :return: A nested array with each sub-array having 2 values for the
        (longitude, latitude) of each polygon vertex.
    """
    # unpack or auto-calculate the conversion factors
    if not conversion_factors:
        meters_to_lon, meters_to_lat = meters_to_long_lat_factors(origin_lon_lat)
    else:
        meters_to_lon, meters_to_lat = conversion_factors

    # get the longitude, latitude values for the polygon
    return [(origin_lon_lat[0] + pt[0] / meters_to_lon,
             origin_lon_lat[1] + pt[1] / meters_to_lat) for pt in polygon]


def lower_left_point(polygon):
    """
    Get (X, Y) values for the lower left corner of the bounding rectangle for a polygon.

    :param polygon: An array of (X, Y) values in any units system.
    :return: X and Y coordinates for the lower left point around the polygon.
    """
    min_pt = [polygon[0][0], polygon[0][1]]
    for point in polygon[1:]:
        if point[0] < min_pt[0]:
            min_pt[0] = point[0]
        if point[1] < min_pt[1]:
            min_pt[1] = point[1]
    return min_pt


def polygon_area(polygon):
    """
    Get the area of polygon.

    :param polygon: An array of (X, Y) values in any units system.
    :return area: A number for the area of the polygon.
    """
    area = 0
    for i, pt in enumerate(polygon):
        area += polygon[i - 1][0] * pt[1] - polygon[i - 1][1] * pt[0]
    return area / 2
