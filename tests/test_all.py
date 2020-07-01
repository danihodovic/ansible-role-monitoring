# pylint: disable=redefined-outer-name,invalid-name
import time

import pytest
import requests
import testinfra


@pytest.fixture
def docker_host(host):
    def fn(container_name):
        container = host.docker(container_name)
        assert container.is_running
        return testinfra.get_host(f"docker://{container.id}")

    return fn


@pytest.mark.parametrize(
    "container", ["prometheus", "alertmanager", "grafana", "blackbox", "loki"]
)
def test_containers_running(container, host):
    assert host.docker(container).is_running


def test_containers_can_ping_prometheus(docker_host):
    cmd = "nc -vz prometheus 9090"
    docker_host("grafana").run_test(cmd)
    docker_host("alertmanager").run_test(cmd)


@pytest.mark.skip(reason="needs session auth")
def test_grafana_datasource_prometheus(_host):
    # Emulate the request Grafana makes when trying to reach the Prometheus
    # source
    requests.get(
        "http://localhost:9099/api/datasources/proxy/1/api/v1/query",
        params={"query": "1+1", "time": int(time.time())},
    )


def test_grafana_stores_db_on_host_disk(host):
    assert host.file("/tmp/grafana/data/grafana.sqlite3").is_file


@pytest.mark.parametrize(
    "component",
    [
        ("prometheus", "http://localhost:9090/-/healthy"),
        ("alertmanager", "http://localhost:9093/-/ready"),
        ("grafana", "http://localhost:9099/api/health"),
        ("blackbox", "http://localhost:9115"),
        ("loki", "http://localhost:9098/ready"),
    ],
)
def test_health_check(component):
    message, url = component
    res = requests.get(url)
    assert res.status_code == 200, message


# TODO: Test grafana datasources
# https://grafana.com/docs/grafana/latest/http_api/data_source/
