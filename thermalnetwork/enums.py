from enum import auto, Enum


class DesignType(Enum):
    AREAPROPORTIONAL = auto()
    UPSTREAM = auto()


class ComponentType(Enum):
    HEATPUMP = auto()
    GROUNDHEATEXCHANGER = auto()
