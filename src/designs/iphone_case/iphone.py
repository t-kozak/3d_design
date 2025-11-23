from dataclasses import dataclass

from dtools.workplane import Workplane


@dataclass
class BtnConfig:
    left: bool
    length: float
    width: float
    height: float
    top_offset: float


@dataclass
class IPhoneDims:
    width: float
    height: float
    thickness: float
    corner_curve: list[tuple[float, float]]

    back_cam_radius: float
    back_cam_to_glass_height: float
    back_cam_locations: list[tuple[float, float]]
    cam_island_thickness: float

    r_cam_island_base_top_left_offset: tuple[float, float]
    r_cam_island_size: tuple[float, float]

    def make_body(self, plane: str) -> Workplane:
        bottom_left_points = list(self.corner_curve)
        bottom_right_points: list[tuple[float, float]] = []
        top_right_points: list[tuple[float, float]] = []
        top_left_points: list[tuple[float, float]] = []

        for pt in reversed(self.corner_curve):
            bottom_right_points.append((self.width - pt[0], pt[1]))

        for pt in self.corner_curve:
            top_right_points.append((self.width - pt[0], self.height - pt[1]))

        for pt in reversed(self.corner_curve):
            top_left_points.append((pt[0], self.height - pt[1]))

        body = (
            Workplane(plane)
            .spline(bottom_left_points)
            .lineTo(*bottom_right_points[0])
            .spline(bottom_right_points)
            .lineTo(*top_right_points[0])
            .spline(top_right_points)
            .lineTo(*top_left_points[0])
            .spline(top_left_points)
            .close()
            .extrude(self.thickness)
        )

        cam_island_center = (
            self.r_cam_island_base_top_left_offset[0] + (self.r_cam_island_size[0] / 2),
            self.height
            - self.r_cam_island_base_top_left_offset[1]
            - (self.r_cam_island_size[1] / 2),
        )

        cam_island_base = (
            Workplane(plane)
            .moveTo(*cam_island_center)
            .rect(*self.r_cam_island_size)
            .extrude(-self.cam_island_thickness)
            .edges("|Z")
            .fillet(10)
        )
        body += cam_island_base

        for cam_loc in self.back_cam_locations:
            abs_loc = (cam_loc[0], self.height - cam_loc[1])
            body += (
                Workplane(plane)
                .moveTo(*abs_loc)
                .circle(self.back_cam_radius)
                .extrude(-self.back_cam_to_glass_height)
            )

        mic_locations = [19.7, 0, 24.21, 47.23, 0, 0, 0, 56.25]
        mic_locations[1] = avg(mic_locations[0], mic_locations[2])
        mic_locations[5] = avg(mic_locations[3], mic_locations[7])
        mic_locations[4] = avg(mic_locations[3], mic_locations[5])
        mic_locations[6] = avg(mic_locations[7], mic_locations[5])

        for loc in mic_locations:
            body -= Workplane("XZ").moveTo(loc, 4.12).circle(1.35 / 2).extrude(-2)

        screw_locs = [28.79, 42.64]
        for loc in screw_locs:
            body -= Workplane("XZ").moveTo(loc, 4.12).circle(1.5 / 2).extrude(-2)

        usb_c_loc_start = 30.86
        usb_c_loc_end = 40.58
        usb_c_size = (usb_c_loc_end - usb_c_loc_start, 3.1)

        body -= (
            Workplane("XZ")
            .moveTo(avg(usb_c_loc_start, usb_c_loc_end), 4.12)
            .rect(*usb_c_size)
            .extrude(-4)
            .edges("|Y")
            .fillet(usb_c_size[1] / 2.1)
        )

        buttons_cfg: list[BtnConfig] = [
            BtnConfig(
                left=True, length=3.45 * 2, width=2.66, height=0.45, top_offset=34.08
            ),
            BtnConfig(
                left=True, length=5.6 * 2, width=2.66, height=0.45, top_offset=48.23
            ),
            BtnConfig(
                left=True, length=5.6 * 2, width=2.66, height=0.45, top_offset=62.43
            ),
            BtnConfig(
                left=False, length=8.85 * 2, width=2.66, height=0.45, top_offset=55.33
            ),
        ]

        for btn in buttons_cfg:
            if btn.left:
                extr_multi = -1
                offset = 0
            else:
                extr_multi = 1
                offset = self.width

            wp = (
                Workplane("YZ")
                .workplane(offset=offset)
                .moveTo(self.height - btn.top_offset, self.thickness / 2)
                .rect(btn.length, btn.width)
                .extrude(extr_multi * btn.height)
                .edges("|X")
                .fillet(btn.width / 2.1)
            )
            body += wp

        top_receiver_size = (14.41, 0.85)
        top_receiver = (
            Workplane("XY")
            .workplane(offset=self.thickness)
            .moveTo(self.width / 2, self.height - top_receiver_size[1])
            .rect(*top_receiver_size)
            .extrude(-1)
            .edges("|Z")
            .fillet(top_receiver_size[1] / 2.01)
        )
        body -= top_receiver

        return body


def avg(a: float, b: float) -> float:
    return (a + b) / 2


class IPhones:
    IPHONE_16_PRO = IPhoneDims(
        width=71.45,
        height=149.61,
        thickness=8.24,
        cam_island_thickness=2.05,
        corner_curve=[
            (0.00, 19.23),
            (0.04, 13.75),
            (0.89, 8.36),
            (3.74, 3.74),
            (8.36, 0.89),
            (13.75, 0.04),
            (19.23, 0.0),
        ],
        back_cam_locations=[
            (14.17, 14.17),
            (14.17, 33.41),
            (32.16, 23.79),
        ],
        back_cam_radius=16.2 / 2,
        back_cam_to_glass_height=4.28,
        r_cam_island_base_top_left_offset=(1.04, 1.04),
        r_cam_island_size=(45.22 - 1.04, 46.54 - 1.04),
    )


if __name__ == "__main__":
    from ocp_vscode import show

    body = IPhones.IPHONE_16_PRO.make_body("XY")
    show(body)
