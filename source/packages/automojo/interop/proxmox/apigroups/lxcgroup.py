"""
    .. module:: lxcgroup
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that contains the :class:`LxcGroup` api group
                   exposing the Proxmox VE LXC container endpoints.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Automation Mojo LLC"
__credits__ = []


from typing import List, Optional

from automojo.restclient.base.restapigroup import RestApiGroup

from automojo.interop.proxmox.aspectsproxmox import (
    AspectsProxmox, DEFAULT_PROXMOX_ASPECTS
)
from automojo.interop.proxmox.apigroups.groupsupport import (
    compose_leaf, extract_data, extract_data_list, require_node_name,
    require_vmid
)
from automojo.interop.proxmox.apigroups.qemugroup import build_task_handle
from automojo.interop.proxmox.model.proxmoxcontainerstatus import (
    ProxmoxContainerStatus
)
from automojo.interop.proxmox.model.proxmoxtaskhandle import ProxmoxTaskHandle
from automojo.interop.proxmox.specs.proxmoxcontainercreatespec import (
    ProxmoxContainerCreateSpec
)


class LxcGroup(RestApiGroup):
    """
        :class:`LxcGroup` exposes the Proxmox VE LXC container endpoints —
        creation, lifecycle power operations, and destruction.  It behaves
        analogously to :class:`QemuGroup`, including the idempotent destroy
        contract.
    """

    def create_container(self, *, node_name: str,
                         spec: ProxmoxContainerCreateSpec,
                         aspects: AspectsProxmox = DEFAULT_PROXMOX_ASPECTS
                         ) -> ProxmoxTaskHandle:
        """
            Create an LXC container.

            :param node_name: The target node.
            :param spec: The :class:`ProxmoxContainerCreateSpec` to apply.
            :param aspects: Behaviour control for the call.

            :returns: A :class:`ProxmoxTaskHandle` for the create task.

            :raises: :class:`SemanticError` when ``node_name`` is empty.
        """
        require_node_name(node_name=node_name)

        client = self.client
        leaf = compose_leaf(parts=["nodes", node_name, "lxc"])
        response = client.request(method="POST", leaf=leaf,
                                  form_body=spec.to_params(), aspects=aspects)
        rtnval = build_task_handle(client=client, node_name=node_name,
                                   response=response,
                                   action="create container")
        return rtnval

    def list_containers(self, *, node_name: str,
                        aspects: AspectsProxmox = DEFAULT_PROXMOX_ASPECTS
                        ) -> List[ProxmoxContainerStatus]:
        """
            List every LXC container on a node.

            :param node_name: The node to query.
            :param aspects: Behaviour control for the call.

            :returns: A list of :class:`ProxmoxContainerStatus` records.

            :raises: :class:`SemanticError` when ``node_name`` is empty.
        """
        require_node_name(node_name=node_name)

        client = self.client
        leaf = compose_leaf(parts=["nodes", node_name, "lxc"])
        response = client.request(method="GET", leaf=leaf, aspects=aspects)
        entries = extract_data_list(response=response,
                                    action="list containers")

        rtnval: List[ProxmoxContainerStatus] = []
        for entry in entries:
            rtnval.append(ProxmoxContainerStatus.from_dict(entry))

        return rtnval

    def get_container_status(self, *, node_name: str, vmid: int,
                             aspects: AspectsProxmox = DEFAULT_PROXMOX_ASPECTS
                             ) -> ProxmoxContainerStatus:
        """
            Retrieve the current status of an LXC container.

            :param node_name: The node hosting the container.
            :param vmid: The numeric container identifier.
            :param aspects: Behaviour control for the call.

            :returns: A :class:`ProxmoxContainerStatus` record.

            :raises: :class:`SemanticError` when arguments are invalid.
        """
        require_node_name(node_name=node_name)
        require_vmid(vmid=vmid)

        client = self.client
        leaf = compose_leaf(parts=["nodes", node_name, "lxc", str(vmid),
                                   "status", "current"])
        response = client.request(method="GET", leaf=leaf, aspects=aspects)
        data = extract_data(response=response, action="get container status")

        detail = data if isinstance(data, dict) else {}
        if "vmid" not in detail:
            detail["vmid"] = vmid
        rtnval = ProxmoxContainerStatus.from_dict(detail)
        return rtnval

    def start_container(self, *, node_name: str, vmid: int,
                        aspects: AspectsProxmox = DEFAULT_PROXMOX_ASPECTS
                        ) -> ProxmoxTaskHandle:
        """
            Start an LXC container.

            :param node_name: The node hosting the container.
            :param vmid: The numeric container identifier.
            :param aspects: Behaviour control for the call.

            :returns: A :class:`ProxmoxTaskHandle` for the start task.
        """
        rtnval = self._power_action(node_name=node_name, vmid=vmid,
                                    power="start", aspects=aspects)
        return rtnval

    def stop_container(self, *, node_name: str, vmid: int,
                       aspects: AspectsProxmox = DEFAULT_PROXMOX_ASPECTS
                       ) -> ProxmoxTaskHandle:
        """
            Stop an LXC container.

            :param node_name: The node hosting the container.
            :param vmid: The numeric container identifier.
            :param aspects: Behaviour control for the call.

            :returns: A :class:`ProxmoxTaskHandle` for the stop task.
        """
        rtnval = self._power_action(node_name=node_name, vmid=vmid,
                                    power="stop", aspects=aspects)
        return rtnval

    def destroy_container(self, *, node_name: str, vmid: int,
                          aspects: AspectsProxmox = DEFAULT_PROXMOX_ASPECTS
                          ) -> Optional[ProxmoxTaskHandle]:
        """
            Destroy an LXC container.  A request that targets an absent
            vmid succeeds as a no-op and returns ``None``.

            :param node_name: The node hosting the container.
            :param vmid: The numeric container identifier.
            :param aspects: Behaviour control for the call.

            :returns: A :class:`ProxmoxTaskHandle` for the destroy task, or
                ``None`` when the container was already absent.

            :raises: :class:`SemanticError` when arguments are invalid.
        """
        require_node_name(node_name=node_name)
        require_vmid(vmid=vmid)

        client = self.client
        leaf = compose_leaf(parts=["nodes", node_name, "lxc", str(vmid)])
        response = client.request(method="DELETE", leaf=leaf, aspects=aspects)

        if response.status_code == 404:
            rtnval: Optional[ProxmoxTaskHandle] = None
            return rtnval
        if response.status_code == 500 and "does not exist" in response.text:
            rtnval = None
            return rtnval

        rtnval = build_task_handle(client=client, node_name=node_name,
                                   response=response,
                                   action="destroy container")
        return rtnval

    def _power_action(self, *, node_name: str, vmid: int, power: str,
                      aspects: AspectsProxmox) -> ProxmoxTaskHandle:
        """
            Issue a container power-state transition.

            :param node_name: The node hosting the container.
            :param vmid: The numeric container identifier.
            :param power: The status sub-path (``start`` or ``stop``).
            :param aspects: Behaviour control for the call.

            :returns: A :class:`ProxmoxTaskHandle` for the power task.
        """
        require_node_name(node_name=node_name)
        require_vmid(vmid=vmid)

        client = self.client
        leaf = compose_leaf(parts=["nodes", node_name, "lxc", str(vmid),
                                   "status", power])
        response = client.request(method="POST", leaf=leaf, aspects=aspects)
        rtnval = build_task_handle(client=client, node_name=node_name,
                                   response=response,
                                   action="{} container".format(power))
        return rtnval
