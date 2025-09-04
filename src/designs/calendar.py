from ctypes import cast
import math
import cadquery as cq
from ocp_vscode import show

from dtools import m_screw
from dtools.dbox import DrawerBoxParams, ParametricDrawerBox
from dtools.workplane import Workplane


class CalMaker:

    pillar_base_radius = 12.5
    pillar_top_radius = 8.0
    pillar_height = 100.0
    pillar_top_center_offset = pillar_top_radius - pillar_base_radius

    pillar_base_center_offset = (0, -20)
    pillar_base_hole_depth = 0.4
    pillar_base_hole_radius = pillar_base_radius + 0.2

    # 4 makes it symmetric, allowing one to rotate the pillar in any direction
    base_to_pillar_pins_count = 4
    base_to_pillar_pins_radius = 2
    base_to_pillar_pins_height = 3.0
    base_to_pillar_pins_clearance = 0.2
    base_pillar_pin_to_center_distance = 14
    top_pillar_pin_to_center_distance = 8

    base_to_pillar_screw = m_screw.MScrew.M3

    def __init__(self):
        self.base_params = DrawerBoxParams(
            content_length=150.0,
            content_width=100.0,
            content_height=20.0,
        )
        self.base_box = ParametricDrawerBox(self.base_params)

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
            loc=cq.Location(cq.Vector(0, 0, self.base_params.box_base_thickness)),
        )

        pillar_xy_loc = base_top.get_center()
        pillar_xy_loc += cq.Vector(
            self.pillar_base_center_offset[0], self.pillar_base_center_offset[1], 0
        )
        pillar_loc = cq.Vector(
            pillar_xy_loc.x,
            pillar_xy_loc.y,
            +base_top_vec.z + base_top.get_bbox().zmax - self.pillar_base_hole_depth,
        )

        ass.add(
            pillar,
            name="pillar",
            loc=cq.Location(pillar_loc),
        )

        head_loc = cq.Vector(
            pillar_loc.x,
            pillar_loc.y + self.pillar_top_center_offset,
            pillar_loc.z + pillar.get_bbox().zmax,
        )
        ass.add(
            head,
            name="head",
            loc=cq.Location(head_loc),
        )

        cap_loc = cq.Vector(
            head_loc.x,
            head_loc.y,
            head_loc.z + head.get_bbox().zmax,
        )
        cap = self.__create_head_cap()
        ass.add(
            cap,
            name="cap",
            loc=cq.Location(cap_loc),
        )
        return ass

    def export_all_for_printing(self):
        self.create_assembly().export("calendar.stl")

    def __create_base_top(self, for_printing: bool = False) -> Workplane:
        top_base = self.base_box.create_box_top()
        base_bbox = top_base.get_bbox()
        center = top_base.get_center()
        center = center + cq.Vector(
            self.pillar_base_center_offset[0], self.pillar_base_center_offset[1], 0
        )
        pillar_hole_plane_z_offset = base_bbox.zmax - self.pillar_base_hole_depth
        # Create pillar hole at the center of the top face
        pillar_hole = (
            Workplane("XY")
            .workplane(offset=pillar_hole_plane_z_offset)
            .moveTo(center.x, center.y)
            .circle(self.pillar_base_hole_radius)
            .extrude(100)
        )
        all = top_base - pillar_hole
        pillar_real_height = (
            self.base_to_pillar_pins_height - self.base_to_pillar_pins_clearance
        )
        pillar_base_radius = (
            self.base_to_pillar_pins_radius - self.base_to_pillar_pins_clearance
        )

        screw_hole = (
            Workplane("XY")
            .moveTo(center.x, center.y)
            .screw_hole(self.base_to_pillar_screw, 8, head_on_top=False)
        )
        all -= screw_hole
        for i in range(self.base_to_pillar_pins_count):
            all += self.__create_pin(
                pillar_hole_plane_z_offset,
                center,
                i,
                self.base_to_pillar_pins_count,
                pillar_base_radius,
                pillar_real_height,
                self.base_pillar_pin_to_center_distance,
            )
        return all

    def __create_pillar(self) -> Workplane:

        # main pillar body
        pillar = (
            Workplane("XY")
            .circle(self.pillar_base_radius)
            .workplane(offset=self.pillar_height)
            .moveTo(0, self.pillar_top_center_offset)
            .circle(self.pillar_top_radius)
            .loft()
        )

        all = pillar

        # Holes for base pins
        for i in range(self.base_to_pillar_pins_count):
            all -= self.__create_pin(
                0,
                pillar.get_center(),
                i,
                self.base_to_pillar_pins_count,
                self.base_to_pillar_pins_radius,
                self.base_to_pillar_pins_height,
                self.base_pillar_pin_to_center_distance,
            )

        heatsert_depth = 20
        # cut heatsert for the base screw
        all -= (
            Workplane("XY")
            .moveTo(pillar.get_center().x, pillar.get_center().y)
            .heatsert(self.base_to_pillar_screw, depth=heatsert_depth)
        )

        # cut a heatsert for the head screw on top
        top_circle_center = cq.Vector(
            pillar.get_center().x, pillar.get_center().y + self.pillar_top_center_offset
        )
        all -= (
            Workplane("XY")
            .moveTo(top_circle_center.x, top_circle_center.y)
            .heatsert(self.base_to_pillar_screw, depth=heatsert_depth)
            .translate((0, 0, self.pillar_height - heatsert_depth))
        )

        # Add pins for the head attachment
        for i in range(self.base_to_pillar_pins_count):
            all += self.__create_pin(
                self.pillar_height,
                top_circle_center,
                i,
                self.base_to_pillar_pins_count,
                self.base_to_pillar_pins_radius,
                self.base_to_pillar_pins_height,
                self.top_pillar_pin_to_center_distance,
            )

        return all

    def __create_head(self) -> Workplane:
        all = self.__create_head_base_shape()
        all = all.intersect(
            Workplane("XY").box(
                2 * self.pillar_top_radius, 2 * self.pillar_top_radius, 35
            )
        )
        return all

    def __create_head_cap(self) -> Workplane:
        all = self.__create_head_base_shape()
        all -= Workplane("XY").box(
            2 * self.pillar_top_radius, 2 * self.pillar_top_radius, 35
        )

        return all

    def __create_head_base_shape(self) -> Workplane:

        all = (
            Workplane("XZ")
            .lineTo(self.pillar_top_radius, 0)
            .bezier(
                [
                    (self.pillar_top_radius, 0),
                    (self.pillar_top_radius, 3),
                    (self.pillar_top_radius * 0.8, 18),
                    (self.pillar_top_radius * 0.2, 22),
                    (4, 30),
                    (0, 30.2),
                ]
            )
            .close()
            .revolve(axisStart=cq.Vector(0, 0, 0), axisEnd=cq.Vector(0, 1, 0))
        )

        return all

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
    show(cal_maker.create_assembly())
