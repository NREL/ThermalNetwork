from math import log, pi

from loguru import logger

from thermalnetwork.enums import FluidTypes
from thermalnetwork.fluid import get_fluid
from thermalnetwork.utilities import inch_to_m, smoothing_function


class Pipe:
    def __init__(
        self,
        dimension_ratio: float,
        length: float,
        fluid_type_str: FluidTypes = FluidTypes.WATER.name,
        fluid_concentration: float = 0,
        fluid_temperature: float = 20,
    ):
        self.fluid = get_fluid(fluid_type_str, fluid_concentration)
        self.fluid_temp = fluid_temperature

        # ratio of outer diameter to wall thickness
        self.dimension_ratio = dimension_ratio

        # set length
        self.length = length

        # placeholders
        self.outer_diameter = None
        self.inner_diameter = None

    def set_diameters(self, outer_dia: float):
        """
        Sets the outer and inner diameters member variables.

        :param outer_dia: outer diameter of the pipe
        :return: inner diameter of the pipe
        """
        self.inner_diameter = outer_dia * (1 - 2 / self.dimension_ratio)
        self.outer_diameter = outer_dia

    def friction_factor(self, re: float) -> float:
        """
        Calculates the friction factor in smooth tubes

        Petukhov, B.S. 1970. 'Heat transfer and friction in turbulent pipe flow with variable physical properties.'
        In Advances in Heat Transfer, ed. T.F. Irvine and J.P. Hartnett, Vol. 6. New York Academic Press.

        :param re: Reynolds number, dimensionless
        """

        # limits picked be within about 1% of actual values
        low_reynolds = 2000
        high_reynolds = 4000

        if re < low_reynolds:
            return self.laminar_friction_factor(re)
        if re > high_reynolds:
            return self.turbulent_friction_factor(re)

        # pure laminar flow
        f_low = self.laminar_friction_factor(re)

        # pure turbulent flow
        f_high = self.turbulent_friction_factor(re)

        return smoothing_function(re, low_reynolds, high_reynolds, f_low, f_high)

    @staticmethod
    def laminar_friction_factor(re: float):
        """
        Laminar friction factor

        :param re: Reynolds number
        :return: friction factor
        """

        return 64.0 / re

    @staticmethod
    def turbulent_friction_factor(re: float):
        """
        Turbulent friction factor

        Petukhov, B. S. (1970). Advances in Heat Transfer, volume 6, Heat transfer and
        friction in turbulent pipe flow with variable physical properties, pages 503-564.
        Academic Press, Inc., New York, NY.

        :param re: Reynolds number
        :return: friction factor
        """

        return (0.79 * log(re) - 1.64) ** (-2.0)

    def vol_flow_rate_to_velocity(self, vol_flow_rate: float) -> float:
        """
        Converts volume flow rate to velocity.

        :param vol_flow_rate: volume flow rate, in m3/s
        :return: mean fluid velocity in m/s
        """
        pipe_inner_cross_section_area = (pi * self.inner_diameter**2) / 4
        return vol_flow_rate / pipe_inner_cross_section_area

    def vol_flow_rate_to_re(self, vol_flow_rate: float) -> float:
        velocity = self.vol_flow_rate_to_velocity(vol_flow_rate)
        density = self.fluid.density(self.fluid_temp)
        viscosity = self.fluid.viscosity(self.fluid_temp)
        return density * velocity * self.inner_diameter / viscosity

    def pressure_loss(self, vol_flow_rate: float) -> float:
        """
        Pressure loss in straight pipe

        :param vol_flow_rate: volume flow rate, m3/s
        :return: pressure loss, Pa
        """

        if vol_flow_rate <= 0:
            return 0

        re = self.vol_flow_rate_to_re(vol_flow_rate)
        velocity = self.vol_flow_rate_to_velocity(vol_flow_rate)
        term_1 = self.friction_factor(re) * self.length / self.inner_diameter
        term_2 = (self.fluid.density(self.fluid_temp) * velocity**2) / 2

        return term_1 * term_2

    def pressure_loss_per_length(self, vol_flow_rate, outside_diameter: float) -> float:
        self.set_diameters(outside_diameter)
        return self.pressure_loss(vol_flow_rate) / self.length

    def size_hydraulic_diameter(
        self,
        vol_flow_rate: float,
        design_pressure_loss_per_length: float,
        return_discrete_pipe_size: bool = True,
    ) -> float:
        """
        Size the pipe diameter to meet the design pressure loss requirements.

        :param vol_flow_rate: volumetric flow rate, in m3/s
        :param design_pressure_loss_per_length: design pressure loss per meter, in Pa/m.
        Typically, this will be 100-300 Pa/m.
        :param return_discrete_pipe_size: setting True will return a discrete pipe size
        that meets the design pressure loss requirements. setting False will return the
        fractional pipe size that meets the design pressure
        loss requirements.
        :return:
        """

        # this is the default and likely to be the most common use case, so we'll put it first
        if return_discrete_pipe_size:
            # https://www.dropbox.com/scl/fi/68q6h2q5kmsi5e5j7cwdl/HDPE-Pipe-Dimensions.pdf?rlkey=lp0t83df3ut8uizdrftg34318&e=1&st=xjbm19cj&dl=0
            ip_pipes = {
                "labels": [
                    '3/4"',
                    '1"',
                    '1-1/4"',
                    '1-1/2"',
                    '2"',
                    '3"',
                    '4"',
                    '5"',
                    '6"',
                    '7"',
                    '8"',
                    '10"',
                    '12"',
                    '14"',
                    '16"',
                    '18"',
                    '20"',
                    '22"',
                    '24"',
                    '26"',
                    '28"',
                    '30"',
                    '32"',
                    '34"',
                    '36"',
                    '42"',
                    '48"',
                    '54"',
                    '63"',
                ],
                "outside_diameter": [
                    1.05,
                    1.315,
                    1.66,
                    1.90,
                    2.375,
                    3.50,
                    4.50,
                    5.563,
                    6.625,
                    7.125,
                    8.625,
                    10.75,
                    12.75,
                    14.00,
                    16.00,
                    18.00,
                    20.00,
                    22.00,
                    24.00,
                    26.00,
                    28.00,
                    30.00,
                    32.00,
                    34.00,
                    36.00,
                    42.00,
                    48.00,
                    54.00,
                    63.00,
                ],
            }

            for idx, d in enumerate(ip_pipes["outside_diameter"]):
                pressure_loss_per_length = self.pressure_loss_per_length(vol_flow_rate, inch_to_m(d))
                if pressure_loss_per_length < design_pressure_loss_per_length:
                    logger.info(f"Network pipe sized to {ip_pipes['labels'][idx]}, SDR-{self.dimension_ratio}")
                    return self.inner_diameter

            logger.info(f"Network pipe sized to {ip_pipes['labels'][-1]}, SDR-{self.dimension_ratio}.")
            logger.warning("Maximum available pipe size used. This may result in unexpected results.")
            return self.inner_diameter

        # if we've made it this far, we're going to need to search for a continuous pipe size
        # that meets the design conditions.

        ## bisection search to find size that meets design condition
        low_od = 0.025  # meter
        high_od = 0.5  # meter

        # find high diameter limit that bounds solution
        high_pressure_loss_per_length = self.pressure_loss_per_length(vol_flow_rate, high_od)
        while high_pressure_loss_per_length > design_pressure_loss_per_length:
            high_od += 0.5
            high_pressure_loss_per_length = self.pressure_loss_per_length(vol_flow_rate, high_od)

        # set test pressure loss high for first iteration
        test_pressure_loss_per_length = 100000

        # bisection search
        pressure_loss_tolerance = 0.1  # Pa/m
        while abs(test_pressure_loss_per_length - design_pressure_loss_per_length) > pressure_loss_tolerance:
            test_dia = (low_od + high_od) / 2
            test_pressure_loss_per_length = self.pressure_loss_per_length(vol_flow_rate, test_dia)
            if (test_pressure_loss_per_length - design_pressure_loss_per_length) > 0:
                # adjust lower bound
                low_od = test_dia
            else:
                # adjust upper bound
                high_od = test_dia

        return self.inner_diameter
