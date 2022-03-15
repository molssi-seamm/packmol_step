#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `packmol_step` package."""

import packmol_step
import pytest
import re


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

    reference = r"""Step 1: Packmol  [-+.0-9a-z]+
    Create a cubic supercell \(box\) of fluid from the current system with a
    density of 0\.7 g/ml containing about 2000 atoms"""

    result = instance.description_text()

    if re.fullmatch(reference, result) is None:
        print(result)
        assert False


@pytest.mark.unit
def test_description_text_expr_expr(instance):
    """Test the default description text"""

    reference = r"""Step 1: Packmol  [-+.0-9a-z]+
    Create a cubic supercell \(box\) of fluid from the current system with the
    method given by \$method and a submethod given by \$submethod"""

    result = instance.description_text(
        {
            "molecule source": "current configuration",
            "operation": "create a fluid box",
            "method": "$method",
            "submethod": "$submethod",
        }
    )

    if re.fullmatch(reference, result) is None:
        print(result)
        assert False


@pytest.mark.unit
def test_description_text_cubic_expr(instance):
    """Test the description text"""

    reference = r"""Step 1: Packmol  [-+.0-9a-z]+
    Create a cubic supercell \(box\) of fluid from the current system 10.0 Å on a
    side and a submethod given by \$submethod"""

    result = instance.description_text(
        {
            "molecule source": "current configuration",
            "operation": "create a fluid box",
            "method": "cubic",
            "size of cubic cell": "10.0 Å",
            "submethod": "$submethod",
        }
    )

    if re.fullmatch(reference, result) is None:
        print(result)
        assert False


@pytest.mark.unit
def test_description_text_cubic_density(instance):
    """Test the description text"""

    reference = r"""Step 1: Packmol  [-+.0-9a-z]+
    Create a cubic supercell \(box\) of fluid from the current system 10.0 Å on a
    side with a density of 1.0 g/mL"""

    result = instance.description_text(
        {
            "molecule source": "current configuration",
            "operation": "create a fluid box",
            "method": "cubic",
            "size of cubic cell": "10.0 Å",
            "submethod": "density",
            "density": "1.0 g/mL",
        }
    )

    if re.fullmatch(reference, result) is None:
        print(result)
        assert False


@pytest.mark.unit
def test_description_text_cubic_nmolecules(instance):
    """Test the description text"""

    reference = r"""Step 1: Packmol  [-+.0-9a-z]+
    Create a cubic supercell \(box\) of fluid from the current system 10.0 Å on a
    side containing 50 molecules"""

    result = instance.description_text(
        {
            "molecule source": "current configuration",
            "operation": "create a fluid box",
            "method": "cubic",
            "size of cubic cell": "10.0 Å",
            "submethod": "number of molecules",
            "number of molecules": "50",
        }
    )

    if re.fullmatch(reference, result) is None:
        print(result)
        assert False


@pytest.mark.unit
def test_description_text_cubic_natoms(instance):
    """Test the description text"""

    reference = r"""Step 1: Packmol  [-+.0-9a-z]+
    Create a cubic supercell \(box\) of fluid from the current system 10.0 Å on a
    side containing about 2000 atoms"""

    result = instance.description_text(
        {
            "molecule source": "current configuration",
            "operation": "create a fluid box",
            "method": "cubic",
            "size of cubic cell": "10.0 Å",
            "submethod": "approximate number of atoms",
            "approximate number of atoms": "2000",
        }
    )

    if re.fullmatch(reference, result) is None:
        print(result)
        assert False


@pytest.mark.unit
def test_description_text_volume_nmolecules(instance):
    """Test the description text"""

    reference = r"""Step 1: Packmol  [-+.0-9a-z]+
    Create a cubic supercell \(box\) of fluid from the current system with a
    volume of 1000.0 Å\^3 containing 50 molecules"""

    result = instance.description_text(
        {
            "molecule source": "current configuration",
            "operation": "create a fluid box",
            "method": "volume",
            "volume": "1000.0 Å^3",
            "submethod": "number of molecules",
            "number of molecules": "50",
        }
    )

    if re.fullmatch(reference, result) is None:
        print(result)
        assert False


@pytest.mark.unit
def test_description_text_nmolecules_volume(instance):
    """Test the description text"""

    reference = r"""Step 1: Packmol  [-+.0-9a-z]+
    Create a cubic supercell \(box\) of fluid from the current system containing
    50 molecules with a volume of 1000\.0 Å\^3"""

    result = instance.description_text(
        {
            "molecule source": "current configuration",
            "operation": "create a fluid box",
            "method": "number of molecules",
            "number of molecules": "50",
            "submethod": "volume",
            "volume": "1000.0 Å^3",
        }
    )

    if re.fullmatch(reference, result) is None:
        print(result)
        assert False


@pytest.mark.unit
def test_description_text_natoms_cubic(instance):
    """Test the description text"""

    reference = r"""Step 1: Packmol  [-+.0-9a-z]+
    Create a cubic supercell \(box\) of fluid from the current system containing
    about 999 atoms in a cell 10.0 Å on a side"""

    result = instance.description_text(
        {
            "molecule source": "current configuration",
            "operation": "create a fluid box",
            "method": "approximate number of atoms",
            "approximate number of atoms": "999",
            "submethod": "cubic",
            "size of cubic cell": "10.0 Å",
        }
    )

    if re.fullmatch(reference, result) is None:
        print(result)
        assert False


@pytest.mark.unit
def test_description_text_method_error(instance):
    """Test the description text"""

    with pytest.raises(RuntimeError, match=r"Don't recognize the method junk"):
        instance.description_text(
            {
                "molecule source": "current configuration",
                "operation": "create a fluid box",
                "method": "junk",
            }
        )


@pytest.mark.unit
def test_description_text_submethod_error(instance):
    """Test the description text"""

    with pytest.raises(RuntimeError, match=r"Don't recognize the submethod junk"):
        instance.description_text(
            {
                "molecule source": "current configuration",
                "operation": "create a fluid box",
                "method": "number of molecules",
                "number of molecules": "50",
                "submethod": "junk",
            }
        )
