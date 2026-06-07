"""
    .. module:: proxmoxvmclonespec
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that contains the :class:`ProxmoxVmCloneSpec`
                   request spec for cloning a QEMU VM from a template.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []


from typing import Any, Dict, Optional


class ProxmoxVmCloneSpec:
    """
        :class:`ProxmoxVmCloneSpec` packages the fields needed to clone a
        QEMU virtual machine from a template via
        ``POST /nodes/<node>/qemu/<source_vmid>/clone``.
    """

    def __init__(self, *, newid: int, name: Optional[str] = None,
                 full: bool = True,
                 target_node: Optional[str] = None,
                 storage: Optional[str] = None,
                 description: Optional[str] = None,
                 extra: Optional[Dict[str, Any]] = None) -> None:
        """
            Initialize a :class:`ProxmoxVmCloneSpec` instance.

            :param newid: The numeric VM identifier of the new clone.
            :param name: The clone name, or ``None``.
            :param full: When ``True`` perform a full clone, otherwise a
                linked clone.
            :param target_node: The target node for the clone, or ``None``.
            :param storage: The target storage pool, or ``None``.
            :param description: A free-form description, or ``None``.
            :param extra: Additional clone parameters merged verbatim.

            :returns: ``None``.
        """
        self.newid = newid
        self.name = name
        self.full = full
        self.target_node = target_node
        self.storage = storage
        self.description = description
        self.extra = extra if extra is not None else {}
        return

    def to_params(self) -> Dict[str, Any]:
        """
            Render the spec into the Proxmox API form-parameter dictionary.

            :returns: A dictionary of clone parameters.
        """
        params: Dict[str, Any] = {}
        params["newid"] = self.newid
        if self.full is True:
            params["full"] = 1
        else:
            params["full"] = 0
        if self.name is not None:
            params["name"] = self.name
        if self.target_node is not None:
            params["target"] = self.target_node
        if self.storage is not None:
            params["storage"] = self.storage
        if self.description is not None:
            params["description"] = self.description
        for key, value in self.extra.items():
            params[key] = value

        rtnval = params
        return rtnval
