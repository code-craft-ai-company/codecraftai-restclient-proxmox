"""
    .. module:: test_properties
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Property-based tests (hypothesis) for the Proxmox VE
                   interop client — nested-URL composition, long-list
                   iteration totality, and UPID task terminal-state
                   correctness.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []


from urllib.parse import quote

import pytest

from ccai.testbase.properties import given
from ccai.testbase.properties import strategies as st

from ccai.errors.exceptions import SemanticError

from ccai.restclient.proxmox.apigroups.groupsupport import (
    API_BASE, compose_leaf
)
from ccai.restclient.proxmox.model.proxmoxtaskstatus import ProxmoxTaskStatus
from ccai.restclient.proxmox.model.proxmoxtaskhandle import ProxmoxTaskHandle


# Path segments that are non-empty and free of slash so per-segment
# encoding is observable.
_segment = st.text(
    alphabet=st.characters(blacklist_characters="/",
                           min_codepoint=33, max_codepoint=126),
    min_size=1, max_size=20,
)


@given(parts=st.lists(_segment, min_size=1, max_size=8))
def test_compose_leaf_is_deterministic_and_encoded(parts):
    """
        For any non-empty segment tuple the composed URL is deterministic,
        prefixed by the API base, and each segment is percent-encoded
        independently.
    """
    first = compose_leaf(parts=list(parts))
    second = compose_leaf(parts=list(parts))
    assert first == second
    assert first.startswith(API_BASE + "/")

    expected_tail = "/".join(quote(part, safe="") for part in parts)
    assert first == "{}/{}".format(API_BASE, expected_tail)


@given(
    constraints={"max_examples": 200},prefix=st.lists(_segment, max_size=3),
       suffix=st.lists(_segment, max_size=3))
def test_compose_leaf_rejects_empty_segment(prefix, suffix):
    """
        An empty path segment anywhere in the parts list is rejected with a
        :class:`SemanticError`.
    """
    parts = list(prefix) + [""] + list(suffix)
    with pytest.raises(SemanticError):
        compose_leaf(parts=parts)


@given(
    constraints={"max_examples": 100},prefix=st.lists(_segment, max_size=3),
       suffix=st.lists(_segment, max_size=3))
def test_compose_leaf_rejects_none_segment(prefix, suffix):
    """
        A ``None`` path segment anywhere in the parts list is rejected.
    """
    parts = list(prefix) + [None] + list(suffix)
    with pytest.raises(SemanticError):
        compose_leaf(parts=parts)


@given(count=st.integers(min_value=0, max_value=600), constraints={"max_examples": 100})
def test_list_vms_total_over_long_lists(client, requests_mock, count):
    """
        VM enumeration remains total over arbitrarily long flat lists.
    """
    from conftest import PROXMOX_BASE

    entries = []
    for index in range(count):
        entries.append({"vmid": 100 + index, "name": "vm-{}".format(index),
                        "status": "running", "template": 0})
    requests_mock.get(
        "{}/api2/json/nodes/pve1/qemu".format(PROXMOX_BASE),
        json={"data": entries},
    )

    vms = client.qemu.list_vms(node_name="pve1")
    assert len(vms) == count


@given(
    constraints={"max_examples": 40},running_polls=st.integers(min_value=0, max_value=20),
       exit_ok=st.booleans())
def test_task_handle_terminal_state(client, requests_mock, running_polls,
                                    exit_ok):
    """
        For any monotonic UPID status stream that ends in ``stopped`` the
        task handle reports the correct terminal success/failure outcome.
    """
    from conftest import PROXMOX_BASE
    from ccai.restclient.proxmox.aspectsproxmox import AspectsProxmox

    upid = "UPID:pve1:abc:task::root@pam:"
    status_url = "{}/api2/json/nodes/pve1/tasks/{}/status".format(
        PROXMOX_BASE, upid
    )

    exitstatus = "OK" if exit_ok else "task error"
    responses = []
    for _ in range(running_polls):
        responses.append({"json": {"data": {"status": "running"}}})
    responses.append({"json": {"data": {"status": "stopped",
                                        "exitstatus": exitstatus}}})
    requests_mock.get(status_url, responses)

    aspects = AspectsProxmox(completion_timeout=30.0,
                             task_poll_interval_seconds=0.0001)
    handle = ProxmoxTaskHandle(upid=upid, node_name="pve1", client=client)
    result = handle.wait(aspects=aspects, raise_on_failure=False)

    assert result.is_running is False
    assert result.is_successful is exit_ok


@given(
    constraints={"max_examples": 60},status=st.sampled_from(["running", "stopped"]),
       exitstatus=st.sampled_from(["OK", "error", None]))
def test_task_status_invariants(status, exitstatus):
    """
        :class:`ProxmoxTaskStatus` success is true only for a stopped task
        with an ``OK`` exit status.
    """
    data = {"upid": "u", "status": status}
    if exitstatus is not None:
        data["exitstatus"] = exitstatus
    task = ProxmoxTaskStatus.from_dict(data)

    expected_running = status == "running"
    assert task.is_running is expected_running

    expected_success = status == "stopped" and exitstatus == "OK"
    assert task.is_successful is expected_success
