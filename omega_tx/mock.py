"""Partial mock of iBTHX.

The purpose of this `mock` is to perform interface testing with more realistic sensor values.
"""

import asyncio
import random
import time

from omega_tx.driver import COMMANDS
from omega_tx.driver import Barometer as RealBarometer
from omega_tx.driver import Hygrometer as RealHygrometer


# average and standard deviation of readings for a little realism
units = {
    '°C': (25.0, 5.0),
    '°F': (77, 10.0),
    'mbar/hPa': (1000.0, 50.0),
    'inHg': (30.0, 2.0),
    'mmHg': (748.0, 50.0),
    '%': (36.0, 20.0)
}


class Barometer(RealBarometer):
    """Mock driver for iBTHX Omega transmitters.

    Records barometric pressure, ambient temperature, and humidity.
    """

    def __init__(self, *args, **kwargs):
        """Initialize the mock device."""
        super().__init__(*args, **kwargs)
        self.data = {}

    async def __aenter__(self):
        """Support `async with` by entering a client session."""
        return self

    async def __aexit__(self, exception_type, exception_value, traceback):
        """Support `async with` by exiting a client session."""
        pass

    async def get(self):
        """Return a mocked reading from the transmitter."""
        await asyncio.sleep(0.1)  # more realistic time delay for writing/reading
        self.data = {'Time in ms': int(time.time() * 1000)}
        for command, desc in COMMANDS.items():
            self.data[desc[0]] = round(random.gauss(*units.get(desc[0].split()[-1])), 1)
        return self.data


class Hygrometer(RealHygrometer):
    """Mock driver for iBTHX Omega transmitters.

    Records barometric pressure, ambient temperature, and humidity.
    """

    def __init__(self, *args, **kwargs):
        """Initialize the mock device."""
        super().__init__(*args, **kwargs)
        self.data = {}

    async def __aenter__(self):
        """Support `async with` by entering a client session."""
        return self

    async def __aexit__(self, exception_type, exception_value, traceback):
        """Support `async with` by exiting a client session."""
        pass

    async def get(self):
        """Return a mocked reading from the transmitter."""
        await asyncio.sleep(0.1)  # more realistic time delay for writing/reading
        self.data = {'Time in ms': int(time.time() * 1000)}
        readings = ['Temperature in °C', 'Relative Humidity in %', 'Dewpoint in °C']
        for desc in readings:
            self.data[desc] = round(random.gauss(*units.get(desc.split()[-1])), 1)
        return self.data
