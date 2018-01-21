# -*- coding: utf-8 -*-
"""Helper class needed for the stevedore integration. Needs to provide
a description() method that returns a dict containing a description of
this node, and a factory() method for creating the graphical and non-graphical
nodes."""

import packmol_step


class PACKMOLStep(object):
    my_description = {
        'description':
        'An interface for PACKMOL',
        'group': 'Building',
        'name': 'PACKMOL'
    }

    def __init__(self, workflow=None, gui=None):
        """Initialize this helper class, which is used by
        the application via stevedore to get information about
        and create node objects for the workflow
        """
        pass

    def description(self):
        """Return a description of what this extension does
        """
        return PACKMOLStep.my_description

    def factory(self, graphical=False, workflow=None, canvas=None, **kwargs):
        """Return the node object or graphical node object"""
        if graphical:
            return packmol_step.TkPACKMOL(canvas=canvas, **kwargs)
        else:
            return packmol_step.PACKMOL(workflow=workflow, **kwargs)
