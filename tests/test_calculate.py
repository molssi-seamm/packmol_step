#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `packmol_step` package."""

import packmol_step
import pytest
from seamm_util import ureg, Q_, units_class  # noqa: F401


m_Ar = 39.8775  # g/mol
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


def test_cell_nmolecules(instance, Argon):
    """Test calculation of cell."""
    result = instance.calculate(
        Argon,
        size=Q_(10, 'Å'),
        n_molecules=100
    )
    assert abs(result['density'].magnitude - density) < 0.000001


def test_cell_natoms(instance, Argon):
    """Test calculation of cell."""
    result = instance.calculate(
        Argon,
        size=Q_(10, 'Å'),
        n_atoms=100
    )
    assert abs(result['density'].magnitude - density) < 0.000001


def test_cell_density(instance, Argon):
    """Test calculation of cell."""
    result = instance.calculate(
        Argon,
        size=Q_(10, 'Å'),
        density=Q_(density, 'g/ml')
    )
    assert result['n_atoms'] == 100


def test_cell_nmoles(instance, Argon):
    """Test calculation of cell."""
    result = instance.calculate(
        Argon,
        size=Q_(10, 'Å'),
        n_moles=Q_(n_atoms/n_A, 'mol')
    )
    assert abs(result['density'].magnitude - density) < 0.000001


def test_cell_mass(instance, Argon):
    """Test calculation of cell."""
    result = instance.calculate(
        Argon,
        size=Q_(10, 'Å'),
        mass=Q_(n_atoms*mass, 'g')
    )
    assert abs(result['density'].magnitude - density) < 0.000001


def test_volume_nmolecules(instance, Argon):
    """Test calculation of cell."""
    result = instance.calculate(
        Argon,
        volume=Q_(1000, 'Å**3'),
        n_molecules=100
    )
    assert abs(result['density'].magnitude - density) < 0.000001


def test_density_nmolecules(instance, Argon):
    """Test calculation of cell."""
    result = instance.calculate(
        Argon,
        density=Q_(density, 'g/ml'),
        n_molecules=100
    )
    assert abs(result['size'].magnitude - 10.0) < 0.000001


def test_density_natoms(instance, Argon):
    """Test calculation of cell."""
    result = instance.calculate(
        Argon,
        density=Q_(density, 'g/ml'),
        n_atoms=100
    )
    assert abs(result['size'].magnitude - 10.0) < 0.000001


def test_density_nmoles(instance, Argon):
    """Test calculation of cell."""
    result = instance.calculate(
        Argon,
        density=Q_(density, 'g/ml'),
        n_moles=Q_(n_atoms/n_A, 'mol')
    )
    assert abs(result['size'].magnitude - 10.0) < 0.000001


def test_density_mass(instance, Argon):
    """Test calculation of cell."""
    result = instance.calculate(
        Argon,
        density=Q_(density, 'g/ml'),
        mass=Q_(n_atoms*mass, 'g')
    )
    assert abs(result['size'].magnitude - 10.0) < 0.000001


# Resets the system! Needs to be at end
def test_no_system(instance, system):
    """Test calculation of cell. First error with empty system."""
    with pytest.raises(
        RuntimeError, match=r"Packmol calculate: there is no structure!"
    ):
        instance.calculate(
            system,
            size=Q_(10, 'Å'),
            n_molecules=100
        )
