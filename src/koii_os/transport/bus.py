from __future__ import annotations

import asyncio
import json
import os
from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Any, Callable
from urllib import request

try:
    from nats.aio.client import Client as NATS  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    NATS = None


class MessageBus(ABC):
    @abstractmethod
    async def publish(self, topic: str, message: dict[str, Any]) -> None:
        raise NotImplementedError

    @abstractmethod
    def subscribe(self, topic: str, handler: Callable[[dict[str, Any]], None]) -> None:
        raise NotImplementedError


class InMemoryBus(MessageBus):
    def __init__(self) -> None:
        self._handlers: dict[str, list[Callable[[dict[str, Any]], None]]] = defaultdict(list)

    async def publish(self, topic: str, message: dict[str, Any]) -> None:
        await asyncio.sleep(0)
        for handler in self._handlers.get(topic, []):
            handler(message)

    def subscribe(self, topic: str, handler: Callable[[dict[str, Any]], None]) -> None:
        self._handlers[topic].append(handler)


class HttpRelayBus(MessageBus):
    def __init__(self, relay_url: str) -> None:
        self.relay_url = relay_url.rstrip("/")
        self._handlers: dict[str, list[Callable[[dict[str, Any]], None]]] = defaultdict(list)

    async def publish(self, topic: str, message: dict[str, Any]) -> None:
        payload = {"topic": topic, "message": message}
        body = json.dumps(payload).encode("utf-8")
        req = request.Request(
            url=f"{self.relay_url}/publish",
            method="POST",
            data=body,
            headers={"Content-Type": "application/json"},
        )

        def _request() -> None:
            try:
                with request.urlopen(req, timeout=10):
                    return None
            except Exception:
                # Best-effort transport in prototype mode.
                return None

        await asyncio.to_thread(_request)

        # Also dispatch local subscribers for single-node dev mode.
        for handler in self._handlers.get(topic, []):
            handler(message)

    def subscribe(self, topic: str, handler: Callable[[dict[str, Any]], None]) -> None:
        self._handlers[topic].append(handler)


class NatsBus(MessageBus):
    def __init__(self, nats_url: str) -> None:
        self.nats_url = nats_url
        self._handlers: dict[str, list[Callable[[dict[str, Any]], None]]] = defaultdict(list)
        self._nc: Any | None = None
        self._connected = False
        self._connect_lock = asyncio.Lock()
        self._subscribed_topics: set[str] = set()

    async def _ensure_connection(self) -> None:
        if self._connected:
            return

        async with self._connect_lock:
            if self._connected:
                return
            if NATS is None:
                raise RuntimeError("NATS transport requested but nats-py is not installed")

            nc = NATS()
            await nc.connect(servers=[self.nats_url])
            self._nc = nc
            self._connected = True

            # Register all already-known topic subscriptions once connected.
            for topic in list(self._handlers.keys()):
                await self._subscribe_remote(topic)

    async def _subscribe_remote(self, topic: str) -> None:
        if not self._connected or self._nc is None:
            return
        if topic in self._subscribed_topics:
            return

        async def _callback(msg: Any) -> None:
            try:
                payload = json.loads(msg.data.decode("utf-8"))
            except Exception:
                return
            if not isinstance(payload, dict):
                return
            for handler in self._handlers.get(topic, []):
                handler(payload)

        await self._nc.subscribe(topic, cb=_callback)
        self._subscribed_topics.add(topic)

    async def publish(self, topic: str, message: dict[str, Any]) -> None:
        await self._ensure_connection()
        assert self._nc is not None
        await self._nc.publish(topic, json.dumps(message).encode("utf-8"))

        # Local dispatch keeps single-node behavior intuitive.
        for handler in self._handlers.get(topic, []):
            handler(message)

    def subscribe(self, topic: str, handler: Callable[[dict[str, Any]], None]) -> None:
        self._handlers[topic].append(handler)

        # Best effort: if loop exists and bus gets connected later, this topic will be subscribed.
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return

        async def _subscribe_when_ready() -> None:
            try:
                await self._ensure_connection()
                await self._subscribe_remote(topic)
            except Exception:
                return

        loop.create_task(_subscribe_when_ready())


def build_message_bus(cfg: dict[str, Any]) -> MessageBus:
    bus_type = os.getenv("KOII_TRANSPORT_TYPE", str(cfg.get("type", "inmemory")))
    if bus_type == "http-relay":
        relay_url = os.getenv("KOII_RELAY_URL", str(cfg.get("relay_url", "http://localhost:8080")))
        return HttpRelayBus(relay_url=relay_url)
    if bus_type == "nats":
        nats_url = os.getenv("KOII_NATS_URL", str(cfg.get("nats_url", "nats://localhost:4222")))
        return NatsBus(nats_url=nats_url)
    return InMemoryBus()
