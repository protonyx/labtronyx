"""
Setuptools build file
"""
__author__ = 'kkennedy'

from setuptools import setup, find_packages

import build

def build_package():
    # Generate version file
    version, full_version = build.generate_ver()

    # Setup Metadata
    setup_meta = dict(
        # Application name
        name='Labtronyx',

        # Version number
        version=full_version,

        # Application author details
        author="Kevin Kennedy",
        author_email="protonyx@users.noreply.github.com",

        # License
        license="MIT",

        # Details
        url="https://github.com/protonyx/labtronyx",

        # Description
        description='Labtronyx Instrument Control',

        # Platforms
        platforms=["Windows", "Mac OS-X", "Linux"],

        # Long Description
        long_description=open("README.rst").read(),

        # Classifiers
        classifiers=[
            "Development Status :: 3 - Alpha",
            "Intended Audience :: Developers",
            "Intended Audience :: Science/Research",
            "License :: OSI Approved :: MIT License",
            "Operating System :: Microsoft :: Windows",
            "Operating System :: POSIX :: Linux",
            "Operating System :: MacOS :: MacOS X",
            "Programming Language :: Python",
            "Programming Language :: Python :: 2.7",
            "Topic :: Software Development :: Libraries :: Python Modules",
            "Topic :: Scientific/Engineering :: Interface Engine/Protocol Translator"
        ],

        # Packages
        packages=find_packages(exclude=['tests']),

        # Package data - e.g. non-python modules
        # package_data = {},
        # Include additional files into the package
        include_package_data=True,

        # Dependencies
        install_requires=['flask', 'requests', 'pyzmq',
                          'python-dateutil',
                          'numpy', 'appdirs'],

        extras_require={
            'VISA': ['pyvisa>=1.6'],
            'Serial': ['pyserial>=2.7'],
            'gui': ['wx']
        },

        # Script entry points
        entry_points={
            'console_scripts': [
                'labtronyx = labtronyx.cli:main',
            ],
            'gui_scripts': [
                'labtronyx-gui = labtronyx.cli:launch_gui'
            ]
        },

        # Can the project run from a zip file?
        zip_safe=False
    )

    # Setuptools
    setup(**setup_meta)

if __name__ == '__main__':
    build_package()