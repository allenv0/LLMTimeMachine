"""Trip-time network guard.

Model downloads happen only in preload. During a trip this context manager
raises if anything tries to open an outbound connection through common HTTP
clients (best-effort; not a full sandbox).
"""

from __future__ import annotations

import socket
from contextlib import contextmanager

from time_machine.errors import TimeMachineError


class NetworkBlockedError(TimeMachineError):
    code = "network_blocked"


@contextmanager
def block_network(enabled: bool = True):
    if not enabled:
        yield
        return

    real_socket = socket.socket
    real_create = socket.create_connection

    def _deny(*args, **kwargs):
        raise NetworkBlockedError(
            "network access is disabled during a trip (local-v1)"
        )

    class GuardedSocket(real_socket):  # type: ignore[misc, valid-type]
        def connect(self, address):  # noqa: ANN001
            raise NetworkBlockedError(
                "network access is disabled during a trip (local-v1)"
            )

    socket.socket = GuardedSocket  # type: ignore[misc]
    socket.create_connection = _deny  # type: ignore[assignment]
    try:
        yield
    finally:
        socket.socket = real_socket  # type: ignore[misc]
        socket.create_connection = real_create  # type: ignore[assignment]
