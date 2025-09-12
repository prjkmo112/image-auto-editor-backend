from typing import Literal
from dataclasses import dataclass

TemplateMethod = Literal[
    "TM_CCOEFF_NORMED", "TM_CCORR_NORMED", "TM_SQDIFF_NORMED"
]
HashMethod = Literal["AHASH", "PHASH", "DHASH"]
MatchingMethod = TemplateMethod | HashMethod


@dataclass
class MatchResult:
    x: int
    y: int
    w: int
    h: int
    similarity: float
    method: str = ""
    scale: float = 1.0

    def __iter__(self):
        return iter(
            (
                self.x,
                self.y,
                self.w,
                self.h,
                self.similarity,
                self.method,
                self.scale,
            )
        )
