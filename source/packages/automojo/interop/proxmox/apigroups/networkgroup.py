"""
    .. module:: networkgroup
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that contains the :class:`NetworkGroup` api group
                   exposing the Proxmox VE node-network endpoints.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Automation Mojo LLC"
__credits__ = []


from typing import List

from automojo.errors.exceptions import SemanticError

from automojo.restclient.base.restapigroup import RestApiGroup

from automojo.interop.proxmox.aspectsproxmox import (
    AspectsProxmox, DEFAULT_PROXMOX_ASPECTS
)
from automojo.interop.proxmox.apigroups.groupsupport import (
    compose_leaf, extract_data_list, raise_for_status, require_node_name
)
from automojo.interop.proxmox.model.proxmoxnetworkinterface import (
    ProxmoxNetworkInterface
)


class NetworkGroup(RestApiGroup):
    """
        :class:`NetworkGroup` exposes the Proxmox VE node-network endpoint —
        the ``/nodes/<node>/network`` listing of bridges, bonds, and VLANs.
    """

    def list_node_networks(self, *, node_name: str,
                           aspects: AspectsProxmox = DEFAULT_PROXMOX_ASPECTS
                           ) -> List[ProxmoxNetworkInterface]:
        """
            List every network interface on a node.

            :param node_name: The node to query.
            :param aspects: Behaviour control for the call.

            :returns: A list of :class:`ProxmoxNetworkInterface` records.

            :raises: :class:`SemanticError` when ``node_name`` is empty.
        """
        require_node_name(node_name=node_name)

        client = self.client
        leaf = compose_leaf(parts=["nodes", node_name, "network"])
        response = client.request(method="GET", leaf=leaf, aspects=aspects)
        entries = extract_data_list(response=response,
                                    action="list node networks")

        rtnval: List[ProxmoxNetworkInterface] = []
        for entry in entries:
            rtnval.append(ProxmoxNetworkInterface.from_dict(entry))

        return rtnval

    def create_bridge(self, *, node_name: str, bridge: str,
                      cidr: str = None, comments: str = None,
                      aspects: AspectsProxmox = DEFAULT_PROXMOX_ASPECTS
                      ) -> bool:
        """
            Create a Linux bridge on a node.  When a bridge with the same
            name already exists the call is a no-op (idempotent contract).

            :param node_name: The node to create the bridge on.
            :param bridge: The bridge interface name (e.g. ``vmbr1``).
            :param cidr: Optional bridge CIDR address.
            :param comments: Optional bridge comment.
            :param aspects: Behaviour control for the call.

            :returns: ``True`` when the bridge was created, ``False`` when
                it already existed.

            :raises: :class:`SemanticError` when arguments are invalid.
        """
        require_node_name(node_name=node_name)
        if bridge is None or len(bridge) == 0:
            raise SemanticError("'bridge' must be a non-empty string.")

        existing = self.list_node_networks(node_name=node_name,
                                           aspects=aspects)
        for entry in existing:
            if entry.iface == bridge:
                rtnval = False
                return rtnval

        client = self.client
        leaf = compose_leaf(parts=["nodes", node_name, "network"])
        form_body = {"iface": bridge, "type": "bridge"}
        if cidr is not None:
            form_body["cidr"] = cidr
        if comments is not None:
            form_body["comments"] = comments
        response = client.request(method="POST", leaf=leaf,
                                  form_body=form_body, aspects=aspects)
        raise_for_status(response=response, action="create bridge")

        rtnval = True
        return rtnval
