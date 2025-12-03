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
class CamIslandCfg:
    # offset from top left edge of the phone to top left edge of the island base
    top_left_offset: tuple[float, float]
    # width, length, corner radius
    base_size: tuple[float, float, float]
    # width, length, corner radius
    plateau_size: tuple[float, float, float]
    cam_radius: float
    base_to_cam_top_height: float
    base_to_island_plateau_height: float
    phone_top_left_edge_to_camera_offsets: list[tuple[float, float]]


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

    buttons_cfg: list[BtnConfig]

    cam_island_cfg: CamIslandCfg

    mic_locations: list[float]
    bottom_screw_locations: list[float]
    connector_size: tuple[float, float]
    top_receiver_size: tuple[float, float]
    bottom_screw_radius: float = 1.5 / 2
    mic_radius: float = 1.35 / 2

    screen_protector_height: float | None = 0.6

    @property
    def mid_point(self) -> tuple[float, float, float]:
        return (self.width / 2, self.height / 2, self._mid_z)

    def create(self, plane: str = "XY") -> Workplane:
        body = self.get_body_outline(plane).extrude(self.thickness)
        if self.screen_protector_height:
            scr_prt = (
                self.get_body_outline(plane, width=67.4, height=145.5)
                .extrude(self.thickness + self.screen_protector_height)
                .aligned(body, ("center", "center", "start"))
            )
            body += scr_prt

        body += self._make_cam_island(plane)

        for loc in self.mic_locations:
            body -= (
                Workplane("XZ")
                .moveTo(loc, self._mid_z)
                .circle(self.mic_radius)
                .extrude(-2)
            )

        for loc in self.bottom_screw_locations:
            body -= (
                Workplane("XZ")
                .moveTo(loc, self._mid_z)
                .circle(self.bottom_screw_radius)
                .extrude(-2)
            )

        body -= (
            Workplane("XZ")
            .moveTo(self.width / 2, self._mid_z)
            .rect(*self.connector_size)
            .extrude(-4)
            .edges("|Y")
            .fillet(self.connector_size[1] / 2.01)
        )

        for btn in self.buttons_cfg:
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

        top_receiver_size = self.top_receiver_size
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

    def get_cam_island_base_outline(
        self, plane: str = "XY", scale_x: float = 1.0, scale_y: float = 1.0
    ) -> Workplane:
        cfg = self.cam_island_cfg
        abs_loc = (
            avg(cfg.top_left_offset[0], cfg.base_size[0]) * scale_x,
            (self.height - avg(cfg.top_left_offset[1], cfg.base_size[1])) * scale_y,
        )
        return (
            Workplane(plane)
            .moveTo(*abs_loc)
            .rrect(
                cfg.base_size[0] * scale_x,
                cfg.base_size[1] * scale_y,
                cfg.base_size[2],
            )
        )

    def get_body_outline(
        self,
        plane: str = "XY",
        scale_x: float = 1.0,
        scale_y: float = 1.0,
        width: float | None = None,
        height: float | None = None,
    ) -> Workplane:
        bottom_left_points: list[tuple[float, float]] = []
        bottom_right_points: list[tuple[float, float]] = []
        top_right_points: list[tuple[float, float]] = []
        top_left_points: list[tuple[float, float]] = []

        width = width or self.width
        height = height or self.height

        for pt in self.corner_curve:
            bottom_left_points.append((pt[0] * scale_x, pt[1] * scale_y))

        for pt in reversed(self.corner_curve):
            bottom_right_points.append(((width - pt[0]) * scale_x, pt[1] * scale_y))

        for pt in self.corner_curve:
            top_right_points.append(
                ((width - pt[0]) * scale_x, (height - pt[1]) * scale_y)
            )

        for pt in reversed(self.corner_curve):
            top_left_points.append((pt[0] * scale_x, (height - pt[1]) * scale_y))

        return (
            Workplane(plane)
            .spline(bottom_left_points)
            .lineTo(*bottom_right_points[0])
            .spline(bottom_right_points)
            .lineTo(*top_right_points[0])
            .spline(top_right_points)
            .lineTo(*top_left_points[0])
            .spline(top_left_points)
            .close()
        )

    def _make_cam_island(self, plane: str) -> Workplane:
        cfg = self.cam_island_cfg
        abs_loc = (
            self.width - avg(cfg.top_left_offset[0], cfg.base_size[0]),
            self.height - avg(cfg.top_left_offset[1], cfg.base_size[1]),
        )
        island = (
            Workplane(plane)
            .moveTo(*abs_loc)
            .rrect(*cfg.base_size)
            .workplane(offset=-cfg.base_to_island_plateau_height / 2)
            .moveTo(*abs_loc)
            .rrect(
                cfg.plateau_size[0] * 1.05,
                cfg.plateau_size[1] * 1.05,
                cfg.plateau_size[2] * 1.05,
            )
            .workplane(offset=-cfg.base_to_island_plateau_height)
            .moveTo(*abs_loc)
            .rrect(*cfg.plateau_size)
            .loft()
        )

        for cam_loc in cfg.phone_top_left_edge_to_camera_offsets:
            abs_loc = (self.width - cam_loc[0], self.height - cam_loc[1])
            island += (
                Workplane(plane)
                .moveTo(*abs_loc)
                .circle(self.back_cam_radius)
                .extrude(-self.back_cam_to_glass_height)
            )

        return island

    @property
    def _mid_z(self) -> float:
        return self.thickness / 2


def avg(a: float, b: float) -> float:
    return (a + b) / 2


def _get_16_pro_mic_locs() -> list[float]:
    mic_locations = [19.7, 0, 24.21, 47.23, 0, 0, 0, 56.25]
    mic_locations[1] = avg(mic_locations[0], mic_locations[2])
    mic_locations[5] = avg(mic_locations[3], mic_locations[7])
    mic_locations[4] = avg(mic_locations[3], mic_locations[5])
    mic_locations[6] = avg(mic_locations[7], mic_locations[5])
    return mic_locations


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
        buttons_cfg=[
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
        ],
        mic_locations=_get_16_pro_mic_locs(),
        bottom_screw_locations=[28.79, 42.64],
        connector_size=(30.86 - 40.58, 3.1),
        cam_island_cfg=CamIslandCfg(
            top_left_offset=(1.04, 1.04),
            base_size=(45.22 - 1.04, 46.54 - 1.04, 12.0),
            plateau_size=(41.56 - 4.70, 42.88 - 4.70, 10.0),
            base_to_island_plateau_height=2.05,
            base_to_cam_top_height=4.28,
            cam_radius=14.17,
            phone_top_left_edge_to_camera_offsets=[
                (14.17, 14.17),
                (14.17, 33.41),
                (32.16, 23.79),
            ],
        ),
        top_receiver_size=(14.41, 0.85),
    )


if __name__ == "__main__":
    from ocp_vscode import show

    body = IPhones.IPHONE_16_PRO.create("XY")
    # body = Workplane("XY").rrect(20, 50, 10).extrude(5)
    # body += Workplane("XY").moveTo(30, 30).rrect(20, 50, 10).extrude(5)
    show(body)
