from enum import Enum, auto


class DesignType(Enum):
    AREAPROPORTIONAL = auto()
    UPSTREAM = auto()


class ComponentType(Enum):
    ENERGYTRANSFERSTATION = auto()
    FAN = auto()
    GROUNDHEATEXCHANGER = auto()
    HEATPUMP = auto()
    PUMP = auto()


class HeatPumpType(Enum):
    COOLING = auto()
    DHW = auto()
    HEATING = auto()


class FluidTypes(Enum):
    ETHYLALCOHOL = auto()
    ETHYLENEGLYCOL = auto()
    METHYLALCOHOL = auto()
    PROPYLENEGLYCOL = auto()
    WATER = auto()


class GHEDesignType(Enum):
    AUTOSIZED_BIRECTANGLE_CONSTRAINED_BOREFIELD = auto()
    AUTOSIZED_BIZONED_RECTANGLE_BOREFIELD = auto()
    AUTOSIZED_NEAR_SQUARE_BOREFIELD = auto()
    AUTOSIZED_RECTANGLE_BOREFIELD = auto()
    AUTOSIZED_RECTANGLE_CONSTRAINED_BOREFIELD = auto()
    AUTOSIZED_ROWWISE_BOREFIELD = auto()
    PREDESIGNED_BOREFIELD = auto()
