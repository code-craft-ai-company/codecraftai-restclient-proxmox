"""
    .. module:: storagegroup
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that contains the :class:`StorageGroup` api group
                   exposing the Proxmox VE node-storage endpoints.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Automation Mojo LLC"
__credits__ = []


from typing import List

from automojo.restclient.base.restapigroup import RestApiGroup

from automojo.interop.proxmox.aspectsproxmox import (
    AspectsProxmox, DEFAULT_PROXMOX_ASPECTS
)
from automojo.errors.exceptions import SemanticError

from automojo.interop.proxmox.apigroups.groupsupport import (
    compose_leaf, extract_data_list, raise_for_status, require_node_name
)
from automojo.interop.proxmox.model.proxmoxstorage import ProxmoxStorage


class StorageGroup(RestApiGroup):
    """
        :class:`StorageGroup` exposes the Proxmox VE node-storage endpoint —
        the ``/nodes/<node>/storage`` listing of storage pools.
    """

    def list_node_storages(self, *, node_name: str,
                           aspects: AspectsProxmox = DEFAULT_PROXMOX_ASPECTS
                           ) -> List[ProxmoxStorage]:
        """
            List every storage pool visible to a node.

            :param node_name: The node to query.
            :param aspects: Behaviour control for the call.

            :returns: A list of :class:`ProxmoxStorage` records.

            :raises: :class:`SemanticError` when ``node_name`` is empty.
        """
        require_node_name(node_name=node_name)

        client = self.client
        leaf = compose_leaf(parts=["nodes", node_name, "storage"])
        response = client.request(method="GET", leaf=leaf, aspects=aspects)
        entries = extract_data_list(response=response,
                                    action="list node storages")

        rtnval: List[ProxmoxStorage] = []
        for entry in entries:
            rtnval.append(ProxmoxStorage.from_dict(entry))

        return rtnval

    def has_snippet(self, *, node_name: str, storage: str, filename: str,
                    aspects: AspectsProxmox = DEFAULT_PROXMOX_ASPECTS
                    ) -> bool:
        """
            Return whether a snippet file already exists on a storage.

            :param node_name: The node the storage lives on.
            :param storage: The storage pool name.
            :param filename: The snippet filename to look for.
            :param aspects: Behaviour control for the call.

            :returns: ``True`` when a snippet with that filename exists.

            :raises: :class:`SemanticError` when arguments are invalid.
        """
        require_node_name(node_name=node_name)
        if storage is None or len(storage) == 0:
            raise SemanticError("'storage' must be a non-empty string.")
        if filename is None or len(filename) == 0:
            raise SemanticError("'filename' must be a non-empty string.")

        client = self.client
        leaf = compose_leaf(parts=["nodes", node_name, "storage", storage,
                                   "content"])
        response = client.request(method="GET", leaf=leaf, aspects=aspects)
        entries = extract_data_list(response=response,
                                    action="list storage content")

        wanted = "{}:snippets/{}".format(storage, filename)
        rtnval = False
        for entry in entries:
            volid = entry.get("volid", "")
            if volid == wanted or volid.endswith("/" + filename):
                rtnval = True
                break

        return rtnval

    def upload_snippet(self, *, node_name: str, storage: str, filename: str,
                       content: str,
                       aspects: AspectsProxmox = DEFAULT_PROXMOX_ASPECTS
                       ) -> str:
        """
            Upload a cloud-init snippet file to a Proxmox storage.

            :param node_name: The node the storage lives on.
            :param storage: The storage pool name.
            :param filename: The snippet filename to write.
            :param content: The snippet body.
            :param aspects: Behaviour control for the call.

            :returns: The Proxmox volume id of the uploaded snippet.

            :raises: :class:`SemanticError` when arguments are invalid.
        """
        require_node_name(node_name=node_name)
        if storage is None or len(storage) == 0:
            raise SemanticError("'storage' must be a non-empty string.")
        if filename is None or len(filename) == 0:
            raise SemanticError("'filename' must be a non-empty string.")
        if content is None or len(content) == 0:
            raise SemanticError("'content' must be a non-empty string.")

        client = self.client
        leaf = compose_leaf(parts=["nodes", node_name, "storage", storage,
                                   "upload"])
        form_body = {"content": "snippets", "filename": filename,
                     "data": content}
        response = client.request(method="POST", leaf=leaf,
                                  form_body=form_body, aspects=aspects)
        raise_for_status(response=response, action="upload snippet")

        rtnval = "{}:snippets/{}".format(storage, filename)
        return rtnval
