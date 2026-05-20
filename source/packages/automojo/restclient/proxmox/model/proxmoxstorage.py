"""
    .. module:: proxmoxstorage
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that contains the :class:`ProxmoxStorage` model
                   describing a storage pool available to a node.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Automation Mojo LLC"
__credits__ = []


from typing import Any, Dict, List, Optional


class ProxmoxStorage:
    """
        :class:`ProxmoxStorage` is a typed view over a single entry of the
        ``/nodes/<node>/storage`` endpoint — a Ceph RBD pool, ZFS pool,
        LVM-thin pool, NFS share, or directory storage.
    """

    def __init__(self, *, storage: str, storage_type: str,
                 content: List[str],
                 active: bool,
                 enabled: bool,
                 total: Optional[int] = None,
                 used: Optional[int] = None,
                 avail: Optional[int] = None,
                 raw: Optional[Dict[str, Any]] = None) -> None:
        """
            Initialize a :class:`ProxmoxStorage` instance.

            :param storage: The storage identifier.
            :param storage_type: The storage backend type.
            :param content: List of content types the storage accepts.
            :param active: Whether the storage is currently active.
            :param enabled: Whether the storage is enabled.
            :param total: Total capacity in bytes, or ``None``.
            :param used: Used capacity in bytes, or ``None``.
            :param avail: Available capacity in bytes, or ``None``.
            :param raw: The raw response dictionary.

            :returns: ``None``.
        """
        self.storage = storage
        self.storage_type = storage_type
        self.content = content
        self.active = active
        self.enabled = enabled
        self.total = total
        self.used = used
        self.avail = avail
        self.raw = raw if raw is not None else {}
        return

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProxmoxStorage":
        """
            Construct a :class:`ProxmoxStorage` from a response entry.

            :param data: The raw storage entry dictionary.

            :returns: A populated :class:`ProxmoxStorage`.
        """
        content_raw = data.get("content", "")
        content_list: List[str] = []
        if isinstance(content_raw, str) and len(content_raw) > 0:
            for token in content_raw.split(","):
                trimmed = token.strip()
                if len(trimmed) > 0:
                    content_list.append(trimmed)
        elif isinstance(content_raw, list):
            content_list = list(content_raw)

        rtnval = cls(storage=data.get("storage", ""),
                     storage_type=data.get("type", "unknown"),
                     content=content_list,
                     active=bool(data.get("active", 0)),
                     enabled=bool(data.get("enabled", 1)),
                     total=data.get("total", None),
                     used=data.get("used", None),
                     avail=data.get("avail", None),
                     raw=dict(data))
        return rtnval
