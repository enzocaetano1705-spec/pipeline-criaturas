"""Forja: code-first, relation-based low-poly modelling for Blockbench / Roblox.

    from forja import Model, T, props
    m = Model("polvo", palette="coral")
    rig = T.cephalopod(m)
    props.sneakers(m, rig.feet)
"""
from .core import Model, Box, Pair, Bone, ForjaError, P
from .style import PALETTES
from . import templates as T
from . import props
from .build import build, build_series

__all__ = ["Model", "Box", "Pair", "Bone", "ForjaError", "P", "PALETTES", "T", "props",
           "build", "build_series"]
