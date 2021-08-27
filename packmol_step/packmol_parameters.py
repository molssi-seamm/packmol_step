# -*- coding: utf-8 -*-
"""Control parameters for Packmol, currently for packing fluids
"""

import logging
import seamm

logger = logging.getLogger(__name__)


class PackmolParameters(seamm.Parameters):
    """The control parameters for Packmol packing fluids"""

    methods = {
        "size of cubic cell": (
            "density",
            "number of molecules",
            "approximate number of atoms",
            "ideal gas pressure",
        ),
        "volume": (
            "density",
            "number of molecules",
            "approximate number of atoms",
            "ideal gas pressure",
        ),
        "density": (
            "size of cubic cell",
            "volume",
            "number of molecules",
            "approximate number of atoms",
        ),
        "number of molecules": (
            "size of cubic cell",
            "volume",
            "density",
            "ideal gas pressure",
        ),
        "approximate number of atoms": (
            "size of cubic cell",
            "volume",
            "density",
            "ideal gas pressure",
        ),
        "ideal gas pressure": (
            "size of cubic cell",
            "volume",
            "number of molecules",
            "approximate number of atoms",
        ),
    }

    parameters = {
        "molecule source": {
            "default": "current configuration",
            "kind": "string",
            "default_units": "",
            "enumeration": ("current configuration", "SMILES"),
            "format_string": "s",
            "description": "Molecule(s) to pack:",
            "help_text": "Where to get the molecules from.",
        },
        "molecules": {
            "default": [],
            "kind": "list",
            "default_units": None,
            "enumeration": tuple(),
            "format_string": "",
            "description": "The molecules",
            "help_text": "An internal place to put the molecule definitions.",
        },
        "method": {
            "default": "density",
            "kind": "enumeration",
            "default_units": "",
            "enumeration": tuple(methods.keys()),
            "format_string": "s",
            "description": "Set the",
            "help_text": "The first parameter controlling the size of the cell.",
        },
        "submethod": {
            "default": "approximate number of atoms",
            "kind": "enumeration",
            "default_units": "",
            "enumeration": tuple(methods.keys()),
            "format_string": "s",
            "description": "and set the",
            "help_text": "The second parameter controlling the size of the cell.",
        },
        "gap": {
            "default": 2.0,
            "kind": "float",
            "default_units": "Å",
            "enumeration": tuple(),
            "format_string": ".1f",
            "description": "Gap around cell:",
            "help_text": (
                "Since Packmol does not support periodic systems "
                "we will build a box with this gap around the "
                "atoms, then make it periodic. The gap ensures "
                "that molecules at the boundary do not hit images"
            ),
        },
        "size of cubic cell": {
            "default": 4.0,
            "kind": "float",
            "default_units": "nm",
            "enumeration": tuple(),
            "format_string": ".1f",
            "description": "Length of the cube edge:",
            "help_text": ("The length of the cube edge."),
        },
        "number of molecules": {
            "default": 100,
            "kind": "integer",
            "default_units": "",
            "enumeration": tuple(),
            "format_string": "d",
            "description": "Number of molecules:",
            "help_text": ("The number of molecules to pack in the cell."),
        },
        "approximate number of atoms": {
            "default": 2000,
            "kind": "integer",
            "default_units": "",
            "enumeration": tuple(),
            "format_string": "d",
            "description": "Approximate number of atoms:",
            "help_text": (
                "The approximate number of atoms packed into the "
                "cell. This will be rounded to give whole molecules"
            ),
        },
        "volume": {
            "default": 64.0,
            "kind": "float",
            "default_units": "nm^3",
            "enumeration": tuple(),
            "format_string": ".1f",
            "description": "The volume of the cell:",
            "help_text": ("The volume of the target cell."),
        },
        "density": {
            "default": 0.7,
            "kind": "float",
            "default_units": "g/ml",
            "enumeration": tuple(),
            "format_string": ".1f",
            "description": "Density:",
            "help_text": ("The target density of the cell."),
        },
        "ideal gas pressure": {
            "default": 1.0,
            "kind": "float",
            "default_units": "atm",
            "enumeration": tuple(),
            "format_string": ".2f",
            "description": "Ideal gas pressure:",
            "help_text": ("The pressure using an ideal gas model (PV=nRT)."),
        },
        "ideal gas temperature": {
            "default": 298.15,
            "kind": "float",
            "default_units": "K",
            "enumeration": tuple(),
            "format_string": ".2f",
            "description": "Ideal gas temperature:",
            "help_text": ("The temperature using an ideal gas model (PV=nRT)."),
        },
    }

    def __init__(self, defaults={}, data=None):
        """Initialize the instance, by default from the default
        parameters given in the class"""

        super().__init__(
            defaults={**PackmolParameters.parameters, **defaults}, data=data
        )
