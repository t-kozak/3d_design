from .texture import HoneycombTexture
from .workplane import Workplane
from ocp_vscode import show
from stopwatch import Stopwatch

if __name__ == "__main__":
    import cadquery as cq

    result = (
        Workplane("XY")
        .box(150, 150, 25)
        .texture(
            HoneycombTexture(hex_side_len=12, hex_height_min=0, hex_height_max=2),
            show_progress=True,
        )
    )
    show(result)
    x = Stopwatch()
