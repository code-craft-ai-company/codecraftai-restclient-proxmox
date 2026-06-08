"""
    .. module:: proxmoxnicspec
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that contains the :class:`ProxmoxNicSpec` request
                   spec for attaching a network interface to a VM.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []


from typing import Optional


class ProxmoxNicSpec:
    """
        :class:`ProxmoxNicSpec` describes a network interface to attach to a
        QEMU VM.  The NIC lands in a slot such as ``net0`` and references a
        bridge plus an optional VLAN tag.
    """

    def __init__(self, *, slot: str, bridge: str,
                 model: str = "virtio",
                 vlan_tag: Optional[int] = None,
                 firewall: bool = False) -> None:
        """
            Initialize a :class:`ProxmoxNicSpec` instance.

            :param slot: The NIC slot (e.g. ``net0``).
            :param bridge: The bridge the NIC attaches to.
            :param model: The virtual NIC model.
            :param vlan_tag: Optional VLAN tag.
            :param firewall: Whether the Proxmox firewall is enabled on the
                NIC.

            :returns: ``None``.
        """
        self.slot = slot
        self.bridge = bridge
        self.model = model
        self.vlan_tag = vlan_tag
        self.firewall = firewall
        return

    def to_config_value(self) -> str:
        """
            Render the NIC into the Proxmox VM config value string.

            :returns: A config value of the form
                ``<model>,bridge=<bridge>[,tag=<vlan>][,firewall=1]``.
        """
        parts = ["{},bridge={}".format(self.model, self.bridge)]
        if self.vlan_tag is not None:
            parts.append("tag={}".format(self.vlan_tag))
        if self.firewall is True:
            parts.append("firewall=1")
        rtnval = ",".join(parts)
        return rtnval
