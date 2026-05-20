"""
    .. module:: proxmoxvmcreatespec
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that contains the :class:`ProxmoxVmCreateSpec`
                   request spec for creating a QEMU VM.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Automation Mojo LLC"
__credits__ = []


from typing import Any, Dict, List, Optional


class ProxmoxVmCreateSpec:
    """
        :class:`ProxmoxVmCreateSpec` packages the fields needed to create a
        QEMU virtual machine via ``POST /nodes/<node>/qemu``.
    """

    def __init__(self, *, vmid: int, name: Optional[str] = None,
                 cores: int = 1, memory_mb: int = 512,
                 ostype: Optional[str] = None,
                 tags: Optional[List[str]] = None,
                 extra: Optional[Dict[str, Any]] = None) -> None:
        """
            Initialize a :class:`ProxmoxVmCreateSpec` instance.

            :param vmid: The numeric VM identifier to assign.
            :param name: The VM name, or ``None``.
            :param cores: Number of virtual CPU cores.
            :param memory_mb: Memory in megabytes.
            :param ostype: The Proxmox ostype hint, or ``None``.
            :param tags: List of Proxmox tag strings.
            :param extra: Additional create parameters merged verbatim.

            :returns: ``None``.
        """
        self.vmid = vmid
        self.name = name
        self.cores = cores
        self.memory_mb = memory_mb
        self.ostype = ostype
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
        params["cores"] = self.cores
        params["memory"] = self.memory_mb
        if self.name is not None:
            params["name"] = self.name
        if self.ostype is not None:
            params["ostype"] = self.ostype
        if len(self.tags) > 0:
            params["tags"] = ";".join(self.tags)
        for key, value in self.extra.items():
            params[key] = value

        rtnval = params
        return rtnval
