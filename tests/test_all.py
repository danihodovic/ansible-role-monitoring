# pylint: disable=redefined-outer-name,invalid-name
import time

import pytest
import requests


@pytest.mark.parametrize(
    "container",
    ["prometheus", "alertmanager", "grafana", "blackbox", "loki", "cadvisor"],
)
def test_containers_running(container, host):
    with host.sudo():
        assert host.docker(container).is_running


def test_containers_can_ping_prometheus(host):
    with host.sudo():
        for container in ["grafana", "alertmanager"]:
            host.check_output(f"docker exec {container} nc -vz prometheus 9090")


@pytest.mark.skip(reason="needs session auth")
def test_grafana_datasource_prometheus(_host):
    # Emulate the request Grafana makes when trying to reach the Prometheus
    # source
    requests.get(
        "http://localhost:9099/api/datasources/proxy/1/api/v1/query",
        params={"query": "1+1", "time": int(time.time())},
    )


def test_grafana_stores_db_on_host_disk(host):
    assert host.file("/opt/grafana/data/grafana.sqlite3").is_file


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
def test_health_check(component, host):
    message, url = component
    res = host.ansible("uri", f"url={url}", check=False)
    assert res["status"] == 200, message
