#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""packmol_step
A SEAMM plug-in for building periodic boxes of fluid using Packmol
"""

import sys
from setuptools import setup, find_packages
import versioneer

short_description = __doc__.splitlines()[1]

# from https://github.com/pytest-dev/pytest-runner#conditional-requirement
needs_pytest = {'pytest', 'test', 'ptr'}.intersection(sys.argv)
pytest_runner = ['pytest-runner'] if needs_pytest else []

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

with open('requirements_install.txt') as fd:
    requirements = fd.read()

setup(
    # Descriptive entries which should always be present
    name='packmol_step',
    author="Paul Saxe",
    author_email='psaxe@molssi.org',
    description=short_description,
    long_description=readme + '\n\n' + history,
    long_description_content_type='text/x-rst',
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    license='BSD-3-Clause',
    url='https://github.com/molssi-seam/packmol_step',
    packages=find_packages(include=['packmol_step']),
    include_package_data=True,
    setup_requires=[] + pytest_runner,
    install_requires=requirements,
    test_suite='tests',
    platforms=['Linux',
               'Mac OS-X',
               'Unix',
               'Windows'],

    # Manual control if final package is compressible or not, set False to
    # prevent the .egg from being made
    zip_safe=True,

    keywords=['SEAMM', 'plug-in', 'flowchart', 'Packmol', 'fluid',
              'molecules'],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    entry_points={
        'console_scripts': [
            'packmol-step-installer=packmol_step.__main__:run',
        ],
        'org.molssi.seamm': [
            'Packmol = packmol_step:PackmolStep',
        ],
        'org.molssi.seamm.tk': [
            'Packmol = packmol_step:PackmolStep',
        ],
    }
)
