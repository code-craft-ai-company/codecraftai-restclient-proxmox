"""
    .. module:: proxmoxdiskspec
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that contains the :class:`ProxmoxDiskSpec` request
                   spec for attaching a virtual disk to a VM.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Automation Mojo LLC"
__credits__ = []


from typing import Optional


class ProxmoxDiskSpec:
    """
        :class:`ProxmoxDiskSpec` describes a virtual disk to attach to a
        QEMU VM.  The disk lands in a slot such as ``scsi1`` or ``virtio2``
        and references a storage pool plus a size in gigabytes.
    """

    def __init__(self, *, slot: str, storage: str, size_gb: int,
                 disk_format: Optional[str] = None) -> None:
        """
            Initialize a :class:`ProxmoxDiskSpec` instance.

            :param slot: The disk bus slot (e.g. ``scsi1``, ``virtio2``).
            :param storage: The storage pool the disk lands on.
            :param size_gb: The disk size in gigabytes.
            :param disk_format: Optional disk image format hint.

            :returns: ``None``.
        """
        self.slot = slot
        self.storage = storage
        self.size_gb = size_gb
        self.disk_format = disk_format
        return

    def to_config_value(self) -> str:
        """
            Render the disk into the Proxmox VM config value string.

            :returns: A config value of the form ``<storage>:<size>``.
        """
        rtnval = "{}:{}".format(self.storage, self.size_gb)
        if self.disk_format is not None:
            rtnval = "{},format={}".format(rtnval, self.disk_format)
        return rtnval
