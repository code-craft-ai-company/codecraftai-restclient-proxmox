# Design

## Overview

`ProxmoxClient` is a `RestClientBase` subclass for the Proxmox VE API on
port 8006. Authentication is ticket + CSRF token, mounted on the session
via the `_authenticate` hook. URL paths are deeply nested under
`/api2/json/nodes/<node>/...` and async ops return a UPID — both modelled
as first-class concerns in the client.

---

## Architecture

```
┌────────────────────────────────────────────────────────┐
│  automojo-provisioning / venues / proxmox              │
└──────────┬─────────────────────────────────────────────┘
           │
           ▼
┌────────────────────────────────────────────────────────┐
│  ProxmoxClient                                         │
│   RestClientBase + AspectsRest                         │
│   ticket+CSRF auth, UPID task handles                  │
│   API groups: cluster, nodes, qemu, lxc, storage,      │
│     network, firewall, tasks                           │
└──────────┬─────────────────────────────────────────────┘
           │ HTTPS :8006 ; PVEAuthCookie + CSRFPreventionToken
           ▼
┌────────────────────────────────────────────────────────┐
│  Proxmox VE node / cluster                             │
└────────────────────────────────────────────────────────┘
```

---

## Data Model

`model/`: `proxmoxclusterstatus.py`, `proxmoxnode.py`,
`proxmoxnetworkinterface.py`, `proxmoxstorage.py`, `proxmoxvmstatus.py`,
`proxmoxcontainerstatus.py`, `proxmoxtaskstatus.py`,
`proxmoxfirewallrule.py`, `proxmoxtaskhandle.py`.

`specs/`: `proxmoxvmcreatespec.py`, `proxmoxvmclonespec.py`,
`proxmoxdiskspec.py`, `proxmoxnicspec.py`, `proxmoxcontainercreatespec.py`,
`proxmoxfirewallrulespec.py`.

Exceptions: `ProxmoxAuthenticationError`, `ProxmoxTaskFailedError`.

---

## Module Layout

```
source/packages/automojo/interop/proxmox/
├── proxmoxclient.py
├── aspectsproxmox.py
├── apigroups/{clustergroup, nodesgroup, qemugroup, lxcgroup,
│              storagegroup, networkgroup, firewallgroup, tasksgroup}.py
├── model/
├── specs/
└── exceptions/
```

---

## See Also

- `automojo-restclient-base/specs/restapigroup-enhancements/`
- `automojo-provisioning/specs/venue-proxmox/`
- `automojo-credentials/specs/proxmox-credentials/`

---

## Testing Strategy

Example-based tests cover ticket+CSRF auth, ticket re-mint on expiry,
VM clone-from-template flow, idempotent disk/NIC attach, UPID task
completion, and HTTP-error reclassification.

Property-based tests (hypothesis) are **required** for:
1. **URL composition** for deeply nested resources — for any node-name,
   vmid, and sub-path tuple, the composed URL is deterministic with
   per-segment percent-encoding and rejects empty/`None` segments.
2. **Paging/iteration** — Proxmox returns flat lists today, but the
   client must remain total over arbitrarily long lists.
3. **Idempotent retry semantics** within and beyond budget.
4. **`ProxmoxTaskHandle.wait`** terminal-state correctness against
   arbitrary monotonic UPID status streams.
