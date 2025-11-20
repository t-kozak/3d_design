import abc

from cadquery import Face, Plane

from dtools.workplane import Workplane


class Texture(abc.ABC):
    pass

    @abc.abstractmethod
    def _create_for_face(self, face: Face) -> Workplane:
        raise NotImplementedError("This should be implemented in subclasses")

    def _wp_for_face(self, face: Face) -> Workplane:
        """Create a workplane aligned with the face.

        The workplane will be positioned at the face center with its normal
        pointing outward, so that extrusions go in the outward direction.

        Args:
            face: The face to create a workplane for

        Returns:
            A workplane aligned with the face
        """
        center = face.Center()
        normal = face.normalAt()  # type: ignore

        # Create a plane using the face's center and normal
        # This automatically handles any face orientation
        plane = Plane(origin=center, normal=normal)

        # Create workplane from the plane
        return Workplane(plane)

    def _cut_to_face_boundary(
        self, face: Face, texture: Workplane, height: float
    ) -> Workplane:
        """Cut the texture workplane to match the face boundary.

        Args:
            face: The face to cut to
            texture: The texture workplane to cut
            height: The height of the texture extrusion

        Returns:
            The cut texture workplane
        """
        # Get the outer wire of the face and extrude it to create a cutting tool
        outer_wire = face.outerWire()
        cutting_solid = (
            self._wp_for_face(face).add(outer_wire).toPending().extrude(height * 2)
        )

        # Intersect the texture with the face boundary
        return texture.intersect(cutting_solid)
