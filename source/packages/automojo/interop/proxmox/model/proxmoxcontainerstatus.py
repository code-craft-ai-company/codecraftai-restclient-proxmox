"""
    .. module:: proxmoxcontainerstatus
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that contains the :class:`ProxmoxContainerStatus`
                   model describing the status of an LXC container.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Automation Mojo LLC"
__credits__ = []


from typing import Any, Dict, List, Optional


class ProxmoxContainerStatus:
    """
        :class:`ProxmoxContainerStatus` is a typed view over an LXC
        container, populated from the ``/nodes/<node>/lxc`` listing or the
        per-container status endpoint.
    """

    def __init__(self, *, vmid: int, name: Optional[str], status: str,
                 cpus: Optional[int] = None,
                 maxmem: Optional[int] = None,
                 maxdisk: Optional[int] = None,
                 uptime: Optional[int] = None,
                 tags: Optional[List[str]] = None,
                 raw: Optional[Dict[str, Any]] = None) -> None:
        """
            Initialize a :class:`ProxmoxContainerStatus` instance.

            :param vmid: The numeric container identifier.
            :param name: The container hostname, or ``None``.
            :param status: The power status (``running``, ``stopped``, ...).
            :param cpus: Number of CPU cores, or ``None``.
            :param maxmem: Configured memory in bytes, or ``None``.
            :param maxdisk: Configured rootfs size in bytes, or ``None``.
            :param uptime: Container uptime in seconds, or ``None``.
            :param tags: List of Proxmox tag strings.
            :param raw: The raw response dictionary.

            :returns: ``None``.
        """
        self.vmid = vmid
        self.name = name
        self.status = status
        self.cpus = cpus
        self.maxmem = maxmem
        self.maxdisk = maxdisk
        self.uptime = uptime
        self.tags = tags if tags is not None else []
        self.raw = raw if raw is not None else {}
        return

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProxmoxContainerStatus":
        """
            Construct a :class:`ProxmoxContainerStatus` from a response
            entry.

            :param data: The raw container entry dictionary.

            :returns: A populated :class:`ProxmoxContainerStatus`.
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

        rtnval = cls(vmid=vmid, name=data.get("name", None),
                     status=data.get("status", "unknown"),
                     cpus=data.get("cpus", None),
                     maxmem=data.get("maxmem", None),
                     maxdisk=data.get("maxdisk", None),
                     uptime=data.get("uptime", None),
                     tags=tag_list, raw=dict(data))
        return rtnval
