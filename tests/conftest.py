#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Fixtures for testing the packmol_step package."""

import pytest

from molsystem.systems import Systems


def pytest_addoption(parser):
    parser.addoption(
        "--run-timing",
        action="store_true",
        default=False,
        help="run timing tests"
    )


def pytest_configure(config):
    config.addinivalue_line("markers", "timing: mark test as timing to run")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--run-timing"):
        # --run-timing given in cli: do not skip timing tests
        return
    skip_timing = pytest.mark.skip(reason="need --run-timing option to run")
    for item in items:
        if "timing" in item.keywords:
            item.add_marker(skip_timing)


@pytest.fixture()
def system():
    systems = Systems()
    system = systems.create_system('seamm', temporary=True)

    yield system

    del systems['seamm']


@pytest.fixture()
def Argon(system):
    """An system object for an argon atom
    """
    system.name = 'argon'
    system['atoms'].append(x=0.0, y=0.0, z=0.0, symbol=['Ar'])

    return system
