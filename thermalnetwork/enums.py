from enum import auto, Enum


class DesignType(Enum):
    AREAPROPORTIONAL = auto()
    UPSTREAM = auto()


class ComponentType(Enum):
    ENERGYTRANSFERSTATION = auto()
    FAN = auto()
    GROUNDHEATEXCHANGER = auto()  # TODO: rename to GHE
    HEATPUMP = auto()
    PUMP = auto()
