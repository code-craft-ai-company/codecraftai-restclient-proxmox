"""
    .. module:: proxmox
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Package exposing the :class:`ProxmoxClient` REST client
                   and the typed Proxmox VE model and spec classes.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []


from ccai.restclient.proxmox.aspectsproxmox import (
    AspectsProxmox, DEFAULT_PROXMOX_ASPECTS
)
from ccai.restclient.proxmox.proxmoxclient import ProxmoxClient


__all__ = ["AspectsProxmox", "DEFAULT_PROXMOX_ASPECTS", "ProxmoxClient"]
