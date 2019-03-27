# -*- coding: utf-8 -*-
"""Control parameters for PACKMOL, currently for packing fluids
"""

import logging
import molssi_workflow
import pprint

logger = logging.getLogger(__name__)


class PACKMOL_Parameters(molssi_workflow.Parameters):
    """The control parameters for PACKMOL packing fluids
    """
    methods = {
        'size of cubic cell': (
            'density',
            'number of molecules',
            'approximate number of atoms',
            'moles',
            'mass'
        ),
        'volume': (
            'density',
            'number of molecules',
            'approximate number of atoms',
            'moles',
            'mass'
        ),
        'density': (
            'size of cubic cell',
            'volume',
            'number of molecules',
            'approximate number of atoms',
            'moles',
            'mass'
        ),
        'number of molecules': (
            'size of cubic cell',
            'volume',
            'density',
        ),
        'approximate number of atoms': (
            'size of cubic cell',
            'volume',
            'density',
        ),
        'moles': (
            'size of cubic cell',
            'volume',
            'density',
        ),
        'mass': (
            'size of cubic cell',
            'volume',
            'density',
        ),
    }

    parameters = {
        "method": {
            "default": "density",
            "kind": "enumeration",
            "default_units": "",
            "enumeration": (
                'size of cubic cell',
                'volume',
                'density',
                'number of molecules',
                'approximate number of atoms',
                'moles',
                'mass',
            ),
            "format_string": "s",
            "description": "Set the",
            "help_text": ("The principal parameter controlling the size of "
                          "the cell.")
        },
        "submethod": {
            "default": "approximate number of atoms",
            "kind": "enumeration",
            "default_units": "",
            "enumeration": (
                'size of cubic cell',
                'volume',
                'density',
                'number of molecules',
                'approximate number of atoms',
                'moles',
                'mass',
            ),
            "format_string": "s",
            "description": "and set the",
            "help_text": ("The secondary parameter controlling the size of "
                          "the cell.")
        },
        "minimize": {
            "default": "no",
            "kind": "boelan",
            "default_units": "",
            "enumeration": ("yes", "no"),
            "format_string": "s",
            "description": "Minimize the structure:",
            "help_text": ("Whether to minimize the structure using one "
                          "of the forcefields supported by OpenBabel.")
        },
        "forcefield": {
            "default": "UFF",
            "kind": "enumeration",
            "default_units": "",
            "enumeration": ("UFF", "GAFF", "MMFF94", "MMFF94s", "Ghemical"),
            "format_string": "s",
            "description": "Forcefield:",
            "help_text": ("The forcefield to use when minimizing the "
                          "structure.")
        },
    }

    def __init__(self, data=parameters):
        """Initialize the instance, by default from the default
        parameters given in the class"""

        logger.debug('PACKMOL_Parameters.__init__')

        super().__init__()

        logger.debug("Initializing PACKMOL_Parameters object:")
        logger.debug("\n{}\n".format(pprint.pformat(data)))

        self.update(data)
