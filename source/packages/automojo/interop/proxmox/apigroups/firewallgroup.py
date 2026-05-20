"""
    .. module:: firewallgroup
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that contains the :class:`FirewallGroup` api group
                   exposing the Proxmox VE firewall-rule endpoints.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Automation Mojo LLC"
__credits__ = []


from typing import List, Optional

from automojo.restclient.base.restapigroup import RestApiGroup

from automojo.interop.proxmox.aspectsproxmox import (
    AspectsProxmox, DEFAULT_PROXMOX_ASPECTS
)
from automojo.interop.proxmox.apigroups.groupsupport import (
    compose_leaf, extract_data_list, raise_for_status, require_node_name,
    require_vmid
)
from automojo.interop.proxmox.model.proxmoxfirewallrule import (
    ProxmoxFirewallRule
)
from automojo.interop.proxmox.specs.proxmoxfirewallrulespec import (
    ProxmoxFirewallRuleSpec
)


class FirewallGroup(RestApiGroup):
    """
        :class:`FirewallGroup` exposes the Proxmox VE per-VM firewall-rule
        endpoints — list, add, and delete.  Add is idempotent by rule-tuple
        identity; delete is idempotent on an unknown position.
    """

    def list_vm_firewall_rules(self, *, node_name: str, vmid: int,
                               aspects: AspectsProxmox = DEFAULT_PROXMOX_ASPECTS
                               ) -> List[ProxmoxFirewallRule]:
        """
            List the firewall rules attached to a VM.

            :param node_name: The node hosting the VM.
            :param vmid: The numeric VM identifier.
            :param aspects: Behaviour control for the call.

            :returns: A list of :class:`ProxmoxFirewallRule` records.

            :raises: :class:`SemanticError` when arguments are invalid.
        """
        require_node_name(node_name=node_name)
        require_vmid(vmid=vmid)

        client = self.client
        leaf = compose_leaf(parts=["nodes", node_name, "qemu", str(vmid),
                                   "firewall", "rules"])
        response = client.request(method="GET", leaf=leaf, aspects=aspects)
        entries = extract_data_list(response=response,
                                    action="list vm firewall rules")

        rtnval: List[ProxmoxFirewallRule] = []
        for entry in entries:
            rtnval.append(ProxmoxFirewallRule.from_dict(entry))

        return rtnval

    def add_vm_firewall_rule(self, *, node_name: str, vmid: int,
                             spec: ProxmoxFirewallRuleSpec,
                             aspects: AspectsProxmox = DEFAULT_PROXMOX_ASPECTS
                             ) -> bool:
        """
            Add a firewall rule to a VM.  When a rule with the same identity
            tuple already exists the call is a no-op (idempotent contract).

            :param node_name: The node hosting the VM.
            :param vmid: The numeric VM identifier.
            :param spec: The :class:`ProxmoxFirewallRuleSpec` to add.
            :param aspects: Behaviour control for the call.

            :returns: ``True`` when a rule was added, ``False`` when an
                identical rule already existed.

            :raises: :class:`SemanticError` when arguments are invalid.
        """
        require_node_name(node_name=node_name)
        require_vmid(vmid=vmid)

        existing = self.list_vm_firewall_rules(node_name=node_name,
                                               vmid=vmid, aspects=aspects)
        desired_identity = spec.identity_tuple()
        for rule in existing:
            if rule.identity_tuple() == desired_identity:
                rtnval = False
                return rtnval

        client = self.client
        leaf = compose_leaf(parts=["nodes", node_name, "qemu", str(vmid),
                                   "firewall", "rules"])
        response = client.request(method="POST", leaf=leaf,
                                  form_body=spec.to_params(), aspects=aspects)
        raise_for_status(response=response, action="add vm firewall rule")
        rtnval = True
        return rtnval

    def delete_vm_firewall_rule(self, *, node_name: str, vmid: int,
                                position: int,
                                aspects: AspectsProxmox = DEFAULT_PROXMOX_ASPECTS
                                ) -> bool:
        """
            Delete a firewall rule from a VM by position.  When the position
            is unknown the call is a no-op (idempotent contract).

            :param node_name: The node hosting the VM.
            :param vmid: The numeric VM identifier.
            :param position: The rule position index to delete.
            :param aspects: Behaviour control for the call.

            :returns: ``True`` when a rule was deleted, ``False`` when the
                position was unknown.

            :raises: :class:`SemanticError` when arguments are invalid.
        """
        require_node_name(node_name=node_name)
        require_vmid(vmid=vmid)

        existing = self.list_vm_firewall_rules(node_name=node_name,
                                               vmid=vmid, aspects=aspects)
        matched: Optional[ProxmoxFirewallRule] = None
        for rule in existing:
            if rule.pos == position:
                matched = rule
                break

        if matched is None:
            rtnval = False
            return rtnval

        client = self.client
        leaf = compose_leaf(parts=["nodes", node_name, "qemu", str(vmid),
                                   "firewall", "rules", str(position)])
        response = client.request(method="DELETE", leaf=leaf, aspects=aspects)

        if response.status_code == 404:
            rtnval = False
            return rtnval

        raise_for_status(response=response, action="delete vm firewall rule")
        rtnval = True
        return rtnval
