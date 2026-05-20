"""
    .. module:: nodesgroup
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that contains the :class:`NodesGroup` api group
                   exposing the Proxmox VE node endpoints.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Automation Mojo LLC"
__credits__ = []


from typing import List

from automojo.restclient.base.restapigroup import RestApiGroup

from automojo.interop.proxmox.aspectsproxmox import (
    AspectsProxmox, DEFAULT_PROXMOX_ASPECTS
)
from automojo.interop.proxmox.apigroups.groupsupport import (
    compose_leaf, extract_data, extract_data_list, require_node_name
)
from automojo.interop.proxmox.model.proxmoxnode import ProxmoxNode


class NodesGroup(RestApiGroup):
    """
        :class:`NodesGroup` exposes the Proxmox VE node-enumeration
        endpoints — the ``/nodes`` listing and per-node detail query.
    """

    def list(self, *,
             aspects: AspectsProxmox = DEFAULT_PROXMOX_ASPECTS) -> List[ProxmoxNode]:
        """
            List every node in the cluster.

            :param aspects: Behaviour control for the call.

            :returns: A list of :class:`ProxmoxNode` records.
        """
        client = self.client
        leaf = compose_leaf(parts=["nodes"])
        response = client.request(method="GET", leaf=leaf, aspects=aspects)
        entries = extract_data_list(response=response, action="list nodes")

        rtnval: List[ProxmoxNode] = []
        for entry in entries:
            rtnval.append(ProxmoxNode.from_dict(entry))

        return rtnval

    def get(self, *, node_name: str,
            aspects: AspectsProxmox = DEFAULT_PROXMOX_ASPECTS) -> ProxmoxNode:
        """
            Retrieve detailed information about a single node.

            :param node_name: The node name to query.
            :param aspects: Behaviour control for the call.

            :returns: A :class:`ProxmoxNode` record.

            :raises: :class:`SemanticError` when ``node_name`` is empty.
        """
        require_node_name(node_name=node_name)

        client = self.client
        # Locate the node within the cluster listing for its online state,
        # then enrich it with the per-node status payload.
        nodes = self.list(aspects=aspects)
        matched = None
        for node in nodes:
            if node.name == node_name:
                matched = node
                break

        leaf = compose_leaf(parts=["nodes", node_name, "status"])
        response = client.request(method="GET", leaf=leaf, aspects=aspects)
        detail = extract_data(response=response, action="get node status")

        if matched is not None:
            if isinstance(detail, dict):
                matched.raw.update(detail)
            rtnval = matched
            return rtnval

        detail_dict = detail if isinstance(detail, dict) else {}
        detail_dict["node"] = node_name
        detail_dict.setdefault("status", "online")
        rtnval = ProxmoxNode.from_dict(detail_dict)
        return rtnval
