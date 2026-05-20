"""
    .. module:: tasksgroup
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that contains the :class:`TasksGroup` api group
                   exposing the Proxmox VE UPID task-status endpoints.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Automation Mojo LLC"
__credits__ = []


from automojo.errors.exceptions import SemanticError

from automojo.restclient.base.restapigroup import RestApiGroup

from automojo.restclient.proxmox.aspectsproxmox import (
    AspectsProxmox, DEFAULT_PROXMOX_ASPECTS
)
from automojo.restclient.proxmox.apigroups.groupsupport import (
    compose_leaf, extract_data, require_node_name
)
from automojo.restclient.proxmox.model.proxmoxtaskstatus import ProxmoxTaskStatus


class TasksGroup(RestApiGroup):
    """
        :class:`TasksGroup` exposes the Proxmox VE task-tracking endpoint —
        the ``/nodes/<node>/tasks/<upid>/status`` query consumed by
        :class:`ProxmoxTaskHandle`.
    """

    def get_status(self, *, node_name: str, upid: str,
                   aspects: AspectsProxmox = DEFAULT_PROXMOX_ASPECTS
                   ) -> ProxmoxTaskStatus:
        """
            Retrieve the status of a UPID task.

            :param node_name: The node the task is running on.
            :param upid: The UPID identifying the task.
            :param aspects: Behaviour control for the call.

            :returns: A :class:`ProxmoxTaskStatus` record.

            :raises: :class:`SemanticError` when ``node_name`` or ``upid``
                is empty.
        """
        require_node_name(node_name=node_name)
        if upid is None or len(upid) == 0:
            raise SemanticError("'upid' must be a non-empty string.")

        client = self.client
        leaf = compose_leaf(parts=["nodes", node_name, "tasks", upid,
                                   "status"], safe=":@!")
        response = client.request(method="GET", leaf=leaf, aspects=aspects)
        data = extract_data(response=response, action="get task status")

        detail = data if isinstance(data, dict) else {}
        if "upid" not in detail:
            detail["upid"] = upid
        if "node" not in detail:
            detail["node"] = node_name

        rtnval = ProxmoxTaskStatus.from_dict(detail)
        return rtnval
