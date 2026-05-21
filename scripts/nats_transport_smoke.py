from __future__ import annotations

import asyncio

from src.koii_os.transport.bus import NatsBus


async def main() -> None:
    bus_a = NatsBus("nats://127.0.0.1:4222")
    bus_b = NatsBus("nats://127.0.0.1:4222")

    got: list[dict[str, object]] = []
    done = asyncio.Event()

    def _handler(msg: dict[str, object]) -> None:
        got.append(msg)
        done.set()

    bus_a.subscribe("mesh.smoke", _handler)
    await asyncio.sleep(0.3)
    await bus_b.publish("mesh.smoke", {"source": "bus_b", "value": 42})

    try:
        await asyncio.wait_for(done.wait(), timeout=3.0)
    except TimeoutError:
        print("NATS_SMOKE_FAIL timeout")
        return

    print("NATS_SMOKE_OK", got[0])


if __name__ == "__main__":
    asyncio.run(main())
