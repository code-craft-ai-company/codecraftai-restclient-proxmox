"""
    .. module:: proxmoxcontainercreatespec
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that contains the :class:`ProxmoxContainerCreateSpec`
                   request spec for creating an LXC container.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []


from typing import Any, Dict, List, Optional


class ProxmoxContainerCreateSpec:
    """
        :class:`ProxmoxContainerCreateSpec` packages the fields needed to
        create an LXC container via ``POST /nodes/<node>/lxc``.
    """

    def __init__(self, *, vmid: int, ostemplate: str,
                 storage: str,
                 hostname: Optional[str] = None,
                 cores: int = 1, memory_mb: int = 512,
                 rootfs_gb: int = 8,
                 tags: Optional[List[str]] = None,
                 extra: Optional[Dict[str, Any]] = None) -> None:
        """
            Initialize a :class:`ProxmoxContainerCreateSpec` instance.

            :param vmid: The numeric container identifier to assign.
            :param ostemplate: The LXC OS template volume identifier.
            :param storage: The storage pool for the container rootfs.
            :param hostname: The container hostname, or ``None``.
            :param cores: Number of CPU cores.
            :param memory_mb: Memory in megabytes.
            :param rootfs_gb: Root filesystem size in gigabytes.
            :param tags: List of Proxmox tag strings.
            :param extra: Additional create parameters merged verbatim.

            :returns: ``None``.
        """
        self.vmid = vmid
        self.ostemplate = ostemplate
        self.storage = storage
        self.hostname = hostname
        self.cores = cores
        self.memory_mb = memory_mb
        self.rootfs_gb = rootfs_gb
        self.tags = tags if tags is not None else []
        self.extra = extra if extra is not None else {}
        return

    def to_params(self) -> Dict[str, Any]:
        """
            Render the spec into the Proxmox API form-parameter dictionary.

            :returns: A dictionary of create parameters.
        """
        params: Dict[str, Any] = {}
        params["vmid"] = self.vmid
        params["ostemplate"] = self.ostemplate
        params["storage"] = self.storage
        params["cores"] = self.cores
        params["memory"] = self.memory_mb
        params["rootfs"] = "{}:{}".format(self.storage, self.rootfs_gb)
        if self.hostname is not None:
            params["hostname"] = self.hostname
        if len(self.tags) > 0:
            params["tags"] = ";".join(self.tags)
        for key, value in self.extra.items():
            params[key] = value

        rtnval = params
        return rtnval
