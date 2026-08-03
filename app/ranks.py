# Valorant competitiveTier integers -> readable rank names.
# Tiers start at 3 (Iron 1). 0 = Unranked. Values step in groups of 3.

_GROUPS = [
    "Iron",
    "Bronze",
    "Silver",
    "Gold",
    "Platinum",
    "Diamond",
    "Ascendant",
    "Immortal",
    "Radiant",
]


def rank_name(tier):
    if not tier or tier < 3:
        return "Unranked"
    group = (tier - 3) // 3
    sub = (tier - 3) % 3 + 1
    if group >= len(_GROUPS):
        return "Radiant"
    name = _GROUPS[group]
    if name == "Radiant":
        return "Radiant"
    return f"{name} {sub}"
