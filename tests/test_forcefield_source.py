#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Where Packmol gets the forcefield it types molecules with."""

import types

from packmol_step import Packmol


def _node(variables, provider=None):
    def get_variable(name):
        return variables[name]

    return types.SimpleNamespace(
        variable_exists=lambda name: name in variables,
        get_variable=get_variable,
        flowchart=types.SimpleNamespace(
            plugin_manager=types.SimpleNamespace(get=lambda name: provider)
        ),
    )


class _Provider:
    """forcefield_step's side: builds the forcefield for a model chemistry."""

    @classmethod
    def forcefield(cls, model_chemistry, node=None):
        return f"built {model_chemistry['level']}"


def _mc(level, type_):
    return {"level": level, "type": type_, "step": "Forcefield", "options": {}}


def test_a_forcefield_model_chemistry():
    node = _node({"_model_chemistry": _mc("FF@oplsaa", "FF")}, _Provider)
    assert Packmol._forcefield(node) == "built FF@oplsaa"
    node = _node({"_model_chemistry": _mc("ReaxFF@CH_2018", "ReaxFF")}, _Provider)
    assert Packmol._forcefield(node) == "built ReaxFF@CH_2018"


def test_the_forcefield_step():
    assert Packmol._forcefield(_node({"_forcefield": "the ff"})) == "the ff"
    # A QM model chemistry does not type atoms; the Forcefield step's still can
    variables = {"_model_chemistry": _mc("MOPAC:SQM@PM7", "SQM")}
    assert Packmol._forcefield(_node(variables)) is None
    variables["_forcefield"] = "the ff"
    assert Packmol._forcefield(_node(variables)) == "the ff"


def test_no_atom_types():
    assert Packmol._forcefield(_node({"_forcefield": "OpenKIM"})) is None
    assert Packmol._forcefield(_node({})) is None
