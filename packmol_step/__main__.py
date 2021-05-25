# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""Handle the installation of the PACKMOL step."""

from .installer import Installer


def run():
    """Handle the extra installation needed.

    * Find and/or install the PACKMOL executables.
    * Add or update information in the SEAMM.ini file for PACKMOL
    """

    # print('The is the installer for the PACKMOL step.')
    # Create an installer object
    installer = Installer()
    installer.run()


if __name__ == "__main__":
    run()
