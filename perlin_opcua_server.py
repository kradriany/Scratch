from __future__ import annotations

"""OPC UA server that exposes Perlin noise values and simple HTTP page.

The server updates a variable with an integer Perlin noise value every
second (1 Hz). A very small HTTP server is also started on port 8000
that shows the most recent noise value. External dependencies:

- ``python-opcua``

Run this script with Python 3. Once started you can:
1. Connect with an OPC UA client to ``opc.tcp://0.0.0.0:4840/`` and read
   the ``NoiseValue`` variable.
2. Open ``http://localhost:8000`` in a browser to see the latest value.
"""

import asyncio
import random
import time
from typing import Callable

from opcua import ua, Server  # type: ignore


class PerlinNoiseGenerator:
    """Generate 1‑D Perlin noise values over time without external libs."""

    def __init__(
        self, scale: float = 1.0, amplitude: float = 100.0, seed: int | None = None
    ) -> None:
        self.scale = scale
        self.amplitude = amplitude
        self.start_time = time.time()

        rng = random.Random(seed)
        p = list(range(256))
        rng.shuffle(p)
        self.permutation = p * 2

    @staticmethod
    def _fade(t: float) -> float:
        return t * t * t * (t * (t * 6 - 15) + 10)

    @staticmethod
    def _lerp(a: float, b: float, t: float) -> float:
        return a + t * (b - a)

    @staticmethod
    def _grad(hash_: int, x: float) -> float:
        g = hash_ & 15
        grad = 1 + (g & 7)
        if g & 8:
            grad = -grad
        return grad * x

    def _noise(self, x: float) -> float:
        xi = int(x) & 255
        xf = x - int(x)
        u = self._fade(xf)
        a = self.permutation[xi]
        b = self.permutation[xi + 1]
        return self._lerp(self._grad(a, xf), self._grad(b, xf - 1), u)

    def __call__(self) -> int:
        t = (time.time() - self.start_time) * self.scale
        value = self._noise(t)
        return int(value * self.amplitude)


def setup_server() -> tuple[Server, ua.Node]:
    """Create and configure the OPC UA server and variable."""
    server = Server()
    server.set_endpoint("opc.tcp://0.0.0.0:4840/")

    idx = server.register_namespace("PerlinOPCUA")
    objects = server.get_objects_node()
    noise_obj = objects.add_object(idx, "Noise")
    noise_var = noise_obj.add_variable(idx, "NoiseValue", 0, ua.VariantType.Int32)
    noise_var.set_writable(False)

    return server, noise_var


LATEST_VALUE: int = 0


async def handle_http(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    """Return the latest noise value as a plain text HTTP response."""
    global LATEST_VALUE

    # Read and discard the HTTP request (headers end with a blank line)
    while True:
        line = await reader.readline()
        if not line or line == b"\r\n":
            break

    body = f"Latest noise value: {LATEST_VALUE}\n"
    header = (
        "HTTP/1.1 200 OK\r\n"
        f"Content-Length: {len(body)}\r\n"
        "Content-Type: text/plain; charset=utf-8\r\n"
        "Connection: close\r\n\r\n"
    )
    writer.write(header.encode("ascii") + body.encode("ascii"))
    await writer.drain()
    writer.close()
    await writer.wait_closed()


async def _start_http_server() -> asyncio.AbstractServer:
    server = await asyncio.start_server(handle_http, "0.0.0.0", 8000)
    return server


async def main(update_func: Callable[[], int], frequency_hz: float = 1.0) -> None:
    global LATEST_VALUE
    server, noise_var = setup_server()
    http_server = await _start_http_server()
    async with server, http_server:
        while True:
            value = update_func()
            LATEST_VALUE = value
            noise_var.set_value(value)
            await asyncio.sleep(1.0 / frequency_hz)


if __name__ == "__main__":
    generator = PerlinNoiseGenerator(scale=0.1, amplitude=100)
    asyncio.run(main(generator))
