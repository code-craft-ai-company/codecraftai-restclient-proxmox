"""
    .. module:: test_apigroups
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Example-based tests for the Proxmox VE api groups —
                   enumeration, VM clone-from-template, idempotent slot
                   updates, and HTTP-error reclassification.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []


from ccai import testbase


from ccai.errors.exceptions import SemanticError

from ccai.restclient.proxmox.specs.proxmoxvmclonespec import ProxmoxVmCloneSpec
from ccai.restclient.proxmox.specs.proxmoxdiskspec import ProxmoxDiskSpec
from ccai.restclient.proxmox.specs.proxmoxnicspec import ProxmoxNicSpec
from ccai.restclient.proxmox.specs.proxmoxfirewallrulespec import (
    ProxmoxFirewallRuleSpec
)

from conftest import PROXMOX_BASE


def test_cluster_status_parses_nodes(client, requests_mock):
    """
        Cluster status separates the cluster entry from node entries.
    """
    requests_mock.get(
        "{}/api2/json/cluster/status".format(PROXMOX_BASE),
        json={"data": [
            {"type": "cluster", "name": "lab", "quorate": 1},
            {"type": "node", "name": "pve1", "online": 1},
            {"type": "node", "name": "pve2", "online": 1},
        ]},
    )

    status = client.cluster.status()
    assert status.name == "lab"
    assert status.quorate is True
    assert len(status.nodes) == 2


def test_list_nodes(client, requests_mock):
    """
        Node enumeration returns typed records with online state.
    """
    requests_mock.get(
        "{}/api2/json/nodes".format(PROXMOX_BASE),
        json={"data": [
            {"node": "pve1", "status": "online", "maxcpu": 8},
            {"node": "pve2", "status": "offline"},
        ]},
    )

    nodes = client.nodes.list()
    assert len(nodes) == 2
    assert nodes[0].name == "pve1"
    assert nodes[0].online is True
    assert nodes[1].online is False


def test_list_node_networks_and_storages(client, requests_mock):
    """
        Network and storage enumeration return typed records.
    """
    requests_mock.get(
        "{}/api2/json/nodes/pve1/network".format(PROXMOX_BASE),
        json={"data": [{"iface": "vmbr0", "type": "bridge", "active": 1}]},
    )
    requests_mock.get(
        "{}/api2/json/nodes/pve1/storage".format(PROXMOX_BASE),
        json={"data": [{"storage": "local-lvm", "type": "lvmthin",
                        "content": "images,rootdir", "active": 1,
                        "total": 100, "avail": 60}]},
    )

    nets = client.networks.list_node_networks(node_name="pve1")
    assert nets[0].iface == "vmbr0"
    assert nets[0].iface_type == "bridge"

    stores = client.storage.list_node_storages(node_name="pve1")
    assert stores[0].storage == "local-lvm"
    assert "images" in stores[0].content


def test_clone_vm_from_template_returns_task_handle(client, requests_mock):
    """
        A VM clone-from-template returns a :class:`ProxmoxTaskHandle` bound
        to the returned UPID.
    """
    matcher = requests_mock.post(
        "{}/api2/json/nodes/pve1/qemu/9000/clone".format(PROXMOX_BASE),
        json={"data": "UPID:pve1:00001234:clone::root@pam:"},
    )

    spec = ProxmoxVmCloneSpec(newid=120, name="worker-1", full=True)
    handle = client.qemu.clone_vm(node_name="pve1", source_vmid=9000,
                                  spec=spec)
    assert handle.upid == "UPID:pve1:00001234:clone::root@pam:"
    assert matcher.last_request.text is not None
    assert "newid=120" in matcher.last_request.text


def test_attach_disk_is_idempotent(client, requests_mock):
    """
        Attaching a disk into a slot that already carries the requested
        config issues no PUT (idempotent contract).
    """
    requests_mock.get(
        "{}/api2/json/nodes/pve1/qemu/120/config".format(PROXMOX_BASE),
        json={"data": {"scsi1": "local-lvm:20"}},
    )
    put_matcher = requests_mock.put(
        "{}/api2/json/nodes/pve1/qemu/120/config".format(PROXMOX_BASE),
        json={"data": None},
    )

    spec = ProxmoxDiskSpec(slot="scsi1", storage="local-lvm", size_gb=20)
    changed = client.qemu.attach_disk(node_name="pve1", vmid=120, spec=spec)
    assert changed is False
    assert put_matcher.call_count == 0


def test_attach_disk_issues_change_when_absent(client, requests_mock):
    """
        Attaching a disk into an empty slot issues a config PUT.
    """
    requests_mock.get(
        "{}/api2/json/nodes/pve1/qemu/120/config".format(PROXMOX_BASE),
        json={"data": {}},
    )
    put_matcher = requests_mock.put(
        "{}/api2/json/nodes/pve1/qemu/120/config".format(PROXMOX_BASE),
        json={"data": None},
    )

    spec = ProxmoxDiskSpec(slot="scsi1", storage="local-lvm", size_gb=20)
    changed = client.qemu.attach_disk(node_name="pve1", vmid=120, spec=spec)
    assert changed is True
    assert put_matcher.call_count == 1


def test_attach_nic_is_idempotent(client, requests_mock):
    """
        Attaching a NIC into a slot already carrying the config is a no-op.
    """
    requests_mock.get(
        "{}/api2/json/nodes/pve1/qemu/120/config".format(PROXMOX_BASE),
        json={"data": {"net0": "virtio,bridge=vmbr0"}},
    )
    put_matcher = requests_mock.put(
        "{}/api2/json/nodes/pve1/qemu/120/config".format(PROXMOX_BASE),
        json={"data": None},
    )

    spec = ProxmoxNicSpec(slot="net0", bridge="vmbr0", model="virtio")
    changed = client.qemu.attach_nic(node_name="pve1", vmid=120, spec=spec)
    assert changed is False
    assert put_matcher.call_count == 0


def test_destroy_vm_absent_is_noop(client, requests_mock):
    """
        Destroying an absent vmid succeeds as a no-op and returns ``None``.
    """
    requests_mock.delete(
        "{}/api2/json/nodes/pve1/qemu/999".format(PROXMOX_BASE),
        status_code=404, text="not found",
    )

    handle = client.qemu.destroy_vm(node_name="pve1", vmid=999)
    assert handle is None


def test_destroy_container_absent_is_noop(client, requests_mock):
    """
        Destroying an absent LXC vmid succeeds as a no-op.
    """
    requests_mock.delete(
        "{}/api2/json/nodes/pve1/lxc/999".format(PROXMOX_BASE),
        status_code=404, text="not found",
    )

    handle = client.lxc.destroy_container(node_name="pve1", vmid=999)
    assert handle is None


def test_list_templates_filters(client, requests_mock):
    """
        Template listing returns only VMs marked as templates.
    """
    requests_mock.get(
        "{}/api2/json/nodes/pve1/qemu".format(PROXMOX_BASE),
        json={"data": [
            {"vmid": 9000, "name": "ubuntu-tmpl", "status": "stopped",
             "template": 1},
            {"vmid": 120, "name": "worker", "status": "running",
             "template": 0},
        ]},
    )

    templates = client.qemu.list_templates(node_name="pve1")
    assert len(templates) == 1
    assert templates[0].vmid == 9000


def test_firewall_add_rule_is_idempotent(client, requests_mock):
    """
        Adding a firewall rule whose identity tuple already exists is a
        no-op.
    """
    requests_mock.get(
        "{}/api2/json/nodes/pve1/qemu/120/firewall/rules".format(PROXMOX_BASE),
        json={"data": [{"pos": 0, "action": "ACCEPT", "type": "in",
                        "enable": 1, "proto": "tcp", "dport": "22"}]},
    )
    post_matcher = requests_mock.post(
        "{}/api2/json/nodes/pve1/qemu/120/firewall/rules".format(PROXMOX_BASE),
        json={"data": None},
    )

    spec = ProxmoxFirewallRuleSpec(action="ACCEPT", rule_type="in",
                                   proto="tcp", dport="22")
    added = client.firewall.add_vm_firewall_rule(node_name="pve1", vmid=120,
                                                 spec=spec)
    assert added is False
    assert post_matcher.call_count == 0


def test_http_error_reclassified_as_semantic_error(client, requests_mock):
    """
        A non-2xx response from a read endpoint is reclassified into a
        descriptive :class:`SemanticError`.
    """
    requests_mock.get(
        "{}/api2/json/nodes".format(PROXMOX_BASE),
        status_code=500, text="internal server error",
    )

    with testbase.raises(SemanticError):
        client.nodes.list()


def test_invalid_node_name_raises_semantic_error(client):
    """
        An empty node name is rejected before any HTTP call.
    """
    with testbase.raises(SemanticError):
        client.qemu.list_vms(node_name="")
