"""
    .. module:: test_taskhandle
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Tests for :class:`ProxmoxTaskHandle` UPID polling and
                   terminal-state behaviour.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []


from ccai import testbase


from ccai.restclient.proxmox.exceptions.proxmoxtaskfailederror import (
    ProxmoxTaskFailedError
)
from ccai.restclient.proxmox.model.proxmoxtaskhandle import ProxmoxTaskHandle

from .factories import (PROXMOX_BASE, create_proxmox_requests_mock)


_UPID = "UPID:pve1:00001234:task::root@pam:"
_STATUS_URL = "{}/api2/json/nodes/pve1/tasks/{}/status".format(
    PROXMOX_BASE, _UPID
)


@testbase.attach.parameter(create_proxmox_requests_mock, identifier="requests_mock")
def test_task_completes_successfully(client, fast_aspects, requests_mock):
    """
        A UPID task that transitions to ``stopped`` with exit status ``OK``
        completes successfully via :meth:`wait`.
    """
    requests_mock.get(_STATUS_URL, [
        {"json": {"data": {"status": "running"}}},
        {"json": {"data": {"status": "running"}}},
        {"json": {"data": {"status": "stopped", "exitstatus": "OK"}}},
    ])

    handle = ProxmoxTaskHandle(upid=_UPID, node_name="pve1", client=client)
    result = handle.wait(aspects=fast_aspects)
    assert result.is_successful is True
    assert handle.is_done() is True


@testbase.attach.parameter(create_proxmox_requests_mock, identifier="requests_mock")
def test_task_failure_raises(client, fast_aspects, requests_mock):
    """
        A UPID task that ends with a non-OK exit status raises
        :class:`ProxmoxTaskFailedError`.
    """
    requests_mock.get(_STATUS_URL, json={
        "data": {"status": "stopped", "exitstatus": "command failed"}
    })

    handle = ProxmoxTaskHandle(upid=_UPID, node_name="pve1", client=client)
    with testbase.raises(ProxmoxTaskFailedError):
        handle.wait(aspects=fast_aspects)


@testbase.attach.parameter(create_proxmox_requests_mock, identifier="requests_mock")
def test_task_timeout_raises(client, requests_mock):
    """
        A UPID task that never reaches a terminal state raises
        :class:`TimeoutError` once the completion timeout elapses.
    """
    from ccai.restclient.proxmox.aspectsproxmox import AspectsProxmox

    requests_mock.get(_STATUS_URL, json={"data": {"status": "running"}})

    short_aspects = AspectsProxmox(completion_timeout=0.05,
                                   task_poll_interval_seconds=0.01)
    handle = ProxmoxTaskHandle(upid=_UPID, node_name="pve1", client=client)
    with testbase.raises(TimeoutError):
        handle.wait(aspects=short_aspects)


def test_task_id_matches_upid(client):
    """
        The task handle reports the UPID as its task identifier.
    """
    handle = ProxmoxTaskHandle(upid=_UPID, node_name="pve1", client=client)
    assert handle.task_id() == _UPID
