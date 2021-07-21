"""Python driver for Omega iTHX and iBTHX transmitters.

Distributed under the GNU General Public License v2
Copyright (C) 2020 NuMat Technologies

"""
import argparse
import json
import logging
import sys

import asyncio

from omega_tx.driver import Barometer, Hygrometer


log = logging.getLogger(__name__)

bash_red, color_off = '\033[0;31m', '\033[0m'


def _parse_args() -> argparse.Namespace:
    """Organize the command line arguments."""
    parser = argparse.ArgumentParser(description="Read Omega transmitters.")
    parser.add_argument(
        "-d", "--debug", action="store_true", help="Verbose debug output")
    parser.add_argument(
        'type', help="Type of Omega transmitter. ibthx and ithx supported.")
    parser.add_argument(
        'address', help="The IP address of the Omega transmitter.")
    parser.add_argument(
        '-port', help="The port of the Omega transmitter (default 2000).", default=2000)
    parser.add_argument(
        '-timeout', help="Request timeout (default 2.0 s).", default=2.0)
    return parser.parse_args()


def command_line() -> int:
    """Command line tool for Omega transmitters."""
    args = _parse_args()
    logging.basicConfig(
        format="[%(asctime)s] %(levelname)s: %(message)s (%(filename)s:%(lineno)d)",
        level=logging.DEBUG if args.debug else logging.INFO)

    async def read_once():
        """Perform a single read from the transmitter."""
        try:
            async with Barometer(args.address, args.port, args.timeout) if args.type == 'ibthx' \
                    else Hygrometer(args.address, args.timeout) as tx:
                sys.stdout.write(
                    json.dumps(await tx.get(), indent=4, sort_keys=True, ensure_ascii=False))
        except asyncio.TimeoutError:
            sys.stderr.write(f'{bash_red}Could not connect to device.{color_off}\n')

    asyncio.run(read_once())
    return 0


if __name__ == '__main__':
    command_line()
