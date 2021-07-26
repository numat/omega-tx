# omega-tx
<b>NOTE: This is in very early stages of development.</b>

Python ≥3.8 driver and command-line tool for Omega [ITHX](https://www.omega.com/en-us/iiot-wireless/p/ITHX-SD-Series) and [IBTHX](https://www.omega.com/en-us/iiot-wireless/p/ibtx-ibthx) transmitters.

![](https://assets.omega.com/images/communication-and-connectivity/signal-conditioners-and-transmitters/signal-conditioners/ibtx_ibthx_l.jpg)


# Installation
python3
```pip install omega-tx```

# Usage

### Command Line
```bash
omega-tx <MODEL> 192.178.6.12 --port 2000 --timeout 1.0 --unit_system metric
```
where `MODEL` is either `ibthx` or `ithx`

### Python
This driver uses Python ≥3.8's async/await syntax to asynchronously communicate with the
transmitter. For example:


```python3
import asyncio
from omega_tx import Barometer

async def read_once():
    async with Barometer('the-tx-ip-address', 'the-tx-port') as tx:
        print(await tx.get())

asyncio.run(read_once())
```

Returns:
```bash
{
    "Dewpoint in °C": 10.9,
    "Humidity in %": 35.9,
    "Pressure in mbar/hPa": 996.0,
    "Pressure in mmHg": 747.1,
    "Temperature in °C": 27.3,
}
```