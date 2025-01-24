import logging

from scp.ethyl_alcohol import EthylAlcohol
from scp.ethylene_glycol import EthyleneGlycol
from scp.methyl_alcohol import MethylAlcohol
from scp.propylene_glycol import PropyleneGlycol
from scp.water import Water


def get_fluid(fluid_type: str, fluid_concentration: float = 0):
    if fluid_concentration < 0:
        logging.warning("Attempting to set <0 water-antifreeze mixture concentration.")
        logging.warning("Expect fluid concentration 0 <= x <= 0.6")
        logging.warning("Defaulting to 0.")
        fluid_concentration = 0

    fluid_name = fluid_type.upper()
    if fluid_name == "WATER":
        if fluid_concentration == 0:
            return Water()
        else:
            logging.warning(f'Fluid "{fluid_name}" - attempting to set non-zero \
                            water-antifreeze mixture concentration "{fluid_concentration:0.3f}".')
            logging.warning("Defaulting to pure water.")
            return Water()

    if fluid_concentration == 0:
        logging.warning(f'Setting fluid "{fluid_name} with fluid-antifreeze mixture concentration = 0')

    if fluid_name == "ETHYLALCOHOL":
        return EthylAlcohol(fluid_concentration)
    elif fluid_name == "ETHYLENEGLYCOL":
        return EthyleneGlycol(fluid_concentration)
    elif fluid_name == "METHYLALCOHOL":
        return MethylAlcohol(fluid_concentration)
    elif fluid_name == "PROPYLENEGLYCOL":
        return PropyleneGlycol(fluid_concentration)
    else:
        logging.error(f'Unsupported fluid "{fluid_name}"')
        assert False
