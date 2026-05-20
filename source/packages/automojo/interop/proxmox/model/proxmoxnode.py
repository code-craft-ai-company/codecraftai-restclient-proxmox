"""
    .. module:: proxmoxnode
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that contains the :class:`ProxmoxNode` model
                   describing a single node within a Proxmox VE cluster.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Automation Mojo LLC"
__credits__ = []


from typing import Any, Dict, Optional


class ProxmoxNode:
    """
        :class:`ProxmoxNode` is a typed view over a single cluster node as
        reported by the ``/nodes`` endpoint.  It carries the node name, the
        online state, and a coarse resource summary.
    """

    def __init__(self, *, name: str, status: str,
                 online: bool,
                 cpu: Optional[float] = None,
                 maxcpu: Optional[int] = None,
                 mem: Optional[int] = None,
                 maxmem: Optional[int] = None,
                 uptime: Optional[int] = None,
                 raw: Optional[Dict[str, Any]] = None) -> None:
        """
            Initialize a :class:`ProxmoxNode` instance.

            :param name: The node name.
            :param status: The node status string reported by Proxmox.
            :param online: Whether the node is currently online.
            :param cpu: Fractional CPU usage (0.0 - 1.0), or ``None``.
            :param maxcpu: Number of CPU cores, or ``None``.
            :param mem: Used memory in bytes, or ``None``.
            :param maxmem: Total memory in bytes, or ``None``.
            :param uptime: Node uptime in seconds, or ``None``.
            :param raw: The raw response dictionary.

            :returns: ``None``.
        """
        self.name = name
        self.status = status
        self.online = online
        self.cpu = cpu
        self.maxcpu = maxcpu
        self.mem = mem
        self.maxmem = maxmem
        self.uptime = uptime
        self.raw = raw if raw is not None else {}
        return

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProxmoxNode":
        """
            Construct a :class:`ProxmoxNode` from a Proxmox response entry.

            :param data: The raw node dictionary.

            :returns: A populated :class:`ProxmoxNode`.
        """
        name = data.get("node", data.get("name", ""))
        status = data.get("status", "unknown")
        online_flag = data.get("online", None)
        if online_flag is not None:
            online = bool(online_flag)
        else:
            online = status == "online"

        rtnval = cls(name=name, status=status, online=online,
                     cpu=data.get("cpu", None), maxcpu=data.get("maxcpu", None),
                     mem=data.get("mem", None), maxmem=data.get("maxmem", None),
                     uptime=data.get("uptime", None), raw=dict(data))
        return rtnval
