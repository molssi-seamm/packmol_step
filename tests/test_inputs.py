#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `packmol_step` package."""

import json
from pathlib import Path

import pytest

from molsystem import SystemDB
import packmol_step

test_dir = Path(__file__).resolve().parent
inputs = [test_dir / path for path in sorted(test_dir.glob("inputs/*.json"))]


@pytest.mark.unit
@pytest.mark.parametrize("input_file", inputs)
def test_spherical_region(input_file):
    """Test making a spherical region"""

    # The parameters fpr the test
    with open(input_file) as fd:
        tmp = json.load(fd)
    parameters = packmol_step.PackmolParameters()
    parameters.from_dict(tmp)
    P = parameters.current_values_to_dict()

    # The golden output file.
    output_filename = input_file.with_suffix(".out").name
    output = test_dir / "outputs" / output_filename

    # Create the two System Databases that are needed
    system_db = SystemDB(filename="file:seamm_db?mode=memory&cache=shared")
    tmp_db = SystemDB(filename="file:tmp_db?mode=memory&cache=shared")

    # And get the input for PACKMOL
    molecules, files, text, cell = packmol_step.Packmol.get_input(P, system_db, tmp_db)

    if output.exists():
        reference = output.read_text()
        if files["input.inp"] != reference:
            new_output = output.with_suffix(".out_new")
            new_output.write_text(files["input.inp"])
            print(f"Updated output written to {new_output}")
        assert files["input.inp"] == reference
    else:
        output.write_text(files["input.inp"])
        print(f"New output written to {output}")
        assert False
