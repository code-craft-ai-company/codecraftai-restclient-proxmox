# Requirements

## Introduction

The `proxmox-client` feature provides a REST client for Proxmox VE on
port 8006 with ticket + CSRF-token authentication. The client covers
cluster/node enumeration, network/storage inspection, VM and container
lifecycle including clone-from-template, disk/NIC management, firewall
rule management, and async-task tracking via UPID.

Transport is REST on `RestClientBase`. Authentication uses
`ProxmoxApiTokenCredential`. Every behaviour-bearing method accepts
`aspects: AspectsRest = DEFAULT_PROXMOX_ASPECTS`.

---

## Requirements

### Requirement 1: Authenticate via Ticket + CSRF Token

#### Acceptance Criteria

1. WHEN the client is constructed with a `ProxmoxApiTokenCredential` THE
   SYSTEM SHALL exchange the credential at `/api2/json/access/ticket`
   and capture the `PVEAuthCookie` and `CSRFPreventionToken` values onto
   the underlying session.
2. WHEN any write call (POST/PUT/DELETE) is issued THE SYSTEM SHALL
   include the `CSRFPreventionToken` header.
3. WHEN the ticket nears expiry THE SYSTEM SHALL transparently re-mint
   it without surfacing the renewal to the caller.
4. WHEN authentication fails THE SYSTEM SHALL raise
   `ProxmoxAuthenticationError`.

### Requirement 2: Enumerate Cluster and Nodes

#### Acceptance Criteria

1. WHEN the caller invokes `cluster_status(aspects)` THE SYSTEM SHALL
   return a `ProxmoxClusterStatus` record.
2. WHEN the caller invokes `list_nodes(aspects)` THE SYSTEM SHALL return
   `ProxmoxNode` records with name, online state, and resource summary.
3. WHEN the caller invokes `get_node(node_name, aspects)` THE SYSTEM
   SHALL return detailed node info.

### Requirement 3: Enumerate Networks and Storage

#### Acceptance Criteria

1. WHEN the caller invokes `list_node_networks(node_name, aspects)` THE
   SYSTEM SHALL return `ProxmoxNetworkInterface` records (bridges, VLANs,
   bonds).
2. WHEN the caller invokes `list_node_storages(node_name, aspects)` THE
   SYSTEM SHALL return `ProxmoxStorage` records with content types and
   free/total capacity.

### Requirement 4: Manage Virtual Machines

#### Acceptance Criteria

1. WHEN the caller invokes `create_vm(node_name, spec, aspects)` THE
   SYSTEM SHALL POST the create request and return a `ProxmoxTaskHandle`.
2. WHEN the caller invokes `clone_vm(node_name, source_vmid, spec, aspects)`
   THE SYSTEM SHALL POST and return a `ProxmoxTaskHandle`.
3. WHEN the caller invokes `get_vm_status(node_name, vmid, aspects)` THE
   SYSTEM SHALL return a `ProxmoxVmStatus` record.
4. WHEN the caller invokes `list_vms(node_name, aspects)` THE SYSTEM SHALL
   return all VMs on the node.
5. WHEN the caller invokes `start_vm/stop_vm/reboot_vm/shutdown_vm/destroy_vm`
   THE SYSTEM SHALL POST/DELETE as appropriate and return a `ProxmoxTaskHandle`.
6. WHEN `destroy_vm` targets an absent vmid THE SYSTEM SHALL succeed as
   a no-op.

### Requirement 5: Manage VM Disks and NICs

#### Acceptance Criteria

1. WHEN the caller invokes `attach_disk(node_name, vmid, spec, aspects)`
   or `detach_disk(node_name, vmid, disk_slot, aspects)` THE SYSTEM SHALL
   PUT the VM config update.
2. WHEN the caller invokes `attach_nic(node_name, vmid, spec, aspects)`
   or `detach_nic(node_name, vmid, nic_slot, aspects)` THE SYSTEM SHALL
   PUT the VM config update.
3. WHEN a slot is already present with the requested config THE SYSTEM
   SHALL return without issuing a change (idempotent).

### Requirement 6: Manage LXC Containers

#### Acceptance Criteria

1. WHEN the caller invokes `create_container(node_name, spec, aspects)`,
   `start_container`, `stop_container`, `destroy_container` THE SYSTEM
   SHALL behave analogously to the VM lifecycle with idempotent destroy.

### Requirement 7: Manage Templates and Cloud-Init

#### Acceptance Criteria

1. WHEN the caller invokes `convert_to_template(node_name, vmid, aspects)`
   THE SYSTEM SHALL POST the template conversion and return a
   `ProxmoxTaskHandle`.
2. WHEN the caller invokes `set_cloud_init_user_data(node_name, vmid, user_data, aspects)`
   THE SYSTEM SHALL PUT the cloud-init payload onto the VM config.
3. WHEN the caller invokes `list_templates(node_name, aspects)` THE
   SYSTEM SHALL return VMs that are marked as templates.

### Requirement 8: Manage Firewall Rules

#### Acceptance Criteria

1. WHEN the caller invokes `list_vm_firewall_rules(node_name, vmid, aspects)`,
   `add_vm_firewall_rule(node_name, vmid, spec, aspects)`,
   `delete_vm_firewall_rule(node_name, vmid, position, aspects)` THE SYSTEM
   SHALL POST/GET/DELETE the appropriate firewall endpoints.
2. Idempotent add by rule-tuple identity; idempotent delete on unknown
   position.

### Requirement 9: Track UPID Tasks

#### Acceptance Criteria

1. WHEN any async call returns a UPID THE SYSTEM SHALL return a
   `ProxmoxTaskHandle` implementing `ITaskHandle`.
2. WHEN `handle.wait(aspects)` is invoked THE SYSTEM SHALL poll
   `/nodes/<node>/tasks/<upid>/status` at the interval dictated by aspects
   and SHALL return the final `ProxmoxTaskStatus` on completion.
3. WHEN the aspects timeout elapses THE SYSTEM SHALL raise `TimeoutError`.

### Requirement 10: Wait for VM Power State

#### Acceptance Criteria

1. WHEN the caller invokes `wait_for_power_state(node_name, vmid, desired_state, aspects)`
   THE SYSTEM SHALL poll `get_vm_status` per aspects.
2. Timeout raises `TimeoutError`.

### Requirement 11: URL Composition

#### Acceptance Criteria

1. WHEN composing nested URLs (`/nodes/<node>/qemu/<vmid>/...`) THE
   SYSTEM SHALL percent-encode each segment independently.
2. Empty/`None` segment raises `SemanticError`.

### Requirement 12: Aspects on Every Behaviour-Bearing Call

#### Acceptance Criteria

1. THE SYSTEM SHALL accept `aspects: AspectsRest = DEFAULT_PROXMOX_ASPECTS`
   on every I/O method; no behaviour-modifying decorators.
