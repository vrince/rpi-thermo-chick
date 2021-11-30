
# Always prefer setuptools over distutils
from setuptools import setup, find_packages

setup(
    name="rpi_thermo_chick",
    version="1.0.14",
    author="Thomas Vincent",
    author_email="vrince@gmail.com",
    license="MIT",
    packages=find_packages(),
    description="Raspbery Pi - Thermostat 🔥 for chicken 🐔",
    package_data={'rpi_thermo_chick': ['index.html', 'rpi-thermo-chick.service']},
    install_requires=[
        'fastapi',
        'uvicorn[standard]',
        'click',
        'appdirs'
    ],
    entry_points={
    'console_scripts': [
        'rpi-thermo-chick = rpi_thermo_chick.api:cli',
        'rpi-thermo-chick.service = rpi_thermo_chick.service:cli'
    ]
}
)