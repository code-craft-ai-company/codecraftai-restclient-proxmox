"""
    .. module:: proxmoxfirewallrulespec
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that contains the :class:`ProxmoxFirewallRuleSpec`
                   request spec for adding a firewall rule.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Automation Mojo LLC"
__credits__ = []


from typing import Any, Dict, Optional


class ProxmoxFirewallRuleSpec:
    """
        :class:`ProxmoxFirewallRuleSpec` packages the fields needed to add a
        firewall rule via a firewall ``/rules`` POST endpoint.
    """

    def __init__(self, *, action: str, rule_type: str,
                 enable: bool = True,
                 source: Optional[str] = None,
                 dest: Optional[str] = None,
                 proto: Optional[str] = None,
                 dport: Optional[str] = None,
                 comment: Optional[str] = None) -> None:
        """
            Initialize a :class:`ProxmoxFirewallRuleSpec` instance.

            :param action: The rule action (``ACCEPT``, ``DROP``, ...).
            :param rule_type: The rule type (``in`` or ``out``).
            :param enable: Whether the rule is enabled on creation.
            :param source: The source address/CIDR, or ``None``.
            :param dest: The destination address/CIDR, or ``None``.
            :param proto: The protocol, or ``None``.
            :param dport: The destination port specification, or ``None``.
            :param comment: A free-form comment, or ``None``.

            :returns: ``None``.
        """
        self.action = action
        self.rule_type = rule_type
        self.enable = enable
        self.source = source
        self.dest = dest
        self.proto = proto
        self.dport = dport
        self.comment = comment
        return

    def identity_tuple(self) -> tuple:
        """
            Return the rule-identity tuple used for idempotent add.

            :returns: A tuple of ``(rule_type, action, source, dest, proto,
                dport)``.
        """
        rtnval = (self.rule_type, self.action, self.source, self.dest,
                  self.proto, self.dport)
        return rtnval

    def to_params(self) -> Dict[str, Any]:
        """
            Render the spec into the Proxmox API form-parameter dictionary.

            :returns: A dictionary of rule parameters.
        """
        params: Dict[str, Any] = {}
        params["action"] = self.action
        params["type"] = self.rule_type
        if self.enable is True:
            params["enable"] = 1
        else:
            params["enable"] = 0
        if self.source is not None:
            params["source"] = self.source
        if self.dest is not None:
            params["dest"] = self.dest
        if self.proto is not None:
            params["proto"] = self.proto
        if self.dport is not None:
            params["dport"] = self.dport
        if self.comment is not None:
            params["comment"] = self.comment

        rtnval = params
        return rtnval
