# -*- coding: utf-8 -*-

"""Installer for the PACKMOL plug-in.

This handles any further installation needed after installing the Python
package `packmol-step`.
"""

import logging
import pkg_resources
from pathlib import Path
import shutil
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
    the executables. There are a number of possibilities:

    1. The correct executables are already available.

        1. If they are already registered in `seamm.ini` there is nothing else
           to do.
        2. They may be in the current path, in which case they need to be added
           to `seamm.ini`.
        3. If a module system is in use, a module may need to be loaded to give
           access to PACKMOL.
        3. They cannot be found automatically, so the user needs to locate the
           executables for the installer.

    2. PACKMOL is not installed on the machine. In this case they can be
       installed in a Conda environment. There is one choice:

        1. They can be installed in a separate environment, `seamm-packmol` by
           default.
    """

    def __init__(self, logger=logger):
        # Call the base class initialization, which sets up the commandline
        # parser, amongst other things.
        super().__init__(logger=logger)

        logger.debug('Initializing the PACKMOL installer object.')

        self.executables = ['packmol']
        # What Conda environment is the default?
        data = self.configuration.get_values('packmol-step')
        if 'conda-environment' in data and data['conda-environment'] != '':
            self.environment = data['conda-environment']
        else:
            self.environment = 'seamm-packmol'

        # The environment.yaml file for Conda installations.
        path = Path(pkg_resources.resource_filename(__name__, 'data/'))
        logger.debug(f"data directory: {path}")
        self.environment_file = path / 'seamm-packmol.yml'

    def check(self):
        """Check the installation and fix errors if requested.

        If the option `yes` is present and True, this method will attempt to
        correct any errors in the configuration file. Use `--yes` on the
        command line to enable this.

        The information in the configuration file is:

            installation
                How PACKMOL is installed. One of `user`, `modules` or `conda`
            conda-environment
                The Conda environment if and only if `installation` = `conda`
            modules
                The environment modules if `installation` = `modules`
            packmol-path
                The path where the PACKMOL executables are. Automatically
                defined if `installation` is `conda` or `modules`, but given
                by the user is it is `user`.

        Returns
        -------
        bool
            True if everything is OK, False otherwise. If `yes` is given as an
            option, the return value is after fixing the configuration.
        """
        self.logger.debug('Entering check method.')
        if not self.configuration.section_exists('packmol-step'):
            if self.options.yes or self.ask_yes_no(
                "There is no section for the PACKMOL step in the configuration "
                f" file ({self.configuration.path}).\nAdd one?",
                default='yes'
            ):
                self.check_configuration_file()
                print("Added the 'packmol-step' section")

        # Get the values from the configuration
        data = self.configuration.get_values('packmol-step')

        # Save the initial values, if any, of the key configuration variables
        if 'packmol-path' in data and data['packmol-path'] != '':
            path = Path(data['packmol-path']).expanduser().resolve()
            initial_packmol_path = path
        else:
            initial_packmol_path = None
        if 'installation' in data and data['installation'] != '':
            initial_installation = data['installation']
        else:
            initial_installation = None
        if 'conda-environment' in data and data['conda-environment'] != '':
            initial_conda_environment = data['conda-environment']
        else:
            initial_conda_environment = None
        if 'modules' in data and data['modules'] != '':
            initial_modules = data['modules']
        else:
            initial_modules = None

        # Is there a valid packmol-path?
        self.logger.debug(
            "Checking for THEexecutable in the initial packmol-path "
            f"{initial_packmol_path}."
        )
        if (
            initial_packmol_path is None or
            not self.have_executables(initial_packmol_path)
        ):
            packmol_path = None
        else:
            packmol_path = initial_packmol_path
        self.logger.debug(f"initial-packmol-path = {initial_packmol_path}.")

        # Is there an installation indicated?
        if initial_installation in ('user', 'conda', 'modules'):
            installation = initial_installation
        else:
            installation = None
        self.logger.debug(f"initial-installation = {initial_installation}.")

        if installation == 'conda':
            # Is there a conda environment?
            conda_environment = None
            if (
                initial_conda_environment is None or
                not self.conda.exists(initial_conda_environment)
            ):
                if packmol_path is not None:
                    # see if this path corresponds to a Conda environment
                    for tmp in self.conda.environments:
                        tmp_path = self.conda.path(tmp) / 'bin'
                        if tmp_path == packmol_path:
                            conda_environment = tmp
                            break
                    if conda_environment is not None:
                        if self.options.yes or self.ask_yes_no(
                            "The Conda environment in the config file "
                            "is not correct.\n"
                            f"It should be {conda_environment}. Fix?",
                            default='yes'
                        ):
                            self.configuration.set_value(
                                'packmol-step', 'installation', 'conda'
                            )
                            self.configuration.set_value(
                                'packmol-step', 'conda-environment',
                                conda_environment
                            )
                            self.configuration.set_value(
                                'packmol-step', 'modules', ''
                            )
                            self.configuration.save()
                            print(
                                "Corrected the conda environment to "
                                f"{conda_environment}"
                            )
            else:
                # Have a Conda environment!
                conda_path = self.conda.path(initial_conda_environment) / 'bin'
                self.logger.debug(
                    f"Checking for executable in conda-path: {conda_path}."
                )
                if self.have_executables(conda_path):
                    # All is good!
                    conda_environment = initial_conda_environment
                    if packmol_path is None:
                        if self.options.yes or self.ask_yes_no(
                            "The packmol-path in the config file is not set,"
                            f"but the Conda environment {conda_environment} "
                            "is.\nFix the packmol-path?",
                            default='yes'
                        ):
                            packmol_path = conda_path
                            self.configuration.set_value(
                                'packmol-step', 'packmol-path', packmol_path
                            )
                            self.configuration.set_value(
                                'packmol-step', 'modules', ''
                            )
                            self.configuration.save()
                            print(f"Set the packmol-path to {conda_path}")
                    elif packmol_path != conda_path:
                        if self.options.yes or self.ask_yes_no(
                            f"The packmol-path in the config file {packmol_path}"
                            "is different from that for  the Conda "
                            f"environment {conda_environment} is.\n"
                            "Use the path from the Conda environment?",
                            default='yes'
                        ):
                            packmol_path = conda_path
                            self.configuration.set_value(
                                'packmol-step', 'packmol-path', packmol_path
                            )
                            self.configuration.set_value(
                                'packmol-step', 'modules', ''
                            )
                            self.configuration.save()
                            print(f"Changed the packmol-path to {conda_path}")
                    else:
                        # Everything is fine!
                        pass
        if installation == 'modules':
            print(f"Can't check the actual modules {initial_modules} yet")
            if initial_conda_environment is not None:
                if self.options.yes or self.ask_yes_no(
                    "A Conda environment is given: "
                    f"{initial_conda_environment}.\n"
                    "A Conda environment should not be used when using "
                    "modules. Remove it from the configuration?",
                    default='yes'
                ):
                    self.configuration.set_value(
                        'packmol-step', 'conda-environment', ''
                    )
                    self.configuration.save()
                    print(
                        "Using modules, so removed the conda-environment from "
                        "the configuration"
                    )
        else:
            if packmol_path is None:
                # No path or executable in the path!
                environments = self.conda.environments
                if self.environment in environments:
                    # Make sure it is first!
                    environments.remove(self.environment)
                    environments.insert(0, self.environment)
                for tmp in environments:
                    tmp_path = self.conda.path(tmp) / 'bin'
                    if self.have_executables(tmp_path):
                        if self.options.yes or self.ask_yes_no(
                            "There are no valid executable in the packmol-path"
                            " in the config file, but there are in the Conda "
                            f"environment {tmp}.\n"
                            "Use them?",
                            default='yes'
                        ):
                            conda_environment = tmp
                            packmol_path = tmp_path
                            self.configuration.set_value(
                                'packmol-step', 'packmol-path', packmol_path
                            )
                            self.configuration.set_value(
                                'packmol-step', 'installation', 'conda'
                            )
                            self.configuration.set_value(
                                'packmol-step', 'conda-environment',
                                conda_environment
                            )
                            self.configuration.set_value(
                                'packmol-step', 'modules', ''
                            )
                            self.configuration.save()
                            print(
                                "Will use the conda environment "
                                f"'{conda_environment}'"
                            )
                            break
            if packmol_path is None:
                # Haven't found it. Check in the path.
                packmol_path = self.executables_in_path()
                if packmol_path is not None:
                    if self.options.yes or self.ask_yes_no(
                        "Found PACKMOL executable in the PATH at "
                        f"{packmol_path}\n"
                        "Use them?",
                        default='yes'
                    ):
                        self.configuration.set_value(
                            'packmol-step', 'installation', 'user'
                        )
                        self.configuration.set_value(
                            'packmol-step', 'conda-environment', ''
                        )
                        self.configuration.set_value(
                            'packmol-step', 'modules', ''
                        )
                        self.configuration.save()
                        print("Using the PACKMOL executable at {packmol_path}")

            if packmol_path is None:
                # Can't find PACKMOL
                print(
                    "Cannot find PACKMOL executable. You will need to install "
                    "them."
                )
                if (
                    initial_installation is not None and
                    initial_installation != 'not installed'
                ):
                    if self.options.yes or self.ask_yes_no(
                        "The configuration file indicates that PACKMOL "
                        "is installed, but it can't be found.\n"
                        "Fix the configuration file?",
                        default='yes'
                    ):
                        self.configuration.set_value(
                            'packmol-step', 'installation', 'not installed'
                        )
                        self.configuration.set_value(
                            'packmol-step', 'packmol-path', ''
                        )
                        self.configuration.set_value(
                            'packmol-step', 'conda-environment', ''
                        )
                        self.configuration.set_value(
                            'packmol-step', 'modules', ''
                        )
                        self.configuration.save()
                        print(
                            "Since no PACKMOL executable were found, cleared "
                            "the configuration."
                        )
            else:
                print('The check completed successfully.')

    def check_configuration_file(self):
        """Checks that the packmol-step section is in the configuration file.
        """
        if not self.configuration.section_exists('packmol-step'):
            # Get the text of the data
            path = Path(pkg_resources.resource_filename(__name__, 'data/'))
            path = path / 'configuration.txt'
            text = path.read_text()

            # Add it to the configuration file and write to disk.
            self.configuration.add_section('packmol-step', text)
            self.configuration.save()

    def have_executables(self, path):
        """Check whether the executables are found at the given path.

        Parameters
        ----------
        path : pathlib.Path
            The directory to check.

        Returns
        -------
        bool
            True if at least one of the PACKMOL executables is found.
        """
        for executables in self.executables:
            tmp_path = path / executables
            if tmp_path.exists():
                self.logger.debug(f"Found executables in {path}")
                return True
        self.logger.debug(f"Did not find executables in {path}")
        return False

    def executables_in_path(self):
        """Check whether the executables are found in the PATH.

        Returns
        -------
        pathlib.Path
            The path where the executables are, or None.
        """
        path = None
        for executables in self.executables:
            path = shutil.which(executables)
            if path is not None:
                path = Path(path).expanduser().resolve()
                break
        return path

    def install(self):
        """Install PACKMOL using a Conda environment."""
        print(
            f"Installing Conda environment '{self.environment}'. This "
            "may take a minute or two."
        )
        self.conda.create_environment(
            self.environment_file, name=self.environment
        )
        # Update the configuration file.
        self.check_configuration_file()
        path = self.conda.path(self.environment) / 'bin'
        self.configuration.set_value('packmol-step', 'packmol-path', str(path))
        self.configuration.set_value('packmol-step', 'installation', 'conda')
        self.configuration.set_value(
            'packmol-step', 'conda-environment', self.environment
        )
        self.configuration.set_value('packmol-step', 'modules', '')
        self.configuration.save()
        print('Done!\n')

    def show(self):
        """Show the current installation status."""
        self.logger.debug('Entering show')

        # See if PACKMOL is already registered in the configuration file
        if not self.configuration.section_exists('packmol-step'):
            print(
                "There is no section in the configuration file for the "
                "PACKMOL step (packmol-step)."
            )
        data = self.configuration.get_values('packmol-step')

        # Keep track of where executables are
        serial = None

        # Is the path in the configuration file?
        if 'packmol-path' in data:
            conf_path = Path(data['packmol-path']).expanduser().resolve()
            if (conf_path / 'packmol').exists():
                serial = conf_path / 'packmol'
                serial_version = self.packmol_version(serial)

            extra = f"from path {conf_path}."
            if 'installation' in data:
                installation = data['installation']
                if installation == 'conda':
                    if (
                        'conda-environment' in data and
                        data['conda-environment'] != ''
                    ):
                        extra = (
                            "from Conda environment "
                            f"{data['conda-environment']}."
                        )
                    else:
                        extra = "from an unknown Conda environment."
                elif installation == 'modules':
                    if 'modules' in data and data['modules'] != '':
                        extra = f"from module(s) {data['modules']}."
                    else:
                        extra = "from unknown modules."
                elif installation == 'user':
                    extra = f"from user-defined path {conf_path}."

            if serial is not None:
                print(f"PACKMOL executable, version {serial_version}")
                print(extra)
            else:
                print("PACKMOL is not configured to run.")
        else:
            print("PACKMOL is not configured to run.")

        # Look in the PATH, but only record if not same as in the conf file
        tmp = shutil.which('packmol')
        if tmp is not None:
            tmp = Path(tmp).expanduser().resolve()
            if serial is not None and serial != tmp:
                version = self.packmol_version(tmp)
                print(
                    f"Another executable of PACKMOL (version {version}) "
                    "is in the PATH:\n"
                    f"    {tmp}"
                )

    def uninstall(self):
        """Uninstall the PACKMOL Conda environment."""
        # See if PACKMOL is already registered in the configuration file
        data = self.configuration.get_values('packmol-step')
        if 'installation' in data and data['installation'] == 'conda':
            environment = self.environment
            if 'conda-environment' in data and data['conda-environment'] != '':
                environment = data['conda-environment']
            print(
                f"Uninstalling Conda environment '{environment}'. This "
                "may take a minute or two."
            )
            self.conda.remove_environment(environment)
            # Update the configuration file.
            self.configuration.set_value('packmol-step', 'packmol-path', '')
            self.configuration.set_value('packmol-step', 'modules', '')
            self.configuration.set_value(
                'packmol-step', 'installation', 'not installed'
            )
            self.configuration.set_value(
                'packmol-step', 'conda-environment', ''
            )
            self.configuration.save()
            print('Done!\n')

    def update(self):
        """Update the installation, if possible."""
        # See if PACKMOL is already registered in the configuration file
        data = self.configuration.get_values('packmol-step')
        if 'installation' in data and data['installation'] == 'conda':
            environment = self.environment
            if 'conda-environment' in data and data['conda-environment'] != '':
                environment = data['conda-environment']
            print(
                f"Updating Conda environment '{environment}'. This may "
                "take a minute or two."
            )
            self.conda.update_environment(
                self.environment_file, name=environment
            )
            # Update the configuration file, just in case.
            path = self.conda.path(environment) / 'bin'
            self.configuration.set_value(
                'packmol-step', 'packmol-path', str(path)
            )
            self.configuration.set_value(
                'packmol-step', 'installation', 'conda'
            )
            self.configuration.set_value(
                'packmol-step', 'conda-environment', environment
            )
            self.configuration.set_value('packmol-step', 'modules', '')
            self.configuration.save()
            print('Done!\n')
        else:
            print(
                "Unable to update PACKMOL because it was not installed using "
                "Conda"
            )

    def packmol_version(self, path):
        """Get the version of the PACKMOL executable.

        Parameters
        ----------
        path : pathlib.Path
            Path to the executable.

        Returns
        -------
        str
            The version reported by PACKMOL, or 'unknown'.
        """
        try:
            result = subprocess.run(
                [str(path), '-log', 'none'],
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True
            )
        except Exception:
            version = 'unknown'
        else:
            version = 'unknown'
            lines = result.stdout.splitlines()
            for line in lines:
                line = line.strip()
                tmp = line.split()
                if len(tmp) == 2:
                    key, value = tmp
                    if key == 'Version':
                        version = value
                        break

        return version
