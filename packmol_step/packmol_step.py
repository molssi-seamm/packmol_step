# -*- coding: utf-8 -*-

"""Helper class needed for the stevedore integration. Needs to provide
a description() method that returns a dict containing a description of
this node, and a factory() method for creating the graphical and non-graphical
nodes."""

import packmol_step


class PackmolStep(object):
    my_description = {
        "description": "An interface for Packmol",
        "group": "Building",
        "name": "Packmol",
    }

    def __init__(self, flowchart=None, gui=None):
        """Initialize this helper class, which is used by
        the application via stevedore to get information about
        and create node objects for the flowchart
        """
        pass

    def description(self):
        """Return a description of what this extension does"""
        return PackmolStep.my_description

    def create_node(self, flowchart=None, **kwargs):
        """Return the new node object"""
        return packmol_step.Packmol(flowchart=flowchart, **kwargs)

    def create_tk_node(self, canvas=None, **kwargs):
        """Return the graphical Tk node object"""
        return packmol_step.TkPackmol(canvas=canvas, **kwargs)
