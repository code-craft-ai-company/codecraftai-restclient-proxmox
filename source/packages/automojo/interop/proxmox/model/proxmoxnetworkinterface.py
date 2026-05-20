"""
    .. module:: proxmoxnetworkinterface
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that contains the :class:`ProxmoxNetworkInterface`
                   model describing a node network interface.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Automation Mojo LLC"
__credits__ = []


from typing import Any, Dict, Optional


class ProxmoxNetworkInterface:
    """
        :class:`ProxmoxNetworkInterface` is a typed view over a single
        entry of the ``/nodes/<node>/network`` endpoint — a bridge, bond,
        VLAN, or physical interface.
    """

    def __init__(self, *, iface: str, iface_type: str,
                 active: bool,
                 cidr: Optional[str] = None,
                 address: Optional[str] = None,
                 bridge_ports: Optional[str] = None,
                 raw: Optional[Dict[str, Any]] = None) -> None:
        """
            Initialize a :class:`ProxmoxNetworkInterface` instance.

            :param iface: The interface name (e.g. ``vmbr0``).
            :param iface_type: The interface type (``bridge``, ``bond``,
                ``vlan``, ``eth``, ...).
            :param active: Whether the interface is currently active.
            :param cidr: The interface CIDR, or ``None``.
            :param address: The interface IPv4 address, or ``None``.
            :param bridge_ports: Space-delimited bridge member ports, or
                ``None``.
            :param raw: The raw response dictionary.

            :returns: ``None``.
        """
        self.iface = iface
        self.iface_type = iface_type
        self.active = active
        self.cidr = cidr
        self.address = address
        self.bridge_ports = bridge_ports
        self.raw = raw if raw is not None else {}
        return

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProxmoxNetworkInterface":
        """
            Construct a :class:`ProxmoxNetworkInterface` from a response
            entry.

            :param data: The raw network entry dictionary.

            :returns: A populated :class:`ProxmoxNetworkInterface`.
        """
        rtnval = cls(iface=data.get("iface", ""),
                     iface_type=data.get("type", "unknown"),
                     active=bool(data.get("active", 0)),
                     cidr=data.get("cidr", None),
                     address=data.get("address", None),
                     bridge_ports=data.get("bridge_ports", None),
                     raw=dict(data))
        return rtnval
