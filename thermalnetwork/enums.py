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
    HEATING = auto()
    COOLING = auto()
    DHW = auto()


class FluidTypes(Enum):
    ETHYLALCOHOL = auto()
    ETHYLENEGLYCOL = auto()
    METHYLALCOHOL = auto()
    PROPYLENEGLYCOL = auto()
    WATER = auto()
