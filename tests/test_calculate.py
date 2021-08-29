#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `packmol_step` package."""

import packmol_step
import pprint  # noqa: F401
import pytest
from seamm_util import ureg, Q_, units_class  # noqa: F401


m_Ar = 39.8775  # g/mol
n_A = 6.02214076e23
L = 10.0e-10  # 10 Å
mass = m_Ar / n_A
n_atoms = 100
density = n_atoms * mass / (L * L * L * 1.0e06)  # 10^6 ml / m^3
input_mass = m_Ar * ureg.g / ureg.mol
input_mass.ito("kg")
molar_volume = 22.710954641485  # L
rho_stp = m_Ar / molar_volume


@pytest.fixture
def instance():
    instance = packmol_step.Packmol()
    instance._id = (1,)
    return instance


@pytest.mark.unit
def test_cell_nmolecules(instance):
    """Test calculation of cell."""
    result = instance.calculate(
        input_n_molecules=1,
        input_n_atoms=1,
        input_mass=input_mass,
        size=Q_(10, "Å"),
        n_molecules=100,
    )
    assert abs(result["density"].magnitude - density) < 0.000001


@pytest.mark.unit
def test_cell_natoms(instance):
    """Test calculation of cell."""
    result = instance.calculate(
        input_n_molecules=1,
        input_n_atoms=1,
        input_mass=input_mass,
        size=Q_(10, "Å"),
        n_atoms=100,
    )
    assert abs(result["density"].magnitude - density) < 0.000001


@pytest.mark.unit
def test_cell_density(instance):
    """Test calculation of cell."""
    result = instance.calculate(
        input_n_molecules=1,
        input_n_atoms=1,
        input_mass=input_mass,
        size=Q_(10, "Å"),
        density=Q_(density, "g/ml"),
    )
    assert result["n_atoms"] == 100


@pytest.mark.unit
def test_cell_nmoles(instance):
    """Test calculation of cell."""
    result = instance.calculate(
        input_n_molecules=1,
        input_n_atoms=1,
        input_mass=input_mass,
        size=Q_(10, "Å"),
        n_moles=Q_(n_atoms / n_A, "mol"),
    )
    assert abs(result["density"].magnitude - density) < 0.000001


@pytest.mark.unit
def test_cell_mass(instance):
    """Test calculation of cell."""
    result = instance.calculate(
        input_n_molecules=1,
        input_n_atoms=1,
        input_mass=input_mass,
        size=Q_(10, "Å"),
        mass=Q_(n_atoms * mass, "g"),
    )
    assert abs(result["density"].magnitude - density) < 0.000001


@pytest.mark.unit
def test_volume_nmolecules(instance):
    """Test calculation of cell."""
    result = instance.calculate(
        input_n_molecules=1,
        input_n_atoms=1,
        input_mass=input_mass,
        volume=Q_(1000, "Å**3"),
        n_molecules=100,
    )
    assert abs(result["density"].magnitude - density) < 0.000001


@pytest.mark.unit
def test_density_nmolecules(instance):
    """Test calculation of cell."""
    result = instance.calculate(
        input_n_molecules=1,
        input_n_atoms=1,
        input_mass=input_mass,
        density=Q_(density, "g/ml"),
        n_molecules=100,
    )
    assert abs(result["size"].magnitude - 10.0) < 0.000001


@pytest.mark.unit
def test_density_natoms(instance):
    """Test calculation of cell."""
    result = instance.calculate(
        input_n_molecules=1,
        input_n_atoms=1,
        input_mass=input_mass,
        density=Q_(density, "g/ml"),
        n_atoms=100,
    )
    assert abs(result["size"].magnitude - 10.0) < 0.000001


@pytest.mark.unit
def test_density_nmoles(instance):
    """Test calculation of cell."""
    result = instance.calculate(
        input_n_molecules=1,
        input_n_atoms=1,
        input_mass=input_mass,
        density=Q_(density, "g/ml"),
        n_moles=Q_(n_atoms / n_A, "mol"),
    )
    assert abs(result["size"].magnitude - 10.0) < 0.000001


@pytest.mark.unit
def test_density_mass(instance):
    """Test calculation of cell."""
    result = instance.calculate(
        input_n_molecules=1,
        input_n_atoms=1,
        input_mass=input_mass,
        density=Q_(density, "g/ml"),
        mass=Q_(n_atoms * mass, "g"),
    )
    assert abs(result["size"].magnitude - 10.0) < 0.000001


@pytest.mark.unit
def test_ideal_gas(instance):
    """Test calculation of cell."""
    result = instance.calculate(
        input_n_molecules=1,
        input_n_atoms=1,
        input_mass=input_mass,
        pressure=Q_(1, "bar"),
        temperature=Q_(273.15, "K"),
        n_molecules=n_A,
    )
    assert abs(result["density"].to("g/L").magnitude - rho_stp) < 0.000001
