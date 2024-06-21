# -*- coding: utf-8 -*-

"""Installer for the PACKMOL plug-in.

This handles any further installation needed after installing the Python
package `packmol-step`.
"""

import logging
from pathlib import Path
import pkg_resources
import subprocess

import seamm_installer

logger = logging.getLogger(__name__)


class Installer(seamm_installer.InstallerBase):
    """Handle further installation needed after installing packmol-step.

    The Python package `packmol-step` should already be installed, using `pip`,
    `conda`, or similar. This plug-in-specific installer then checks for the
    PACKMOL executable, installing it if needed, and registers its
    location in seamm.ini.

    There are a number of ways to determine which are the correct PACKMOL
    executables to use. The aim of this installer is to help the user locate
    the executables. There are a number of possibilities

    1.  The correct executables are already available.

        1. If they are already registered in `seamm.ini` there is nothing else
           to do.
        #. They may be in the current path, in which case they need to be added
           to `seamm.ini`.
        #. If a module system is in use, a module may need to be loaded to give
           access to PACKMOL.
        #. They cannot be found automatically, so the user needs to locate the
           executables for the installer.

    #.  PACKMOL is not installed on the machine. In this case they can be
        installed in a Conda environment. There is one choice

        1. They can be installed in a separate environment, `seamm-packmol` by
           default.
    """

    def __init__(self, logger=logger):
        # Call the base class initialization, which sets up the commandline
        # parser, amongst other things.
        super().__init__(logger=logger)

        logger.debug("Initializing the PACKMOL installer object.")

        self.section = "packmol-step"
        self.executables = ["packmol"]
        self.resource_path = Path(pkg_resources.resource_filename(__name__, "data/"))

        # The environment.yaml file for Conda installations.
        logger.debug(f"data directory: {self.resource_path}")
        self.environment_file = self.resource_path / "seamm-packmol.yml"

    def check(self):
        """Check the status of the Packmol installation."""
        print("Checking the Packmol installation.")

        # What Conda environment is the default?
        path = self.configuration.path.parent / "packmol.ini"
        if not path.exists():
            text = (self.resource_path / "packmol.ini").read_text()
            path.write_text(text)
            print(f"    The packmol.ini file did not exist. Created {path}")

        self.exe_config.path = path

        # Get the current values
        data = self.exe_config.get_values("local")

        if "conda-environment" in data and data["conda-environment"] != "":
            self.environment = data["conda-environment"]
        else:
            self.environment = "seamm-packmol"

        super().check()

    def install(self):
        """Install Packmol in a conda environment."""
        print("Installing Packmol.")

        # What Conda environment is the default?
        path = self.configuration.path.parent / "packmol.ini"
        if not path.exists():
            text = (self.resource_path / "packmol.ini").read_text()
            path.write_text(text)
            print(f"    The packmol.ini file did not exist. Created {path}")

        self.exe_config.path = path

        # Get the current values
        data = self.exe_config.get_values("local")

        if "conda-environment" in data and data["conda-environment"] != "":
            self.environment = data["conda-environment"]
        else:
            self.environment = "seamm-packmol"

        super().install()

    def show(self):
        """Show the status of the Packmol installation."""
        print("Showing the Packmol installation.")

        # What Conda environment is the default?
        path = self.configuration.path.parent / "packmol.ini"
        if not path.exists():
            text = (self.resource_path / "packmol.ini").read_text()
            path.write_text(text)
            print(f"    The packmol.ini file does not exist at {path}")
            print("    The 'check' command will create it if Packmol is installed.")
            print("    Otherwise 'install' will install Packmol.")
            return

        self.exe_config.path = path

        if not self.exe_config.section_exists("local"):
            print(
                "    Packmol is not configured: there is no 'local' section in "
                f"     {path}."
            )
            return

        # Get the current values
        data = self.exe_config.get_values("local")

        if "conda-environment" in data and data["conda-environment"] != "":
            self.environment = data["conda-environment"]
        else:
            self.environment = "seamm-packmol"

        super().show()

    def uninstall(self):
        """Uninstall the Packmol installation."""
        print("Uninstall the Packmol installation.")

        # What Conda environment is the default?
        path = self.configuration.path.parent / "packmol.ini"
        if not path.exists():
            text = (self.resource_path / "packmol.ini").read_text()
            path.write_text(text)
            print(
                f""""    The packmol.ini file does not exist at {path}
    Perhaps Packmol is not installed, but if it is the 'check' command may locate it
    and create the ini file, after which 'uninstall' will remove it."""
            )
            return

        self.exe_config.path = path

        if not self.exe_config.section_exists("local"):
            print(
                f""""    The packmol.ini file at {path} does not have local section.
    Perhaps Packmol is not installed, but if it is the 'check' command may locate it
    and update the ini file, after which 'uninstall' will remove it."""
            )
            return

        # Get the current values
        data = self.exe_config.get_values("local")

        if "conda-environment" in data and data["conda-environment"] != "":
            self.environment = data["conda-environment"]
        else:
            self.environment = "seamm-packmol"

        super().uninstall()

    def update(self):
        """Updates the Packmol installation."""
        print("Updating the Packmol installation.")

        # What Conda environment is the default?
        path = self.configuration.path.parent / "packmol.ini"
        if not path.exists():
            text = (self.resource_path / "packmol.ini").read_text()
            path.write_text(text)
            print(f"    The packmol.ini file did not exist. Created {path}")

        self.exe_config.path = path

        # Get the current values
        data = self.exe_config.get_values("local")

        if "conda-environment" in data and data["conda-environment"] != "":
            self.environment = data["conda-environment"]
        else:
            self.environment = "seamm-packmol"

        super().update()

    def exe_version(self, config):
        """Get the version of the PACKMOL executable.

        Parameters
        ----------
        config : dict
            Dictionary of options for running Packmol

        Returns
        -------
        "Packmol", str
            The version reported by the executable, or 'unknown'.
        """
        environment = config["conda-environment"]
        conda = config["conda"]
        if environment[0] == "~":
            environment = str(Path(environment).expanduser())
            command = f"'{conda}' run --live-stream -p '{environment}'"
        elif Path(environment).is_absolute():
            command = f"'{conda}' run --live-stream -p '{environment}'"
        else:
            command = f"'{conda}' run --live-stream -n '{environment}'"
        command += " packmol -log none"

        logger.debug(f"    Running {command}")
        try:
            result = subprocess.run(
                command,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                shell=True,
            )
        except Exception:
            version = "unknown"
        else:
            version = "unknown"
            lines = result.stdout.splitlines()
            for line in lines:
                line = line.strip()
                tmp = line.split()
                if len(tmp) == 2:
                    key, value = tmp
                    if key == "Version":
                        version = value
                        break

        return "Packmol", version
