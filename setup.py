from distutils.core import setup

import labtronyx.config.default as config
conf = config.Config()

setup(
    # Application name:
    name=conf.name,

    # Version number (initial):
    version=conf.version,

    # Application author details:
    author="Kevin Kennedy",
    author_email="kennedy.kevin@gmail.com",

    # Packages
    packages=["labtronyx"],

    # Include additional files into the package
    include_package_data=True,

    # Details
    url="",

    #
    # license="LICENSE.txt",
    description=conf.longname,

    # long_description=open("README.txt").read(),

    # Dependent packages (distributions)
    install_requires=[
        "jsonlib2",
        "visa",
        "serial",
        "numpy",
        "matplotlib",
    ],
)