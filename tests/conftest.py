#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Fixtures for testing the packmol_step package."""

import pytest

from molsystem import SystemDB


def pytest_addoption(parser):
    parser.addoption(
        "--no-unit", action="store_true", default=False, help="don't run the unit tests"
    )
    parser.addoption(
        "--integration",
        action="store_true",
        default=False,
        help="run the integration tests",
    )
    parser.addoption(
        "--timing", action="store_true", default=False, help="run the timing tests"
    )


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "unit: unit tests run by default, use '--no-unit' to turn off"
    )
    config.addinivalue_line(
        "markers", "integration: integration test, run with --integration"
    )
    config.addinivalue_line("markers", "timing: timing tests, run with --timing")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--no-unit"):
        skip = pytest.mark.skip(reason="remove --no-unit option to run")
        for item in items:
            if "unit" in item.keywords:
                item.add_marker(skip)
    if not config.getoption("--integration"):
        skip = pytest.mark.skip(reason="use the --integration option to run")
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip)
    if not config.getoption("--timing"):
        skip = pytest.mark.skip(reason="need --timing option to run")
        for item in items:
            if "timing" in item.keywords:
                item.add_marker(skip)


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


@pytest.fixture()
def db(empty_db):
    """Create an empty system db."""
    system = empty_db.create_system(name="default")
    system.create_configuration(name="default")

    return empty_db


@pytest.fixture()
def system(db):
    """An empty system."""
    return db.system


@pytest.fixture()
def configuration(system):
    """An empty system."""
    return system.configuration


@pytest.fixture()
def Argon(configuration):
    """An system object for an argon atom"""
    configuration.name = "argon"
    configuration.atoms.append(x=0.0, y=0.0, z=0.0, symbol=["Ar"])

    return configuration
