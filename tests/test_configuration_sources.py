#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Packmol with several configurations as sources (ChemAI job 5260)."""

import json
from pathlib import Path

import pytest
import seamm

from molsystem import SystemDB
import packmol_step

test_dir = Path(__file__).resolve().parent


@pytest.mark.unit
def test_two_configuration_sources():
    """Each source keeps its bonds, and so do the configurations themselves."""
    seamm.flowchart_variables = seamm.Variables()
    system_db = SystemDB(filename="file:sources_db?mode=memory&cache=shared")
    tmp_db = SystemDB(filename="file:sources_tmp_db?mode=memory&cache=shared")
    try:
        n_bonds = {}
        for name, smiles in (("CO2", "O=C=O"), ("PF6", "F[P-](F)(F)(F)(F)F")):
            system = system_db.create_system(name=name)
            configuration = system.create_configuration(name="initial")
            configuration.from_smiles(smiles)
            n_bonds[name] = configuration.bonds.n_bonds
        assert n_bonds == {"CO2": 2, "PF6": 6}

        data = json.loads(
            (test_dir / "inputs" / "test_1_spherical_region.json").read_text()
        )
        data["molecules"]["value"] = [
            {
                "component": "fluid",
                "source": "configuration",
                "definition": f"{name}/initial",
                "count": "2",
            }
            for name in ("CO2", "PF6")
        ]
        parameters = packmol_step.PackmolParameters()
        parameters.from_dict(data)
        P = parameters.current_values_to_dict(context=seamm.flowchart_variables._data)

        molecules, files, text, cell = packmol_step.Packmol.get_input(
            P, system_db, tmp_db, seamm.flowchart_variables
        )

        assert [len(m["bonds"]) for m in molecules] == [2, 6]
        for name, n in n_bonds.items():
            configuration = system_db.get_system(name).get_configuration("initial")
            assert configuration.bonds.n_bonds == n
        for key, value in files.items():
            if key.endswith(".pdb"):
                assert "CONECT" not in value
    finally:
        system_db.close()
        tmp_db.close()


@pytest.mark.unit
def test_rectangular_cell_uses_ratios():
    """The box's shape comes from the ratios the dialog shows, not a, b, c."""
    seamm.flowchart_variables = seamm.Variables()
    system_db = SystemDB(filename="file:ratios_db?mode=memory&cache=shared")
    tmp_db = SystemDB(filename="file:ratios_tmp_db?mode=memory&cache=shared")
    try:
        data = json.loads(
            (test_dir / "inputs" / "test_1_spherical_region.json").read_text()
        )
        data["molecules"]["value"] = [
            {"component": "fluid", "source": "SMILES", "definition": "O", "count": "1"}
        ]
        for key, value in (
            ("periodic", "Yes"),
            ("shape", "rectangular"),
            ("dimensions", "calculated from the volume"),
            ("fluid amount", "rounding this number of molecules"),
            ("a_ratio", "1"),
            ("b_ratio", "2"),
            ("c_ratio", "3"),
        ):
            data[key] = {"value": value, "units": None}
        for key in ("a", "b", "c"):
            data[key] = {"value": "20", "units": "Å"}
        parameters = packmol_step.PackmolParameters()
        parameters.from_dict(data)
        P = parameters.current_values_to_dict(context=seamm.flowchart_variables._data)

        molecules, files, text, cell = packmol_step.Packmol.get_input(
            P, system_db, tmp_db, seamm.flowchart_variables
        )

        a, b, c = cell
        assert b / a == pytest.approx(2.0) and c / a == pytest.approx(3.0)
        assert a * b * c == pytest.approx(8000.0)  # the default volume, 8 nm^3
    finally:
        system_db.close()
        tmp_db.close()
