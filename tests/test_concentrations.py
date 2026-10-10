#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Amounts given as molalities, molarities and proportions by mass."""

import json
from pathlib import Path

import pytest
import seamm

from molsystem import SystemDB
import packmol_step

test_dir = Path(__file__).resolve().parent
AVOGADRO = 6.02214076e23

EC = "O=C1OCCO1"
DMC = "COC(=O)OC"
LI = "[Li+]"
PF6 = "F[P-](F)(F)(F)(F)F"


def run(molecules, **settings):
    """get_input for these molecules and settings; the molecules and cell."""
    seamm.flowchart_variables = seamm.Variables()
    data = json.loads(
        (test_dir / "inputs" / "test_1_spherical_region.json").read_text()
    )
    data["molecules"]["value"] = [
        {
            "component": "fluid",
            "source": "SMILES",
            "definition": definition,
            "count": str(count),
            "measure": measure,
        }
        for definition, count, measure in molecules
    ]
    for key, value in settings.items():
        units = None
        if isinstance(value, tuple):
            value, units = value
        data[key] = {"value": str(value), "units": units}
    parameters = packmol_step.PackmolParameters()
    parameters.from_dict(data)
    P = parameters.current_values_to_dict(context=seamm.flowchart_variables._data)

    system_db = SystemDB(filename="file:conc_db?mode=memory&cache=shared")
    tmp_db = SystemDB(filename="file:conc_tmp_db?mode=memory&cache=shared")
    try:
        molecules, files, text, cell = packmol_step.Packmol.get_input(
            P, system_db, tmp_db, seamm.flowchart_variables
        )
    finally:
        system_db.close()
        tmp_db.close()
    return {m["definition"]: m for m in molecules}, cell, text


def kg(molecule):
    return molecule["number"] * molecule["mass"].m_as("kg")


@pytest.mark.unit
def test_molality_with_mass_proportions():
    """1 mol/kg LiPF6 in EC:DMC 3:7 by weight, from the density."""
    m, cell, text = run(
        [
            (EC, 3, "proportion"),
            (DMC, 7, "proportion"),
            (LI, 1.0, "molality (mol/kg)"),
            (PF6, 1.0, "molality (mol/kg)"),
        ],
        periodic="Yes",
        shape="cubic",
        dimensions="calculated from the density",
        density=("1.3", "g/ml"),
        proportions="by mass",
        **{"fluid amount": "rounding this number of atoms"},
        **{"approximate number of atoms": 5000},
    )
    solvent = kg(m[EC]) + kg(m[DMC])
    assert kg(m[EC]) / solvent == pytest.approx(0.3, abs=0.01)
    assert m[LI]["number"] == m[PF6]["number"]
    molality = m[LI]["number"] / AVOGADRO / solvent
    assert molality == pytest.approx(1.0, abs=1.0 / AVOGADRO / solvent)
    assert m[LI]["molality"] == pytest.approx(molality)
    assert "wt%" in text and "mol/kg" in text


@pytest.mark.unit
def test_molarity_with_explicit_volume():
    """1 M of Li+ and PF6- in a 30 Å cube of EC filled to the density."""
    m, cell, text = run(
        [
            (EC, 1, "proportion"),
            (LI, 1.0, "molarity (mol/L)"),
            (PF6, 1.0, "molarity (mol/L)"),
        ],
        periodic="Yes",
        shape="cubic",
        dimensions="given explicitly",
        **{"edge length": ("30", "Å")},
        **{"fluid amount": "using the density"},
        density=("1.3", "g/ml"),
    )
    liters = 30.0**3 * 1.0e-27
    assert m[LI]["number"] == round(1.0 * AVOGADRO * liters) == m[PF6]["number"]
    total = kg(m[EC]) + kg(m[LI]) + kg(m[PF6])
    # The EC fills the rest of the mass to within one molecule
    assert total / liters == pytest.approx(1.3, abs=m[EC]["mass"].m_as("kg") / liters)


@pytest.mark.unit
def test_molarity_from_the_density():
    """1 M LiPF6 in EC:DMC 1:1, the volume following from the density."""
    m, cell, text = run(
        [
            (EC, 1, "proportion"),
            (DMC, 1, "proportion"),
            (LI, 1.0, "molarity (mol/L)"),
            (PF6, 1.0, "molarity (mol/L)"),
        ],
        periodic="Yes",
        shape="cubic",
        dimensions="calculated from the density",
        density=("1.3", "g/ml"),
        **{"fluid amount": "rounding this number of atoms"},
        **{"approximate number of atoms": 5000},
    )
    liters = cell[0] * cell[1] * cell[2] * 1.0e-27
    total = sum(kg(x) for x in m.values())
    assert total / liters == pytest.approx(1.3, rel=1e-6)
    assert m[LI]["number"] == m[PF6]["number"]
    assert m[LI]["molarity"] == pytest.approx(1.0, abs=0.6 / AVOGADRO / liters)
    assert sum(x["number"] * x["n_atoms"] for x in m.values()) == pytest.approx(
        5000, abs=20
    )


@pytest.mark.unit
def test_a_solvent_is_needed():
    with pytest.raises(RuntimeError, match="as a proportion"):
        run(
            [(LI, 1.0, "molality (mol/kg)"), (PF6, 1.0, "molality (mol/kg)")],
            dimensions="calculated from the density",
        )


@pytest.mark.unit
def test_molarity_needs_a_volume():
    with pytest.raises(RuntimeError, match="Ideal Gas Law"):
        run(
            [(EC, 1, "proportion"), (LI, 0.1, "molarity (mol/L)")],
            dimensions="calculated using the Ideal Gas Law",
        )
