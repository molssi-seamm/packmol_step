#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `packmol_step` package."""

import packmol_step
import pytest


@pytest.fixture
def instance():
    instance = packmol_step.Packmol()
    instance._id = (1,)
    return instance


@pytest.mark.unit
def test_construction():
    """Simplest test that we can make a PACKMOL object"""
    instance = packmol_step.Packmol()
    assert str(type(instance)) == "<class 'packmol_step.packmol.Packmol'>"


@pytest.mark.unit
def test_version():
    """Test that the object returns a version"""
    instance = packmol_step.Packmol()
    result = instance.version
    assert isinstance(result, str) and len(result) > 0


@pytest.mark.unit
def test_git_revision():
    """Test that the object returns a git revision"""
    instance = packmol_step.Packmol()
    result = instance.git_revision
    assert isinstance(result, str) and len(result) > 0


@pytest.mark.unit
def test_description_text_default(instance):
    """Test the default description text"""

    reference = r"""    Will create a spherical region containing the following molecules:

        +-------------+-------------+---------+
        | Component   | Structure   | Ratio   |
        |-------------+-------------+---------|
        +-------------+-------------+---------+

    The dimensions of the region will be calculated from the density 0.7 g/ml.
    The number of molecules of the fluid will be obtained by rounding 2000 atoms
    to give a whole number of molecules with the requested ratios."""

    result = instance.description_text()
    result = "\n".join(result.splitlines()[1:])

    if reference != result:
        for ref, line in zip(reference.splitlines(), result.splitlines()):
            if ref != line:
                print(ref)
                print(line)
                print("")
        print(result)
        assert False
