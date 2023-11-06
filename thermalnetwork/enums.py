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
