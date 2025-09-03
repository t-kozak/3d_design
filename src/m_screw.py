import enum


class MScrew(enum.Enum):
    M2 = {
        "head_diameter": 3.8,
        "core_diameter": 2,
        "heatsert_diameter": 3.5,
        "heatsert_depth": 4,
        "pilot_hole_diameter": 1.6,
    }
    M3 = {
        "head_diameter": 5.5,
        "core_diameter": 3,
        "heatsert_diameter": 4,
        "heatsert_depth": 5.8,
        "pilot_hole_diameter": 2.5,
    }
    M4 = {
        "head_diameter": 7.0,
        "core_diameter": 4,
        "heatsert_diameter": 5.6,
        "heatsert_depth": 8.1,
        "pilot_hole_diameter": 3.3,
    }
    M5 = {
        "head_diameter": 8.5,
        "core_diameter": 5,
        "heatsert_diameter": 6.4,
        "heatsert_depth": 9.5,
        "pilot_hole_diameter": 4.2,
    }
    M6 = {
        "head_diameter": 10.0,
        "core_diameter": 6,
        "heatsert_diameter": 8,
        "heatsert_depth": 12.7,
        "pilot_hole_diameter": 5.0,
    }

    def __init__(self, attributes: dict[str, float]):
        self.head_diameter = attributes["head_diameter"]
        self.core_diameter = attributes["core_diameter"]
        self.heatsert_diameter = attributes["heatsert_diameter"]
        self.heatsert_depth = attributes["heatsert_depth"]
        self.pilot_hole_diameter = attributes["pilot_hole_diameter"]
