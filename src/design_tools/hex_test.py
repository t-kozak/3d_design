import logging
from .texture import HoneycombTexture
from .workplane import Workplane
from ocp_vscode import show
from stopwatch import Stopwatch

_log = logging.getLogger(__name__)

if __name__ == "__main__":
    import cadquery as cq

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s - %(message)s (%(name)s)",
        datefmt="%H:%M:%S",
    )
    with Stopwatch() as x:
        _log.info("Starting HexTest example")

        result = (
            Workplane("XY")
            .box(150, 150, 25)
            .edges("|Z")
            .fillet(5)
            .texture(
                HoneycombTexture(hex_side_len=100, hex_height_min=0, hex_height_max=2),
                show_progress=True,
            )
        )
        show(result)
        _log.info(f"HexTest example completed in {x.elapsed:.2f} seconds")
