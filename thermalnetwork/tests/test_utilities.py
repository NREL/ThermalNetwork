import unittest

from thermalnetwork.utilities import smoothing_function


class TestUtilities(unittest.TestCase):
    def test_smoothing_function(self):
        self.assertAlmostEqual(smoothing_function(0, 0, 10, 0, 10), 0, delta=1e-3)
        self.assertAlmostEqual(smoothing_function(5, 0, 10, 0, 10), 5, delta=1e-3)
        self.assertAlmostEqual(smoothing_function(10, 0, 10, 0, 10), 10, delta=1e-3)
