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

    def __setattr__(self, key, value):
        if key == "x" and value < 0: value = 0
        if key == "y" and value < 0: value = 0
        if key == "similarity" and value < 0: value = 0
        super().__setattr__(key, value)

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
