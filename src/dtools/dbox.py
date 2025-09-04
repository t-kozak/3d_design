from dataclasses import dataclass

import logging
import time


from .texture.tex_details import TextureDetails
from .texture import HoneycombTexture
from .m_screw import MScrew
from .workplane import Workplane
from ocp_vscode import show
import cadquery as cq

_log = logging.getLogger(__name__)


@dataclass
class DrawerBoxParams:
    drawer_wall_thickness = 2.0
    drawer_clearance = 0.2

    box_wall_thickness = 10.0
    box_base_thickness = 2.0
    box_top_thickness = 5.5
    box_radius = 5.0

    screw_type = MScrew.M2
    screw_head_height = 5.0
    content_length: float
    content_width: float
    content_height: float
    top_texture: TextureDetails | None = None


class ParametricDrawerBox:

    def __init__(self, params: DrawerBoxParams) -> None:
        _log.debug(
            f"Initializing ParametricDrawerBox with dimensions: {params.content_length}x{params.content_width}x{params.content_height}"
        )
        _log.debug(f"Top texture: {params.top_texture}")
        self.__p = params
        _log.debug("ParametricDrawerBox initialization completed")

    def create_assembly(self) -> cq.Assembly:
        start_time = time.time()
        _log.debug("Starting create_assembly")

        ass = cq.Assembly(name="Box")
        ass.add(self.create_box_base(), name="box_base")
        ass.add(
            self.create_box_top(),
            name="box_top",
            loc=cq.Location(
                (
                    0,
                    0,
                    self.__p.content_height
                    + self.__p.box_base_thickness
                    + self.__p.drawer_wall_thickness,
                )
            ),
        )
        ass.add(
            self.create_drawer(),
            name="drawer",
            color=cq.Color("red"),
            loc=cq.Location(
                (
                    0,
                    0,
                    self.__p.box_base_thickness,
                )
            ),
        )

        elapsed_time = time.time() - start_time
        _log.debug(f"create_assembly completed in {elapsed_time:.3f} seconds")
        return ass

    def create_drawer(self, for_printing: bool = False) -> Workplane:
        start_time = time.time()
        _log.debug("Starting create_drawer")

        front = self.__create_box_body(
            self.__p.content_height
            + self.__p.drawer_wall_thickness
            + self.__p.box_top_thickness,
            True,
        )

        front -= (
            Workplane("XY")
            .box(
                self.__box_length,
                self.__box_width,
                self.__base_height * 2,
                centered=False,
            )
            .translate((0, self.__p.box_wall_thickness, 0))
        )

        real_drawer_wall_thickness = (
            self.__p.drawer_wall_thickness - self.__p.drawer_clearance
        )
        d_length = self.__p.content_length + 2 * (real_drawer_wall_thickness)
        d_width = self.__p.content_width + 2 * (real_drawer_wall_thickness)
        d_height = self.__p.content_height + (real_drawer_wall_thickness)
        _log.debug(f"Drawer dimensions: {d_length}x{d_width}x{d_height}")

        drawer = Workplane("XY").box(d_length, d_width, d_height, centered=False)
        content_hole = (
            Workplane("XY")
            .box(
                self.__p.content_length,
                self.__p.content_width,
                self.__p.content_height,
                centered=False,
            )
            .translate(
                (
                    real_drawer_wall_thickness,
                    real_drawer_wall_thickness,
                    self.__p.drawer_wall_thickness,
                )
            )
        )
        drawer = drawer - content_hole
        drawer = drawer.translate(
            (
                # Really don't know why I need to move it by 2x the drawer clearance
                # but it works
                self.__p.box_wall_thickness + (self.__p.drawer_clearance * 2),
                self.__p.box_wall_thickness,
                0,
            )
        )
        all = drawer + front

        elapsed_time = time.time() - start_time
        _log.debug(f"create_drawer completed in {elapsed_time:.3f} seconds")
        return all

    def create_box_base(self, for_printing: bool = False) -> Workplane:
        start_time = time.time()
        _log.debug("Starting create_box_base")

        drawer_hole_length = (
            self.__p.content_length + 2 * self.__p.drawer_wall_thickness
        )
        drawer_hole_width = (
            self.__p.content_width
            + 2 * self.__p.drawer_wall_thickness
            + self.__p.box_wall_thickness
        )
        drawer_hole_height = (
            self.__p.content_height
            + self.__p.drawer_wall_thickness
            + self.__p.drawer_clearance
        )
        _log.debug(
            f"Drawer hole dimensions: {drawer_hole_length}x{drawer_hole_width}x{drawer_hole_height}"
        )

        # Create base body
        box = self.__create_box_body(
            self.__p.box_base_thickness
            + self.__p.drawer_wall_thickness
            + self.__p.content_height,
            False,
        )

        # Cut off space for the drawer's front
        box -= (
            Workplane("XY")
            .box(
                self.__box_length,
                self.__p.box_wall_thickness,
                self.__base_height,
                centered=False,
            )
            .translate((0, 0, self.__p.box_base_thickness))
        )

        drawer_hole = (
            Workplane("XY")
            .box(
                drawer_hole_length + 2 * self.__p.drawer_clearance,
                drawer_hole_width + self.__p.drawer_clearance,
                drawer_hole_height + self.__p.drawer_clearance,
                centered=False,
            )
            .translate(
                (
                    self.__p.box_wall_thickness,
                    0,
                    self.__p.box_base_thickness,
                )
            )
        )

        all = box - drawer_hole
        _log.debug("Adding screw holes to box base")
        for center in self._get_box_screw_hole_centers():
            all = all - self._create_box_screw_hole(center)

        elapsed_time = time.time() - start_time
        _log.debug(f"create_box_base completed in {elapsed_time:.3f} seconds")
        return all

    def create_box_top(self, for_printing: bool = False) -> Workplane:
        start_time = time.time()
        _log.debug("Starting create_box_top")

        # Create top body
        all = self.__create_box_body(self.__p.box_top_thickness, True)
        _log.debug("Box top body created, cutting front")
        # Cut off space for the drawer's front
        all -= Workplane("XY").box(
            self.__box_length,
            self.__p.box_wall_thickness,
            self.__p.box_top_thickness * 2,
            centered=False,
        )

        _log.debug("Adding heatserts to box top")
        for center in self._get_box_screw_hole_centers():
            heatsert = Workplane("XY").moveTo(*center).heatsert(self.__p.screw_type)
            all = all - heatsert

        elapsed_time = time.time() - start_time
        _log.debug(f"create_box_top completed in {elapsed_time:.3f} seconds")
        return all

    def _get_box_screw_hole_centers(self) -> list[tuple[float, float]]:
        low_x = self.__p.box_wall_thickness / 2
        low_y = self.__p.box_wall_thickness * 1.5
        high_x = self.__box_length - (self.__p.box_wall_thickness / 2)
        high_y = self.__box_width - (self.__p.box_wall_thickness / 2)
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
            .circle(self.__p.screw_type.head_diameter / 2 + 0.2)
            .extrude(self.__p.screw_head_height)
        )
        screw_hole += (
            Workplane("XY")
            .moveTo(*center)
            .circle(self.__p.screw_type.core_diameter / 2 + 0.1)
            .extrude(100)
        )
        return screw_hole

    def __create_box_body(self, height: float, add_texture: bool) -> Workplane:
        _log.debug("Creating box body...")
        box = (
            Workplane("XY")
            .box(self.__box_length, self.__box_width, height, centered=False)
            .edges("|Z")
            .fillet(self.__p.box_radius)
        )
        if add_texture and self.__p.top_texture is not None:
            _log.debug("Applying texture to top face...")
            box = box.faces(">Z").texture(
                self.__p.top_texture,
                show_progress=True,
            )
            _log.debug("Applying texture to top face... done")
        _log.debug("Creating box body... done")
        return box

    @property
    def __box_length(self) -> float:
        return (
            self.__p.content_length
            + 2 * self.__p.box_wall_thickness
            + 2 * self.__p.drawer_wall_thickness
            + 2 * self.__p.drawer_clearance
        )

    @property
    def __box_width(self) -> float:
        return (
            self.__p.content_width
            + 2 * self.__p.box_wall_thickness
            + 2 * self.__p.drawer_wall_thickness
            + 2 * self.__p.drawer_clearance
        )

    @property
    def __base_height(self):
        return (
            self.__p.content_height
            + self.__p.drawer_wall_thickness
            + self.__p.box_base_thickness
            + self.__p.box_top_thickness
        )


if __name__ == "__main__":
    # Setup basic logging
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s - %(message)s (%(name)s)",
        datefmt="%H:%M:%S",
    )

    _log.info("Starting ParametricDrawerBox example")

    texture = HoneycombTexture(
        hex_side_len=15,
        hex_height_min=1,
        hex_height_max=3,
        random_seed=42,
        spacing_coefficient=0.85,
        height_steps=3,
    )
    params = DrawerBoxParams(
        content_length=150.0,
        content_width=100.0,
        content_height=20.0,
        # top_texture=texture,
    )
    dbox = ParametricDrawerBox(params)
    show(dbox.create_assembly(), axes=True, axes0=True)

    _log.info("ParametricDrawerBox example completed")
