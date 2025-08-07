import cadquery as cq
from IPython.display import clear_output, display


def show(itm: cq.Workplane, show_coords: bool = False):
    if show_coords:
        show_with_coords(itm)

    else:
        _show(itm)


def _show(itm: cq.Workplane | cq.Assembly):
    clear_output(wait=True)
    display(itm)


def show_with_coords(itm: cq.Workplane):
    origin_pt = cq.Workplane().sphere(2)

    x_axis = cq.Workplane("YZ").circle(1).extrude(10)
    y_axis = cq.Workplane("XZ").circle(1).extrude(10)
    z_axis = cq.Workplane("XY").circle(1).extrude(10)

    assem = cq.Assembly()
    assem.add(
        origin_pt, name="origin", color=cq.Color("white"), loc=cq.Location((-0.5, -0.5, -0.5))
    )
    assem.add(x_axis, name="x_axis", color=cq.Color("red"), loc=cq.Location((-0.5, -0.5, -0.5)))
    assem.add(y_axis, name="y_axis", color=cq.Color("green"), loc=cq.Location((-0.5, -0.5, -0.5)))
    assem.add(z_axis, name="z_axis", color=cq.Color("blue"), loc=cq.Location((-0.5, -0.5, -0.5)))
    assem.add(itm)
    _show(assem)
