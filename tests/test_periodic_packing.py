#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Runs PACKMOL, if it is installed, to check that molecules packed into a periodic
cell are kept apart across its faces."""

import json
from pathlib import Path
import shutil
import subprocess

import numpy as np
import pytest
import seamm

from molsystem import SystemDB
import packmol_step

test_dir = Path(__file__).resolve().parent


def packmol_executable():
    path = shutil.which("packmol")
    if path is None:
        candidate = Path.home() / "miniconda3/envs/seamm-packmol/bin/packmol"
        if candidate.exists():
            path = str(candidate)
    return path


@pytest.mark.skipif(packmol_executable() is None, reason="PACKMOL is not installed")
def test_molecules_are_apart_across_the_cell(tmp_path):
    data = json.loads((test_dir / "inputs/test_4_periodic_cubic_cell.json").read_text())
    data["molecules"]["value"] = data["molecules"]["value"][1:]  # just water
    data["approximate number of atoms"]["value"] = "1536"  # 512 waters
    seamm.flowchart_variables = seamm.Variables()
    parameters = packmol_step.PackmolParameters()
    parameters.from_dict(data)
    P = parameters.current_values_to_dict(context=seamm.flowchart_variables._data)

    system_db = SystemDB(filename="file:pbc_db?mode=memory&cache=shared")
    tmp_db = SystemDB(filename="file:pbc_tmp_db?mode=memory&cache=shared")
    molecules, files, text, cell = packmol_step.Packmol.get_input(
        P, system_db, tmp_db, seamm.flowchart_variables
    )
    assert "pbc" not in files["input.inp"]
    for name, contents in files.items():
        (tmp_path / name).write_text(contents)
    with open(tmp_path / "input.inp") as fd:
        subprocess.run(
            [packmol_executable()],
            stdin=fd,
            cwd=tmp_path,
            capture_output=True,
            check=True,
        )

    xyz = []
    for line in (tmp_path / "packmol.pdb").read_text().splitlines():
        if line.startswith(("ATOM", "HETATM")):
            xyz.append([float(line[30:38]), float(line[38:46]), float(line[46:54])])
    xyz = np.array(xyz)
    L = np.array(cell[:3])
    molecule = np.arange(len(xyz)) // 3
    d = xyz[:, None, :] - xyz[None, :, :]
    d -= L * np.round(d / L)
    r = np.sqrt((d**2).sum(axis=-1))
    r[molecule[:, None] == molecule[None, :]] = np.inf
    # PACKMOL's tolerance is 2.0 Å; it may be missed by a little
    assert r.min() > 1.8
