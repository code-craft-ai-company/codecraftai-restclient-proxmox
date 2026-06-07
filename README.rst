=========================================
Code Craft AI Interop - Proxmox VE
=========================================

The ``codecraftai-restclient-proxmox`` package is the venue-specific REST client for Proxmox VE,
an open-source virtualization platform combining KVM virtual machines and LXC containers
under a clustered management plane. Proxmox exposes a REST API on port 8006 with a
ticket-based session scheme; the ``PVEAuthCookie`` ticket and ``CSRFPreventionToken`` are
handled inside this client via ``RestClientBase``'s authentication hook so callers see a
uniform credential-in, calls-out shape.

Highlights
==========

- ``ProxmoxClient`` — a ``RestClientBase`` subclass handling ticket-based session auth and CSRF token management.
- Cluster and inventory enumeration — cluster and node enumeration, network (bridge/VLAN) inspection, and storage pool enumeration.
- VM and container lifecycle — create/clone/start/stop/reboot/destroy for both KVM VMs and LXC containers, plus disk and NIC management and template-based provisioning.
- Firewall and async tasks — firewall rule management and async-task tracking via the ``UPID`` returned by Proxmox for long-running operations.
- Aspects-driven transport — every behaviour-bearing call accepts ``aspects: AspectsRest = DEFAULT_PROXMOX_ASPECTS``; credentials enter as typed ``ProxmoxApiTokenCredential`` instances from ``codecraftai-credentials``.

Repository Structure
====================

- ``development/`` - Runtime environment scripts.
- ``repository-setup/`` - Repository homing and setup scripts.
- ``source/packages/ccai/restclient/proxmox/`` - Package source code.
- ``source/testroots/testbase/ccai/tests/restclient/proxmox/`` - TestBase test roots.
- ``specs/`` - Requirements, design, and task documentation (Kiro-style).
- ``userguide/`` - Standards, conventions, and documentation.

Environment Setup
=================

When working in a Codex container:

.. code-block:: bash

   ./development/setup-agent-container

For local development:

.. code-block:: bash

   ./repository-setup/rehome-repository
   ./development/setup-environment

Running Tests
=============

.. code-block:: bash

   source .venv/bin/activate
   PYTHONPATH=source/packages:source/testroots/testbase python -m pytest source/testroots -q

Standards and Conventions
=========================

- Naming conventions: ``userguide/10-02-naming-conventions.rst``
- Code organization: ``userguide/10-01-code-organization.rst``
- Coding standards: ``userguide/10-00-coding-standards.rst``

Additional Resources
====================

- User guide entry point: ``userguide/userguide.rst``
