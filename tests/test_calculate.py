#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `packmol_step` package."""

import packmol_step
import pytest
from seamm import data
from seamm_util import ureg, Q_, units_class  # noqa: F401


m_Ar = 39.948  # g/mol
n_A = 6.02214076E+23
L = 10.0E-10  # 10 Å
mass = m_Ar / n_A
n_atoms = 100
density = n_atoms * mass / (L*L*L * 1.0e+06)  # 10^6 ml / m^3


@pytest.fixture
def instance():
    instance = packmol_step.Packmol()
    instance._id = (1,)
    return instance


# Add a structure with 1 Ar atom
data.structure = {
    'atoms': {
        'elements': ['Ar']
    }
}


def test_cell_nmolecules(instance):
    """Test calculation of cell."""
    result = instance.calculate(
        size=Q_(10, 'Å'),
        n_molecules=100
    )
    assert abs(result['density'].magnitude - density) < 0.000001


def test_cell_natoms(instance):
    """Test calculation of cell."""
    result = instance.calculate(
        size=Q_(10, 'Å'),
        n_atoms=100
    )
    assert abs(result['density'].magnitude - density) < 0.000001


def test_cell_density(instance):
    """Test calculation of cell."""
    result = instance.calculate(
        size=Q_(10, 'Å'),
        density=Q_(density, 'g/ml')
    )
    assert result['n_atoms'] == 100


def test_cell_nmoles(instance):
    """Test calculation of cell."""
    result = instance.calculate(
        size=Q_(10, 'Å'),
        n_moles=Q_(n_atoms/n_A, 'mol')
    )
    assert abs(result['density'].magnitude - density) < 0.000001


def test_cell_mass(instance):
    """Test calculation of cell."""
    result = instance.calculate(
        size=Q_(10, 'Å'),
        mass=Q_(n_atoms*mass, 'g')
    )
    assert abs(result['density'].magnitude - density) < 0.000001


def test_volume_nmolecules(instance):
    """Test calculation of cell."""
    result = instance.calculate(
        volume=Q_(1000, 'Å**3'),
        n_molecules=100
    )
    assert abs(result['density'].magnitude - density) < 0.000001


def test_density_nmolecules(instance):
    """Test calculation of cell."""
    result = instance.calculate(
        density=Q_(density, 'g/ml'),
        n_molecules=100
    )
    assert abs(result['size'].magnitude - 10.0) < 0.000001


def test_density_natoms(instance):
    """Test calculation of cell."""
    result = instance.calculate(
        density=Q_(density, 'g/ml'),
        n_atoms=100
    )
    assert abs(result['size'].magnitude - 10.0) < 0.000001


def test_density_nmoles(instance):
    """Test calculation of cell."""
    result = instance.calculate(
        density=Q_(density, 'g/ml'),
        n_moles=Q_(n_atoms/n_A, 'mol')
    )
    assert abs(result['size'].magnitude - 10.0) < 0.000001


def test_density_mass(instance):
    """Test calculation of cell."""
    result = instance.calculate(
        density=Q_(density, 'g/ml'),
        mass=Q_(n_atoms*mass, 'g')
    )
    assert abs(result['size'].magnitude - 10.0) < 0.000001


# Resets the system! Needs to be at end
def test_no_system(instance):
    """Test calculation of cell. First error with no system."""
    from seamm import data
    data.structure = None
    with pytest.raises(
            RuntimeError, match=r"Packmol calculate: there is no structure!"
    ):
        instance.calculate(
            size=Q_(10, 'Å'),
            n_molecules=100
        )
