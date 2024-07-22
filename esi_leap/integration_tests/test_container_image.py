"""These tests bring up an esi-container and then run tests against the esi-leap API.

Note that the fixtures in this file are session-scoped (rather than
the default method-scoped) in avoid the cost of repeatedly
creating/deleting the container environment. This means that any tests
in this file must be avoid side effects that would impact subsequent
tests.
"""

import os
import subprocess
import requests
import pytest
import string
import random
import tempfile
import time
import docker

from pathlib import Path

esi_leap_config_template = """
[DEFAULT]

log_dir=
log_file=
transport_url=fake://

[database]
connection=mysql+pymysql://esi_leap:{mysql_user_password}@{mysql_container}/esi_leap

[oslo_messaging_notifications]
driver=messagingv2
transport_url=fake://

[oslo_concurrency]
lock_path={tmp_path}/locks

[dummy_node]
dummy_node_dir={tmp_path}/nodes

[pecan]
auth_enable=false
"""


@pytest.fixture(scope="session")
def docker_client():
    """A client for interacting with the Docker API"""
    client = docker.from_env()
    return client


@pytest.fixture(scope="session")
def tmp_path():
    """A session-scoped temporary directory that will be removed when the
    session closes."""

    with tempfile.TemporaryDirectory(prefix="pytest") as tmpdir:
        yield Path(tmpdir)


@pytest.fixture(scope="session")
def random_string():
    """A session-scoped random string that we use to generate names,
    credentials, etc. that are unique to the test session."""

    return "".join(random.sample(string.ascii_lowercase, 8))


@pytest.fixture(scope="session")
def test_network(docker_client, random_string):
    """Create a Docker network for the test (and clean it up when we're done)"""

    network_name = f"esi-leap-{random_string}"
    network = docker_client.networks.create(network_name)
    yield network_name
    network.remove()


@pytest.fixture(scope="session")
def mysql_user_password(random_string):
    """A random password for authenticating to the mysql service"""
    return f"user-{random_string}"


@pytest.fixture(scope="session")
def esi_leap_port():
    """The esi-leap service will be published on this host port."""
    return random.randint(10000, 30000)


@pytest.fixture(scope="session")
def mysql_container(docker_client, test_network, mysql_user_password, random_string):
    """Run a mysql container and wait until it is healthy. The fixture value
    is the container name."""

    container_name = f"mysql-{random_string}"
    root_password = f"root-{random_string}"
    env = {
        "MYSQL_ROOT_PASSWORD": root_password,
        "MYSQL_DATABASE": "esi_leap",
        "MYSQL_USER": "esi_leap",
        "MYSQL_PASSWORD": mysql_user_password,
    }

    # We use the healthcheck so that we can wait until mysql is ready
    # before bringing up the esi-leap container.
    healthcheck = {
        "test": [
            "CMD",
            "mysqladmin",
            "ping",
            f"-p{root_password}",
        ],
        "start_period": int(30e9),
        "interval": int(5e9),
    }

    container = docker_client.containers.run(
        "docker.io/mysql:8",
        detach=True,
        network=test_network,
        name=container_name,
        environment=env,
        healthcheck=healthcheck,
        init=True,
        labels={"pytest": None, "esi-leap-test": random_string},
    )

    for _ in range(30):
        container.reload()

        if container.health == "healthy":
            break

        time.sleep(1)
    else:
        raise OSError("failed to start mysql container")

    yield container_name

    container.remove(force=True)


@pytest.fixture(scope="session")
def esi_leap_image(random_string):
    """This will either build a new esi-leap image and return the name, or, if the
    ESI_LEAP_IMAGE environment variable is set, simply return the value of that
    variable."""

    # Note that the := operator requires python >= 3.8
    if image_name := os.getenv("ESI_LEAP_IMAGE"):
        return image_name

    image_name = f"esi-leap-{random_string}"
    subprocess.run(
        ["docker", "build", "-t", image_name, "-f", "Containerfile", "."], check=True
    )
    return image_name


@pytest.fixture(scope="session")
def esi_leap_container(
    docker_client,
    test_network,
    mysql_container,
    mysql_user_password,
    tmp_path,
    random_string,
    esi_leap_port,
    esi_leap_image,
):
    """Run the esi-leap container. Create an esi-leap configuration file from
    the template and mount it at /etc/esi-leap/esi-leap.conf in the
    container.

    The service is exposed on esi_leap_port so that we can access it from our
    tests."""

    container_name = f"esi-leap-api-{random_string}"
    config_file = tmp_path / "esi-leap.conf"
    with config_file.open("w") as fd:
        fd.write(
            esi_leap_config_template.format(
                **{
                    "tmp_path": tmp_path,
                    "mysql_container": mysql_container,
                    "mysql_user_password": mysql_user_password,
                }
            )
        )

    (tmp_path / "nodes").mkdir()
    (tmp_path / "locks").mkdir()

    container = docker_client.containers.run(
        esi_leap_image,
        detach=True,
        network=test_network,
        name=container_name,
        init=True,
        labels={"pytest": None, "esi-leap-test": random_string},
        ports={"7777/tcp": esi_leap_port},
        volumes=[f"{tmp_path}/esi-leap.conf:/etc/esi-leap/esi-leap.conf"],
    )

    for _ in range(30):
        try:
            res = requests.get(f"http://localhost:{esi_leap_port}/v1/offers")
            if res.status_code == 200:
                break
        except requests.RequestException:
            pass

        time.sleep(1)
    else:
        raise OSError("failed to start esi-leap container")

    yield container_name

    container.remove(force=True)


def test_api_list_offers(esi_leap_container, esi_leap_port):
    res = requests.get(f"http://localhost:{esi_leap_port}/v1/offers")
    assert res.status_code == 200
    assert res.json() == {"offers": []}


def test_api_list_leases(esi_leap_container, esi_leap_port):
    res = requests.get(f"http://localhost:{esi_leap_port}/v1/leases")
    assert res.status_code == 200
    assert res.json() == {"leases": []}


def test_api_list_events(esi_leap_container, esi_leap_port):
    res = requests.get(f"http://localhost:{esi_leap_port}/v1/events")
    assert res.status_code == 200
    assert res.json() == {"events": []}


@pytest.mark.xfail(reason="nodes endpoint requires keystone")
def test_api_list_nodes(esi_leap_container, esi_leap_port):
    res = requests.get(f"http://localhost:{esi_leap_port}/v1/nodes")
    assert res.status_code == 200
    assert res.json() == {"nodes": []}
