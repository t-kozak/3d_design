import cadquery as cq
from IPython.display import clear_output, display


def show(itm: cq.Workplane):
    clear_output(wait=True)
    display(itm)
