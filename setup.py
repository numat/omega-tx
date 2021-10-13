"""Package manager setup for the omega transmitter driver."""
from setuptools import setup

with open('README.md', 'r') as in_file:
    long_description = in_file.read()

setup(
    name='omega-tx',
    version='0.2.0',
    description='Python driver for Omega iTHX-W and iBTHX-W transmitters.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/numat/omega-tx/',
    author='Ross Verploegh, PhD',
    author_email='ross@numat-tech.com',
    packages=['omega_tx'],
    install_requires=[
        'aiohttp>=3.7.2'
    ],
    entry_points={
        'console_scripts': [
            'omega-tx = omega_tx:command_line',
        ],
    },
    license='GPLv2',
    classifiers=[
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
        'Development Status :: 2 - Pre-Alpha',
        'Natural Language :: English',
        'Programming Language :: Python',
        'Topic :: Scientific/Engineering :: Human Machine Interfaces'
    ]
)
