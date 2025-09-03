import enum
import math
import random
from typing import Literal, Self, cast, TYPE_CHECKING

import cadquery as cq

from .m_screw import MScrew
from . import teardrop
from . import heatserts

if TYPE_CHECKING:
    from .texture import TextureDetails


class Workplane(cq.Workplane):
    def teardrop(
        self, radius: float = 1, rotate: float = 0, clip: float | None = None
    ) -> Self:
        return cast(Self, teardrop.teardrop(self, radius, rotate, clip))

    def heatsert(
        self,
        size: MScrew = MScrew.M4,
        depth: float | None = None,
    ) -> Self:
        return cast(Self, heatserts.heatsert(self, size, depth))

    def texture(self, details: "TextureDetails", show_progress: bool = False) -> Self:
        # Import here to avoid circular import
        from .texture import add_texture

        return cast(Self, add_texture(self, details, show_progress))
