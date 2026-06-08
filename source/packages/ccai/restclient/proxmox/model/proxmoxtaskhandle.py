"""
    .. module:: proxmoxtaskhandle
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that contains the :class:`ProxmoxTaskHandle` which
                   tracks a Proxmox UPID async task to completion.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []


import os
import time

from typing import TYPE_CHECKING, Optional

from ccai.errors.exceptions import SemanticError

from ccai.restclient.proxmox.aspectsproxmox import (
    AspectsProxmox, DEFAULT_PROXMOX_ASPECTS
)
from ccai.restclient.proxmox.model.proxmoxtaskstatus import ProxmoxTaskStatus
from ccai.restclient.proxmox.exceptions.proxmoxtaskfailederror import (
    ProxmoxTaskFailedError
)


if TYPE_CHECKING:
    from ccai.restclient.proxmox.proxmoxclient import ProxmoxClient


class ProxmoxTaskHandle:
    """
        :class:`ProxmoxTaskHandle` is the typed handle returned by every
        Proxmox async operation.  Proxmox identifies long-running operations
        by a UPID (unique process id) returned in the response ``data``
        field; this handle polls the per-node task-status endpoint until the
        task reaches a terminal state.

        It implements the ``ITaskHandle`` shape — :meth:`task_id`,
        :meth:`is_done`, and :meth:`wait` — so consumers expecting a task
        handle can substitute it transparently.
    """

    def __init__(self, *, upid: str, node_name: str,
                 client: "ProxmoxClient") -> None:
        """
            Initialize a :class:`ProxmoxTaskHandle` instance.

            :param upid: The UPID identifying the Proxmox task.
            :param node_name: The node the task is running on.
            :param client: The owning :class:`ProxmoxClient`.

            :returns: ``None``.

            :raises: :class:`SemanticError` when ``upid`` or ``node_name``
                is empty.
        """
        if upid is None or len(upid) == 0:
            raise SemanticError("ProxmoxTaskHandle requires a non-empty 'upid'.")
        if node_name is None or len(node_name) == 0:
            raise SemanticError(
                "ProxmoxTaskHandle requires a non-empty 'node_name'."
            )

        self._upid = upid
        self._node_name = node_name
        self._client = client
        self._last_status: Optional[ProxmoxTaskStatus] = None
        return

    @property
    def upid(self) -> str:
        """
            The UPID identifying the Proxmox task.

            :returns: The UPID string.
        """
        rtnval = self._upid
        return rtnval

    @property
    def node_name(self) -> str:
        """
            The node the task is running on.

            :returns: The node name string.
        """
        rtnval = self._node_name
        return rtnval

    def task_id(self) -> str:
        """
            Return the vendor task identifier (the UPID).

            :returns: The UPID string.
        """
        rtnval = self._upid
        return rtnval

    def is_done(self) -> bool:
        """
            Return whether the most recently observed task state is
            terminal.  Does not poll the network.

            :returns: ``True`` when the last observed status was ``stopped``.
        """
        rtnval = False
        if self._last_status is not None:
            if self._last_status.is_running is False:
                rtnval = True
        return rtnval

    def poll(self, *,
             aspects: AspectsProxmox = DEFAULT_PROXMOX_ASPECTS) -> ProxmoxTaskStatus:
        """
            Perform a single status poll without waiting.

            :param aspects: Behaviour control for the call.

            :returns: The current :class:`ProxmoxTaskStatus`.
        """
        status = self._client.tasks.get_status(node_name=self._node_name,
                                                upid=self._upid,
                                                aspects=aspects)
        self._last_status = status
        rtnval = status
        return rtnval

    def wait(self, *,
             aspects: AspectsProxmox = DEFAULT_PROXMOX_ASPECTS,
             raise_on_failure: bool = True) -> ProxmoxTaskStatus:
        """
            Poll the task status endpoint until the task reaches a terminal
            state or the aspects completion timeout elapses.

            :param aspects: Behaviour control supplying the poll interval
                and the completion timeout.
            :param raise_on_failure: When ``True``, raise
                :class:`ProxmoxTaskFailedError` if the task ends with a
                non-``OK`` exit status.

            :returns: The terminal :class:`ProxmoxTaskStatus`.

            :raises: :class:`TimeoutError` when the completion timeout
                elapses; :class:`ProxmoxTaskFailedError` when the task fails
                and ``raise_on_failure`` is ``True``.
        """
        interval = aspects.task_poll_interval_seconds
        timeout = aspects.completion_timeout

        if interval <= 0:
            raise SemanticError(
                "ProxmoxTaskHandle.wait requires task_poll_interval_seconds > 0."
            )
        if timeout <= 0:
            raise SemanticError(
                "ProxmoxTaskHandle.wait requires completion_timeout > 0."
            )

        start = time.monotonic()
        deadline = start + timeout

        rtnval: Optional[ProxmoxTaskStatus] = None
        while True:
            status = self.poll(aspects=aspects)

            if status.is_running is False:
                rtnval = status
                break

            now = time.monotonic()
            if now >= deadline:
                err_msg_lines = ["Proxmox task did not complete before the "
                                 "configured timeout."]
                err_msg_lines.append("UPID: {}".format(self._upid))
                err_msg_lines.append("NODE: {}".format(self._node_name))
                err_msg_lines.append("TIMEOUT: {}s".format(timeout))
                err_msg = os.linesep.join(err_msg_lines)
                raise TimeoutError(err_msg)

            time.sleep(interval)

        if raise_on_failure is True and rtnval.is_successful is False:
            err_msg_lines = ["Proxmox task ended with a non-OK exit status."]
            err_msg_lines.append("UPID: {}".format(self._upid))
            err_msg_lines.append("NODE: {}".format(self._node_name))
            err_msg_lines.append("EXITSTATUS: {!r}".format(rtnval.exitstatus))
            err_msg = os.linesep.join(err_msg_lines)
            raise ProxmoxTaskFailedError(err_msg)

        return rtnval
