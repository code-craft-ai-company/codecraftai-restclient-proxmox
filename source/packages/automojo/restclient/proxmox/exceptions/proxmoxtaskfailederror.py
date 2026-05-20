"""
    .. module:: proxmoxtaskfailederror
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that contains the :class:`ProxmoxTaskFailedError`
                   exception raised when a Proxmox UPID task ends in error.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Automation Mojo LLC"
__credits__ = []


class ProxmoxTaskFailedError(RuntimeError):
    """
        :class:`ProxmoxTaskFailedError` is raised when a Proxmox async task
        identified by a UPID reaches a terminal state whose exit status is
        not ``OK``.
    """
