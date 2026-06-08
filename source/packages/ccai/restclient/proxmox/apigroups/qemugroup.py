"""
    .. module:: qemugroup
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that contains the :class:`QemuGroup` api group
                   exposing the Proxmox VE QEMU virtual-machine endpoints.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []


import os
import time

from typing import Any, Dict, List, Optional

from ccai.errors.exceptions import SemanticError

from ccai.restclient.base.restapigroup import RestApiGroup

from ccai.restclient.proxmox.aspectsproxmox import (
    AspectsProxmox, DEFAULT_PROXMOX_ASPECTS
)
from ccai.restclient.proxmox.apigroups.groupsupport import (
    compose_leaf, extract_data, extract_data_list, raise_for_status,
    require_node_name, require_vmid
)
from ccai.restclient.proxmox.model.proxmoxtaskhandle import ProxmoxTaskHandle
from ccai.restclient.proxmox.model.proxmoxvmstatus import ProxmoxVmStatus
from ccai.restclient.proxmox.specs.proxmoxvmclonespec import ProxmoxVmCloneSpec
from ccai.restclient.proxmox.specs.proxmoxvmcreatespec import ProxmoxVmCreateSpec
from ccai.restclient.proxmox.specs.proxmoxdiskspec import ProxmoxDiskSpec
from ccai.restclient.proxmox.specs.proxmoxnicspec import ProxmoxNicSpec


def build_task_handle(*, client: Any, node_name: str,
                      response: Any, action: str) -> ProxmoxTaskHandle:
    """
        Build a :class:`ProxmoxTaskHandle` from a Proxmox response whose
        ``data`` member carries a UPID.

        :param client: The owning :class:`ProxmoxClient`.
        :param node_name: The node the task is running on.
        :param response: The :class:`requests.Response` from an async call.
        :param action: A short description of the attempted action.

        :returns: A :class:`ProxmoxTaskHandle` bound to the returned UPID.

        :raises: :class:`SemanticError` when no UPID was returned.
    """
    upid = extract_data(response=response, action=action)
    if upid is None or not isinstance(upid, str) or len(upid) == 0:
        err_msg_lines = ["Proxmox async call returned no UPID."]
        err_msg_lines.append("ACTION: {}".format(action))
        err_msg = os.linesep.join(err_msg_lines)
        raise SemanticError(err_msg)

    rtnval = ProxmoxTaskHandle(upid=upid, node_name=node_name, client=client)
    return rtnval


class QemuGroup(RestApiGroup):
    """
        :class:`QemuGroup` exposes the Proxmox VE QEMU virtual-machine
        endpoints — creation, clone-from-template, lifecycle power
        operations, disk and NIC management, template conversion, and
        cloud-init configuration.  Every async operation returns a
        :class:`ProxmoxTaskHandle`.
    """

    def create_vm(self, *, node_name: str, spec: ProxmoxVmCreateSpec,
                  aspects: AspectsProxmox = DEFAULT_PROXMOX_ASPECTS
                  ) -> ProxmoxTaskHandle:
        """
            Create a QEMU virtual machine.

            :param node_name: The target node.
            :param spec: The :class:`ProxmoxVmCreateSpec` to apply.
            :param aspects: Behaviour control for the call.

            :returns: A :class:`ProxmoxTaskHandle` for the create task.

            :raises: :class:`SemanticError` when ``node_name`` is empty.
        """
        require_node_name(node_name=node_name)

        client = self.client
        leaf = compose_leaf(parts=["nodes", node_name, "qemu"])
        response = client.request(method="POST", leaf=leaf,
                                  form_body=spec.to_params(), aspects=aspects)
        rtnval = build_task_handle(client=client, node_name=node_name,
                                   response=response, action="create vm")
        return rtnval

    def clone_vm(self, *, node_name: str, source_vmid: int,
                 spec: ProxmoxVmCloneSpec,
                 aspects: AspectsProxmox = DEFAULT_PROXMOX_ASPECTS
                 ) -> ProxmoxTaskHandle:
        """
            Clone a QEMU virtual machine from a template.

            :param node_name: The node hosting the source template.
            :param source_vmid: The numeric id of the source template.
            :param spec: The :class:`ProxmoxVmCloneSpec` to apply.
            :param aspects: Behaviour control for the call.

            :returns: A :class:`ProxmoxTaskHandle` for the clone task.

            :raises: :class:`SemanticError` when ``node_name`` is empty or
                ``source_vmid`` is invalid.
        """
        require_node_name(node_name=node_name)
        require_vmid(vmid=source_vmid)

        client = self.client
        leaf = compose_leaf(parts=["nodes", node_name, "qemu",
                                   str(source_vmid), "clone"])
        response = client.request(method="POST", leaf=leaf,
                                  form_body=spec.to_params(), aspects=aspects)
        # A clone may land on a different target node.
        landing_node = node_name
        if spec.target_node is not None:
            landing_node = spec.target_node
        rtnval = build_task_handle(client=client, node_name=landing_node,
                                   response=response, action="clone vm")
        return rtnval

    def get_vm_status(self, *, node_name: str, vmid: int,
                      aspects: AspectsProxmox = DEFAULT_PROXMOX_ASPECTS
                      ) -> ProxmoxVmStatus:
        """
            Retrieve the current status of a virtual machine.

            :param node_name: The node hosting the VM.
            :param vmid: The numeric VM identifier.
            :param aspects: Behaviour control for the call.

            :returns: A :class:`ProxmoxVmStatus` record.

            :raises: :class:`SemanticError` when arguments are invalid.
        """
        require_node_name(node_name=node_name)
        require_vmid(vmid=vmid)

        client = self.client
        leaf = compose_leaf(parts=["nodes", node_name, "qemu", str(vmid),
                                   "status", "current"])
        response = client.request(method="GET", leaf=leaf, aspects=aspects)
        data = extract_data(response=response, action="get vm status")

        detail = data if isinstance(data, dict) else {}
        if "vmid" not in detail:
            detail["vmid"] = vmid
        rtnval = ProxmoxVmStatus.from_dict(detail)
        return rtnval

    def list_vms(self, *, node_name: str,
                 aspects: AspectsProxmox = DEFAULT_PROXMOX_ASPECTS
                 ) -> List[ProxmoxVmStatus]:
        """
            List every QEMU virtual machine on a node.

            :param node_name: The node to query.
            :param aspects: Behaviour control for the call.

            :returns: A list of :class:`ProxmoxVmStatus` records.

            :raises: :class:`SemanticError` when ``node_name`` is empty.
        """
        require_node_name(node_name=node_name)

        client = self.client
        leaf = compose_leaf(parts=["nodes", node_name, "qemu"])
        response = client.request(method="GET", leaf=leaf, aspects=aspects)
        entries = extract_data_list(response=response, action="list vms")

        rtnval: List[ProxmoxVmStatus] = []
        for entry in entries:
            rtnval.append(ProxmoxVmStatus.from_dict(entry))

        return rtnval

    def list_templates(self, *, node_name: str,
                       aspects: AspectsProxmox = DEFAULT_PROXMOX_ASPECTS
                       ) -> List[ProxmoxVmStatus]:
        """
            List the QEMU virtual machines on a node that are templates.

            :param node_name: The node to query.
            :param aspects: Behaviour control for the call.

            :returns: A list of template :class:`ProxmoxVmStatus` records.

            :raises: :class:`SemanticError` when ``node_name`` is empty.
        """
        all_vms = self.list_vms(node_name=node_name, aspects=aspects)

        rtnval: List[ProxmoxVmStatus] = []
        for vm in all_vms:
            if vm.template is True:
                rtnval.append(vm)

        return rtnval

    def start_vm(self, *, node_name: str, vmid: int,
                 aspects: AspectsProxmox = DEFAULT_PROXMOX_ASPECTS
                 ) -> ProxmoxTaskHandle:
        """
            Start a virtual machine.

            :param node_name: The node hosting the VM.
            :param vmid: The numeric VM identifier.
            :param aspects: Behaviour control for the call.

            :returns: A :class:`ProxmoxTaskHandle` for the start task.
        """
        rtnval = self._power_action(node_name=node_name, vmid=vmid,
                                    power="start", aspects=aspects)
        return rtnval

    def stop_vm(self, *, node_name: str, vmid: int,
                aspects: AspectsProxmox = DEFAULT_PROXMOX_ASPECTS
                ) -> ProxmoxTaskHandle:
        """
            Stop a virtual machine (immediate power-off).

            :param node_name: The node hosting the VM.
            :param vmid: The numeric VM identifier.
            :param aspects: Behaviour control for the call.

            :returns: A :class:`ProxmoxTaskHandle` for the stop task.
        """
        rtnval = self._power_action(node_name=node_name, vmid=vmid,
                                    power="stop", aspects=aspects)
        return rtnval

    def reboot_vm(self, *, node_name: str, vmid: int,
                  aspects: AspectsProxmox = DEFAULT_PROXMOX_ASPECTS
                  ) -> ProxmoxTaskHandle:
        """
            Reboot a virtual machine.

            :param node_name: The node hosting the VM.
            :param vmid: The numeric VM identifier.
            :param aspects: Behaviour control for the call.

            :returns: A :class:`ProxmoxTaskHandle` for the reboot task.
        """
        rtnval = self._power_action(node_name=node_name, vmid=vmid,
                                    power="reboot", aspects=aspects)
        return rtnval

    def shutdown_vm(self, *, node_name: str, vmid: int,
                    aspects: AspectsProxmox = DEFAULT_PROXMOX_ASPECTS
                    ) -> ProxmoxTaskHandle:
        """
            Gracefully shut down a virtual machine.

            :param node_name: The node hosting the VM.
            :param vmid: The numeric VM identifier.
            :param aspects: Behaviour control for the call.

            :returns: A :class:`ProxmoxTaskHandle` for the shutdown task.
        """
        rtnval = self._power_action(node_name=node_name, vmid=vmid,
                                    power="shutdown", aspects=aspects)
        return rtnval

    def destroy_vm(self, *, node_name: str, vmid: int,
                   aspects: AspectsProxmox = DEFAULT_PROXMOX_ASPECTS
                   ) -> Optional[ProxmoxTaskHandle]:
        """
            Destroy a virtual machine.  A request that targets an absent
            vmid succeeds as a no-op and returns ``None``.

            :param node_name: The node hosting the VM.
            :param vmid: The numeric VM identifier.
            :param aspects: Behaviour control for the call.

            :returns: A :class:`ProxmoxTaskHandle` for the destroy task, or
                ``None`` when the VM was already absent.

            :raises: :class:`SemanticError` when arguments are invalid.
        """
        require_node_name(node_name=node_name)
        require_vmid(vmid=vmid)

        client = self.client
        leaf = compose_leaf(parts=["nodes", node_name, "qemu", str(vmid)])
        response = client.request(method="DELETE", leaf=leaf, aspects=aspects)

        if response.status_code == 404:
            rtnval: Optional[ProxmoxTaskHandle] = None
            return rtnval
        if response.status_code == 500 and "does not exist" in response.text:
            rtnval = None
            return rtnval

        rtnval = build_task_handle(client=client, node_name=node_name,
                                   response=response, action="destroy vm")
        return rtnval

    def convert_to_template(self, *, node_name: str, vmid: int,
                            aspects: AspectsProxmox = DEFAULT_PROXMOX_ASPECTS
                            ) -> ProxmoxTaskHandle:
        """
            Convert a stopped virtual machine into a template.

            :param node_name: The node hosting the VM.
            :param vmid: The numeric VM identifier.
            :param aspects: Behaviour control for the call.

            :returns: A :class:`ProxmoxTaskHandle` for the conversion task.

            :raises: :class:`SemanticError` when arguments are invalid.
        """
        require_node_name(node_name=node_name)
        require_vmid(vmid=vmid)

        client = self.client
        leaf = compose_leaf(parts=["nodes", node_name, "qemu", str(vmid),
                                   "template"])
        response = client.request(method="POST", leaf=leaf, aspects=aspects)
        rtnval = build_task_handle(client=client, node_name=node_name,
                                   response=response,
                                   action="convert to template")
        return rtnval

    def set_cloud_init_user_data(self, *, node_name: str, vmid: int,
                                 user_data: str,
                                 aspects: AspectsProxmox = DEFAULT_PROXMOX_ASPECTS
                                 ) -> None:
        """
            Set the cloud-init custom user-data reference on a VM config.

            :param node_name: The node hosting the VM.
            :param vmid: The numeric VM identifier.
            :param user_data: The ``cicustom`` config value referencing an
                uploaded cloud-init user snippet.
            :param aspects: Behaviour control for the call.

            :returns: ``None``.

            :raises: :class:`SemanticError` when arguments are invalid.
        """
        require_node_name(node_name=node_name)
        require_vmid(vmid=vmid)
        if user_data is None or len(user_data) == 0:
            raise SemanticError("'user_data' must be a non-empty string.")

        self._update_config(node_name=node_name, vmid=vmid,
                             changes={"cicustom": user_data}, aspects=aspects)
        return

    def set_tags(self, *, node_name: str, vmid: int, tags: List[str],
                 aspects: AspectsProxmox = DEFAULT_PROXMOX_ASPECTS) -> bool:
        """
            Set the Proxmox tag list on a VM config.  Proxmox stores tags as
            a single semicolon-delimited string; when the live config
            already carries the requested set the call is a no-op (the
            idempotent contract).

            :param node_name: The node hosting the VM.
            :param vmid: The numeric VM identifier.
            :param tags: The ordered list of tag strings to set.
            :param aspects: Behaviour control for the call.

            :returns: ``True`` when a config change was issued, ``False``
                when the tag set was already in shape.

            :raises: :class:`SemanticError` when arguments are invalid.
        """
        require_node_name(node_name=node_name)
        require_vmid(vmid=vmid)
        if tags is None:
            raise SemanticError("'tags' must be a list of tag strings.")

        desired_value = ";".join(tags)

        config = self._get_config(node_name=node_name, vmid=vmid,
                                  aspects=aspects)
        if config.get("tags", "") == desired_value:
            rtnval = False
            return rtnval

        self._update_config(node_name=node_name, vmid=vmid,
                             changes={"tags": desired_value}, aspects=aspects)
        rtnval = True
        return rtnval

    def set_ip_config(self, *, node_name: str, vmid: int, slot: str,
                      value: str,
                      aspects: AspectsProxmox = DEFAULT_PROXMOX_ASPECTS
                      ) -> bool:
        """
            Set a cloud-init ``ipconfigN`` value on a VM config.  When the
            live config already carries the requested value the call is a
            no-op (the idempotent contract).

            :param node_name: The node hosting the VM.
            :param vmid: The numeric VM identifier.
            :param slot: The ip-config slot (e.g. ``ipconfig0``).
            :param value: The ip-config value (e.g. ``ip=dhcp``).
            :param aspects: Behaviour control for the call.

            :returns: ``True`` when a config change was issued, ``False``
                when the slot was already in shape.

            :raises: :class:`SemanticError` when arguments are invalid.
        """
        require_node_name(node_name=node_name)
        require_vmid(vmid=vmid)
        if slot is None or len(slot) == 0:
            raise SemanticError("'slot' must be a non-empty string.")
        if value is None or len(value) == 0:
            raise SemanticError("'value' must be a non-empty string.")

        config = self._get_config(node_name=node_name, vmid=vmid,
                                  aspects=aspects)
        if config.get(slot, None) == value:
            rtnval = False
            return rtnval

        self._update_config(node_name=node_name, vmid=vmid,
                             changes={slot: value}, aspects=aspects)
        rtnval = True
        return rtnval

    def attach_disk(self, *, node_name: str, vmid: int,
                    spec: ProxmoxDiskSpec,
                    aspects: AspectsProxmox = DEFAULT_PROXMOX_ASPECTS) -> bool:
        """
            Attach a virtual disk to a VM.  When the slot already carries
            the requested config the call is a no-op (idempotent contract).

            :param node_name: The node hosting the VM.
            :param vmid: The numeric VM identifier.
            :param spec: The :class:`ProxmoxDiskSpec` describing the disk.
            :param aspects: Behaviour control for the call.

            :returns: ``True`` when a config change was issued, ``False``
                when the slot was already in shape.
        """
        require_node_name(node_name=node_name)
        require_vmid(vmid=vmid)

        config = self._get_config(node_name=node_name, vmid=vmid,
                                  aspects=aspects)
        desired_value = spec.to_config_value()
        if config.get(spec.slot, None) == desired_value:
            rtnval = False
            return rtnval

        self._update_config(node_name=node_name, vmid=vmid,
                             changes={spec.slot: desired_value},
                             aspects=aspects)
        rtnval = True
        return rtnval

    def detach_disk(self, *, node_name: str, vmid: int, disk_slot: str,
                    aspects: AspectsProxmox = DEFAULT_PROXMOX_ASPECTS) -> bool:
        """
            Detach a virtual disk from a VM.  When the slot is already
            absent the call is a no-op (idempotent contract).

            :param node_name: The node hosting the VM.
            :param vmid: The numeric VM identifier.
            :param disk_slot: The disk slot to detach (e.g. ``scsi1``).
            :param aspects: Behaviour control for the call.

            :returns: ``True`` when a detach was issued, ``False`` when the
                slot was already absent.
        """
        require_node_name(node_name=node_name)
        require_vmid(vmid=vmid)
        if disk_slot is None or len(disk_slot) == 0:
            raise SemanticError("'disk_slot' must be a non-empty string.")

        config = self._get_config(node_name=node_name, vmid=vmid,
                                  aspects=aspects)
        if disk_slot not in config:
            rtnval = False
            return rtnval

        self._update_config(node_name=node_name, vmid=vmid,
                             changes={"delete": disk_slot}, aspects=aspects)
        rtnval = True
        return rtnval

    def attach_nic(self, *, node_name: str, vmid: int, spec: ProxmoxNicSpec,
                   aspects: AspectsProxmox = DEFAULT_PROXMOX_ASPECTS) -> bool:
        """
            Attach a network interface to a VM.  When the slot already
            carries the requested config the call is a no-op (idempotent
            contract).

            :param node_name: The node hosting the VM.
            :param vmid: The numeric VM identifier.
            :param spec: The :class:`ProxmoxNicSpec` describing the NIC.
            :param aspects: Behaviour control for the call.

            :returns: ``True`` when a config change was issued, ``False``
                when the slot was already in shape.
        """
        require_node_name(node_name=node_name)
        require_vmid(vmid=vmid)

        config = self._get_config(node_name=node_name, vmid=vmid,
                                  aspects=aspects)
        desired_value = spec.to_config_value()
        existing_value = config.get(spec.slot, None)
        if existing_value is not None and desired_value in str(existing_value):
            rtnval = False
            return rtnval

        self._update_config(node_name=node_name, vmid=vmid,
                             changes={spec.slot: desired_value},
                             aspects=aspects)
        rtnval = True
        return rtnval

    def detach_nic(self, *, node_name: str, vmid: int, nic_slot: str,
                   aspects: AspectsProxmox = DEFAULT_PROXMOX_ASPECTS) -> bool:
        """
            Detach a network interface from a VM.  When the slot is already
            absent the call is a no-op (idempotent contract).

            :param node_name: The node hosting the VM.
            :param vmid: The numeric VM identifier.
            :param nic_slot: The NIC slot to detach (e.g. ``net0``).
            :param aspects: Behaviour control for the call.

            :returns: ``True`` when a detach was issued, ``False`` when the
                slot was already absent.
        """
        require_node_name(node_name=node_name)
        require_vmid(vmid=vmid)
        if nic_slot is None or len(nic_slot) == 0:
            raise SemanticError("'nic_slot' must be a non-empty string.")

        config = self._get_config(node_name=node_name, vmid=vmid,
                                  aspects=aspects)
        if nic_slot not in config:
            rtnval = False
            return rtnval

        self._update_config(node_name=node_name, vmid=vmid,
                             changes={"delete": nic_slot}, aspects=aspects)
        rtnval = True
        return rtnval

    def wait_for_power_state(self, *, node_name: str, vmid: int,
                             desired_state: str,
                             aspects: AspectsProxmox = DEFAULT_PROXMOX_ASPECTS
                             ) -> ProxmoxVmStatus:
        """
            Poll the VM status until it reaches a desired power state.

            :param node_name: The node hosting the VM.
            :param vmid: The numeric VM identifier.
            :param desired_state: The status to wait for (``running``,
                ``stopped``, ...).
            :param aspects: Behaviour control supplying the poll interval
                and completion timeout.

            :returns: The :class:`ProxmoxVmStatus` once the state is reached.

            :raises: :class:`TimeoutError` when the completion timeout
                elapses before the desired state is reached.
        """
        require_node_name(node_name=node_name)
        require_vmid(vmid=vmid)

        interval = aspects.task_poll_interval_seconds
        timeout = aspects.completion_timeout
        start = time.monotonic()
        deadline = start + timeout

        rtnval: Optional[ProxmoxVmStatus] = None
        while True:
            status = self.get_vm_status(node_name=node_name, vmid=vmid,
                                        aspects=aspects)
            if status.status == desired_state:
                rtnval = status
                break

            now = time.monotonic()
            if now >= deadline:
                err_msg_lines = ["VM did not reach the desired power state "
                                 "before the configured timeout."]
                err_msg_lines.append("VMID: {}".format(vmid))
                err_msg_lines.append("DESIRED: {}".format(desired_state))
                err_msg_lines.append("OBSERVED: {}".format(status.status))
                err_msg = os.linesep.join(err_msg_lines)
                raise TimeoutError(err_msg)

            time.sleep(interval)

        return rtnval

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _power_action(self, *, node_name: str, vmid: int, power: str,
                      aspects: AspectsProxmox) -> ProxmoxTaskHandle:
        """
            Issue a VM power-state transition.

            :param node_name: The node hosting the VM.
            :param vmid: The numeric VM identifier.
            :param power: The status sub-path (``start``, ``stop``, ...).
            :param aspects: Behaviour control for the call.

            :returns: A :class:`ProxmoxTaskHandle` for the power task.
        """
        require_node_name(node_name=node_name)
        require_vmid(vmid=vmid)

        client = self.client
        leaf = compose_leaf(parts=["nodes", node_name, "qemu", str(vmid),
                                   "status", power])
        response = client.request(method="POST", leaf=leaf, aspects=aspects)
        rtnval = build_task_handle(client=client, node_name=node_name,
                                   response=response,
                                   action="{} vm".format(power))
        return rtnval

    def _get_config(self, *, node_name: str, vmid: int,
                    aspects: AspectsProxmox) -> Dict[str, Any]:
        """
            Retrieve the current QEMU VM config.

            :param node_name: The node hosting the VM.
            :param vmid: The numeric VM identifier.
            :param aspects: Behaviour control for the call.

            :returns: The VM config dictionary.
        """
        client = self.client
        leaf = compose_leaf(parts=["nodes", node_name, "qemu", str(vmid),
                                   "config"])
        response = client.request(method="GET", leaf=leaf, aspects=aspects)
        data = extract_data(response=response, action="get vm config")

        rtnval = data if isinstance(data, dict) else {}
        return rtnval

    def _update_config(self, *, node_name: str, vmid: int,
                       changes: Dict[str, Any],
                       aspects: AspectsProxmox) -> None:
        """
            Apply a config change to a QEMU VM via the config endpoint.

            :param node_name: The node hosting the VM.
            :param vmid: The numeric VM identifier.
            :param changes: The config keys to set (or ``delete``).
            :param aspects: Behaviour control for the call.

            :returns: ``None``.
        """
        client = self.client
        leaf = compose_leaf(parts=["nodes", node_name, "qemu", str(vmid),
                                   "config"])
        response = client.request(method="PUT", leaf=leaf, form_body=changes,
                                  aspects=aspects)
        raise_for_status(response=response, action="update vm config")
        return
