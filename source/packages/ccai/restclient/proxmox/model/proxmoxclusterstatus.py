"""
    .. module:: proxmoxclusterstatus
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that contains the :class:`ProxmoxClusterStatus`
                   model describing the status of a Proxmox VE cluster.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []


from typing import Any, Dict, List, Optional


class ProxmoxClusterStatus:
    """
        :class:`ProxmoxClusterStatus` is a typed view over the
        ``/cluster/status`` endpoint.  Proxmox returns a flat list mixing a
        ``cluster`` entry with one ``node`` entry per member; this model
        separates them into the cluster name, quorate flag, and node list.
    """

    def __init__(self, *, name: Optional[str], quorate: bool,
                 nodes: List[Dict[str, Any]],
                 raw: Optional[List[Dict[str, Any]]] = None) -> None:
        """
            Initialize a :class:`ProxmoxClusterStatus` instance.

            :param name: The cluster name, or ``None`` for a standalone node.
            :param quorate: Whether the cluster currently has quorum.
            :param nodes: List of node entry dictionaries.
            :param raw: The raw status list.

            :returns: ``None``.
        """
        self.name = name
        self.quorate = quorate
        self.nodes = nodes
        self.raw = raw if raw is not None else []
        return

    @classmethod
    def from_list(cls, data: List[Dict[str, Any]]) -> "ProxmoxClusterStatus":
        """
            Construct a :class:`ProxmoxClusterStatus` from the raw status
            list.

            :param data: The list returned by ``/cluster/status``.

            :returns: A populated :class:`ProxmoxClusterStatus`.
        """
        name: Optional[str] = None
        quorate = False
        nodes: List[Dict[str, Any]] = []

        if data is not None:
            for entry in data:
                if not isinstance(entry, dict):
                    continue
                entry_type = entry.get("type", "")
                if entry_type == "cluster":
                    name = entry.get("name", None)
                    quorate = bool(entry.get("quorate", 0))
                elif entry_type == "node":
                    nodes.append(entry)

        raw_list = list(data) if data is not None else []
        rtnval = cls(name=name, quorate=quorate, nodes=nodes, raw=raw_list)
        return rtnval
