"""Heuristic smurf score. Always a probability, never a certainty — expect false
positives. Signals: high rank on a low-level / hidden account, plus a hot streak.
"""

DIAMOND = 21  # competitiveTier for Diamond 1


def smurf_score(tier, account_level, winrate):
    score = 0
    reasons = []

    if account_level and account_level < 40:
        score += 40
        reasons.append(f"very low account level ({account_level})")
    elif account_level and account_level < 80:
        score += 20
        reasons.append(f"low account level ({account_level})")

    if tier >= DIAMOND and account_level and account_level < 120:
        score += 30
        reasons.append("high rank on a young account")

    if winrate is not None and winrate >= 0.75:
        score += 20
        reasons.append(f"{round(winrate * 100)}% recent win rate")

    if not account_level:  # hidden level is itself a mild signal
        score += 10
        reasons.append("account level hidden")

    score = min(score, 99)
    return {"score": score, "likely_smurf": score >= 50, "reasons": reasons}
