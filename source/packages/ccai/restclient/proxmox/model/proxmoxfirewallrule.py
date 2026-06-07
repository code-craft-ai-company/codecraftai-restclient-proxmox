"""
    .. module:: proxmoxfirewallrule
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that contains the :class:`ProxmoxFirewallRule`
                   model describing a single firewall rule.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []


from typing import Any, Dict, Optional


class ProxmoxFirewallRule:
    """
        :class:`ProxmoxFirewallRule` is a typed view over a single firewall
        rule as returned by the firewall ``/rules`` endpoints.
    """

    def __init__(self, *, pos: int, action: str, rule_type: str,
                 enable: bool,
                 source: Optional[str] = None,
                 dest: Optional[str] = None,
                 proto: Optional[str] = None,
                 dport: Optional[str] = None,
                 comment: Optional[str] = None,
                 raw: Optional[Dict[str, Any]] = None) -> None:
        """
            Initialize a :class:`ProxmoxFirewallRule` instance.

            :param pos: The rule position index.
            :param action: The rule action (``ACCEPT``, ``DROP``, ...).
            :param rule_type: The rule type (``in`` or ``out``).
            :param enable: Whether the rule is enabled.
            :param source: The source address/CIDR, or ``None``.
            :param dest: The destination address/CIDR, or ``None``.
            :param proto: The protocol, or ``None``.
            :param dport: The destination port specification, or ``None``.
            :param comment: A free-form comment, or ``None``.
            :param raw: The raw response dictionary.

            :returns: ``None``.
        """
        self.pos = pos
        self.action = action
        self.rule_type = rule_type
        self.enable = enable
        self.source = source
        self.dest = dest
        self.proto = proto
        self.dport = dport
        self.comment = comment
        self.raw = raw if raw is not None else {}
        return

    def identity_tuple(self) -> tuple:
        """
            Return the rule-identity tuple used for idempotent add/delete.

            :returns: A tuple of ``(rule_type, action, source, dest, proto,
                dport)``.
        """
        rtnval = (self.rule_type, self.action, self.source, self.dest,
                  self.proto, self.dport)
        return rtnval

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProxmoxFirewallRule":
        """
            Construct a :class:`ProxmoxFirewallRule` from a response entry.

            :param data: The raw firewall rule dictionary.

            :returns: A populated :class:`ProxmoxFirewallRule`.
        """
        pos_raw = data.get("pos", 0)
        try:
            pos = int(pos_raw)
        except (TypeError, ValueError):
            pos = 0

        rtnval = cls(pos=pos, action=data.get("action", ""),
                     rule_type=data.get("type", ""),
                     enable=bool(data.get("enable", 1)),
                     source=data.get("source", None),
                     dest=data.get("dest", None),
                     proto=data.get("proto", None),
                     dport=data.get("dport", None),
                     comment=data.get("comment", None),
                     raw=dict(data))
        return rtnval
