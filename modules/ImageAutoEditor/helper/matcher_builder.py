import copy
import logging
from typing import List

import numpy as np

from modules.ImageAutoEditor.common.types import TemplateMethod, HashMethod
from modules.ImageAutoEditor.matchers import (
    BaseMatcher,
    TemplateMatcher,
    HashMatcher,
    SiftMatcher,
)

logger = logging.getLogger(__name__)


class MatcherBuilder:
    matchers: List[BaseMatcher]

    def __init__(self):
        self.matchers = []
        self.__config = {}

    def set_tm_matcher(self, threshold: float, method: TemplateMethod):
        matcher = TemplateMatcher(threshold, method)
        self.matchers.append(matcher)
        return self

    def set_hash_matcher(
        self,
        threshold: float,
        method: HashMethod,
        hash_size: int = 8,
        stride_ratio: float = 0.25,
    ):
        matcher = HashMatcher(threshold, method, hash_size, stride_ratio)
        self.matchers.append(matcher)
        return self

    def set_sift_matcher(self, threshold: float, min_match_count: int = 10):
        matcher = SiftMatcher(threshold, min_match_count)
        self.matchers.append(matcher)
        return self

    def set_config(self, k: str, v):
        self.__config[k] = v
        return self

    def build(self):
        return self.matchers

    def match(self, org: np.ndarray, targ: np.ndarray, **kwargs):
        allconfig = {**self.__config, **kwargs}

        matches = []
        for matcher in self.matchers:
            res = matcher.match(org, targ)

            matches.extend(res)

            # early stop 기능
            if allconfig.get("early_stop") and len(res) > 0:
                break

        return matches

    def serialize(self):
        items = []
        for m in self.matchers:
            if isinstance(m, TemplateMatcher):
                items.append(
                    ("tm", {"threshold": m.threshold, "method": m.method})
                )
            elif isinstance(m, HashMatcher):
                items.append(
                    (
                        "hash",
                        {
                            "threshold": m.threshold,
                            "method": m.method,
                            "hash_size": m.hash_size,
                            "stride_ratio": m.stride_ratio,
                        },
                    )
                )
            elif isinstance(m, SiftMatcher):
                items.append(
                    (
                        "sift",
                        {
                            "threshold": m.threshold,
                            "min_match_count": m.min_match_count,
                        },
                    )
                )

        specs = {"version": 1, "items": items}
        return specs, copy.deepcopy(self.__config)

    def deserialize(self, specs, config):
        version = specs.get("version")
        if version not in [1]:
            raise ValueError("Unsupport specs version")

        items = specs.get("items")
        if items is None or not isinstance(items, list):
            raise ValueError("Invalid specs")

        self.matchers = []
        self.__config = copy.deepcopy(config)

        for model, params in items:
            if model == "tm":
                self.set_tm_matcher(params["threshold"], params["method"])
            elif model == "hash":
                self.set_hash_matcher(
                    params["threshold"],
                    params["method"],
                    params["hash_size"],
                    params["stride_ratio"],
                )
            elif model == "sift":
                self.set_sift_matcher(
                    params["threshold"], params["min_match_count"]
                )

        return self

    @classmethod
    def from_specs(cls, builder_info):
        return cls().deserialize(*builder_info)
