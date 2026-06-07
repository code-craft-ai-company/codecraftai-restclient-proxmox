"""
    .. module:: proxmoxclient
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that contains the :class:`ProxmoxClient` REST
                   client for the Proxmox VE API
                   (``https://<host>:8006/api2/json/``).

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []


import json
import os
import time

from typing import Any, Dict, Optional, Union

from requests import Response, Session

from ccai.errors.exceptions import ConfigurationError

from ccai.restclient.base.restclientbase import RestClientBase

from ccai.restclient.proxmox.aspectsproxmox import (
    AspectsProxmox, DEFAULT_PROXMOX_ASPECTS
)
from ccai.restclient.proxmox.exceptions.proxmoxauthenticationerror import (
    ProxmoxAuthenticationError
)
from ccai.restclient.proxmox.apigroups.clustergroup import ClusterGroup
from ccai.restclient.proxmox.apigroups.nodesgroup import NodesGroup
from ccai.restclient.proxmox.apigroups.networkgroup import NetworkGroup
from ccai.restclient.proxmox.apigroups.storagegroup import StorageGroup
from ccai.restclient.proxmox.apigroups.qemugroup import QemuGroup
from ccai.restclient.proxmox.apigroups.lxcgroup import LxcGroup
from ccai.restclient.proxmox.apigroups.firewallgroup import FirewallGroup
from ccai.restclient.proxmox.apigroups.tasksgroup import TasksGroup


PROXMOX_DEFAULT_PORT = 8006

# Proxmox token-id realms.  We accept any credential exposing token_id +
# secret so the package does not hard-fail when codecraftai-credentials is at a
# different revision; the duck-typed contract is documented in AGENTS.md.
_REQUIRED_CREDENTIAL_ATTRS = ("token_id", "secret")


class ProxmoxClient(RestClientBase):
    """
        :class:`ProxmoxClient` is the typed, aspect-driven REST client for
        the Proxmox VE API.  It is built on :class:`RestClientBase` and
        targets the API on port 8006 under the ``/api2/json`` prefix.

        Proxmox supports two authentication schemes — a username/password
        ticket exchange and an API token.  Both resolve, inside the
        :meth:`_authenticate` hook, to a session that carries the right
        headers.  API-token authentication carries an ``Authorization:
        PVEAPIToken=`` header and needs no CSRF token; ticket
        authentication captures a ``PVEAuthCookie`` plus a
        ``CSRFPreventionToken`` that is replayed on every write.

        The client exposes its surface through eight api groups
        (:attr:`cluster`, :attr:`nodes`, :attr:`networks`, :attr:`storage`,
        :attr:`qemu`, :attr:`lxc`, :attr:`firewall`, :attr:`tasks`).  All
        HTTP behaviour is carried by :class:`AspectsProxmox`; no
        behaviour-modifying decorators are used.
    """

    VERIFY_CERTIFICATE = False

    def __init__(self, *, credential: Any, host: str,
                 port: int = PROXMOX_DEFAULT_PORT,
                 verify_certificate: Optional[bool] = None,
                 aspects: AspectsProxmox = DEFAULT_PROXMOX_ASPECTS) -> None:
        """
            Initialize the Proxmox VE REST client.

            :param credential: A ``ProxmoxApiTokenCredential`` (or any object
                exposing ``token_id`` and ``secret``).
            :param host: The Proxmox host name or address.
            :param port: The API port (defaults to 8006).
            :param verify_certificate: Optional TLS verification override;
                Proxmox lab clusters commonly use self-signed certificates,
                so verification defaults to ``False``.
            :param aspects: Default :class:`AspectsProxmox` applied when a
                call omits an explicit aspects argument.

            :returns: ``None``.

            :raises: :class:`ConfigurationError` when ``credential`` does not
                expose the required token attributes.
        """
        for attr_name in _REQUIRED_CREDENTIAL_ATTRS:
            if not hasattr(credential, attr_name):
                err_msg_lines = ["ProxmoxClient requires a Proxmox "
                                 "API-token credential."]
                err_msg_lines.append("EXPECTED ATTRIBUTES: {}".format(
                    ", ".join(_REQUIRED_CREDENTIAL_ATTRS)
                ))
                err_msg_lines.append("FOUND: {}".format(
                    type(credential).__name__
                ))
                err_msg = os.linesep.join(err_msg_lines)
                raise ConfigurationError(err_msg)

        super().__init__(host=host, credential=credential, port=port,
                         scheme="https",
                         verify_certificate=verify_certificate,
                         aspects=aspects)

        # Ticket / CSRF state captured by the authentication hook.  When the
        # credential is an API token these stay None and the token header is
        # used directly.
        self._ticket: Optional[str] = None
        self._csrf_token: Optional[str] = None
        self._ticket_minted_at: float = 0.0

        self._cluster = ClusterGroup(self)
        self._nodes = NodesGroup(self)
        self._networks = NetworkGroup(self)
        self._storage = StorageGroup(self)
        self._qemu = QemuGroup(self)
        self._lxc = LxcGroup(self)
        self._firewall = FirewallGroup(self)
        self._tasks = TasksGroup(self)
        return

    # ------------------------------------------------------------------
    # API group accessors
    # ------------------------------------------------------------------

    @property
    def cluster(self) -> ClusterGroup:
        """
            The cluster api group.

            :returns: The :class:`ClusterGroup` instance.
        """
        rtnval = self._cluster
        return rtnval

    @property
    def nodes(self) -> NodesGroup:
        """
            The nodes api group.

            :returns: The :class:`NodesGroup` instance.
        """
        rtnval = self._nodes
        return rtnval

    @property
    def networks(self) -> NetworkGroup:
        """
            The network api group.

            :returns: The :class:`NetworkGroup` instance.
        """
        rtnval = self._networks
        return rtnval

    @property
    def storage(self) -> StorageGroup:
        """
            The storage api group.

            :returns: The :class:`StorageGroup` instance.
        """
        rtnval = self._storage
        return rtnval

    @property
    def qemu(self) -> QemuGroup:
        """
            The qemu (virtual machine) api group.

            :returns: The :class:`QemuGroup` instance.
        """
        rtnval = self._qemu
        return rtnval

    @property
    def lxc(self) -> LxcGroup:
        """
            The lxc (container) api group.

            :returns: The :class:`LxcGroup` instance.
        """
        rtnval = self._lxc
        return rtnval

    @property
    def firewall(self) -> FirewallGroup:
        """
            The firewall api group.

            :returns: The :class:`FirewallGroup` instance.
        """
        rtnval = self._firewall
        return rtnval

    @property
    def tasks(self) -> TasksGroup:
        """
            The tasks api group.

            :returns: The :class:`TasksGroup` instance.
        """
        rtnval = self._tasks
        return rtnval

    # ------------------------------------------------------------------
    # Transport
    # ------------------------------------------------------------------

    def request(self, *, method: str, leaf: str,
                params: Optional[Dict[str, Any]] = None,
                form_body: Optional[Dict[str, Any]] = None,
                headers: Optional[Dict[str, str]] = None,
                aspects: AspectsProxmox = DEFAULT_PROXMOX_ASPECTS) -> Response:
        """
            Issue a single REST call against the Proxmox VE API.

            The call attaches the resolved authentication material,
            form-encodes ``form_body`` (Proxmox accepts urlencoded form
            bodies on write calls), and replays the CSRF token on
            write methods when ticket authentication is in use.

            :param method: HTTP method to invoke.
            :param leaf: API leaf path beginning with ``/api2/json``.
            :param params: Optional query-string parameters.
            :param form_body: Optional form-encoded request body.
            :param headers: Optional additional request headers.
            :param aspects: Behaviour-control aspects for the call.

            :returns: The :class:`Response` object from the call.
        """
        session = self._authenticated_session(aspects=aspects)

        call_url = self._format_call_url(leaf)
        send_timeouts = (aspects.connection_timeout, aspects.inactivity_timeout)

        send_headers: Dict[str, str] = {}
        if headers is not None:
            send_headers.update(headers)

        upper_method = method.upper()
        is_write = upper_method in ("POST", "PUT", "DELETE")
        if is_write is True and self._csrf_token is not None:
            send_headers["CSRFPreventionToken"] = self._csrf_token

        response = session.request(method=upper_method, url=call_url,
                                   params=params, data=form_body,
                                   headers=send_headers,
                                   timeout=send_timeouts,
                                   verify=self._verify_certificate)
        rtnval = response
        return rtnval

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    def _authenticated_session(self, *,
                               aspects: AspectsProxmox) -> Session:
        """
            Build a :class:`Session` carrying current authentication
            material, transparently re-minting the ticket when it nears
            expiry.

            :param aspects: Behaviour-control aspects supplying the ticket
                refresh margin.

            :returns: A :class:`Session` ready to issue authenticated calls.
        """
        if aspects.session is not None:
            rtnval = aspects.session
            return rtnval

        token_id = getattr(self._credential, "token_id", None)
        secret = getattr(self._credential, "secret", None)
        password = getattr(self._credential, "password", None)

        # API-token authentication — no ticket exchange, no CSRF token.
        if password is None and token_id is not None and secret is not None:
            session = Session()
            session.verify = self._verify_certificate
            auth_value = "PVEAPIToken={}={}".format(token_id, secret)
            session.headers.update({
                "Authorization": auth_value,
                "Accept": "application/json",
            })
            self._session = session
            rtnval = session
            return rtnval

        # Ticket authentication — exchange username/password for a ticket.
        margin = aspects.ticket_refresh_margin_seconds
        now_ts = time.time()
        ticket_age = now_ts - self._ticket_minted_at
        ticket_stale = self._ticket is None or ticket_age >= (3600 - margin)

        if ticket_stale is True:
            self._mint_ticket(aspects=aspects)

        session = Session()
        session.verify = self._verify_certificate
        session.headers.update({
            "Accept": "application/json",
        })
        session.cookies.set("PVEAuthCookie", self._ticket)
        self._session = session
        rtnval = session
        return rtnval

    def _mint_ticket(self, *, aspects: AspectsProxmox) -> None:
        """
            Exchange the credential for a ``PVEAuthCookie`` ticket and a
            ``CSRFPreventionToken`` at ``/api2/json/access/ticket``.

            :param aspects: Behaviour-control aspects.

            :returns: ``None``.

            :raises: :class:`ProxmoxAuthenticationError` when the access
                endpoint refuses the credential.
        """
        username = getattr(self._credential, "username", None)
        password = getattr(self._credential, "password", None)
        token_id = getattr(self._credential, "token_id", None)

        # token_id carries the user@realm form even for ticket auth.
        login_user = username
        if login_user is None and token_id is not None:
            login_user = token_id.split("!")[0]

        ticket_url = "{}/api2/json/access/ticket".format(self._host_url)
        send_timeouts = (aspects.connection_timeout, aspects.inactivity_timeout)

        mint_session = Session()
        mint_session.verify = self._verify_certificate
        form_body = {"username": login_user, "password": password}

        response = mint_session.post(ticket_url, data=form_body,
                                     timeout=send_timeouts,
                                     verify=self._verify_certificate)

        if response.status_code != 200:
            err_msg_lines = ["Proxmox VE rejected the ticket request."]
            err_msg_lines.append("STATUS: {}".format(response.status_code))
            err_msg_lines.append("RESPONSE:")
            err_msg_lines.append(response.text)
            err_msg = os.linesep.join(err_msg_lines)
            raise ProxmoxAuthenticationError(err_msg)

        try:
            payload = response.json()
        except ValueError:
            err_msg = "Proxmox VE ticket response was not valid JSON."
            raise ProxmoxAuthenticationError(err_msg) from None

        data = payload.get("data", None)
        if data is None:
            err_msg = "Proxmox VE ticket response carried no 'data' member."
            raise ProxmoxAuthenticationError(err_msg)

        ticket = data.get("ticket", None)
        csrf_token = data.get("CSRFPreventionToken", None)
        if ticket is None:
            err_msg = "Proxmox VE ticket response carried no 'ticket' value."
            raise ProxmoxAuthenticationError(err_msg)

        self._ticket = ticket
        self._csrf_token = csrf_token
        self._ticket_minted_at = time.time()
        return

    def authenticate(self) -> None:
        """
            Establish an authenticated session.  Provided to satisfy the
            :class:`RestClientBase` contract; the per-call transport in
            :meth:`request` is the primary path.

            :returns: ``None``.
        """
        self._session = self._authenticated_session(aspects=self._aspects)
        return
