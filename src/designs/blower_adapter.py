from ocp_vscode import show

from dtools.workplane import Workplane


def main():
    base_circle_radius = 16 / 2
    mid_circle_radius = 14.9 / 2
    top_circle_radius = mid_circle_radius
    inner_circle_radius = 11.9 / 2
    shell = (
        Workplane("XY")
        .circle(base_circle_radius)
        .workplane(offset=5)
        .circle(mid_circle_radius)
        .loft()
        .circle(top_circle_radius)
        .extrude(12)
    )

    hole = Workplane("XY").circle(inner_circle_radius).extrude(25)

    all = shell - hole
    show(all)
    all.export("build/blow_adapter.stl")


if __name__ == "__main__":
    main()
