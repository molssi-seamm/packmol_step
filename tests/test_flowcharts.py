#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `packmol_step` running full flowcharts."""

from pathlib import Path
import shutil

import pytest
from seamm_exec import run

test_dir = Path(__file__).resolve().parent

# The flowcharts run Packmol, so they need it: configured in the SEAMM installation, or
# on the PATH. Neither is there in CI.
needs_packmol = pytest.mark.skipif(
    not (Path("~/SEAMM/packmol.ini").expanduser().exists() or shutil.which("packmol")),
    reason="Packmol is not installed",
)

flowcharts = [
    str(test_dir / path)
    for path in sorted(test_dir.glob("flowcharts/integration_*.flow"))
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

    run(wdir=str(tmp_path))


@pytest.mark.unit
@needs_packmol
@pytest.mark.parametrize("flowchart", unit_flowcharts)
def test_unit(monkeypatch, tmp_path, flowchart):
    """Unit tests with flowcharts"""
    monkeypatch.setattr(
        "sys.argv",
        [
            "testing",
            flowchart,
            "--standalone",
        ],
    )

    run(wdir=str(tmp_path))
