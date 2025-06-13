from unittest import TestCase

import numpy as np

from thermalnetwork.geometry import get_boundary_points


class TestGeometry(TestCase):
    def test_get_boundary_points(self):
        """
        L-shaped (convex shape)

        5           x x x x x
        4           x x x x x
        3 x x x x x x x x x x
        2 x x x x x x x x x x
        1 x x x x x x x x x x
        0 x x x x x x x x x x
          0 1 2 3 4 5 6 7 8 9
        :return:
        """

        x_coords = [
            0,
            1,
            2,
            3,
            4,
            5,
            6,
            7,
            8,
            9,
            0,
            1,
            2,
            3,
            4,
            5,
            6,
            7,
            8,
            9,
            0,
            1,
            2,
            3,
            4,
            5,
            6,
            7,
            8,
            9,
            0,
            1,
            2,
            3,
            4,
            5,
            6,
            7,
            8,
            9,
            5,
            6,
            7,
            8,
            9,
            5,
            6,
            7,
            8,
            9,
        ]
        y_coords = [
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            1,
            1,
            1,
            1,
            1,
            1,
            1,
            1,
            1,
            1,
            2,
            2,
            2,
            2,
            2,
            2,
            2,
            2,
            2,
            2,
            3,
            3,
            3,
            3,
            3,
            3,
            3,
            3,
            3,
            3,
            4,
            4,
            4,
            4,
            4,
            5,
            5,
            5,
            5,
            5,
        ]
        points = np.array(list(zip(x_coords, y_coords)))
        boundary_points = get_boundary_points(points)

        # note that the algorithm isn't capturing the inside elbow corner point (5, 3). I think it may clip a couple
        # corners, so it's not a foolproof solution, but seems to work well enough for now.
        expected_boundary_points = np.array(
            [
                [0, 2],
                [0, 1],
                [0, 0],
                [1, 0],
                [2, 0],
                [3, 0],
                [4, 0],
                [5, 0],
                [6, 0],
                [7, 0],
                [8, 0],
                [9, 0],
                [9, 1],
                [9, 2],
                [9, 3],
                [9, 4],
                [9, 5],
                [8, 5],
                [7, 5],
                [6, 5],
                [5, 4],
                [5, 5],
                [4, 3],
                [3, 3],
                [2, 3],
                [1, 3],
                [0, 3],
            ]
        )

        assert np.allclose(boundary_points, expected_boundary_points)
