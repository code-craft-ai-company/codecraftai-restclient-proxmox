"""
    .. module:: conftest
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Shared fixtures for the Proxmox VE interop client tests.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Automation Mojo LLC"
__credits__ = []


import pytest

from automojo.credentials.proxmoxapitokencredential import (
    ProxmoxApiTokenCredential
)

from automojo.restclient.proxmox.aspectsproxmox import AspectsProxmox
from automojo.restclient.proxmox.proxmoxclient import ProxmoxClient


PROXMOX_HOST = "pve.example.test"
PROXMOX_BASE = "https://pve.example.test:8006"


@pytest.fixture
def token_credential() -> ProxmoxApiTokenCredential:
    """
        Build a Proxmox API-token credential for the test client.

        :returns: A :class:`ProxmoxApiTokenCredential`.
    """
    rtnval = ProxmoxApiTokenCredential(
        identifier="proxmox-test",
        categories=["vm-venue"],
        token_id="root@pam!automation",
        secret="00000000-0000-0000-0000-000000000000",
    )
    return rtnval


@pytest.fixture
def fast_aspects() -> AspectsProxmox:
    """
        Build aspects tuned for fast, deterministic test polling.

        :returns: An :class:`AspectsProxmox` with short timeouts.
    """
    rtnval = AspectsProxmox(completion_timeout=5.0,
                            task_poll_interval_seconds=0.001)
    return rtnval


@pytest.fixture
def client(token_credential, fast_aspects) -> ProxmoxClient:
    """
        Build a :class:`ProxmoxClient` bound to the test host.

        :returns: A :class:`ProxmoxClient`.
    """
    rtnval = ProxmoxClient(credential=token_credential, host=PROXMOX_HOST,
                           aspects=fast_aspects)
    return rtnval
