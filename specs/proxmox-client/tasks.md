# Implementation Plan — Proxmox Client

## Package Skeleton

- [x] 1. Create `source/packages/automojo/interop/proxmox/` package tree.
- [x] 2. Add `aspectsproxmox.py` with `DEFAULT_PROXMOX_ASPECTS`.

## Client Core

- [x] 3. Implement `ProxmoxClient(RestClientBase)` with ticket + CSRF auth in `_authenticate` and transparent ticket renewal.
- [x] 4. Implement nested-URL composition helper (per-segment encoding, empty/`None` rejection).
- [x] 5. Implement HTTP-error reclassification into typed exceptions.

## Data Model & Specs

- [x] 6. Implement model dataclasses for cluster status, node, network interface, storage, VM status, container status, task status, firewall rule.
- [x] 7. Implement spec dataclasses for VM create/clone/disk/NIC, container create, firewall rule.
- [x] 8. Implement `ProxmoxTaskHandle` against `ITaskHandle` using UPID polling.

## API Groups

- [x] 9. Implement `ClusterGroup.status`.
- [x] 10. Implement `NodesGroup.list/get`.
- [x] 11. Implement `NetworkGroup.list_node_networks`.
- [x] 12. Implement `StorageGroup.list_node_storages`.
- [x] 13. Implement `QemuGroup.create/clone/get_status/list/start/stop/reboot/shutdown/destroy/attach_disk/detach_disk/attach_nic/detach_nic/convert_to_template/set_cloud_init_user_data/list_templates` with idempotent destroy and idempotent slot updates.
- [x] 14. Implement `LxcGroup.create/start/stop/destroy` with idempotent destroy.
- [x] 15. Implement `FirewallGroup.list_vm_rules/add_vm_rule/delete_vm_rule` with idempotency.
- [x] 16. Implement `TasksGroup.get_status` consumed by `ProxmoxTaskHandle.wait`.

## Waiters

- [x] 17. Implement `wait_for_power_state(node_name, vmid, desired_state, aspects)`.

## Tests — Example-Based

- [x] 18. Ticket + CSRF auth happy path and renewal-on-expiry tests.
- [x] 19. VM clone-from-template flow.
- [x] 20. Idempotent disk/NIC attach tests.
- [x] 21. UPID task completion happy path.
- [x] 22. HTTP-error reclassification.

## Tests — Property-Based (hypothesis)

- [x] 23. Nested-URL composition determinism, per-segment encoding, empty/`None` rejection.
- [x] 24. Long-list iteration totality.
- [x] 25. Idempotent-retry equivalence.
- [x] 26. `ProxmoxTaskHandle.wait` terminal-state correctness.

## Integration

- [ ] 27. Smoke-test fixture against a live Proxmox lab cluster. (deferred: live-integration smoke test gated on real hardware/cluster)
