"""
    .. module:: factories
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Shared fixtures for the Proxmox VE interop client tests.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []


from collections.abc import Generator

import requests_mock as requests_mock_module

from ccai import testbase

from ccai.credentials.proxmoxapitokencredential import (
    ProxmoxApiTokenCredential
)

from ccai.restclient.proxmox.aspectsproxmox import AspectsProxmox
from ccai.restclient.proxmox.proxmoxclient import ProxmoxClient


PROXMOX_HOST = "pve.example.test"
PROXMOX_BASE = "https://pve.example.test:8006"

@testbase.register.resource_factory()
def create_proxmox_token_credential(constraints=None) -> Generator[ProxmoxApiTokenCredential, None, None]:
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
    yield rtnval


@testbase.register.resource_factory()
def create_proxmox_fast_aspects(constraints=None) -> Generator[AspectsProxmox, None, None]:
    """
        Build aspects tuned for fast, deterministic test polling.

        :returns: An :class:`AspectsProxmox` with short timeouts.
    """
    rtnval = AspectsProxmox(completion_timeout=5.0,
                            task_poll_interval_seconds=0.001)
    yield rtnval


@testbase.register.resource_factory()
def create_proxmox_client(token_credential, fast_aspects, constraints=None) -> Generator[ProxmoxClient, None, None]:
    """
        Build a :class:`ProxmoxClient` bound to the test host.

        :returns: A :class:`ProxmoxClient`.
    """
    rtnval = ProxmoxClient(credential=token_credential, host=PROXMOX_HOST,
                           aspects=fast_aspects)
    yield rtnval


@testbase.register.resource_factory()
def create_proxmox_requests_mock(
        constraints=None) -> Generator[requests_mock_module.Mocker, None, None]:
    """
        Yield an active ``requests_mock`` Mocker for one test.

        Stands in for the ``requests_mock`` pytest plugin fixture, which
        testbase cannot supply.

        Attached per test rather than originated in this scope: a Mocker
        accumulates the URIs registered against it, so a shared one would let
        one test's registrations answer another test's requests.

        :param constraints: Optional constraint dictionary.

        :returns: A generator yielding an active Mocker, deactivated afterwards.
    """
    with requests_mock_module.Mocker() as mocker:
        yield mocker
