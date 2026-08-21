"""
    Originates the proxmox test resources into this scope.

    Replaces conftest.py, which testbase does not read.

    Only the resources that accumulate no state are originated here.
    The stateful doubles are attached to the test cases themselves, so
    each test gets a fresh instance; a scope origination is one
    instance for the whole package.
"""

from ccai import testbase

from .factories import (
    create_proxmox_token_credential,
    create_proxmox_fast_aspects,
    create_proxmox_client,
)

testbase.originate.parameter(create_proxmox_token_credential, identifier="token_credential")
testbase.originate.parameter(create_proxmox_fast_aspects, identifier="fast_aspects")
testbase.originate.parameter(create_proxmox_client, identifier="client")
