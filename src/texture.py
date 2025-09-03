from dataclasses import dataclass
import math
import random
import cadquery as cq
from .workplane import Workplane


@dataclass
class TextureDetails:
    pass


@dataclass
class HoneycombTexture(TextureDetails):
    hex_side_len: float
    hex_height_min: float
    hex_height_max: float
    height_steps: int = 10
    rotation_degrees: float = 0.0
    spacing_coefficient: float = 1.0


def add_hex_texture_to_faces(
    workplane: Workplane,
    details: HoneycombTexture,
) -> Workplane:
    """
    Add hexagonal texture to the currently selected faces of a workplane.

    Args:
        workplane: CadQuery workplane with faces selected
        details: Details of the honeycomb texture

    Returns:
        Workplane with hexagonal texture added to selected faces
    """

    # Get the selected faces
    selected_faces = workplane.faces()

    if len(selected_faces.vals()) == 0:
        raise ValueError(
            "No faces selected. Please select faces before applying texture."
        )

    result = workplane

    # Process each selected face
    for face in selected_faces.vals():
        # Get face bounding box to determine texture area
        assert isinstance(face, cq.Face)

        # Generate hex texture for this face
        res = _generate_hex_texture_for_face(
            face,
            details,
        )
        if not res:
            continue
        hex_texture, u_vec, v_vec = res

        # Intersect texture with face boundary to clean up edges

        # Get the face wire (boundary)
        face_wire = face.outerWire()

        # Create a workplane aligned with the face
        face_plane_obj = cq.Plane(
            origin=face.Center(),
            xDir=u_vec,
            normal=face.normalAt(),  # pyright: ignore[reportCallIssue]
        )
        face_workplane = cq.Workplane(face_plane_obj)

        # Add the face wire to this oriented workplane and extrude along the face normal
        face_solid = (
            face_workplane.add(face_wire)
            .toPending()
            .extrude(
                details.hex_height_max * 3
            )  # Extrude thick enough to encompass all hexagons
            .translate(
                (
                    face.normalAt().multiply(  # pyright: ignore[reportCallIssue]
                        -details.hex_height_max * 1.5
                    )
                )  # Offset to center the extrusion
            )
        )

        # Only keep hexagons that intersect with the face area
        clipped_texture = hex_texture.intersect(face_solid)
        result = result.union(clipped_texture)

    return result


def _get_face_coordinate_system(
    face_normal: cq.Vector, details: HoneycombTexture
) -> tuple[cq.Vector, cq.Vector]:
    """
    Calculate proper u and v vectors for a face based on its normal and apply rotation.
    This ensures consistent orientation across all face types.
    """
    # Normalize the normal vector
    normal = face_normal.normalized()

    # Choose a reference vector that is guaranteed not to be parallel
    # We'll test multiple reference vectors to find one that works
    reference_candidates = [
        cq.Vector(1, 0, 0),  # X axis
        cq.Vector(0, 1, 0),  # Y axis
        cq.Vector(0, 0, 1),  # Z axis
    ]

    u_vec = None

    for reference in reference_candidates:
        # Calculate cross product
        cross_result = normal.cross(reference)

        # Check if cross product has sufficient magnitude (not parallel)
        cross_magnitude = math.sqrt(
            cross_result.x**2 + cross_result.y**2 + cross_result.z**2
        )

        if cross_magnitude > 1e-6:  # Not parallel (within tolerance)
            u_vec = cross_result.normalized()
            break

    if u_vec is None:
        # This should never happen with our three orthogonal reference vectors
        raise ValueError("Could not find suitable reference vector for face normal")

    # Calculate v vector (second tangent vector, perpendicular to both normal and u)
    v_vec = normal.cross(u_vec).normalized()

    # Apply rotation if specified
    if abs(details.rotation_degrees) > 1e-6:  # Only rotate if rotation is significant
        rotation_radians = math.radians(details.rotation_degrees)
        cos_theta = math.cos(rotation_radians)
        sin_theta = math.sin(rotation_radians)

        # Rotate u and v vectors around the normal vector using Rodrigues' rotation formula
        # For rotation around normal vector: new_u = u*cos(θ) + v*sin(θ)
        # new_v = -u*sin(θ) + v*cos(θ)
        rotated_u = u_vec.multiply(cos_theta).add(v_vec.multiply(sin_theta))
        rotated_v = u_vec.multiply(-sin_theta).add(v_vec.multiply(cos_theta))

        u_vec = rotated_u.normalized()
        v_vec = rotated_v.normalized()

    return u_vec, v_vec


def _hex_would_intersect_face(
    local_x: float,
    local_y: float,
    hex_side_len: float,
    face: cq.Face,
    face_center: cq.Vector,
    u_vec: cq.Vector,
    v_vec: cq.Vector,
) -> bool:
    """
    Check if a hexagon at the given local coordinates would intersect with the face.
    This checks if any part of the hexagon intersects with the face boundary.
    """
    # Convert local coordinates to 3D world position
    world_pos = face_center + u_vec.multiply(local_x) + v_vec.multiply(local_y)

    # Project the world position back onto the face plane
    # This gives us the 2D coordinates in the face's local coordinate system
    relative_pos = world_pos - face_center
    u_proj = relative_pos.dot(u_vec)
    v_proj = relative_pos.dot(v_vec)

    # Get face vertices in the face's coordinate system
    face_vertices = face.outerWire().Vertices()
    face_2d_points = []

    for vertex in face_vertices:
        vertex_pos = vertex.Center()
        vertex_relative = vertex_pos - face_center
        vertex_u = vertex_relative.dot(u_vec)
        vertex_v = vertex_relative.dot(v_vec)
        face_2d_points.append((vertex_u, vertex_v))

    # Calculate hexagon vertices in 2D face coordinate system
    # Hexagon radius (distance from center to vertex)
    hex_radius = hex_side_len

    # Generate hexagon vertices (6 vertices of a regular hexagon)
    hex_vertices = []
    for i in range(6):
        angle = i * math.pi / 3  # 60 degrees per vertex
        hex_u = u_proj + hex_radius * math.cos(angle)
        hex_v = v_proj + hex_radius * math.sin(angle)
        hex_vertices.append((hex_u, hex_v))

    # Check if any hexagon vertex is inside the face
    for hex_u, hex_v in hex_vertices:
        if _point_in_polygon(hex_u, hex_v, face_2d_points):
            return True

    # Check if any face vertex is inside the hexagon
    for face_u, face_v in face_2d_points:
        if _point_in_polygon(face_u, face_v, hex_vertices):
            return True

    # Check if any hexagon edge intersects with any face edge
    for i in range(6):
        hex_p1 = hex_vertices[i]
        hex_p2 = hex_vertices[(i + 1) % 6]

        for j in range(len(face_2d_points)):
            face_p1 = face_2d_points[j]
            face_p2 = face_2d_points[(j + 1) % len(face_2d_points)]

            if _line_segments_intersect(hex_p1, hex_p2, face_p1, face_p2):
                return True

    return False


def _point_in_polygon(x: float, y: float, polygon: list[tuple[float, float]]) -> bool:
    """
    Point-in-polygon test using ray casting algorithm.
    """
    n = len(polygon)
    inside = False

    p1x, p1y = polygon[0]
    for i in range(1, n + 1):
        p2x, p2y = polygon[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    else:
                        xinters = p1x  # Handle horizontal edge case
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y

    return inside


def _line_segments_intersect(
    p1: tuple[float, float],
    p2: tuple[float, float],
    p3: tuple[float, float],
    p4: tuple[float, float],
) -> bool:
    """
    Check if two line segments intersect.
    """
    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = p3
    x4, y4 = p4

    # Calculate the direction of the lines
    denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)

    # Lines are parallel
    if abs(denom) < 1e-10:
        return False

    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
    u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / denom

    # Check if intersection point is on both line segments
    return 0 <= t <= 1 and 0 <= u <= 1


def _generate_hex_texture_for_face(
    face: cq.Face,
    details: HoneycombTexture,
) -> tuple[Workplane, cq.Vector, cq.Vector] | None:
    """
    Generate hexagonal texture positioned and oriented for a specific face.
    """

    # Get face center and normal
    face_center = face.Center()
    face_normal = face.normalAt()  # type: ignore

    # Create proper coordinate system for the face
    u_vec, v_vec = _get_face_coordinate_system(face_normal, details)

    # Calculate face dimensions in the texture coordinate system
    # Project face vertices onto the texture plane to get accurate dimensions
    face_vertices = face.outerWire().Vertices()

    # Project all vertices onto the texture coordinate system
    u_coords = []
    v_coords = []

    for vertex in face_vertices:
        vertex_pos = vertex.Center()
        # Vector from face center to vertex
        relative_pos = vertex_pos - face_center

        # Project onto u and v vectors
        u_proj = relative_pos.dot(u_vec)
        v_proj = relative_pos.dot(v_vec)

        u_coords.append(u_proj)
        v_coords.append(v_proj)

    # Calculate dimensions in texture coordinate system
    u_min, u_max = min(u_coords), max(u_coords)
    v_min, v_max = min(v_coords), max(v_coords)

    face_width = u_max - u_min
    face_height = v_max - v_min

    # Calculate hexagon spacing for proper honeycomb pattern
    x_spacing = details.hex_side_len * math.sqrt(3)
    y_spacing = details.hex_side_len * 0.5
    x_spacing *= details.spacing_coefficient
    y_spacing *= details.spacing_coefficient

    # Calculate grid dimensions with tighter bounds since we're doing intersection checks
    cols = (
        int(math.ceil(face_width / x_spacing)) + 1
    )  # Reduced margin since we check intersections
    rows = int(math.ceil(face_height / y_spacing)) + 1

    # Discretize heights
    height_range = details.hex_height_max - details.hex_height_min
    height_step_size = (
        height_range / details.height_steps if details.height_steps > 1 else 0
    )

    # Group positions by discretized height
    height_groups = {}

    # Calculate texture bounds in texture coordinate system
    # Center the texture grid on the face
    u_center = (u_min + u_max) / 2
    v_center = (v_min + v_max) / 2

    half_width = face_width / 2
    half_height = face_height / 2

    for row in range(rows):
        for col in range(cols):
            # Local 2D coordinates in texture plane (relative to face center)
            local_x = (col * x_spacing) - half_width
            local_y = (row * y_spacing) - half_height

            # Offset every other row for honeycomb pattern
            if row % 2 == 1:
                local_x += x_spacing / 2

            # Check if hexagon would intersect with the face before creating it
            if _hex_would_intersect_face(
                local_x, local_y, details.hex_side_len, face, face_center, u_vec, v_vec
            ):
                # Generate random height and discretize
                random_height = random.uniform(
                    details.hex_height_min, details.hex_height_max
                )
                if details.height_steps > 1:
                    step_index = int(
                        (random_height - details.hex_height_min) / height_step_size
                    )
                    step_index = min(step_index, details.height_steps - 1)
                    discretized_height = details.hex_height_min + (
                        step_index * height_step_size
                    )
                else:
                    discretized_height = random_height

                # Convert local 2D coordinates to 3D world coordinates
                world_pos = (
                    face_center + u_vec.multiply(local_x) + v_vec.multiply(local_y)
                )

                if discretized_height not in height_groups:
                    height_groups[discretized_height] = []
                height_groups[discretized_height].append((world_pos, local_x, local_y))

    if not height_groups:
        return None

    # Create hexagons at the face location and orientation
    result = None

    for batch_height, positions in height_groups.items():
        if not positions:
            continue

        # Create workplane aligned with the face
        face_plane_obj = cq.Plane(
            origin=face_center,
            xDir=u_vec,
            normal=face.normalAt(),  # pyright: ignore[reportCallIssue]
        )
        face_plane = Workplane(face_plane_obj)

        # Create all hexagons for this height level
        for world_pos, local_x, local_y in positions:
            try:
                # Create hexagon in the face plane
                hex_shape = (
                    face_plane.moveTo(local_x, local_y)
                    .polygon(6, details.hex_side_len)
                    .extrude(batch_height)  # Extrude along the face normal
                )

                if result is None:
                    result = hex_shape
                else:
                    result = result.union(hex_shape)
            except Exception as e:
                print(f"Warning: Could not create hexagon at {local_x}, {local_y}: {e}")
                continue

    assert result is not None
    return result, u_vec, v_vec


def create_textured_cube_example():
    """Example: Create a cube and add hex texture to the top face"""
    cube = Workplane("XY").box(50, 50, 10).edges("|Z").fillet(8)

    # Select the top face and add texture
    details = HoneycombTexture(
        hex_side_len=6.0,
        hex_height_min=0.5,
        hex_height_max=3.0,
        height_steps=5,
        rotation_degrees=33,
        spacing_coefficient=0.87,
    )
    textured_cube = add_hex_texture_to_faces(
        cube.faces(">Z"),  # Select top face
        details,
    )

    return textured_cube


# def create_textured_cylinder_example():
#     """Example: Create a cylinder and add hex texture to multiple faces"""
#     cylinder = Workplane("XY").cylinder(20, 5)

#     details = HoneycombTexture(
#         hex_side_len=1,
#         hex_height_min=0.2,
#         hex_height_max=3.0,
#         height_steps=8,
#     )

#     # Select top and bottom faces and add texture
#     textured_cylinder = add_hex_texture_to_faces(
#         cylinder.faces(">Z"),
#         details,
#     )

#     return textured_cylinder


if __name__ == "__main__":
    from ocp_vscode import show

    ass = cq.Assembly()

    textured_cube = create_textured_cube_example()
    ass.add(textured_cube, loc=cq.Location((0, 0, 0)))

    # textured_cylinder = create_textured_cylinder_example()
    # ass.add(textured_cylinder, loc=cq.Location((50, 0, 0)))

    show(ass)
