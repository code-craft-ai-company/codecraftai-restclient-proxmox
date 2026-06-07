"""
    .. module:: clustergroup
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that contains the :class:`ClusterGroup` api group
                   exposing the Proxmox VE cluster endpoints.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []


from ccai.restclient.base.restapigroup import RestApiGroup

from ccai.restclient.proxmox.aspectsproxmox import (
    AspectsProxmox, DEFAULT_PROXMOX_ASPECTS
)
from ccai.restclient.proxmox.apigroups.groupsupport import (
    compose_leaf, extract_data_list
)
from ccai.restclient.proxmox.model.proxmoxclusterstatus import (
    ProxmoxClusterStatus
)


class ClusterGroup(RestApiGroup):
    """
        :class:`ClusterGroup` exposes the Proxmox VE cluster-level
        endpoints — currently the ``/cluster/status`` query.
    """

    def status(self, *,
               aspects: AspectsProxmox = DEFAULT_PROXMOX_ASPECTS) -> ProxmoxClusterStatus:
        """
            Retrieve the cluster status.

            :param aspects: Behaviour control for the call.

            :returns: A :class:`ProxmoxClusterStatus` record.
        """
        client = self.client
        leaf = compose_leaf(parts=["cluster", "status"])
        response = client.request(method="GET", leaf=leaf, aspects=aspects)
        entries = extract_data_list(response=response, action="cluster status")

        rtnval = ProxmoxClusterStatus.from_list(entries)
        return rtnval
