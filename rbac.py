"""Role-based access control: injects a scope WHERE clause by role.

  SHO  -> own police station (Unit)
  DCP  -> own district
  ADGP -> whole state (no restriction)

Each role carries a scope value (unit name or district name). The engine resolves
that to the relevant CaseMaster filter and appends it to every query. The same
scope string is recorded in the audit log so it is auditable.
"""
from __future__ import annotations

from dataclasses import dataclass

from .db import query

ROLES = ("SHO", "DCP", "ADGP")


@dataclass
class User:
    username: str
    role: str
    scope_value: str  # unit name for SHO, district name for DCP, "Karnataka" for ADGP

    @property
    def scope_label(self) -> str:
        if self.role == "SHO":
            return f"Station: {self.scope_value}"
        if self.role == "DCP":
            return f"District: {self.scope_value}"
        return "State: Karnataka (full access)"


# Demo users for the login screen.
DEMO_USERS = {
    "sho_koramangala": User("sho_koramangala", "SHO", "Koramangala PS"),
    "dcp_bengaluru": User("dcp_bengaluru", "DCP", "Bengaluru City"),
    "adgp_state": User("adgp_state", "ADGP", "Karnataka"),
}


def resolve_unit_ids(user: User) -> list[int] | None:
    """Return the list of UnitIDs in scope, or None for unrestricted (ADGP)."""
    if user.role == "ADGP":
        return None
    if user.role == "SHO":
        rows = query("SELECT UnitID FROM Unit WHERE UnitName = ?", (user.scope_value,))
        return [r["UnitID"] for r in rows]
    if user.role == "DCP":
        rows = query(
            """SELECT u.UnitID FROM Unit u JOIN District d ON u.DistrictID = d.DistrictID
               WHERE d.DistrictName = ?""",
            (user.scope_value,),
        )
        return [r["UnitID"] for r in rows]
    return []


def scope_where(user: User, case_alias: str = "cm") -> tuple[str, list]:
    """Build a ' AND <alias>.PoliceStationID IN (...)' clause for the user's scope.

    Returns (clause, params). For ADGP returns ('', []).
    """
    unit_ids = resolve_unit_ids(user)
    if unit_ids is None:
        return "", []
    if not unit_ids:
        # No matching units -> force empty result.
        return f" AND {case_alias}.PoliceStationID IN (-1)", []
    placeholders = ",".join("?" for _ in unit_ids)
    return f" AND {case_alias}.PoliceStationID IN ({placeholders})", list(unit_ids)
