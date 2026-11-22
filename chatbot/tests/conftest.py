"""Shared fixtures. Memory tests run against a REAL redis-server when one is installed (so WATCH,
TTL and JSON behave exactly as in production), and fall back to fakeredis when it is not."""
import shutil
import socket
import subprocess
import time

import pytest
import redis


def _free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@pytest.fixture(scope="session")
def redis_backend():
    binary = shutil.which("redis-server")
    if binary is None:
        import fakeredis

        yield "fakeredis", fakeredis.FakeRedis(decode_responses=True)
        return
    port = _free_port()
    process = subprocess.Popen(
        [binary, "--port", str(port), "--bind", "127.0.0.1", "--save", "", "--appendonly", "no"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    client = redis.Redis(port=port, decode_responses=True)
    for _ in range(50):
        try:
            client.ping()
            break
        except redis.ConnectionError:
            time.sleep(0.1)
    else:
        process.terminate()
        pytest.fail("redis-server did not start")
    yield "redis-server", client
    process.terminate()
    process.wait(timeout=5)


@pytest.fixture
def redis_client(redis_backend):
    _, client = redis_backend
    client.flushall()
    return client
