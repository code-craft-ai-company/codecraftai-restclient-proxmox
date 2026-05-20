"""
    .. module:: groupsupport
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that contains shared helpers used by the Proxmox VE
                   api-group classes — nested-URL composition and response
                   handling.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Automation Mojo LLC"
__credits__ = []


import os

from typing import Any, Dict, List
from urllib.parse import quote

from requests import Response

from automojo.errors.exceptions import SemanticError


API_BASE = "/api2/json"


def compose_leaf(*, parts: List[str], safe: str = "") -> str:
    """
        Compose a Proxmox VE API leaf path by percent-encoding each path
        segment independently and joining them under the ``/api2/json``
        prefix.

        :param parts: Ordered list of path segments.  Each segment is
            required to be a non-empty string; ``None`` or empty segments
            are rejected.
        :param safe: Additional characters that must not be percent-encoded
            within a segment.  Proxmox UPID segments contain ``:`` and
            ``@`` which are valid path characters and must be preserved so
            the server-side route matches.

        :returns: The composed leaf path beginning with ``/api2/json/``.

        :raises: :class:`SemanticError` when a segment is ``None`` or empty.
    """
    if parts is None:
        raise SemanticError("compose_leaf requires a non-None 'parts' list.")
    if len(parts) == 0:
        raise SemanticError("compose_leaf requires at least one path segment.")

    encoded_segments: List[str] = []
    for part in parts:
        if part is None:
            err_msg_lines = ["compose_leaf path segment must not be None."]
            err_msg_lines.append("PARTS: {!r}".format(parts))
            err_msg = os.linesep.join(err_msg_lines)
            raise SemanticError(err_msg)
        if not isinstance(part, str):
            err_msg_lines = ["compose_leaf path segments must be strings."]
            err_msg_lines.append("SEGMENT: {!r}".format(part))
            err_msg = os.linesep.join(err_msg_lines)
            raise SemanticError(err_msg)
        if len(part) == 0:
            err_msg_lines = ["compose_leaf path segment must not be empty."]
            err_msg_lines.append("PARTS: {!r}".format(parts))
            err_msg = os.linesep.join(err_msg_lines)
            raise SemanticError(err_msg)

        encoded = quote(part, safe=safe)
        encoded_segments.append(encoded)

    joined = "/".join(encoded_segments)
    rtnval = "{}/{}".format(API_BASE, joined)
    return rtnval


def require_node_name(*, node_name: str) -> None:
    """
        Validate a node-name argument.

        :param node_name: The node name to check.

        :returns: ``None``.

        :raises: :class:`SemanticError` when ``node_name`` is empty.
    """
    if node_name is None or len(node_name) == 0:
        raise SemanticError("'node_name' must be a non-empty string.")
    return


def require_vmid(*, vmid: int) -> None:
    """
        Validate a VM/container identifier argument.

        :param vmid: The numeric identifier to check.

        :returns: ``None``.

        :raises: :class:`SemanticError` when ``vmid`` is not a positive int.
    """
    if vmid is None:
        raise SemanticError("'vmid' must be a positive integer.")
    if not isinstance(vmid, int):
        raise SemanticError("'vmid' must be a positive integer.")
    if vmid <= 0:
        raise SemanticError("'vmid' must be a positive integer.")
    return


def raise_for_status(*, response: Response, action: str) -> None:
    """
        Raise a descriptive :class:`SemanticError` for a non-2xx response.

        :param response: The :class:`Response` to inspect.
        :param action: A short description of the attempted action.

        :returns: ``None``.

        :raises: :class:`SemanticError` when the status is not 2xx.
    """
    status = response.status_code
    if 200 <= status < 300:
        return

    err_msg_lines = ["Proxmox VE API call failed: {}.".format(action)]
    err_msg_lines.append("STATUS: {}".format(status))
    err_msg_lines.append("RESPONSE:")
    err_msg_lines.append(response.text)
    err_msg = os.linesep.join(err_msg_lines)
    raise SemanticError(err_msg)


def extract_data(*, response: Response, action: str) -> Any:
    """
        Extract the ``data`` member from a Proxmox VE JSON response.

        Proxmox wraps every payload in a ``{"data": ...}`` envelope.  This
        helper validates the response status and returns the unwrapped
        value.

        :param response: The :class:`Response` to parse.
        :param action: A short description of the attempted action.

        :returns: The unwrapped ``data`` value (dict, list, scalar, or
            ``None``).

        :raises: :class:`SemanticError` when the response is not 2xx or the
            body is not a JSON object.
    """
    raise_for_status(response=response, action=action)

    try:
        payload = response.json()
    except ValueError:
        err_msg_lines = ["Proxmox VE response was not valid JSON: {}.".format(
            action
        )]
        err_msg_lines.append("RESPONSE:")
        err_msg_lines.append(response.text)
        err_msg = os.linesep.join(err_msg_lines)
        raise SemanticError(err_msg) from None

    if not isinstance(payload, dict):
        err_msg_lines = ["Proxmox VE response envelope was not an object."]
        err_msg_lines.append("ACTION: {}".format(action))
        err_msg = os.linesep.join(err_msg_lines)
        raise SemanticError(err_msg)

    rtnval = payload.get("data", None)
    return rtnval


def extract_data_list(*, response: Response, action: str) -> List[Dict[str, Any]]:
    """
        Extract the ``data`` member from a Proxmox VE response and coerce it
        into a list of dictionaries.

        :param response: The :class:`Response` to parse.
        :param action: A short description of the attempted action.

        :returns: A list of dictionaries (empty when ``data`` is ``None``).
    """
    data = extract_data(response=response, action=action)

    rtnval: List[Dict[str, Any]] = []
    if data is None:
        return rtnval
    if isinstance(data, list):
        for entry in data:
            if isinstance(entry, dict):
                rtnval.append(entry)
        return rtnval

    return rtnval
