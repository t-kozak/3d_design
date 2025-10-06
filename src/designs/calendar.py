from ctypes import cast
import logging
import math
from pathlib import Path
import cadquery as cq
from ocp_vscode import show

from dtools import m_screw
from dtools.dbox import DrawerBoxParams, ParametricDrawerBox
from dtools.texture.hex import HoneycombTexture
from dtools.workplane import Workplane

_log = logging.getLogger(__name__)

Workplane.auto_clean = False


class CalMaker:

    base_box_params = DrawerBoxParams(
        content_length=155.0,
        content_width=105.0,
        content_height=20.0,
        box_top_thickness=5.0,
        add_drawer_magnets=True,
        top_texture=HoneycombTexture(
            hex_side_len=5,
            hex_height_min=0,
            hex_height_max=3,
            height_steps=3,
            rotation_degrees=37.0,
            spacing_coefficient=0.85,
            random_seed=123432,
        ),
    )

    base_to_pillar_screw = m_screw.MScrew.M3
    base_to_pillar_screw_core_length = 10.0
    base_to_pillar_screw_head_height = 3.0
    base_to_pillar_screw_head_height = 3.0
    base_to_pillar_screw_heatsink_depth = 12.0

    pillar_base_width = 50.0
    pillar_base_length = 80.0
    pillar_base_side_thickness = 10.0
    pillar_base_top_thickness = 12.0
    pillar_base_hole_depth = 0.4
    pillar_base_clearance = 0.2

    pillar_height = 100.0
    pillar_top_side_len = 20.0

    head_pillar_connector_side = 8.5
    head_pillar_connector_depth = 15.0
    head_pillar_connector_magnet_radius = 5.0 / 2
    head_pillar_connector_magnet_depth = 2.0
    head_pillar_connector_clearance = 0.4

    head_front_side_len = 20.0
    head_front_thickness = 12.0

    head_clip_magnet_radius = 3.92 / 2
    head_clip_magnet_depth = 2.0

    easy_handle_hole_cylinder_radius = 6.0

    def __init__(self):
        self.base_box = ParametricDrawerBox(self.base_box_params)

        # Cache attributes for created objects
        self.__base_top_cache = None
        self.__drawer_cache = None
        self.__pillar_cache = None
        self.__head_cache = None

    def create_assembly(self) -> cq.Assembly:
        _log.info("Creating calendar assembly")
        ass = cq.Assembly(name="Calendar")

        _log.debug("Creating base components")
        base_top = self.__create_base_top()
        base_base = self.base_box.create_box_base()
        drawer = self.__create_drawer_with_easy_handle()
        pillar = self.__create_pillar()
        head = self.__create_head()

        _log.debug("Adding base components to assembly")
        ass.add(base_base, name="base")
        base_top_vec = cq.Vector(0, 0, base_base.get_bbox().zmax)
        ass.add(
            base_top,
            name="base_top",
            loc=cq.Location(base_top_vec),
        )
        ass.add(
            drawer,
            name="drawer",
            loc=cq.Location(cq.Vector(0, 0, self.base_box_params.box_base_thickness)),
        )

        _log.debug("Positioning pillar relative to base top")
        pillar_xy_loc = base_top.get_center() - pillar.get_center()
        pillar_loc = cq.Vector(
            pillar_xy_loc.x,
            pillar_xy_loc.y,
            base_top_vec.z + base_top.get_bbox().zmax - self.pillar_base_hole_depth,
        )

        ass.add(
            pillar,
            name="pillar",
            loc=cq.Location(pillar_loc),
        )

        _log.debug("Positioning head relative to pillar")
        pillar_bbox = pillar.get_bbox()
        head_loc = cq.Vector(
            pillar_loc.x + pillar_bbox.xlen / 2,
            pillar_loc.y + 14,
            pillar_loc.z + pillar_bbox.zmax - 16.7,
        )
        ass.add(
            head.rotate_center("Y", 90).rotate_center("Z", 90),
            name="head",
            loc=cq.Location(head_loc),
        )

        _log.info("Calendar assembly created successfully")
        return ass

    def export_all_for_printing(self):
        _log.info("Exporting all components for printing")
        output = Path("build") / "cal"
        output.mkdir(parents=True, exist_ok=True)
        _log.debug(f"Output directory: {output}")

        _log.debug("Exporting head component")
        self.__create_head().export(output / "head.stl")

        # Pillar
        _log.debug("Creating and exporting pillar components")
        pillar = self.__create_pillar()
        _log.info("Exporting pillar component. This will take a while...")

        tolerance = 0.02
        angularTolerance = 0.02
        pillar.export(
            output / "pillar.stl",
            tolerance=tolerance,
            angularTolerance=angularTolerance,
        )
        _log.info("Pillar component exported successfully.")
        _log.debug("Creating pillar head sample (top portion)")
        # (pillar - Workplane("XY").box(1000, 1000, 180)).export(
        #     output / "sample_pillar_head.stl",
        #     tolerance=tolerance,
        #     angularTolerance=angularTolerance,
        # )
        # _log.debug("Creating pillar base sample (bottom portion)")
        # (pillar.intersect(Workplane("XY").box(1000, 1000, 20))).export(
        #     output / "sample_pillar_base.stl",
        #     tolerance=tolerance,
        #     angularTolerance=angularTolerance,
        # )

        # Base top
        _log.debug("Creating and exporting base top components")
        box_top = self.__create_base_top(for_printing=True)
        translation_vec = box_top.get_center() - pillar.get_center()
        _log.debug(f"Translation vector for base top: {translation_vec}")
        _log.debug("Creating base top sample (intersection with pillar area)")
        (
            box_top.intersect(
                Workplane("XY")
                .moveTo(box_top.get_center().x, box_top.get_center().y)
                .box(pillar.get_bbox().xlen + 3, pillar.get_bbox().ylen + 3, 100)
            )
        ).export(
            output / "sample_base_top.stl",
            tolerance=0.01,
            angularTolerance=0.01,
        )
        box_top.export(output / "base_top.stl")

        # Rest of the base
        _log.debug("Exporting remaining base components")
        self.base_box.create_box_base().export(output / "base_base.stl")
        self.__create_drawer_with_easy_handle().export(output / "drawer.stl")
        _log.info("All components exported successfully")

    def __create_base_top(self, for_printing: bool = False) -> Workplane:
        # Check cache first (only for default for_printing=False)
        if not for_printing and self.__base_top_cache is not None:
            _log.debug("Returning cached base top")
            return self.__base_top_cache

        _log.debug(f"Creating base top (for_printing={for_printing})")
        top_base = self.base_box.create_box_top()

        center = top_base.get_center()
        pillar_hole_plane_z_offset = (
            self.base_box_params.box_top_thickness - self.pillar_base_hole_depth
        )

        # Create pillar hole at the center of the top face
        _log.debug("Creating pillar hole in base top")
        pillar_hole = Workplane("XY").workplane(offset=pillar_hole_plane_z_offset)
        pillar_hole = self.__create_pillar_base_shape(
            pillar_hole, with_clearance=True
        ).extrude(100)
        pillar_center = pillar_hole.get_center()
        center_diff = center - pillar_center
        pillar_hole = pillar_hole.translate((center_diff.x, center_diff.y, 0))
        pil_hole_bbox = pillar_hole.get_bbox()
        _log.debug("Cutting pillar hole from base top")
        all = top_base - pillar_hole

        _log.debug("Adding screw holes for pillar attachment")
        for screw_loc in self.__get_pillar_screw_location(pil_hole_bbox):
            all -= (
                Workplane("XY")
                .moveTo(screw_loc.x, screw_loc.y)
                .screw_hole(
                    self.base_to_pillar_screw,
                    core_length=self.base_to_pillar_screw_core_length,
                    head_height=self.base_to_pillar_screw_head_height,
                    head_on_top=False,
                )
            )

        _log.debug("Base top creation completed")

        # Cache the result if not for_printing
        if not for_printing:
            self.__base_top_cache = all
            _log.debug("Cached base top for future use")

        return all

    def __create_drawer_with_easy_handle(self) -> Workplane:
        # Check cache first
        if self.__drawer_cache is not None:
            _log.debug("Returning cached drawer")
            return self.__drawer_cache

        _log.debug("Creating drawer with easy handle")
        all = self.base_box.create_drawer()
        _log.debug("Cutting easy handle hole in drawer")
        all -= (
            Workplane("XY")
            .circle(self.easy_handle_hole_cylinder_radius)
            .extrude(100)
            .translate((self.base_box_params.box_wall_thickness, 40, 0))
        )
        _log.debug("Drawer with easy handle completed")

        # Cache the result
        self.__drawer_cache = all
        _log.debug("Cached drawer for future use")

        return all

    def __create_pillar(self) -> Workplane:
        # Check cache first
        if self.__pillar_cache is not None:
            _log.debug("Returning cached pillar")
            return self.__pillar_cache

        _log.debug("Creating pillar component")

        _log.debug("Creating pillar base shape")
        base = self.__create_pillar_base_shape(Workplane("XY"))
        base_b_box = base.get_bbox()
        _log.debug("Creating pillar loft from base to top")
        base = (
            base.workplane(offset=self.pillar_height)
            .moveTo(base_b_box.center.x, base_b_box.center.y)
            .rect(self.pillar_top_side_len, self.pillar_top_side_len)
            .loft()
        )

        _log.debug("Adding heatsert holes for pillar attachment")
        for screw_loc in self.__get_pillar_screw_location(base_b_box):
            base -= (
                Workplane("XY")
                .moveTo(screw_loc.x, screw_loc.y)
                .heatsert(
                    self.base_to_pillar_screw,
                    depth=self.base_to_pillar_screw_heatsink_depth,
                    guide_hole_location="bottom",
                )
            )

        all = base
        _log.debug("Adding pillar head box")
        head = (
            Workplane("XY")
            .box(
                self.pillar_top_side_len,
                self.pillar_top_side_len,
                self.pillar_top_side_len / 2,
            )
            .translate(
                (
                    base_b_box.center.x,
                    base_b_box.center.y,
                    self.pillar_height + self.pillar_top_side_len * 0.25,
                )
            )
        )

        _log.debug("Adding pillar head cylinder")
        head_cylinder = (
            Workplane("XZ")
            .cylinder(self.pillar_top_side_len, self.pillar_top_side_len / 2)
            .translate(
                (
                    base_b_box.center.x,
                    base_b_box.center.y,
                    self.pillar_height + self.pillar_top_side_len * 0.5,
                )
            )
        )
        head_cylinder_center = head_cylinder.get_center()

        _log.debug("Creating hole for head connector")
        hole_for_head = Workplane("XY").box(
            self.head_pillar_connector_side,
            self.head_pillar_connector_depth,
            self.head_pillar_connector_side,
        )

        hole_for_head = hole_for_head.rotate_center("Y", 45).translate(
            (
                head_cylinder_center.x,
                head_cylinder_center.y
                - (self.pillar_top_side_len - self.head_pillar_connector_depth),
                head_cylinder_center.z,
            )
        )

        _log.debug("Creating magnet hole in pillar head")
        hole_for_magnet = (
            Workplane("XZ")
            .teardrop(self.head_pillar_connector_magnet_radius)
            .extrude(self.head_pillar_connector_magnet_depth)
            .translate(
                (
                    head_cylinder_center.x,
                    hole_for_head.get_bbox().ymax
                    + self.head_pillar_connector_magnet_depth,
                    head_cylinder_center.z,
                )
            )
        )
        _log.debug("Assembling pillar components")
        all += head
        all += head_cylinder
        all -= hole_for_head
        all -= hole_for_magnet

        _log.debug("Pillar creation completed")

        # Cache the result
        self.__pillar_cache = all
        _log.debug("Cached pillar for future use")

        return all

    def __create_head(self) -> Workplane:
        # Check cache first
        if self.__head_cache is not None:
            _log.debug("Returning cached head")
            return self.__head_cache

        _log.debug("Creating head component")

        _log.debug("Creating head front face with fillets")
        front = (
            Workplane("XY")
            .box(
                self.head_front_side_len,
                self.head_front_side_len,
                self.head_front_thickness,
            )
            .faces()
            .fillet(self.head_front_thickness / 4)
        )

        _log.debug("Creating magnet holes for head clips")
        magnet_hole = (
            Workplane("XZ")
            .teardrop(self.head_clip_magnet_radius)
            .extrude(self.head_clip_magnet_depth)
        )
        front_bbox = front.get_bbox()
        front_center = front_bbox.center
        z_offset = front_bbox.center.z
        magnet_hole = magnet_hole.translate((0, 0, z_offset))

        _log.debug("Cutting magnet holes in head front")
        front -= magnet_hole.translate(
            (
                front_center.x - 4,
                (-self.head_front_side_len / 2) + self.head_clip_magnet_depth,
                0,
            )
        )
        front -= magnet_hole.translate(
            (
                front_center.x + 4,
                (-self.head_front_side_len) / 2 + self.head_clip_magnet_depth,
                0,
            )
        )
        front -= magnet_hole.translate(
            (
                front_center.x - 4,
                (self.head_front_side_len / 2),
                0,
            )
        )
        front -= magnet_hole.translate(
            (
                front_center.x + 4,
                (self.head_front_side_len) / 2,
                0,
            )
        )

        _log.debug("Creating head connector")
        connector = (
            Workplane("XY")
            .box(
                self.head_pillar_connector_side - self.head_pillar_connector_clearance,
                self.head_pillar_connector_side - self.head_pillar_connector_clearance,
                self.head_pillar_connector_depth - 2,
            )
            .rotate_center("Z", 45)
            .translate((0, 0, self.head_front_thickness))
        )

        _log.debug("Creating connector magnet hole")
        connector_magnet_hole = (
            Workplane("XY")
            .teardrop(self.head_pillar_connector_magnet_radius)
            .extrude(self.head_pillar_connector_magnet_depth)
            .translate(
                (
                    0,
                    0,
                    connector.get_bbox().zmax - self.head_pillar_connector_magnet_depth,
                )
            )
        )

        _log.debug("Assembling head components")
        all = front + connector - connector_magnet_hole
        _log.debug("Head creation completed")

        # Cache the result
        self.__head_cache = all
        _log.debug("Cached head for future use")

        return all

    def __get_pillar_screw_location(self, bbox: cq.BoundBox) -> list[cq.Vector]:
        _log.debug(f"Calculating pillar screw locations for bbox: {bbox}")
        locations = [
            cq.Vector(bbox.xmin + 9, bbox.ymin + 13),
            cq.Vector(bbox.xmax - 9, bbox.ymin + 13),
            cq.Vector(bbox.center.x, bbox.ymax - 7),
        ]
        _log.debug(f"Generated {len(locations)} screw locations")
        return locations

    def __create_pillar_base_shape(
        self, w: Workplane, with_clearance: bool = False
    ) -> Workplane:
        _log.debug(f"Creating pillar base shape (with_clearance={with_clearance})")
        length = self.pillar_base_length
        width = self.pillar_base_width
        side_thickness = self.pillar_base_side_thickness
        top_thickness = self.pillar_base_top_thickness
        if with_clearance:
            _log.debug("Applying clearance adjustments to pillar base dimensions")
            length += 2 * self.pillar_base_clearance
            width += 2 * self.pillar_base_clearance
            side_thickness += 2 * self.pillar_base_clearance
            top_thickness += 2 * self.pillar_base_clearance

        _log.debug(
            f"Creating parabolic channel: {length}x{width}x{side_thickness}x{top_thickness}"
        )
        return w.parabolic_channel(
            length=length,
            width=width,
            side_thickness=side_thickness,
            top_thickness=top_thickness,
        )


if __name__ == "__main__":
    # Setup basic logging
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s - %(message)s (%(name)s)",
        datefmt="%H:%M:%S",
    )

    cal_maker = CalMaker()

    show(cal_maker.create_assembly())
    _log.info("Exporting all components for printing")
    cal_maker.export_all_for_printing()
