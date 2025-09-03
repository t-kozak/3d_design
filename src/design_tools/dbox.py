import enum
from typing import Literal
from .texture import HoneycombTexture
from .workplane import MScrew, Workplane
from ocp_vscode import show
import cadquery as cq


class ParametricDrawerBox:
    drawer_wall_thickness = 2.0
    drawer_clearance = 0.4

    box_wall_thickness = 10.0
    box_base_thickness = 2.0
    box_top_thickness = 5.5
    box_radius = 5.0

    screw_type = MScrew.M2
    screw_head_height = 5.0

    def __init__(
        self,
        content_width: float,
        content_length: float,
        content_height: float,
        top_texture: Literal["none"] = "none",
        side_texture: Literal["none"] = "none",
    ) -> None:
        self.content_width = content_width
        self.content_length = content_length
        self.content_height = content_height
        self.top_texture = top_texture
        self.side_texture = side_texture

    def create_assembly(self) -> cq.Assembly:

        ass = cq.Assembly()
        ass.add(self._create_box_base(), name="box_base")
        ass.add(
            self._create_box_top(),
            name="box_top",
            loc=cq.Location(
                (
                    0,
                    0,
                    self.content_height
                    + self.box_base_thickness
                    + self.drawer_wall_thickness,
                )
            ),
        )
        ass.add(
            self._create_drawer(),
            name="drawer",
            loc=cq.Location(
                (
                    self.box_wall_thickness
                    + self.drawer_wall_thickness
                    + self.drawer_clearance,
                    self.drawer_wall_thickness,
                    self.box_base_thickness,
                )
            ),
        )

        return ass

    def _create_drawer(self) -> Workplane:
        all = Workplane("XY").box(
            self.content_width,
            self.content_length,
            self.content_height
            + self.drawer_wall_thickness
            - self.drawer_clearance,  # + wall thickness for the top empty space
            centered=False,
        )
        all = all.faces(">Z").shell(self.drawer_wall_thickness)
        return all

    def _create_box_base(self) -> Workplane:

        drawer_width = self.content_width + 2 * self.drawer_wall_thickness
        drawer_length = self.content_length + 2 * self.drawer_wall_thickness
        drawer_height = self.content_height + 2 * self.drawer_wall_thickness

        box = self.__box_base_shape()
        box = box.intersect(
            Workplane("XY").box(
                self.__box_width, self.__box_length, self.__base_height, centered=False
            )
        )

        drawer_hole = (
            Workplane("XY")
            .box(
                drawer_width + 2 * self.drawer_clearance,
                drawer_length + self.drawer_clearance,
                drawer_height + self.drawer_clearance,
                centered=False,
            )
            .translate(
                (
                    self.box_wall_thickness,
                    0,
                    self.box_base_thickness,
                )
            )
        )

        all = box - drawer_hole
        for center in self._get_box_screw_hole_centers():
            all = all - self._create_box_screw_hole(center)

        return all

    def _create_box_top(self) -> Workplane:

        all = self.__box_base_shape()
        all = all.intersect(
            Workplane("XY")
            .box(
                self.__box_width,
                self.__box_length,
                self.box_top_thickness,
                centered=False,
            )
            .translate(
                (
                    0,
                    0,
                    self.__base_height,
                )
            ),
        )
        all = all.translate((0, 0, -self.__base_height))

        # Apply texture to the top face
        all = all.faces(">Z").texture(
            HoneycombTexture(
                hex_side_len=10,
                hex_height_min=1,
                hex_height_max=3,
                random_seed=42,
                spacing_coefficient=0.85,
                height_steps=3,
            ),
            show_progress=True,
        )
        for center in self._get_box_screw_hole_centers():
            heatsert = Workplane("XY").moveTo(*center).heatsert(self.screw_type)
            all = all - heatsert
        return all

    def _get_box_screw_hole_centers(self) -> list[tuple[float, float]]:
        low_x = self.box_wall_thickness / 2
        low_y = self.box_wall_thickness / 2
        high_x = self.__box_width - (self.box_wall_thickness / 2)
        high_y = self.__box_length - (self.box_wall_thickness / 2)
        return [
            (low_x, low_y),
            (low_x, high_y),
            (high_x, low_y),
            (high_x, high_y),
        ]

    def _create_box_screw_hole(self, center: tuple[float, float]) -> Workplane:
        screw_hole = (
            Workplane("XY")
            .moveTo(*center)
            .circle(self.screw_type.head_diameter / 2 + 0.2)
            .extrude(self.screw_head_height)
        )
        screw_hole += (
            Workplane("XY")
            .moveTo(*center)
            .circle(self.screw_type.core_diameter / 2 + 0.1)
            .extrude(100)
        )
        return screw_hole

    def __box_base_shape(self) -> Workplane:
        box = (
            Workplane("XY")
            .box(self.__box_width, self.__box_length, self.__box_height, centered=False)
            .edges("|Z")
            .fillet(self.box_radius)
        )
        return box

    @property
    def __box_width(self) -> float:
        return (
            self.content_width
            + 2 * self.box_wall_thickness
            + 2 * self.drawer_wall_thickness
        )

    @property
    def __box_length(self) -> float:
        return (
            self.content_length
            + self.box_wall_thickness
            + 2 * self.drawer_wall_thickness
        )

    @property
    def __box_height(self) -> float:
        return (
            self.content_length
            + self.box_base_thickness
            + self.box_top_thickness
            + self.drawer_wall_thickness
        )

    @property
    def __base_height(self):
        return (
            self.content_height + self.drawer_wall_thickness + self.box_base_thickness
        )


if __name__ == "__main__":

    dbox = ParametricDrawerBox(
        content_width=150.0,
        content_length=100.0,
        content_height=20.0,
    )
    show(dbox.create_assembly(), axes=True, axes0=True)
