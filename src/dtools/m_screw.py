import enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dtools.workplane import Workplane


class MScrew(enum.Enum):
    M1_6 = {
        "thread_pitch": 0.35,
        "body_diameter_max": 1.60,
        "body_diameter_min": 1.46,
        "head_diameter_max": 3.00,
        "head_diameter_min": 2.87,
        "head_height_max": 1.60,
        "head_height_min": 1.52,
        "chamfer_radius": 0.16,
        "hex_socket_size": 1.5,
        "spline_socket_size": 1.829,
        "key_engagement": 0.80,
        "transition_dia_min": 2.0,
        "transition_dia_max": 2.0,
        # Legacy attributes for backward compatibility
        "core_diameter": 1.6,
        "heatsert_diameter": 3.5,
        "heatsert_depth": 4,
        "pilot_hole_diameter": 1.6,
    }
    M2 = {
        "thread_pitch": 0.4,
        "body_diameter_max": 2.00,
        "body_diameter_min": 1.86,
        "head_diameter_max": 3.80,
        "head_diameter_min": 3.65,
        "head_height_max": 2.00,
        "head_height_min": 1.91,
        "chamfer_radius": 0.20,
        "hex_socket_size": 1.5,
        "spline_socket_size": 1.829,
        "key_engagement": 1.00,
        "transition_dia_min": 2.6,
        "transition_dia_max": 2.6,
        # Legacy attributes for backward compatibility
        "core_diameter": 2.0,
        "heatsert_diameter": 3.5,
        "heatsert_depth": 4,
        "pilot_hole_diameter": 1.6,
    }
    M2_5 = {
        "thread_pitch": 0.45,
        "body_diameter_max": 2.50,
        "body_diameter_min": 2.36,
        "head_diameter_max": 4.50,
        "head_diameter_min": 4.33,
        "head_height_max": 2.50,
        "head_height_min": 2.40,
        "chamfer_radius": 0.25,
        "hex_socket_size": 2.0,
        "spline_socket_size": 2.438,
        "key_engagement": 1.25,
        "transition_dia_min": 3.1,
        "transition_dia_max": 3.1,
        # Legacy attributes for backward compatibility
        "core_diameter": 2.5,
        "heatsert_diameter": 4.0,
        "heatsert_depth": 5.0,
        "pilot_hole_diameter": 2.0,
    }
    M3 = {
        "thread_pitch": 0.5,
        "body_diameter_max": 3.00,
        "body_diameter_min": 2.86,
        "head_diameter_max": 5.50,
        "head_diameter_min": 5.32,
        "head_height_max": 3.00,
        "head_height_min": 2.89,
        "chamfer_radius": 0.30,
        "hex_socket_size": 2.5,
        "spline_socket_size": 2.819,
        "key_engagement": 1.50,
        "transition_dia_min": 3.6,
        "transition_dia_max": 3.6,
        # Legacy attributes for backward compatibility
        "core_diameter": 3.0,
        "heatsert_diameter": 4.0,
        "heatsert_depth": 5.8,
        "pilot_hole_diameter": 2.5,
    }
    M4 = {
        "thread_pitch": 0.7,
        "body_diameter_max": 4.00,
        "body_diameter_min": 3.82,
        "head_diameter_max": 7.00,
        "head_diameter_min": 6.80,
        "head_height_max": 4.00,
        "head_height_min": 3.88,
        "chamfer_radius": 0.40,
        "hex_socket_size": 3.0,
        "spline_socket_size": 3.378,
        "key_engagement": 2.00,
        "transition_dia_min": 4.7,
        "transition_dia_max": 4.7,
        # Legacy attributes for backward compatibility
        "core_diameter": 4.0,
        "heatsert_diameter": 5.6,
        "heatsert_depth": 8.1,
        "pilot_hole_diameter": 3.3,
    }
    M5 = {
        "thread_pitch": 0.8,
        "body_diameter_max": 5.00,
        "body_diameter_min": 4.82,
        "head_diameter_max": 8.50,
        "head_diameter_min": 8.27,
        "head_height_max": 5.00,
        "head_height_min": 4.86,
        "chamfer_radius": 0.50,
        "hex_socket_size": 4.0,
        "spline_socket_size": 4.648,
        "key_engagement": 2.50,
        "transition_dia_min": 5.7,
        "transition_dia_max": 5.7,
        # Legacy attributes for backward compatibility
        "core_diameter": 5.0,
        "heatsert_diameter": 6.4,
        "heatsert_depth": 9.5,
        "pilot_hole_diameter": 4.2,
    }
    M6 = {
        "thread_pitch": 1.0,
        "body_diameter_max": 6.00,
        "body_diameter_min": 5.82,
        "head_diameter_max": 10.00,
        "head_diameter_min": 9.74,
        "head_height_max": 6.00,
        "head_height_min": 5.85,
        "chamfer_radius": 0.60,
        "hex_socket_size": 5.0,
        "spline_socket_size": 5.486,
        "key_engagement": 3.00,
        "transition_dia_min": 6.8,
        "transition_dia_max": 6.8,
        # Legacy attributes for backward compatibility
        "core_diameter": 6.0,
        "heatsert_diameter": 8.0,
        "heatsert_depth": 12.7,
        "pilot_hole_diameter": 5.0,
    }
    M8 = {
        "thread_pitch": 1.25,
        "body_diameter_max": 8.00,
        "body_diameter_min": 7.78,
        "head_diameter_max": 13.00,
        "head_diameter_min": 12.70,
        "head_height_max": 8.00,
        "head_height_min": 7.83,
        "chamfer_radius": 0.80,
        "hex_socket_size": 6.0,
        "spline_socket_size": 7.391,
        "key_engagement": 4.00,
        "transition_dia_min": 9.2,
        "transition_dia_max": 9.2,
        # Legacy attributes for backward compatibility
        "core_diameter": 8.0,
        "heatsert_diameter": 10.0,
        "heatsert_depth": 15.0,
        "pilot_hole_diameter": 6.8,
    }
    M10 = {
        "thread_pitch": 1.5,
        "body_diameter_max": 10.00,
        "body_diameter_min": 9.78,
        "head_diameter_max": 16.00,
        "head_diameter_min": 15.67,
        "head_height_max": 10.00,
        "head_height_min": 9.81,
        "chamfer_radius": 1.00,
        "hex_socket_size": 8.0,
        "spline_socket_size": None,  # Not specified in table
        "key_engagement": 5.00,
        "transition_dia_min": 11.2,
        "transition_dia_max": 11.2,
        # Legacy attributes for backward compatibility
        "core_diameter": 10.0,
        "heatsert_diameter": 12.0,
        "heatsert_depth": 18.0,
        "pilot_hole_diameter": 8.5,
    }
    M12 = {
        "thread_pitch": 1.75,
        "body_diameter_max": 12.00,
        "body_diameter_min": 11.73,
        "head_diameter_max": 18.00,
        "head_diameter_min": 17.63,
        "head_height_max": 12.00,
        "head_height_min": 11.79,
        "chamfer_radius": 1.20,
        "hex_socket_size": 10.0,
        "spline_socket_size": None,  # Not specified in table
        "key_engagement": 6.00,
        "transition_dia_min": 14.2,
        "transition_dia_max": 14.2,
        # Legacy attributes for backward compatibility
        "core_diameter": 12.0,
        "heatsert_diameter": 14.0,
        "heatsert_depth": 20.0,
        "pilot_hole_diameter": 10.2,
    }
    M14 = {
        "thread_pitch": 2.0,
        "body_diameter_max": 14.00,
        "body_diameter_min": 13.73,
        "head_diameter_max": 21.00,
        "head_diameter_min": 20.60,
        "head_height_max": 14.00,
        "head_height_min": 13.77,
        "chamfer_radius": 1.40,
        "hex_socket_size": 12.0,
        "spline_socket_size": None,  # Not specified in table
        "key_engagement": 7.00,
        "transition_dia_min": 16.2,
        "transition_dia_max": 16.2,
        # Legacy attributes for backward compatibility
        "core_diameter": 14.0,
        "heatsert_diameter": 16.0,
        "heatsert_depth": 22.0,
        "pilot_hole_diameter": 12.0,
    }
    M16 = {
        "thread_pitch": 2.0,
        "body_diameter_max": 16.00,
        "body_diameter_min": 15.73,
        "head_diameter_max": 24.00,
        "head_diameter_min": 23.58,
        "head_height_max": 16.00,
        "head_height_min": 15.76,
        "chamfer_radius": 1.60,
        "hex_socket_size": 14.0,
        "spline_socket_size": None,  # Not specified in table
        "key_engagement": 8.00,
        "transition_dia_min": 18.2,
        "transition_dia_max": 18.2,
        # Legacy attributes for backward compatibility
        "core_diameter": 16.0,
        "heatsert_diameter": 18.0,
        "heatsert_depth": 24.0,
        "pilot_hole_diameter": 14.0,
    }
    M20 = {
        "thread_pitch": 2.5,
        "body_diameter_max": 20.00,
        "body_diameter_min": 19.67,
        "head_diameter_max": 30.00,
        "head_diameter_min": 29.53,
        "head_height_max": 20.00,
        "head_height_min": 19.73,
        "chamfer_radius": 2.00,
        "hex_socket_size": 17.0,
        "spline_socket_size": None,  # Not specified in table
        "key_engagement": 10.00,
        "transition_dia_min": 22.4,
        "transition_dia_max": 22.4,
        # Legacy attributes for backward compatibility
        "core_diameter": 20.0,
        "heatsert_diameter": 22.0,
        "heatsert_depth": 28.0,
        "pilot_hole_diameter": 17.5,
    }
    M24 = {
        "thread_pitch": 3.0,
        "body_diameter_max": 24.00,
        "body_diameter_min": 23.67,
        "head_diameter_max": 36.00,
        "head_diameter_min": 35.48,
        "head_height_max": 24.00,
        "head_height_min": 23.70,
        "chamfer_radius": 2.40,
        "hex_socket_size": 19.0,
        "spline_socket_size": None,  # Not specified in table
        "key_engagement": 12.00,
        "transition_dia_min": 26.4,
        "transition_dia_max": 26.4,
        # Legacy attributes for backward compatibility
        "core_diameter": 24.0,
        "heatsert_diameter": 26.0,
        "heatsert_depth": 32.0,
        "pilot_hole_diameter": 21.0,
    }
    M30 = {
        "thread_pitch": 3.5,
        "body_diameter_max": 30.00,
        "body_diameter_min": 29.67,
        "head_diameter_max": 45.00,
        "head_diameter_min": 44.42,
        "head_height_max": 30.00,
        "head_height_min": 29.67,
        "chamfer_radius": 3.00,
        "hex_socket_size": 22.0,
        "spline_socket_size": None,  # Not specified in table
        "key_engagement": 15.00,
        "transition_dia_min": 33.4,
        "transition_dia_max": 33.4,
        # Legacy attributes for backward compatibility
        "core_diameter": 30.0,
        "heatsert_diameter": 32.0,
        "heatsert_depth": 38.0,
        "pilot_hole_diameter": 26.5,
    }
    M36 = {
        "thread_pitch": 4.0,
        "body_diameter_max": 36.00,
        "body_diameter_min": 35.61,
        "head_diameter_max": 54.00,
        "head_diameter_min": 53.37,
        "head_height_max": 36.00,
        "head_height_min": 35.64,
        "chamfer_radius": 3.60,
        "hex_socket_size": 27.0,
        "spline_socket_size": None,  # Not specified in table
        "key_engagement": 18.00,
        "transition_dia_min": 39.4,
        "transition_dia_max": 39.4,
        # Legacy attributes for backward compatibility
        "core_diameter": 36.0,
        "heatsert_diameter": 38.0,
        "heatsert_depth": 44.0,
        "pilot_hole_diameter": 32.0,
    }
    M42 = {
        "thread_pitch": 4.5,
        "body_diameter_max": 42.00,
        "body_diameter_min": 41.61,
        "head_diameter_max": 63.00,
        "head_diameter_min": 62.31,
        "head_height_max": 42.00,
        "head_height_min": 41.61,
        "chamfer_radius": 4.20,
        "hex_socket_size": 32.0,
        "spline_socket_size": None,  # Not specified in table
        "key_engagement": 21.00,
        "transition_dia_min": 45.6,
        "transition_dia_max": 45.6,
        # Legacy attributes for backward compatibility
        "core_diameter": 42.0,
        "heatsert_diameter": 44.0,
        "heatsert_depth": 50.0,
        "pilot_hole_diameter": 37.5,
    }
    M48 = {
        "thread_pitch": 5.0,
        "body_diameter_max": 48.00,
        "body_diameter_min": 47.61,
        "head_diameter_max": 72.00,
        "head_diameter_min": 71.27,
        "head_height_max": 48.00,
        "head_height_min": 47.58,
        "chamfer_radius": 4.80,
        "hex_socket_size": 36.0,
        "spline_socket_size": None,  # Not specified in table
        "key_engagement": 24.00,
        "transition_dia_min": 52.6,
        "transition_dia_max": 52.6,
        # Legacy attributes for backward compatibility
        "core_diameter": 48.0,
        "heatsert_diameter": 50.0,
        "heatsert_depth": 56.0,
        "pilot_hole_diameter": 43.0,
    }

    def __init__(self, attributes: dict[str, float]):
        # ANSI specification attributes
        self.thread_pitch = attributes["thread_pitch"]
        self.body_diameter_max = attributes["body_diameter_max"]
        self.body_diameter_min = attributes["body_diameter_min"]
        self.head_diameter_max = attributes["head_diameter_max"]
        self.head_diameter_min = attributes["head_diameter_min"]
        self.head_height_max = attributes["head_height_max"]
        self.head_height_min = attributes["head_height_min"]
        self.chamfer_radius = attributes["chamfer_radius"]
        self.hex_socket_size = attributes["hex_socket_size"]
        self.spline_socket_size = attributes.get("spline_socket_size")
        self.key_engagement = attributes["key_engagement"]
        self.transition_dia_min = attributes["transition_dia_min"]
        self.transition_dia_max = attributes["transition_dia_max"]

        # Legacy attributes for backward compatibility
        self.head_diameter = attributes[
            "head_diameter_max"
        ]  # Use max for backward compatibility
        self.core_diameter = attributes["core_diameter"]
        self.heatsert_diameter = attributes["heatsert_diameter"]
        self.heatsert_depth = attributes["heatsert_depth"]
        self.pilot_hole_diameter = attributes["pilot_hole_diameter"]


def create_screw_core_hole(wp: "Workplane", screw: MScrew, depth: float) -> "Workplane":
    return wp.circle(screw.core_diameter / 2).extrude(depth)


def create_screw_hole(
    wp: "Workplane",
    screw: MScrew,
    core_depth: float,
    head_on_top: bool = True,
    head_height: float | None = None,
    clearance: float = 0.2,
) -> "Workplane":
    head_height = head_height or screw.head_height_max
    core = wp.circle(screw.body_diameter_max / 2 + clearance).extrude(core_depth)
    head = wp.circle(screw.head_diameter_max / 2 + clearance).extrude(head_height)
    if head_on_top:
        head = head.translate((0, 0, core_depth))
    else:
        core = core.translate((0, 0, head_height))
    return head + core
