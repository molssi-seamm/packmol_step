# -*- coding: utf-8 -*-

"""
packmol_step
A step for building fluid boxes using Packmol
"""

# Bring up the classes so that they appear to be directly in
# the packmol_step package.

from packmol_step.packmol import Packmol  # noqa: F401
from packmol_step.packmol_parameters import PackmolParameters  # noqa: F401
from packmol_step.packmol_step import PackmolStep  # noqa: F401
from packmol_step.tk_packmol import TkPackmol  # noqa: F401

# Handle versioneer
from ._version import get_versions

__author__ = """Paul Saxe"""
__email__ = "psaxe@molssi.org"
versions = get_versions()
__version__ = versions["version"]
__git_revision__ = versions["full-revisionid"]
del get_versions, versions
