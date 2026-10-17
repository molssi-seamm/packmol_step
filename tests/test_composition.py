# -*- coding: utf-8 -*-

"""The name Packmol gives a box: what is in it."""

from types import SimpleNamespace

from packmol_step.packmol import composition_text


def molecule(number, formula):
    return {"number": number, "configuration": SimpleNamespace(formula=[formula])}


def test_composition_of_an_electrolyte():
    molecules = [molecule(512, "H2O"), molecule(9, "[Na]+"), molecule(9, "[Cl]-")]
    assert composition_text(molecules) == "512 H2O, 9 Na+, 9 Cl-"


def test_composition_of_a_mixture():
    assert composition_text([molecule(20, "C3 H4 O3"), molecule(4, "[B F4]-")]) == (
        "20 C3H4O3, 4 BF4-"
    )
