# -*- coding: utf-8 -*-
"""Control parameters for Packmol, currently for packing fluids
"""

import logging
import seamm

logger = logging.getLogger(__name__)


class PackmolParameters(seamm.Parameters):
    """The control parameters for Packmol packing fluids"""

    shapes = (
        "cubic",
        "rectangular",
        "spherical",
    )
    periodic_shapes = (
        "cubic",
        "rectangular",
    )
    amounts = (
        "rounding this number of atoms",
        "rounding this number of molecules",
        "using the density",
        "using the Ideal Gas Law",
    )
    amounts_for_layer = (
        "using the density",
        "using the Ideal Gas Law",
    )
    amounts_for_density = (
        "rounding this number of atoms",
        "rounding this number of molecules",
    )

    parameters = {
        "molecules": {
            "default": [],
            "kind": "list",
            "default_units": None,
            "enumeration": tuple(),
            "format_string": "",
            "description": "The molecules",
            "help_text": "An internal place to put the molecule definitions.",
        },
        "periodic": {
            "default": "No",
            "kind": "boolean",
            "default_units": "",
            "enumeration": (
                "Yes",
                "No",
            ),
            "format_string": "s",
            "description": "Create periodic system:",
            "help_text": "Whether to create a periodic system or not.",
        },
        "shape": {
            "default": "spherical",
            "kind": "enumeration",
            "default_units": "",
            "enumeration": shapes,
            "format_string": "s",
            "description": "Shape of the region:",
            "help_text": "The shape of the desired region.",
        },
        "dimensions": {
            "default": "calculated from the density",
            "kind": "enumeration",
            "default_units": "",
            "enumeration": (
                "given explicitly",
                "calculated from the volume",
                "calculated from the solute dimensions",
                "calculated from the density",
                "calculated using the Ideal Gas Law",
            ),
            "format_string": "s",
            "description": "The dimensions will be",
            "help_text": "How to get the dimensions of the region",
        },
        "fluid amount": {
            "default": "rounding this number of atoms",
            "kind": "enumeration",
            "default_units": "",
            "enumeration": amounts_for_density,
            "format_string": "s",
            "description": "Get number of fluid molecules by",
            "help_text": "How to get the number of fluid molecules",
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
        "volume": {
            "default": 8.0,
            "kind": "float",
            "default_units": "nm^3",
            "enumeration": tuple(),
            "format_string": ".1f",
            "description": "The volume of the cell:",
            "help_text": ("The volume of the target cell."),
        },
        "temperature": {
            "default": 298.15,
            "kind": "float",
            "default_units": "K",
            "enumeration": tuple(),
            "format_string": ".2f",
            "description": "T:",
            "help_text": ("The temperature using an ideal gas model (PV=nRT)."),
        },
        "pressure": {
            "default": 1.0,
            "kind": "float",
            "default_units": "atm",
            "enumeration": tuple(),
            "format_string": ".2f",
            "description": "P:",
            "help_text": ("The pressure using an ideal gas model (PV=nRT)."),
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
        "edge length": {
            "default": 20,
            "kind": "float",
            "default_units": "Å",
            "enumeration": tuple(),
            "format_string": ".1f",
            "description": "Length of the cube edge:",
            "help_text": ("The length of the cube edge."),
        },
        "a": {
            "default": 20,
            "kind": "float",
            "default_units": "Å",
            "enumeration": tuple(),
            "format_string": ".1f",
            "description": "a:",
            "help_text": "The length of the first side of the box.",
        },
        "b": {
            "default": 20,
            "kind": "float",
            "default_units": "Å",
            "enumeration": tuple(),
            "format_string": ".1f",
            "description": "b:",
            "help_text": "The length of the second side of the box.",
        },
        "c": {
            "default": 20,
            "kind": "float",
            "default_units": "Å",
            "enumeration": tuple(),
            "format_string": ".1f",
            "description": "c:",
            "help_text": "The length of the third side of the box.",
        },
        "a_ratio": {
            "default": 1,
            "kind": "float",
            "default_units": "",
            "enumeration": tuple(),
            "format_string": ".1f",
            "description": "a ratio:",
            "help_text": "The ratio for the first side of the box.",
        },
        "b_ratio": {
            "default": 1,
            "kind": "float",
            "default_units": "",
            "enumeration": tuple(),
            "format_string": ".1f",
            "description": "b ratio:",
            "help_text": "The ratio for the second side of the box.",
        },
        "c_ratio": {
            "default": 1,
            "kind": "float",
            "default_units": "",
            "enumeration": tuple(),
            "format_string": ".1f",
            "description": "c ratio:",
            "help_text": "The ratio for the third side of the box.",
        },
        "diameter": {
            "default": 20.0,
            "kind": "float",
            "default_units": "Å",
            "enumeration": tuple(),
            "format_string": ".1f",
            "description": "The diameter:",
            "help_text": "The diameter of the sphere or cylinder.",
        },
        "solvent thickness": {
            "default": 10.0,
            "kind": "float",
            "default_units": "Å",
            "enumeration": tuple(),
            "format_string": ".1f",
            "description": "Solvent thickness:",
            "help_text": "The thickness of the layer of solvent around the solute",
        },
        "approximate number of molecules": {
            "default": 100,
            "kind": "integer",
            "default_units": "",
            "enumeration": tuple(),
            "format_string": "d",
            "description": "Approximate number of molecules:",
            "help_text": ("The approximate number of molecules to pack in the cell."),
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
        "assign forcefield": {
            "default": "If not assigned",
            "kind": "enum",
            "default_units": "",
            "enumeration": (
                "If not assigned",
                "Always",
                "No",
            ),
            "format_string": "s",
            "description": "Assign forcefield:",
            "help_text": "Whether to assign the forcefield to the molecules.",
        },
    }

    def __init__(self, defaults={}, data=None):
        """Initialize the instance, by default from the default
        parameters given in the class"""

        super().__init__(
            defaults={
                **PackmolParameters.parameters,
                **seamm.standard_parameters.structure_handling_parameters,
                **defaults,
            },
            data=data,
        )
