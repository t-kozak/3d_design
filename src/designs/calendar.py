from ctypes import cast
import math
from pathlib import Path
import cadquery as cq
from ocp_vscode import show

from dtools import m_screw
from dtools.dbox import DrawerBoxParams, ParametricDrawerBox
from dtools.workplane import Workplane


class CalMaker:

    base_box_params = DrawerBoxParams(
        content_length=160.0,
        content_width=110.0,
        content_height=30.0,
        box_top_thickness=7.0,
    )

    base_to_pillar_screw = m_screw.MScrew.M3
    base_to_pillar_screw_core_length = 10.0
    base_to_pillar_screw_head_height = 3.0
    base_to_pillar_screw_head_height = 3.0

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
    head_pillar_connector_magnet_depth = 1.8
    head_pillar_connector_clearance = 0.2

    head_front_side_len = 20.0
    head_front_thickness = 12.0

    head_clip_magnet_radius = 3.92 / 2
    head_clip_magnet_depth = 1.91

    def __init__(self):
        self.base_box = ParametricDrawerBox(self.base_box_params)

    def create_assembly(self) -> cq.Assembly:
        ass = cq.Assembly(name="Calendar")

        base_top = self.__create_base_top()
        base_base = self.base_box.create_box_base()
        drawer = self.base_box.create_drawer()
        pillar = self.__create_pillar()
        head = self.__create_head()
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

        return ass

    def export_all_for_printing(self):
        output = Path("build") / "cal"
        output.mkdir(parents=True, exist_ok=True)
        self.__create_head().export(str(output / "head.stl"))
        pillar = self.__create_pillar()
        pillar_head_sample = pillar - Workplane("XY").box(
            1000,
            1000,
            180,
        )
        pillar_head_sample.export(str(output / "pillar_head_sample.stl"))
        # self.base_box.create_box_base().export("base_base.stl")
        # self.base_box.create_box_top().export("base_top.stl")
        # self.base_box.create_drawer().export("drawer.stl")

    def __create_base_top(self, for_printing: bool = False) -> Workplane:
        top_base = self.base_box.create_box_top()
        base_bbox = top_base.get_bbox()

        center = top_base.get_center()
        pillar_hole_plane_z_offset = base_bbox.zmax - self.pillar_base_hole_depth

        # Create pillar hole at the center of the top face
        pillar_hole = Workplane("XY").workplane(offset=pillar_hole_plane_z_offset)
        pillar_hole = self.__create_pillar_base_shape(
            pillar_hole, with_clearance=True
        ).extrude(100)
        pillar_center = pillar_hole.get_center()
        center_diff = center - pillar_center
        pillar_hole = pillar_hole.translate((center_diff.x, center_diff.y, 0))
        pil_hole_bbox = pillar_hole.get_bbox()
        all = top_base - pillar_hole

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
                # .translate((0, 0, -top_base.get_bbox().zlen))
            )

        return all

    def __create_pillar(self) -> Workplane:

        base = self.__create_pillar_base_shape(Workplane("XY"))
        base_b_box = base.get_bbox()
        base = (
            base.workplane(offset=self.pillar_height)
            .moveTo(base_b_box.center.x, base_b_box.center.y)
            .rect(self.pillar_top_side_len, self.pillar_top_side_len)
            .loft()
        )

        for screw_loc in self.__get_pillar_screw_location(base_b_box):
            base -= (
                Workplane("XY")
                .moveTo(screw_loc.x, screw_loc.y)
                .heatsert(
                    self.base_to_pillar_screw,
                )
            )

        all = base
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
        all += head
        all += head_cylinder
        all -= hole_for_head
        all -= hole_for_magnet

        return all

    def __create_head(self) -> Workplane:
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

        magnet_hole = (
            Workplane("XZ")
            .teardrop(self.head_clip_magnet_radius)
            .extrude(self.head_clip_magnet_depth)
        )
        front_bbox = front.get_bbox()
        front_center = front_bbox.center
        z_offset = front_bbox.center.z
        magnet_hole = magnet_hole.translate((0, 0, z_offset))
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

        connector = (
            Workplane("XY")
            .box(
                self.head_pillar_connector_side - self.head_pillar_connector_clearance,
                self.head_pillar_connector_side - self.head_pillar_connector_clearance,
                self.head_pillar_connector_depth - self.head_pillar_connector_clearance,
            )
            .rotate_center("Z", 45)
            .translate((0, 0, self.head_front_thickness))
        )

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

        all = front + connector - connector_magnet_hole
        return all

    def __get_pillar_screw_location(self, bbox: cq.BoundBox) -> list[cq.Vector]:
        return [
            cq.Vector(bbox.xmin + 9, bbox.ymin + 13),
            cq.Vector(bbox.xmax - 9, bbox.ymin + 13),
            cq.Vector(bbox.center.x, bbox.ymax - 7),
        ]

    def __create_pillar_base_shape(
        self, w: Workplane, with_clearance: bool = False
    ) -> Workplane:
        length = self.pillar_base_length
        width = self.pillar_base_width
        side_thickness = self.pillar_base_side_thickness
        top_thickness = self.pillar_base_top_thickness
        if with_clearance:
            length += 2 * self.pillar_base_clearance
            width += 2 * self.pillar_base_clearance
            side_thickness += 2 * self.pillar_base_clearance
            top_thickness += 2 * self.pillar_base_clearance

        return w.parabolic_channel(
            length=length,
            width=width,
            side_thickness=side_thickness,
            top_thickness=top_thickness,
        )

    def __create_pin(
        self,
        z_offset: float,
        center: cq.Vector,
        idx: int,
        count: int,
        radius: float,
        height: float,
        distance_to_center: float,
    ) -> Workplane:
        pin = (
            Workplane("XY")
            .workplane(offset=z_offset)
            .moveTo(center.x, center.y)
            .polar_move_to(
                idx / count * 2 * math.pi,
                distance_to_center,
                relative=True,
            )
            .circle(radius)
            .extrude(height)
            .faces(">Z")
            .fillet(radius)
        )
        return pin


if __name__ == "__main__":

    cal_maker = CalMaker()

    cal_maker.export_all_for_printing()
    show(cal_maker.create_assembly())
