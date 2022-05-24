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


@pytest.fixture
def instance():
    instance = packmol_step.Packmol()
    instance._id = (1,)
    return instance


@pytest.fixture()
def empty_db():
    """Create a system db with no systems."""
    db = SystemDB(filename="file:seamm_db?mode=memory&cache=shared")

    yield db

    db.close()
    try:
        del db
    except:  # noqa: E722
        print("Caught error deleting the database")


@pytest.mark.unit
@pytest.mark.parametrize("input_file", inputs)
def test_spherical_region(instance, input_file):
    """Test making a spherical region"""

    with open(input_file) as fd:
        P = json.load(fd)
    output = test_dir / "outputs" / input_file.with_suffix(".out").name

    system_db = SystemDB(filename="file:seamm_db?mode=memory&cache=shared")
    tmp_db = SystemDB(filename="file:tmp_db?mode=memory&cache=shared")

    molecules, files, output, cell = instance.get_input(P, system_db, tmp_db)

    if output.exists():
        reference = output.read_text()
        assert files["input.inp"] == reference
    else:
        output.write_text(files["input.inp"])
        assert False
