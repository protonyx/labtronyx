from distutils.core import setup

setup(
    # Application name:
    name="Animus Framework",

    # Version number (initial):
    version="dev",

    # Application author details:
    author="Kevin Kennedy",
    author_email="kennedy.kevin@gmail.com",

    # Packages
    packages=["application", "common", "manager", "config"],

    # Include additional files into the package
    include_package_data=True,

    # Details
    url="",

    #
    # license="LICENSE.txt",
    description="Instrumentation Control and Automation Framework",

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