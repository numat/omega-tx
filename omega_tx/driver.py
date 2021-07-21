"""Python driver for Omega transmitters.

Distributed under the GNU General Public License v2
Copyright (C) 2020 NuMat Technologies
"""
import aiohttp
import asyncio
import logging
import sys
import time


# for the iBTHX-W transmitter
COMMANDS = {
    'SRTC': 'Temperature in °C',
    'SRTF': 'Temperature in °F',
    'SRHb': 'Pressure in mbar/hPa',
    'SRHi': 'Pressure in inHg',
    'SRHm': 'Pressure in mmHg',
    'SRH2': 'Relative Humidity in %',
    'SRDF2': 'Dewpoint in °F',
    'SRDC2': 'Dewpoint in °C'}

logger = logging.getLogger(__name__)


class Barometer:
    """Driver for the iBTHX-W Omega transmitter.

    Reads barometric pressure, ambient temperature, and relative humidity.
    """
    def __init__(self, address: str, port: str = 2000, timeout: float = 2.0):
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
            self.writer = None

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

    async def get(self):
        """Write and read from the IBTHX sensor.

        This method should not be used for time sensitive operations. However, this sensor
        is designed for `low resolution` (> 5 minute) monitoring.
        """
        if self.writer is None:
            logger.error('TCP connection not created before the request.')
            raise Exception('No stream writer has been defined.')

        self.data, response = {'Time in ms': int(time.time() * 1000)}, None
        for command, desc in COMMANDS.items():
            self.writer.write(f'*{command}\r'.encode())
            await self.writer.drain()

            try:
                fut = await asyncio.wait_for(self.reader.read(1024), timeout=self.timeout)
                response = fut.decode()
            except asyncio.TimeoutError:
                logger.warning(f'Failed to read based on timeout of {self.timeout} s.')

            try:
                if str(response) == 'ERROR!\r':  # response from IBTHX on malformed command
                    logger.error(f'Failed read from device; exited with {str(response)}.')
                else:
                    self.data[desc] = float(response)
            except ValueError:
                logger.warning(f'Failed read from device; unidentified error with response:'
                               f' {(str(response))}.')

            if not self.data.get(desc):
                self.data[desc] = None  # bad read value
        return self.data if any(self.data.values()) is not None else {}


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
                    'Time in ms': int(time.time() * 1000),
                    'Temperature in °C': float(temp.split()[2]),
                    'Relative Humidity in %': float(humid.split()[2]),
                    'Dewpoint in °C': float(dew.split()[2]),
                }
            except ValueError:
                logger.error('Failed to properly parse the HTML.')
        return self.data
