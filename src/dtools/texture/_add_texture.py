from cadquery import Face

from dtools.texture.tex_details import Texture
from dtools.workplane import Workplane


def add_texture(workplane: Workplane, details: Texture):
    # Determine which faces to process
    selected_faces = workplane.faces().vals()

    if len(selected_faces) > 0:
        faces_to_texture = selected_faces
    else:
        # No selection - get all faces
        try:
            solid = workplane.findSolid()
            faces_to_texture = solid.Faces()
        except Exception as e:
            raise ValueError("Workplane contains no solid") from e

    # Process each face
    for face in faces_to_texture:
        assert isinstance(face, Face)
        # Apply texture (your implementation)
        texture_geometry = details._create_for_face(face)

        # Union or cut the texture into the original
        workplane += texture_geometry

    return workplane
