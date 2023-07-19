from setuptools import setup

from thermalnetwork import VERSION

short_description = """A thermal network solver for GHE sizing."""

setup(
    name='ThermalNetwork',
    url='https://github.com/mitchute/ThermalNetwork',
    description=short_description,
    license='BSD-3',
    version=VERSION,
    packages=['thermalnetwork'],
    author='Matt Mitchell',
    author_email='mitchute@gmail.com',
    classifiers=[
        'Topic :: Scientific/Engineering',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10'
        'Programming Language :: Python :: 3.11'
    ],
    install_requires=[
        'click>=8.1.6',
        'ghedesigner>=1.1'
    ],
    entry_points={
        'console_scripts': ['thermalnetwork=thermalnetwork.network.run_sizer_from_cli']
    }
)
