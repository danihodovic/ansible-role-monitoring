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


@pytest.mark.parametrize("container", ["prometheus", "alertmanager", "grafana"])
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
