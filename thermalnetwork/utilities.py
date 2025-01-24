import json
from math import exp
from pathlib import Path


def ft_to_m(x: float) -> float:
    """
    Convert feet to meters

    :param x: input value, in feet
    :return: converted value, in meters
    """

    return x * 0.3048


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


def smoothing_function(x: float, a: float, b: float) -> float:
    """
    Sigmoid smoothing function

    https://en.wikipedia.org/wiki/Sigmoid_function

    :param x: independent variable
    :param a: fitting parameter 1
    :param b: fitting parameter 2
    :return: float between 0-1
    """

    return 1 / (1 + exp(-(x - a) / b))


def write_json(write_path: Path, input_dict: dict, indent: int = 2, sort_keys: bool = False) -> None:
    with write_path.open("w") as f:
        f.write(json.dumps(input_dict, sort_keys=sort_keys, indent=indent, separators=(",", ": ")))


def load_json(read_path: Path) -> dict:
    return json.loads(read_path.read_text())
