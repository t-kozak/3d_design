import cadquery as cq
from design_tools import Workplane
from design_tools.dbox import DrawerBoxParams, ParametricDrawerBox


class CalMaker:
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
        pass


if __name__ == "__main__":
    cal_maker = CalMaker()
    cal_maker.create_assembly()
