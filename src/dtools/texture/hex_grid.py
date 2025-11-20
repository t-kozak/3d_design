import logging
import math
from dataclasses import dataclass
from typing import override

from cadquery import Face
from ocp_vscode import show

from dtools.workplane import Workplane

from .tex_details import Texture

_log = logging.getLogger(__name__)

try:
    from tqdm import tqdm  # pyright: ignore[reportAssignmentType]
except ImportError:
    # Fallback if tqdm is not available
    def tqdm(iterable, desc=None, total=None, disable=False):  # noqa: ARG001
        if disable:
            return iterable
        _log.debug(f"{desc}: Starting...")
        return iterable


@dataclass
class HexGridTexture(Texture):
    hex_diameter: float
    hex_height: float
    side_thickness: float

    @override
    def _create_for_face(self, face: Face) -> Workplane:
        raise NotImplementedError()


def add_texture2(
    workplane: Workplane,
    details: HexGridTexture,
) -> Workplane:
    # --- 1. CALCULATION ---
    d = details.hex_diameter
    h = details.hex_height

    # The flat-to-flat width of a hexagon is d * sqrt(3)/2
    flat_width = d * math.sqrt(3) / 2

    # Spacing for the rectangular arrays
    # We need large gaps in the individual arrays so the second array can fit in between
    x_spacing = d * 1.5
    y_spacing = flat_width

    # Offsets for the second grid (Grid B) to interlock with the first (Grid A)
    x_offset = d * 0.75
    y_offset = flat_width / 2

    # --- 2. POSITIONING ---
    # Get the boundary to determine where to start
    face_b_box = workplane.get_bbox()

    # Central point for the first array
    # (Adjust logic here if you want the array centered on the face vs starting at min)
    # rarray centers the grid at the current location, so we move to the center of the face
    # or the specific start point you chose.
    c_x = face_b_box.xmin - (d * 2.1)
    c_y = face_b_box.ymin - (d * 4.1)

    # Grid counts (ensure enough coverage)
    xc = int(face_b_box.xlen / details.hex_diameter) - 1
    yc = int(face_b_box.ylen / details.hex_diameter) + 3

    # --- 3. GENERATION ---

    # Hexagon Grid A (Base)
    hex1 = (
        workplane.workplane()
        .rarray(xSpacing=x_spacing, ySpacing=y_spacing, xCount=xc, yCount=yc)
        .polygon(6, d)
        .extrude(h)
    )

    t_vec = (10, 10, 15)
    # Hexagon Grid B (Offset)
    hex2 = (
        workplane.workplane()
        .rarray(xSpacing=x_spacing, ySpacing=y_spacing, xCount=xc, yCount=yc)
        .polygon(6, d)
        .extrude(h)
        .translate(t_vec)
    )

    # Holes Grid A (Matches Hex 1 position)
    holes1 = (
        workplane.workplane()
        .translate(t_vec)
        .rarray(xSpacing=x_spacing, ySpacing=y_spacing, xCount=xc, yCount=yc)
        .circle(d * 0.4)
        .extrude(h)
    )

    # Holes Grid B (Matches Hex 2 position)
    holes2 = (
        workplane.workplane()
        .moveTo(c_x + x_offset, c_y + y_offset)
        .rarray(xSpacing=x_spacing, ySpacing=y_spacing, xCount=xc, yCount=yc)
        .circle(d * 0.4)
        .extrude(h)
    )

    # --- 4. BOOLEAN OPERATIONS ---

    # texture = (hex1 - holes1) + (hex2 - holes2)

    texture = hex2
    return hex2
    return workplane + texture


if __name__ == "__main__":
    # Set up logging to see debug messages
    logging.basicConfig(level=logging.DEBUG)

    # Create a simple test case: cube with hex grid on top face
    print("Creating test cube with hex grid texture...")

    box = Workplane("XY").box(50, 50, 10)
    box = add_texture2(
        box.faces(">Z"),
        HexGridTexture(
            hex_diameter=5.0,
            hex_height=2.0,
            side_thickness=0.8,
        ),
    )

    show(box)


# def add_texture(
#     workplane: Workplane,
#     details: HexGridTexture,
#     show_progress: bool = False,
# ) -> Workplane:
#     """
#     Add hexagonal grid texture to the currently selected faces of a workplane.

#     Creates a honeycomb pattern of hexagonal wire outlines with uniform height.

#     Args:
#         workplane: CadQuery workplane with faces selected
#         details: Details of the hex grid texture
#         show_progress: Whether to show progress bars

#     Returns:
#         Workplane with hexagonal grid texture added to selected faces
#     """
#     # Get the selected faces
#     selected_faces = workplane.faces()

#     if len(selected_faces.vals()) == 0:
#         raise ValueError(
#             "No faces selected. Please select faces before applying texture."
#         )

#     result = workplane

#     # Process each selected face
#     for face in tqdm(
#         selected_faces.vals(),
#         desc="Processing faces",
#         disable=not show_progress,
#     ):
#         assert isinstance(face, cq.Face)

#         # Generate hex grid texture for this face
#         hex_texture = _generate_hex_grid_for_face(face, details, show_progress)

#         if not hex_texture:
#             continue

#         # Union with result
#         _log.debug("Union hex texture with result...")
#         result = result.union(hex_texture, clean=False)
#         _log.debug("Union hex texture with result... done")

#     return result


# def _get_face_coordinate_system(
#     face_normal: cq.Vector,
# ) -> tuple[cq.Vector, cq.Vector]:
#     """
#     Calculate proper u and v vectors for a face based on its normal.
#     This ensures consistent orientation across all face types.
#     """
#     # Normalize the normal vector
#     normal = face_normal.normalized()

#     # Choose a reference vector that is guaranteed not to be parallel
#     # We'll test multiple reference vectors to find one that works
#     reference_candidates = [
#         cq.Vector(1, 0, 0),  # X axis
#         cq.Vector(0, 1, 0),  # Y axis
#         cq.Vector(0, 0, 1),  # Z axis
#     ]

#     u_vec = None

#     for reference in reference_candidates:
#         # Calculate cross product
#         cross_result = normal.cross(reference)

#         # Check if cross product has sufficient magnitude (not parallel)
#         cross_magnitude = math.sqrt(
#             cross_result.x**2 + cross_result.y**2 + cross_result.z**2
#         )

#         if cross_magnitude > 1e-6:  # Not parallel (within tolerance)
#             u_vec = cross_result.normalized()
#             break

#     if u_vec is None:
#         # This should never happen with our three orthogonal reference vectors
#         raise ValueError("Could not find suitable reference vector for face normal")

#     # Calculate v vector (second tangent vector, perpendicular to both normal and u)
#     v_vec = normal.cross(u_vec).normalized()

#     return u_vec, v_vec


# def _hex_would_intersect_face(
#     local_x: float,
#     local_y: float,
#     hex_side_len: float,
#     face: cq.Face,
#     face_center: cq.Vector,
#     u_vec: cq.Vector,
#     v_vec: cq.Vector,
# ) -> bool:
#     """
#     Check if a hexagon at the given local coordinates would intersect with the face.
#     This checks if any part of the hexagon intersects with the face boundary.
#     """
#     # Convert local coordinates to 3D world position
#     world_pos = face_center + u_vec.multiply(local_x) + v_vec.multiply(local_y)

#     # Project the world position back onto the face plane
#     # This gives us the 2D coordinates in the face's local coordinate system
#     relative_pos = world_pos - face_center
#     u_proj = relative_pos.dot(u_vec)
#     v_proj = relative_pos.dot(v_vec)

#     # Get face vertices in the face's coordinate system
#     face_vertices = face.outerWire().Vertices()
#     face_2d_points = []

#     for vertex in face_vertices:
#         vertex_pos = vertex.Center()
#         vertex_relative = vertex_pos - face_center
#         vertex_u = vertex_relative.dot(u_vec)
#         vertex_v = vertex_relative.dot(v_vec)
#         face_2d_points.append((vertex_u, vertex_v))

#     # Calculate hexagon vertices in 2D face coordinate system
#     # Hexagon radius (distance from center to vertex)
#     hex_radius = hex_side_len

#     # Generate hexagon vertices (6 vertices of a regular hexagon)
#     hex_vertices = []
#     for i in range(6):
#         angle = i * math.pi / 3  # 60 degrees per vertex
#         hex_u = u_proj + hex_radius * math.cos(angle)
#         hex_v = v_proj + hex_radius * math.sin(angle)
#         hex_vertices.append((hex_u, hex_v))

#     # Check if any hexagon vertex is inside the face
#     for hex_u, hex_v in hex_vertices:
#         if _point_in_polygon(hex_u, hex_v, face_2d_points):
#             return True

#     # Check if any face vertex is inside the hexagon
#     for face_u, face_v in face_2d_points:
#         if _point_in_polygon(face_u, face_v, hex_vertices):
#             return True

#     # Check if any hexagon edge intersects with any face edge
#     for i in range(6):
#         hex_p1 = hex_vertices[i]
#         hex_p2 = hex_vertices[(i + 1) % 6]

#         for j in range(len(face_2d_points)):
#             face_p1 = face_2d_points[j]
#             face_p2 = face_2d_points[(j + 1) % len(face_2d_points)]

#             if _line_segments_intersect(hex_p1, hex_p2, face_p1, face_p2):
#                 return True

#     return False


# def _point_in_polygon(x: float, y: float, polygon: list[tuple[float, float]]) -> bool:
#     """
#     Point-in-polygon test using ray casting algorithm.
#     """
#     n = len(polygon)
#     inside = False

#     p1x, p1y = polygon[0]
#     for i in range(1, n + 1):
#         p2x, p2y = polygon[i % n]
#         if y > min(p1y, p2y):
#             if y <= max(p1y, p2y):
#                 if x <= max(p1x, p2x):
#                     if p1y != p2y:
#                         xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
#                     else:
#                         xinters = p1x  # Handle horizontal edge case
#                     if p1x == p2x or x <= xinters:
#                         inside = not inside
#         p1x, p1y = p2x, p2y

#     return inside


# def _line_segments_intersect(
#     p1: tuple[float, float],
#     p2: tuple[float, float],
#     p3: tuple[float, float],
#     p4: tuple[float, float],
# ) -> bool:
#     """
#     Check if two line segments intersect.
#     """
#     x1, y1 = p1
#     x2, y2 = p2
#     x3, y3 = p3
#     x4, y4 = p4

#     # Calculate the direction of the lines
#     denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)

#     # Lines are parallel
#     if abs(denom) < 1e-10:
#         return False

#     t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
#     u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / denom

#     # Check if intersection point is on both line segments
#     return 0 <= t <= 1 and 0 <= u <= 1


# def _calculate_hex_grid(
#     face: cq.Face,
#     details: HexGridTexture,
#     u_vec: cq.Vector,
#     v_vec: cq.Vector,
# ) -> tuple[int, int, float, float, float, float, float, float]:
#     """
#     Calculate the grid dimensions and spacing for hexagonal texture on a face.

#     Returns:
#         Tuple of (rows, cols, x_spacing, y_spacing, face_width, face_height,
#         half_width, half_height)
#     """
#     # Get face center
#     face_center = face.Center()

#     # Calculate face dimensions in the texture coordinate system
#     # Project face vertices onto the texture plane to get accurate dimensions
#     face_vertices = face.outerWire().Vertices()

#     # Project all vertices onto the texture coordinate system
#     u_coords = []
#     v_coords = []

#     for vertex in face_vertices:
#         vertex_pos = vertex.Center()
#         # Vector from face center to vertex
#         relative_pos = vertex_pos - face_center

#         # Project onto u and v vectors
#         u_proj = relative_pos.dot(u_vec)
#         v_proj = relative_pos.dot(v_vec)

#         u_coords.append(u_proj)
#         v_coords.append(v_proj)

#     # Calculate dimensions in texture coordinate system
#     u_min, u_max = min(u_coords), max(u_coords)
#     v_min, v_max = min(v_coords), max(v_coords)

#     face_width = u_max - u_min
#     face_height = v_max - v_min

#     # Calculate hexagon spacing for proper honeycomb pattern
#     # x_spacing = details.hex_side_len * math.sqrt(3)
#     # y_spacing = details.hex_side_len * 1.5  # For flat-top hexagons

#     # # Add margin of 2x hexagon width
#     # margin = 2 * details.hex_side_len * math.sqrt(3)

#     # Calculate grid dimensions with margin
#     cols = int(math.ceil((face_width + 2 * margin) / x_spacing)) + 1
#     rows = int(math.ceil((face_height + 2 * margin) / y_spacing)) + 1

#     _log.debug(
#         f"Hex grid: {cols} columns × {rows} rows = {cols * rows} potential positions"
#     )

#     half_width = (face_width + 2 * margin) / 2
#     half_height = (face_height + 2 * margin) / 2

#     return (
#         rows,
#         cols,
#         x_spacing,
#         y_spacing,
#         face_width,
#         face_height,
#         half_width,
#         half_height,
#     )


# def _generate_hex_grid_for_face(
#     face: cq.Face,
#     details: HexGridTexture,
#     show_progress: bool = False,
# ) -> Workplane | None:
#     """
#     Generate hexagonal grid texture for a specific face.
#     """
#     _log.debug("Generating hex grid for face...")

#     # Get face center and normal
#     face_center = face.Center()
#     face_normal = face.normalAt()  # type: ignore

#     # Create proper coordinate system for the face
#     u_vec, v_vec = _get_face_coordinate_system(face_normal)

#     # Calculate grid dimensions and spacing
#     (
#         rows,
#         cols,
#         x_spacing,
#         y_spacing,
#         _face_width,
#         _face_height,
#         half_width,
#         half_height,
#     ) = _calculate_hex_grid(face, details, u_vec, v_vec)

#     # Create workplane aligned with the face
#     face_plane_obj = cq.Plane(
#         origin=face_center,
#         xDir=u_vec,
#         normal=face_normal,
#     )
#     face_plane = Workplane(face_plane_obj)

#     # Generate all hexagon positions that would intersect the face
#     hex_positions = []
#     for row in range(rows):
#         for col in range(cols):
#             # Local 2D coordinates in texture plane (relative to face center)
#             local_x = (col * x_spacing) - half_width
#             local_y = (row * y_spacing) - half_height

#             # Offset every other row for honeycomb pattern
#             if row % 2 == 1:
#                 local_x += x_spacing / 2

#             # Check if hexagon would intersect with the face before creating it
#             if _hex_would_intersect_face(
#                 local_x, local_y, details.hex_side_len, face, face_center, u_vec, v_vec
#             ):
#                 hex_positions.append((local_x, local_y))

#     _log.debug(f"Will generate {len(hex_positions)} hexagons")

#     if not hex_positions:
#         _log.debug("Generating hex grid for face... failed - no positions.")
#         return None

#     # Create all hexagon wires and combine them
#     all_wires = []
#     for local_x, local_y in tqdm(
#         hex_positions,
#         desc="Creating hexagon wires",
#         disable=not show_progress,
#     ):
#         try:
#             # Create hexagon wire in the face plane
#             hex_wire = (
#                 face_plane.moveTo(local_x, local_y)
#                 .polygon(6, details.hex_side_len)
#                 .val()
#             )
#             all_wires.append(hex_wire)
#         except Exception as e:
#             _log.warning(f"Could not create hexagon at {local_x}, {local_y}: {e}")
#             continue

#     if not all_wires:
#         _log.debug("Generating hex grid for face... failed - no wires created.")
#         return None

#     # Combine all wires into a single workplane
#     combined_wires = face_plane.newObject(all_wires)

#     # Apply offset2D to create thick outlines
#     _log.debug("Applying offset2D for thickness...")
#     try:
#         # Create outer boundary
#         outer = combined_wires.wires().toPending().offset2D(details.side_thickness / 2)

#         # Create inner boundary
#         inner = combined_wires.wires().toPending().offset2D(-details.side_thickness / 2)

#         # Subtract inner from outer to get thick outline
#         thick_outline = outer.cut(inner)

#     except Exception as e:
#         _log.warning(f"Failed to apply offset2D: {e}")
#         # Fallback: just extrude the wires directly
#         thick_outline = combined_wires.wires().toPending()

#     # Extrude to uniform height
#     _log.debug("Extruding to height...")
#     hex_texture = thick_outline.extrude(details.hex_height)

#     # Create face boundary solid for clipping
#     face_wire = face.outerWire()
#     face_solid = (
#         face_plane.add(face_wire)
#         .toPending()
#         .extrude(details.hex_height * 3)  # Extrude thick enough to encompass texture
#         .translate(
#             face_normal.multiply(-details.hex_height * 1.5)  # Offset to center
#         )
#     )

#     # Clip texture to face boundary
#     _log.debug("Clipping hex texture with face solid...")
#     clipped_texture = hex_texture.intersect(face_solid)
#     _log.debug("Clipping hex texture with face solid... done")

#     _log.debug("Generating hex grid for face... done.")
#     return clipped_texture
