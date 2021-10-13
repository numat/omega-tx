"""Python driver for Omega transmitters.

Distributed under the GNU General Public License v2
Copyright (C) 2020 NuMat Technologies
"""
import asyncio
import logging
import sys

import aiohttp


# for the iBTHX-W transmitter
COMMANDS = {
    'SRTC': ('Temperature in °C', 'metric'),
    'SRTF': ('Temperature in °F', 'imperial'),
    'SRHb': ('Pressure in mbar/hPa', 'metric'),
    'SRHi': ('Pressure in inHg', 'imperial'),
    'SRHm': ('Pressure in mmHg', 'metric'),
    'SRH2': ('Relative Humidity in %', 'universal'),
    'SRDF2': ('Dewpoint in °F', 'imperial'),
    'SRDC2': ('Dewpoint in °C', 'metric')}

logger = logging.getLogger(__name__)


class Barometer:
    """Driver for the iBTHX-W Omega transmitter.

    Reads barometric pressure, ambient temperature, and relative humidity.
    """

    def __init__(self, address: str, port: str = '2000', timeout: float = 2.0,
                 unit_system: str = 'metric'):
        """Initialize the device for the iBTHX-W.

        Note that this constructor does not connect. Connection happens on call:
        `tx = await Barometer().connect()` or `async with Barometer() as tx`.

        Parameters
        ----------
        address : str
            Assigned iBTHX IP address.
        port : str
            Default port is 2000.
        timeout : float
            Applied both for establishing the connection as well as reading.
        unit_system : str
            Select either metric, imperial, or all units for the sensor request.

        Methods
        -------
        get()
            Bad reads are reported as None; an empty dictionary is returned if any write/read
            fails.
        """
        self.address = address
        self.port = port
        self.reader = None
        self.writer = None
        self.timeout = timeout
        self.data = None
        self.unit_system = unit_system

    async def __aenter__(self):
        """Support `async with` by entering a client session."""
        try:
            await self.connect()
        except Exception as err:  # noqa
            await self.__aexit__(*sys.exc_info())
            logger.error(f'Connection failed at address {self.address} and port {self.port}.')
            raise err
        return self

    async def __aexit__(self, exception_type, exception_value, traceback):
        """Support `async with` by exiting a client session."""
        if self.writer is not None:
            await self.disconnect()

    async def connect(self):
        """Establish the TCP connection with asyncio.streams.

        Refer to https://docs.python.org/3/library/asyncio-stream.html.
        """
        try:
            self.reader, self.writer = await asyncio.wait_for(
                asyncio.open_connection(self.address, self.port), timeout=self.timeout)
        except ConnectionRefusedError:
            logger.error('Failed connection attempt.')

    async def disconnect(self):
        """Close the underlying socket connection, if exists."""
        if self.writer is not None:
            self.writer.close()
            self.writer = None

    async def get(self):
        """Write and read from the IBTHX sensor.

        This method should not be used for time sensitive operations. However, this sensor
        is designed for `low resolution` (> 5 minute) monitoring.

        A connection is made when the user calls this method, even when the connect() method has
        not yet been explicitly called. Users can unplug (replug) sensors without the
        logging/control script being aware. This removes the need to handle re-connects outside the
        driver but the driver user is warned that the sensor has potentially been unplugged or lost
         power somewhere along the way.
        """
        if self.writer is None:
            logger.warning('TCP connection not created before the request.')
            await self.connect()
            logger.warning('A stream writer has been defined without the user explicitly calling '
                           'connect() method. Sensor may have been unplugged at some point.')

        self.data, response = {}, None
        commands = {
            command: (desc, unit) for command, (desc, unit) in COMMANDS.items()
            if unit == self.unit_system or unit == 'universal' or self.unit_system == 'all'}
        for command, (desc, units) in commands.items():
            self.data[desc] = None  # bad read value
            self.writer.write(f'*{command}\r'.encode())
            await self.writer.drain()

            try:
                fut = await asyncio.wait_for(self.reader.read(1024), timeout=self.timeout)
                response = fut.decode()
            except asyncio.TimeoutError:
                logger.warning(f'Failed to read on command {command} response, based on timeout '
                               f'of {self.timeout} s.')
                response = 'TIMEOUT!'

            try:
                if str(response) == 'ERROR!\r':  # response from IBTHX on malformed command
                    logger.error(f'Failed read from device; exited with {response} due to '
                                 f'malformed write command.')
                else:
                    self.data[desc] = float(response)
            except (ValueError, TypeError):
                logger.warning(f'Failed read from device on command {command}; unidentified'
                               f' error with response: {response}.')
        return self.data


class Hygrometer:
    """Driver for the iTHX-W Omega transmitter.

    Reads ambient temperature and relative humidity.
    """

    def __init__(self, address: str, timeout: float = 2.0):
        """Initialize the device for the iTHX-W.

        Parameters
        ----------
        address : str
            Assigned iBTHX IP address.
        timeout : float
            Applied both for establishing the connection as well as reading.

        Methods
        -------
        get()
            Bad reads are reported as -888.88.
        """
        self.address = address
        self.data = None
        self.session = None
        self.timeout = timeout

    async def __aenter__(self):
        """Support `async with` by entering a client session."""
        try:
            await self.connect()
        except Exception as err:  # noqa
            await self.__aexit__(*sys.exc_info())
        return self

    async def __aexit__(self, exception_type, exception_value, traceback):
        """Support `async with` by exiting a client session."""
        if self.session is not None:
            await self.disconnect()

    async def connect(self):
        """Establish a connector instance for making HTTP requests."""
        self.session = aiohttp.ClientSession()

    async def disconnect(self):
        """Close the connector instance used for making HTTP requests."""
        if self.session is not None:
            await self.session.close()

    async def get(self):
        """Read and parse hygrometer (iTHX-W) data from the hosted HTML page."""
        self.data, response, text = {}, None, None
        try:
            response = await asyncio.wait_for(
                self.session.get(f'http://{self.address}/postReadHtml?a='), self.timeout)  # noqa
            assert response.status == 200
            text = await response.text()
        except aiohttp.ClientConnectorError:
            logger.error('Failed to establish HTTP connector instance.')
        except AssertionError:
            logger.error(f'Failed to read from transmitter HTML page: {response.status}')

        if text:
            try:
                temp, humid, dew = text.split('\n')[1:4]
                self.data = {
                    'Temperature in °C': float(temp.split()[2]),
                    'Relative Humidity in %': float(humid.split()[2]),
                    'Dewpoint in °C': float(dew.split()[2]),
                }
            except ValueError:
                logger.error('Failed to properly parse the HTML.')
        return self.data
