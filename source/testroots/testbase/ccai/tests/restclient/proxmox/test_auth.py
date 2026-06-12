"""
    .. module:: test_auth
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Tests for :class:`ProxmoxClient` ticket + CSRF
                   authentication and API-token authentication.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []


import pytest

from ccai.errors.exceptions import ConfigurationError

from ccai.credentials.basiccredential import BasicCredential

from ccai.restclient.proxmox.proxmoxclient import ProxmoxClient
from ccai.restclient.proxmox.exceptions.proxmoxauthenticationerror import (
    ProxmoxAuthenticationError
)

from conftest import PROXMOX_BASE, PROXMOX_HOST


def test_api_token_auth_sets_authorization_header(client, requests_mock):
    """
        An API-token credential drives a ``PVEAPIToken`` Authorization
        header on outbound calls and skips the ticket exchange.
    """
    matcher = requests_mock.get(
        "{}/api2/json/cluster/status".format(PROXMOX_BASE),
        json={"data": [{"type": "cluster", "name": "lab", "quorate": 1}]},
    )

    client.cluster.status()

    sent_auth = matcher.last_request.headers.get("Authorization", "")
    assert sent_auth.startswith("PVEAPIToken=root@pam!automation=")


def test_construction_rejects_non_proxmox_credential():
    """
        A credential lacking the token attributes is rejected.
    """
    bad_credential = BasicCredential(
        identifier="bad", categories=["basic"],
        username="root", password="secret",
    )
    with pytest.raises(ConfigurationError):
        ProxmoxClient(credential=bad_credential, host=PROXMOX_HOST)


def test_ticket_auth_captures_ticket_and_csrf(requests_mock):
    """
        A ticket credential exchanges at ``/access/ticket`` and the captured
        CSRF token is replayed on write calls.
    """
    class _TicketCredential:
        username = "root@pam"
        password = "rootpassword"
        token_id = "root@pam!ignored"
        secret = "ignored"

    requests_mock.post(
        "{}/api2/json/access/ticket".format(PROXMOX_BASE),
        json={"data": {"ticket": "PVE:ticket-value",
                       "CSRFPreventionToken": "csrf-value"}},
    )
    write_matcher = requests_mock.post(
        "{}/api2/json/nodes/pve1/qemu/100/status/start".format(PROXMOX_BASE),
        json={"data": "UPID:pve1:start:OK"},
    )

    client = ProxmoxClient(credential=_TicketCredential(), host=PROXMOX_HOST)
    client.qemu.start_vm(node_name="pve1", vmid=100)

    assert client._ticket == "PVE:ticket-value"
    assert write_matcher.last_request.headers.get(
        "CSRFPreventionToken", "") == "csrf-value"


def test_ticket_auth_failure_raises(requests_mock):
    """
        A rejected ticket exchange raises :class:`ProxmoxAuthenticationError`.
    """
    class _TicketCredential:
        username = "root@pam"
        password = "wrong"
        token_id = "root@pam!ignored"
        secret = "ignored"

    requests_mock.post(
        "{}/api2/json/access/ticket".format(PROXMOX_BASE),
        status_code=401, text="authentication failure",
    )

    client = ProxmoxClient(credential=_TicketCredential(), host=PROXMOX_HOST)
    with pytest.raises(ProxmoxAuthenticationError):
        client.cluster.status()


def test_ticket_remint_on_expiry(requests_mock):
    """
        A stale ticket is transparently re-minted without surfacing the
        renewal to the caller.
    """
    class _TicketCredential:
        username = "root@pam"
        password = "rootpassword"
        token_id = "root@pam!ignored"
        secret = "ignored"

    ticket_matcher = requests_mock.post(
        "{}/api2/json/access/ticket".format(PROXMOX_BASE),
        json={"data": {"ticket": "PVE:ticket-1",
                       "CSRFPreventionToken": "csrf-1"}},
    )
    requests_mock.get(
        "{}/api2/json/cluster/status".format(PROXMOX_BASE),
        json={"data": []},
    )

    client = ProxmoxClient(credential=_TicketCredential(), host=PROXMOX_HOST)
    client.cluster.status()
    assert ticket_matcher.call_count == 1

    # Force the ticket to look stale; the next call re-mints transparently.
    client._ticket_minted_at = 0.0
    client.cluster.status()
    assert ticket_matcher.call_count == 2
