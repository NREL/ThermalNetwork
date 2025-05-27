"""Utilities for performing geometric operations on polygons."""

import math


def lower_left_point(polygon):
    """
    Get (X, Y) values for the lower left corner of the bounding rectangle for a polygon.

    :param polygon: An array of (X, Y) values in any units system.
    :return: X and Y coordinates for the lower left point around the polygon.
    """
    min_pt = [polygon[0][0], polygon[0][1]]
    for point in polygon[1:]:
        min_pt[0] = min(point[0], min_pt[0])
        min_pt[1] = min(point[1], min_pt[1])
    return min_pt


def upper_right_point(polygon):
    """
    Get (X, Y) values for the upper right corner of the bounding rectangle for a polygon.

    :param polygon: An array of (X, Y) values in any units system.
    :return: X and Y coordinates for the upper right point around the polygon.
    """
    max_pt = [polygon[0][0], polygon[0][1]]
    for point in polygon[1:]:
        max_pt[0] = max(point[0], max_pt[0])
        max_pt[1] = max(point[1], max_pt[1])
    return max_pt


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


def vector_angle(vector_1, vector_2):
    """
    Get the smallest angle between two vectors.

    :param vector_1: (X, Y) values for the first vector.
    :param vector_2: (X, Y) values for the second vector.
    :return angle: The angle between the input vectors in degrees.
    """

    def magnitude(vec):
        return math.sqrt(vec[0] ** 2 + vec[1] ** 2)

    def dot(v1, v2):
        return v1[0] * v2[0] + v1[1] * v2[1]

    try:
        ang = math.acos(dot(vector_1, vector_2) / (magnitude(vector_1) * magnitude(vector_2)))
        return math.degrees(ang)
    except ValueError:  # python floating tolerance can cause math domain error
        if dot(vector_1, vector_2) < 0:
            return math.degrees(math.acos(-1))
        return math.degrees(math.acos(1))
    except ZeroDivisionError:  # zero-length vector
        return 0


def vector_angle_counterclockwise(vector_1, vector_2):
    """
    Get the counterclockwise angle between two vectors.

    :param vector_1: (X, Y) values for the first vector.
    :param vector_2: (X, Y) values for the second vector.
    :return angle: The counterclockwise angle between the input vectors in degrees.
    """

    def determinant(v1, v2):
        return v1[0] * v2[1] - v1[1] * v2[0]

    inner = vector_angle(vector_1, vector_2)
    det = determinant(vector_1, vector_2)
    if det >= 0:
        return inner  # if the det > 0 then v1 is immediately counterclockwise of v2
    else:
        return 360 - inner  # if the det < 0 then v2 is counterclockwise of v1


def rotate(point, angle, origin):
    """Rotate a point counterclockwise by a certain angle around an origin.

    :param point: (X, Y) values for a point to be rotated.
    :param angle: An angle for rotation in degrees. Positive rotates counterclockwise.
        Negative rotates clockwise.
    :param origin: (X, Y) values for the origin around which the point will be rotated.
    :return rotated_point: The input point that has been rotated by the input angle.
    """
    trans_pt = (point[0] - origin[0], point[1] - origin[1])
    angle_rad = math.radians(angle)
    cos_a = math.cos(angle_rad)
    sin_a = math.sin(angle_rad)
    qx = cos_a * trans_pt[0] - sin_a * trans_pt[1]
    qy = sin_a * trans_pt[0] + cos_a * trans_pt[1]
    return qx + origin[0], qy + origin[1]


def rotate_polygon_to_axes(polygon):
    """
    Rotate a polygon to align with XY axes if the first few vertices form a right angle.

    :param polygon: An array of (X, Y) values in any units system.
    :return rotated_polygon: The input polygon that has been rotated to align
        with XY axes.
    """

    def distance_to_point(pt1, pt2):
        vec = (pt1[0] - pt2[0], pt1[1] - pt2[1])
        return math.sqrt(vec[0] ** 2 + vec[1] ** 2)

    # first make sure that the polygon is oriented counter-clockwise
    bound_poly = polygon[0][:-1]
    poly_area = polygon_area(bound_poly)
    if poly_area < 0:  # clockwise polygon; reverse
        bound_poly = list(reversed(bound_poly))

    # get the point of the polygon representing the lower left corner
    min_pt = lower_left_point(bound_poly)
    pt_dists = []
    for i, point in enumerate(bound_poly):
        dist = distance_to_point(min_pt, point)
        pt_dists.append((dist, i))
    sorted_i = [x for _, x in sorted(pt_dists, key=lambda pair: pair[0])]
    origin_i = sorted_i[0]
    origin = bound_poly[origin_i]
    prev_pt = bound_poly[origin_i - 1]
    next_pt = bound_poly[origin_i + 1] if origin_i < len(bound_poly) - 1 else bound_poly[0]

    # check if there is a need to rotate the polygon
    if origin[0] == min_pt[0] and origin[1] == min_pt[1]:
        return polygon  # polygon is already oriented to XY axes
    vec_1 = (next_pt[0] - origin[0], next_pt[1] - origin[1])
    vec_2 = (prev_pt[0] - origin[0], prev_pt[1] - origin[1])
    if not (89 < vector_angle(vec_1, vec_2) < 91):
        return polygon  # polygon does not have a right angle

    # calculate the angle to rotate the polygon
    y_axis = (0, 1)
    rot_ang = vector_angle_counterclockwise(vec_2, y_axis)
    rot_ang = rot_ang - 360 if rot_ang > 180 else rot_ang

    # rotate the polygon
    rotated_polygon = []
    for o_poly in polygon:
        rotated_polygon.append([rotate(pt, rot_ang, origin) for pt in o_poly])

    # ensure all points are positive, shift if not
    x_shift = 0
    y_shift = 0

    for this_polygon in rotated_polygon:
        for coord_pair in this_polygon:
            if coord_pair[0] < 0:
                x_shift = max(abs(coord_pair[0]), x_shift)
            if coord_pair[1] < 0:
                y_shift = max(abs(coord_pair[1]), y_shift)

    rotated_polygon = [[(x + x_shift, y + y_shift) for x, y in this_polygon] for this_polygon in rotated_polygon]

    return rotated_polygon
