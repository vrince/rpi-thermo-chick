
# Always prefer setuptools over distutils
from setuptools import setup, find_packages

# read the contents of your README file
from pathlib import Path
long_description = (Path(__file__).parent / "readme.md").read_text()

setup(
    name="rpi_thermo_chick",
    version="1.2.1",
    author="Thomas Vincent",
    author_email="vrince@gmail.com",
    license="MIT",
    packages=find_packages(),
    description="Raspberry Pi - Thermostat 🔥 for chicken 🐔",
    url="https://github.com/vrince/rpi-thermo-chick",
    long_description=long_description,
    long_description_content_type='text/markdown',
    package_data={'rpi_thermo_chick': ['index.html', 'rpi-thermo-chick.service']},
    install_requires=[
        'fastapi==0.70.0',
        'uvicorn[standard]==0.15.0',
        'click==8.0.3',
        'appdirs==1.4.4',
        'influxdb-client==1.33.0'
    ],
    entry_points={
    'console_scripts': [
        'rpi-thermo-chick = rpi_thermo_chick.api:cli',
        'rpi-thermo-chick.service = rpi_thermo_chick.service:cli'
    ]
}
)