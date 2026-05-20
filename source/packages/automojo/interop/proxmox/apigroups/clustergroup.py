"""
    .. module:: clustergroup
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that contains the :class:`ClusterGroup` api group
                   exposing the Proxmox VE cluster endpoints.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Automation Mojo LLC"
__credits__ = []


from automojo.restclient.base.restapigroup import RestApiGroup

from automojo.interop.proxmox.aspectsproxmox import (
    AspectsProxmox, DEFAULT_PROXMOX_ASPECTS
)
from automojo.interop.proxmox.apigroups.groupsupport import (
    compose_leaf, extract_data_list
)
from automojo.interop.proxmox.model.proxmoxclusterstatus import (
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
