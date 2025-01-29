import json
from math import exp
from pathlib import Path


def lps_to_cms(x: float) -> float:
    """
    Convert liters per second to meters cubed per second

    :param x: input value, in liters per second
    :return: converted value, in meters cubed per second
    """

    return x * 0.001


def inch_to_m(x_inch: float) -> float:
    """
    Convert inches to meters

    :param x_inch: value to convert, inches
    :return: float value, meters
    """
    return x_inch * 0.0254


def write_json(write_path: Path, input_dict: dict, indent: int = 2, sort_keys: bool = False) -> None:
    with write_path.open("w") as f:
        f.write(json.dumps(input_dict, sort_keys=sort_keys, indent=indent, separators=(",", ": ")))


def load_json(read_path: Path) -> dict:
    return json.loads(read_path.read_text())


def smoothing_function(x, x_low_limit, x_high_limit, y_low_limit, y_high_limit) -> float:
    """
    Sigmoid smoothing function

    https://en.wikipedia.org/wiki/Sigmoid_function

    :param x: independent variable
    :param x_low_limit: lower limit on x range
    :param x_high_limit: upper limit on x range
    :param y_low_limit: lower limit on y range
    :param y_high_limit: upper limit on y range
    :return smoothed value between x_low_limit and x_high_limit. returns y_low_limit and y_high_limit
    below and above the x_low_limit and x_high_limit, respectively.
    """

    # check lower and upper bounds
    if x < x_low_limit:
        return y_low_limit

    if x > x_high_limit:
        return y_high_limit

    # interp x range to value between -10 to 10 for sigmoid function
    s_x_max = 10
    s_x_min = -10
    s_x = (x - x_low_limit) / (x_high_limit - x_low_limit) * (s_x_max - s_x_min) + s_x_min

    # get sigmoid function for interpolation between real y values
    s_y = 1 / (1 + exp(-s_x))

    # finally interpolate to the final value
    return s_y * (y_high_limit - y_low_limit) + y_low_limit
