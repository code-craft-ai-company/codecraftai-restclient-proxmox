"""
    .. module:: proxmoxvmstatus
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that contains the :class:`ProxmoxVmStatus` model
                   describing the status of a QEMU virtual machine.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Automation Mojo LLC"
__credits__ = []


from typing import Any, Dict, List, Optional


class ProxmoxVmStatus:
    """
        :class:`ProxmoxVmStatus` is a typed view over a QEMU virtual
        machine, populated from the ``/nodes/<node>/qemu`` listing or the
        ``/nodes/<node>/qemu/<vmid>/status/current`` endpoint.
    """

    def __init__(self, *, vmid: int, name: Optional[str], status: str,
                 template: bool,
                 cpus: Optional[int] = None,
                 maxmem: Optional[int] = None,
                 maxdisk: Optional[int] = None,
                 uptime: Optional[int] = None,
                 tags: Optional[List[str]] = None,
                 raw: Optional[Dict[str, Any]] = None) -> None:
        """
            Initialize a :class:`ProxmoxVmStatus` instance.

            :param vmid: The numeric VM identifier.
            :param name: The VM name, or ``None``.
            :param status: The power status (``running``, ``stopped``, ...).
            :param template: Whether the VM is marked as a template.
            :param cpus: Number of virtual CPUs, or ``None``.
            :param maxmem: Configured memory in bytes, or ``None``.
            :param maxdisk: Configured disk size in bytes, or ``None``.
            :param uptime: VM uptime in seconds, or ``None``.
            :param tags: List of Proxmox tag strings.
            :param raw: The raw response dictionary.

            :returns: ``None``.
        """
        self.vmid = vmid
        self.name = name
        self.status = status
        self.template = template
        self.cpus = cpus
        self.maxmem = maxmem
        self.maxdisk = maxdisk
        self.uptime = uptime
        self.tags = tags if tags is not None else []
        self.raw = raw if raw is not None else {}
        return

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProxmoxVmStatus":
        """
            Construct a :class:`ProxmoxVmStatus` from a response entry.

            :param data: The raw VM entry dictionary.

            :returns: A populated :class:`ProxmoxVmStatus`.
        """
        vmid_raw = data.get("vmid", 0)
        try:
            vmid = int(vmid_raw)
        except (TypeError, ValueError):
            vmid = 0

        tags_raw = data.get("tags", "")
        tag_list: List[str] = []
        if isinstance(tags_raw, str) and len(tags_raw) > 0:
            for token in tags_raw.split(";"):
                trimmed = token.strip()
                if len(trimmed) > 0:
                    tag_list.append(trimmed)
        elif isinstance(tags_raw, list):
            tag_list = list(tags_raw)

        template_flag = bool(data.get("template", 0))

        rtnval = cls(vmid=vmid, name=data.get("name", None),
                     status=data.get("status", "unknown"),
                     template=template_flag,
                     cpus=data.get("cpus", None),
                     maxmem=data.get("maxmem", None),
                     maxdisk=data.get("maxdisk", None),
                     uptime=data.get("uptime", None),
                     tags=tag_list, raw=dict(data))
        return rtnval
