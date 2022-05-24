#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `packmol_step` running full flowcharts."""
import os
from pathlib import Path
import pytest
from seamm import run_flowchart

test_dir = Path(__file__).resolve().parent

flowcharts = [
    str(test_dir / path) for path in sorted(test_dir.glob("flowcharts/*.flow"))
]
unit_flowcharts = [
    str(test_dir / path) for path in sorted(test_dir.glob("flowcharts/unit_*.flow"))
]


@pytest.mark.integration
@pytest.mark.parametrize("flowchart", flowcharts)
def test_ideal_gas(monkeypatch, tmp_path, flowchart):
    """Test creating a cell from an ideal gas."""
    monkeypatch.setattr(
        "sys.argv",
        [
            "testing",
            flowchart,
            "--standalone",
        ],
    )

    run_flowchart(wdir=str(tmp_path))


@pytest.mark.unit
@pytest.mark.parametrize("flowchart", unit_flowcharts)
def test_unit(monkeypatch, tmp_path, flowchart):
    """Test creating a cell from an ideal gas."""
    monkeypatch.setattr(
        "sys.argv",
        [
            "testing",
            flowchart,
            "--standalone",
        ],
    )

    run_flowchart(wdir=str(tmp_path))

    print(f"Files from run, in {tmp_path}")
    files = [f for f in os.listdir(tmp_path)]
    for f in files:
        print(f)
    print(40 * "+")

    assert False
