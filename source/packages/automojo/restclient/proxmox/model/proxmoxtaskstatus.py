"""
    .. module:: proxmoxtaskstatus
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that contains the :class:`ProxmoxTaskStatus` model
                   describing the status of a Proxmox UPID task.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Automation Mojo LLC"
__credits__ = []


from typing import Any, Dict, Optional


class ProxmoxTaskStatus:
    """
        :class:`ProxmoxTaskStatus` is a typed view over the
        ``/nodes/<node>/tasks/<upid>/status`` endpoint.  A task is finished
        when :attr:`status` is ``stopped``; :attr:`exitstatus` is ``OK`` on
        success and an error string otherwise.
    """

    def __init__(self, *, upid: str, status: str,
                 exitstatus: Optional[str] = None,
                 node: Optional[str] = None,
                 task_type: Optional[str] = None,
                 raw: Optional[Dict[str, Any]] = None) -> None:
        """
            Initialize a :class:`ProxmoxTaskStatus` instance.

            :param upid: The unique process identifier of the task.
            :param status: The task status (``running`` or ``stopped``).
            :param exitstatus: The exit status string once stopped.
            :param node: The node the task ran on.
            :param task_type: The task type string.
            :param raw: The raw response dictionary.

            :returns: ``None``.
        """
        self.upid = upid
        self.status = status
        self.exitstatus = exitstatus
        self.node = node
        self.task_type = task_type
        self.raw = raw if raw is not None else {}
        return

    @property
    def is_running(self) -> bool:
        """
            Whether the task is still running.

            :returns: ``True`` when the task status is ``running``.
        """
        rtnval = self.status == "running"
        return rtnval

    @property
    def is_successful(self) -> bool:
        """
            Whether the task finished successfully.

            :returns: ``True`` when the task is stopped with exit status
                ``OK``.
        """
        rtnval = False
        if self.status == "stopped":
            if self.exitstatus is not None and self.exitstatus == "OK":
                rtnval = True
        return rtnval

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProxmoxTaskStatus":
        """
            Construct a :class:`ProxmoxTaskStatus` from a response entry.

            :param data: The raw task status dictionary.

            :returns: A populated :class:`ProxmoxTaskStatus`.
        """
        rtnval = cls(upid=data.get("upid", data.get("id", "")),
                     status=data.get("status", "unknown"),
                     exitstatus=data.get("exitstatus", None),
                     node=data.get("node", None),
                     task_type=data.get("type", None),
                     raw=dict(data))
        return rtnval
