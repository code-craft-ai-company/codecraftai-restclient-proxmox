"""
    .. module:: proxmoxauthenticationerror
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that contains the :class:`ProxmoxAuthenticationError`
                   exception raised when Proxmox ticket/token auth fails.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Automation Mojo LLC"
__credits__ = []


class ProxmoxAuthenticationError(RuntimeError):
    """
        :class:`ProxmoxAuthenticationError` is raised when the Proxmox VE
        access endpoint refuses the supplied credential, or when a ticket
        re-mint fails to produce a usable ticket and CSRF token.
    """
