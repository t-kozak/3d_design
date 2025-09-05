from dtools.texture.hex import HoneycombTexture
from dtools.workplane import Workplane
from ocp_vscode import show
import logging

_log = logging.getLogger(__name__)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    w = (
        Workplane("XY").box(150, 100, 10)
        # .texture(HoneycombTexture(hex_side_len=3, hex_height_min=1, hex_height_max=5))
    )
    w = (
        w.edges("|Z")
        .fillet(10)
        .faces(">Z")
        .texture(
            HoneycombTexture(hex_side_len=30, hex_height_min=1, hex_height_max=5),
            show_progress=True,
        )
    )

    show(w)
    w.export("hex_test.stl")
