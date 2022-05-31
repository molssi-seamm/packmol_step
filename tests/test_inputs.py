#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `packmol_step` package."""

import json
from pathlib import Path
import seamm
from seamm_util import units_class

import pytest

from molsystem import SystemDB
import packmol_step

test_dir = Path(__file__).resolve().parent
inputs = [test_dir / path for path in sorted(test_dir.glob("inputs/*.json"))]


@pytest.mark.unit
@pytest.mark.parametrize("input_file", inputs)
def test_spherical_region(input_file):
    """Test the PACKMOL input and description"""

    # The parameters for the test
    with open(input_file) as fd:
        tmp = json.load(fd)

    # Handle any local variables that need definition
    variables = tmp.pop("_variables_", {})
    seamm.flowchart_variables = seamm.Variables(**variables)

    parameters = packmol_step.PackmolParameters()
    parameters.from_dict(tmp)
    P = parameters.current_values_to_dict(context=seamm.flowchart_variables._data)
    # The golden output file and PACKMOL input file
    output = test_dir / "outputs" / input_file.with_suffix(".out").name
    input = test_dir / "outputs" / input_file.with_suffix(".inp").name

    # Create the two System Databases that are needed
    system_db = SystemDB(filename="file:seamm_db?mode=memory&cache=shared")
    tmp_db = SystemDB(filename="file:tmp_db?mode=memory&cache=shared")

    # Print what we are doing. Have to fix formatting for printing...
    PP = dict(P)
    for key in PP:
        if isinstance(PP[key], units_class):
            PP[key] = "{:~P}".format(PP[key])

    instance = packmol_step.Packmol()
    instance._id = (1,)
    instance.parameters = parameters

    # Get the description
    description = instance.description_text(PP)
    output_text = "\n".join(description.splitlines()[1:])

    # And get the input for PACKMOL
    molecules, files, text, cell = packmol_step.Packmol.get_input(
        P, system_db, tmp_db, seamm.flowchart_variables
    )

    output_text += "\n"
    output_text += text

    output_reference = ""
    input_reference = ""
    if output.exists():
        output_reference = output.read_text()
        if output_text != output_reference:
            new_output = output.with_suffix(".out_new")
            new_output.write_text(output_text)
            print(f"Updated output written to {new_output}")
    else:
        output.write_text(output_text)
        print(f"New output written to {output}")

    if input.exists():
        input_reference = input.read_text()
        if files["input.inp"] != input_reference:
            new_input = input.with_suffix(".inp_new")
            new_input.write_text(files["input.inp"])
            print(f"Updated PACKMOL input written to {new_input}")
    else:
        input.write_text(files["input.inp"])
        print(f"New PACKMOL input written to {input}")

    assert output_text == output_reference
    assert files["input.inp"] == input_reference
