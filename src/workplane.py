from typing import Self, cast

import cadquery as cq

import teardrop


class Workplane(cq.Workplane):
    def teardrop(self, radius: float = 1, rotate: float = 0, clip: float | None = None) -> Self:
        return cast(Self, teardrop.teardrop(self, radius, rotate, clip))
