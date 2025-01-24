import unittest
from math import log

from thermalnetwork.fluid import PropyleneGlycol, Water
from thermalnetwork.pipe import Pipe
from thermalnetwork.utilities import inch_to_m


class TestPipe(unittest.TestCase):
    def test_init(self):
        # test water
        pipe = Pipe(
            dimension_ratio=11,
            length=100,
        )

        self.assertIsInstance(pipe, Pipe)
        self.assertEqual(pipe.length, 100)
        self.assertIsInstance(pipe.fluid, Water)

        # test propylene glycol
        pg_pipe = Pipe(dimension_ratio=11, length=100, fluid_type="PROPYLENEGLYCOL", fluid_concentration=0.2)

        self.assertIsInstance(pg_pipe, Pipe)
        self.assertEqual(pg_pipe.length, 100)
        self.assertIsInstance(pg_pipe.fluid, PropyleneGlycol)
        self.assertEqual(pg_pipe.fluid.x, 0.2)

    def test_set_diameters(self):
        pipe = Pipe(
            dimension_ratio=11,
            length=100,
        )

        # 1-1/4" HDPE, SDR-11. Returned value within 1.5% of tabulated value
        outer_dia_inches = 1.66
        pipe.set_diameters(inch_to_m(outer_dia_inches))
        self.assertAlmostEqual(pipe.outer_diameter, inch_to_m(outer_dia_inches), delta=0.0001)
        self.assertAlmostEqual(pipe.inner_diameter, inch_to_m(1.36), delta=0.0001)

    def test_friction_factor(self):
        tol = 0.00001

        pipe = Pipe(dimension_ratio=11, length=100)

        pipe.set_diameters(0.0334)

        # laminar tests
        re = 100
        self.assertEqual(pipe.friction_factor(re), 64.0 / re)

        re = 1000
        self.assertEqual(pipe.friction_factor(re), 64.0 / re)

        re = 1400
        self.assertEqual(pipe.friction_factor(re), 64.0 / re)

        # transitional tests
        re = 2000
        self.assertAlmostEqual(pipe.friction_factor(re), 0.034003503, delta=tol)

        re = 3000
        self.assertAlmostEqual(pipe.friction_factor(re), 0.033446219, delta=tol)

        re = 4000
        self.assertAlmostEqual(pipe.friction_factor(re), 0.03895358, delta=tol)

        # turbulent tests
        re = 5000
        self.assertEqual(pipe.friction_factor(re), (0.79 * log(re) - 1.64) ** (-2.0))

        re = 15000
        self.assertEqual(pipe.friction_factor(re), (0.79 * log(re) - 1.64) ** (-2.0))

        re = 25000
        self.assertEqual(pipe.friction_factor(re), (0.79 * log(re) - 1.64) ** (-2.0))

    def test_vol_flow_rate_to_velocity(self):
        pipe = Pipe(
            dimension_ratio=11,
            length=100,
        )

        pipe.set_diameters(0.0334)
        self.assertAlmostEqual(pipe.vol_flow_rate_to_velocity(0.001), 1.75, delta=0.1)

    def test_vol_flow_to_re(self):
        pipe = Pipe(
            dimension_ratio=11,
            length=100,
        )

        pipe.set_diameters(0.0334)

        # compared against: https://www.engineeringtoolbox.com/reynolds-number-d_237.html
        self.assertAlmostEqual(pipe.vol_flow_rate_to_re(0.001), 46415, delta=1)

    def test_pressure_loss(self):
        pipe = Pipe(
            dimension_ratio=11,
            length=100,
        )

        pipe.set_diameters(0.0334)

        # compared against: https://www.irrigationking.com/help/irrigation-resources/pressure-loss-calculators/?srsltid=AfmBOoqgG8RfzO0AQSdBNm8vPieVDT32zOppPGjUrzwsIoLN7njBDGg7
        self.assertAlmostEqual(pipe.pressure_loss(0.001), 113185, delta=1)

    def test_size_hydraulic_diameter(self):
        pipe = Pipe(
            dimension_ratio=11,
            length=100,
        )

        # test to find regular pipe sizes
        # 1 lps, sized to 1-1/2"
        self.assertAlmostEqual(pipe.size_hydraulic_diameter(0.001, 300), 0.03948, delta=0.0001)

        # 100 lps, sized to 10"
        self.assertAlmostEqual(pipe.size_hydraulic_diameter(0.1, 300), 0.2234, delta=0.0001)

        # 1000 lps (1 m3/s), sized to 24"
        self.assertAlmostEqual(pipe.size_hydraulic_diameter(1.0, 300), 0.4987, delta=0.0001)

        # 10 m3/s, sized to 63"
        self.assertAlmostEqual(pipe.size_hydraulic_diameter(10.0, 300), 1.3092, delta=0.0001)

        # 100 m3/s, sized to 63" with warning about being above max available pipe size
        self.assertAlmostEqual(pipe.size_hydraulic_diameter(100.0, 300), 1.3092, delta=0.0001)

        # test to find exact pipe sizes
        # 1 lps
        self.assertAlmostEqual(pipe.size_hydraulic_diameter(0.001, 300, False), 0.03611, delta=0.0001)

        # 100 lps
        self.assertAlmostEqual(pipe.size_hydraulic_diameter(0.1, 300, False), 0.2024, delta=0.0001)

        # 10 m3/s
        self.assertAlmostEqual(pipe.size_hydraulic_diameter(10.0, 300, False), 1.1671, delta=0.0001)
