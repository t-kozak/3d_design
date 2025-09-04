import os
from pathlib import Path
import sys
from typing import cast
import cadquery as cq

from dtools import Workplane
from dtools.dbox import DrawerBoxParams, ParametricDrawerBox


class CalMaker:

    pillar_base_center_offset = (0, 0)
    pillar_base_hole_depth = 1.0
    pillar_base_hole_radius = 10.0

    def __init__(self):
        self.base_box = ParametricDrawerBox(
            DrawerBoxParams(
                content_length=150.0,
                content_width=100.0,
                content_height=20.0,
            )
        )

    def create_assembly(self) -> cq.Assembly:
        return cq.Assembly()

    def export_all_for_printing(self):
        self.base_box.create_box_base(for_printing=True).export("base.stl")
        self.__create_base_top(for_printing=True).export("top.stl")
        self.base_box.create_drawer(for_printing=True).export("drawer.stl")

    def __create_base_top(self, for_printing: bool = False) -> cq.Workplane:
        top_base = self.base_box.create_box_top()

        center = top_base.get_center()

        pillar_hole_plane = (
            top_base.faces(">Z")
            .workplane()
            .workplane(offset=-self.pillar_base_hole_depth)
        )
        pillar_hole = (
            pillar_hole_plane.moveTo(center.x, center.y)
            .circle(self.pillar_base_hole_radius)
            .extrude(self.pillar_base_hole_depth * 2)
        )

        print(center)
        all = top_base - pillar_hole_plane
        return all


if __name__ == "__main__":
    cal_maker = CalMaker()
    cal_maker.export_all_for_printing()
