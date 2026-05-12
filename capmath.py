"""
Dilution Lab — cap table math.

Approach:
- Track shares (integers) per shareholder, never percentages.
- Each shareholder has a class: COMMON, OPTION_POOL, SAFE (unconverted), PREFERRED.
- Rounds are processed in order. Each round mutates the cap table.
- For SAFE rounds: SAFEs are added as pending; they do NOT dilute anyone until conversion.
- For priced rounds: SAFEs convert first (post-money cap math), then option pool top-up,
  then new investors purchase shares.
- Liquidation prefs assumed 1x non-participating on all PREFERRED (incl. converted SAFEs).
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Literal
import copy

INITIAL_SHARES = 10_000_000  # founder common pool baseline

ShareClass = Literal["COMMON", "OPTION_POOL", "SAFE", "PREFERRED"]


@dataclass
class Holder:
    name: str
    share_class: ShareClass
    shares: float = 0.0
    # For preferred/SAFE: liquidation preference $ (1x of money invested)
    investment: float = 0.0
    # For unconverted SAFEs only:
    safe_cap: float = 0.0  # post-money valuation cap
    # Bookkeeping
    round_origin: str = ""

    def is_unconverted_safe(self) -> bool:
        return self.share_class == "SAFE"


@dataclass
class Round:
    name: str
    kind: Literal["SAFE", "PRICED"]
    # For SAFE round: list of {name, amount, cap}
    safes: List[Dict] = field(default_factory=list)
    # For priced round:
    pre_money: float = 0.0
    raise_amount: float = 0.0
    option_pool_pct_post: float = 0.10  # target post-round option pool %
    investors: List[Dict] = field(default_factory=list)  # {name, amount}


@dataclass
class CapTable:
    holders: List[Holder] = field(default_factory=list)

    def total_outstanding_shares(self) -> float:
        """Outstanding shares = everything except unconverted SAFEs."""
        return sum(h.shares for h in self.holders if not h.is_unconverted_safe())

    def total_fully_diluted(self) -> float:
        """Fully diluted = everything, treating SAFE shares as already issued."""
        return sum(h.shares for h in self.holders)

    def percent(self, holder: Holder) -> float:
        total = self.total_outstanding_shares()
        if total == 0:
            return 0.0
        if holder.is_unconverted_safe():
            return 0.0  # SAFEs don't show as % until converted
        return holder.shares / total

    def clone(self) -> "CapTable":
        return copy.deepcopy(self)


def initialize_cap_table(
    founders: List[Dict],  # [{name, pct}, ...] summing to 100
    option_pool_pct: float = 0.10,
) -> CapTable:
    """Initialize with founders + reserved option pool. Founders+pool = 100%."""
    ct = CapTable()
    # Reserve option pool first, then split remaining among founders by their relative pct
    pool_shares = INITIAL_SHARES * option_pool_pct
    founder_shares_total = INITIAL_SHARES - pool_shares
    total_pct = sum(f["pct"] for f in founders)
    if total_pct == 0:
        total_pct = 1
    for f in founders:
        ct.holders.append(
            Holder(
                name=f["name"],
                share_class="COMMON",
                shares=founder_shares_total * (f["pct"] / total_pct),
                round_origin="Founding",
            )
        )
    if pool_shares > 0:
        ct.holders.append(
            Holder(
                name="Option Pool",
                share_class="OPTION_POOL",
                shares=pool_shares,
                round_origin="Founding",
            )
        )
    return ct


def apply_safe_round(ct: CapTable, rnd: Round) -> None:
    """Add SAFEs as unconverted holders. They sit until next priced round."""
    for safe in rnd.safes:
        ct.holders.append(
            Holder(
                name=safe["name"],
                share_class="SAFE",
                shares=0.0,
                investment=float(safe["amount"]),
                safe_cap=float(safe["cap"]),
                round_origin=rnd.name,
            )
        )


def apply_priced_round(ct: CapTable, rnd: Round) -> None:
    """
    Order of operations for a priced round:
      1. Convert all outstanding SAFEs (post-money cap math).
         Each SAFE owns (investment / cap) of the cap table AFTER all SAFEs convert
         but BEFORE option pool top-up and new investor shares.
         Multiple post-money SAFEs do NOT dilute each other — founders absorb.
      2. Top up option pool to target post-round %. The top-up is sized so that
         after the new round closes, the option pool = target %. Top-up dilutes
         all existing (including freshly converted SAFEs) — i.e., it's "pre-money."
      3. New priced investors buy shares: investor_shares such that
         investor_amount / (pre_money + raise) = investor_shares / total_post.
         Equivalently: new shares issued for the round = (raise/pre_money) * pre_shares.
    """

    # ---- STEP 1: Convert SAFEs ----
    unconverted_safes = [h for h in ct.holders if h.is_unconverted_safe()]
    existing_non_safe_shares = sum(
        h.shares for h in ct.holders if not h.is_unconverted_safe()
    )

    if unconverted_safes:
        # Each SAFE locks in pct = investment / cap of the post-SAFE-conversion cap table.
        # Sum of SAFE pcts:
        total_safe_pct = sum(s.investment / s.safe_cap for s in unconverted_safes)
        if total_safe_pct >= 1.0:
            # Edge case: SAFEs would own >= 100%. Cap at 99% for sanity.
            total_safe_pct = 0.99

        # Post-SAFE-conversion total shares: existing non-SAFE shares = (1 - total_safe_pct) of new total
        # => new_total = existing / (1 - total_safe_pct)
        new_total_after_safes = existing_non_safe_shares / (1.0 - total_safe_pct)

        for s in unconverted_safes:
            pct = s.investment / s.safe_cap
            s.shares = new_total_after_safes * pct
            s.share_class = "PREFERRED"  # converted SAFE becomes preferred
            # investment carried forward as 1x liquidation pref

    # Recompute current shares
    pre_round_shares = sum(h.shares for h in ct.holders)

    # ---- STEP 2: Option pool top-up (pre-money) ----
    target_pool_pct_post = rnd.option_pool_pct_post
    # The pool top-up should result in pool being target_pool_pct_post of POST-money cap table.
    # Post-money cap table = pre_round_shares + pool_top_up + new_investor_shares.
    # New_investor_shares = (raise / pre_money) * (pre_round_shares + pool_top_up).
    # Let:
    #   P = current pool shares (pre top-up)
    #   T = pool top-up
    #   S = pre_round_shares (current total, includes P)
    #   raise/pre_money = r
    # Post-money total = (S + T) * (1 + r)
    # Pool after = P + T
    # We want (P + T) / [(S + T) * (1 + r)] = target_pool_pct_post
    # => (P + T) = target_pool_pct_post * (S + T) * (1 + r)
    # Solve for T:
    # (P + T) = target * (1+r) * S + target * (1+r) * T
    # T - target*(1+r)*T = target*(1+r)*S - P
    # T * (1 - target*(1+r)) = target*(1+r)*S - P
    # T = (target*(1+r)*S - P) / (1 - target*(1+r))
    current_pool = next(
        (h.shares for h in ct.holders if h.share_class == "OPTION_POOL"), 0.0
    )
    pool_holder = next(
        (h for h in ct.holders if h.share_class == "OPTION_POOL"), None
    )

    if rnd.pre_money > 0:
        r = rnd.raise_amount / rnd.pre_money
    else:
        r = 0

    denom = 1.0 - target_pool_pct_post * (1 + r)
    if denom <= 0:
        top_up = 0.0
    else:
        top_up = (target_pool_pct_post * (1 + r) * pre_round_shares - current_pool) / denom
    top_up = max(top_up, 0.0)

    if top_up > 0:
        if pool_holder is None:
            pool_holder = Holder(
                name="Option Pool",
                share_class="OPTION_POOL",
                shares=0.0,
                round_origin=rnd.name,
            )
            ct.holders.append(pool_holder)
        pool_holder.shares += top_up

    # Updated pre-money shares after top-up
    pre_money_shares = sum(h.shares for h in ct.holders)

    # ---- STEP 3: New investors ----
    if rnd.pre_money > 0 and rnd.raise_amount > 0:
        # Price per share = pre_money / pre_money_shares
        price_per_share = rnd.pre_money / pre_money_shares
        for inv in rnd.investors:
            inv_shares = inv["amount"] / price_per_share
            ct.holders.append(
                Holder(
                    name=inv["name"],
                    share_class="PREFERRED",
                    shares=inv_shares,
                    investment=float(inv["amount"]),
                    round_origin=rnd.name,
                )
            )


def apply_round(ct: CapTable, rnd: Round) -> None:
    if rnd.kind == "SAFE":
        apply_safe_round(ct, rnd)
    elif rnd.kind == "PRICED":
        apply_priced_round(ct, rnd)


def simulate(
    founders: List[Dict],
    initial_pool_pct: float,
    rounds: List[Round],
) -> List[CapTable]:
    """Return list of cap tables: [initial, after_round_1, after_round_2, ...]"""
    ct = initialize_cap_table(founders, initial_pool_pct)
    snapshots = [ct.clone()]
    for rnd in rounds:
        apply_round(ct, rnd)
        snapshots.append(ct.clone())
    return snapshots


# =========================================================================
# Exit waterfall
# =========================================================================


def waterfall_all_common(ct: CapTable, exit_value: float) -> Dict[str, float]:
    """Pro-rata distribution — everyone converts to common."""
    # Convert any remaining unconverted SAFEs at face: treat each as preferred with 0 pref
    total = ct.total_outstanding_shares()
    if total == 0:
        return {h.name: 0.0 for h in ct.holders}
    out = {}
    for h in ct.holders:
        if h.is_unconverted_safe():
            # Treat as "would convert at exit pro-rata" — fallback: zero
            out[h.name] = 0.0
        else:
            out[h.name] = exit_value * (h.shares / total)
    return out


def waterfall_with_prefs(ct: CapTable, exit_value: float) -> Dict[str, float]:
    """
    1x non-participating preferred:
      Each preferred holder takes MAX(preference, as-converted pro-rata).
      Iterate to converge: if a preferred takes preference, those shares come off the table.
    """
    # Start with all preferred "as-converted"
    holders = ct.holders
    # Build state: for each preferred, decide convert or take pref
    take_pref = {id(h): False for h in holders if h.share_class == "PREFERRED"}

    # Iterate until stable
    for _ in range(50):  # bounded iterations
        # Compute remaining-for-common pool
        # Holders taking pref: get their investment back, remove from common pool
        pref_payouts = 0.0
        for h in holders:
            if h.share_class == "PREFERRED" and take_pref[id(h)]:
                pref_payouts += h.investment

        remaining = max(exit_value - pref_payouts, 0.0)

        # Shares in the "common pool" = all common + all option pool + all preferred who are converting
        common_shares = 0.0
        for h in holders:
            if h.is_unconverted_safe():
                continue
            if h.share_class == "PREFERRED" and take_pref[id(h)]:
                continue
            common_shares += h.shares

        # For each preferred, evaluate: should they take pref or convert?
        changed = False
        for h in holders:
            if h.share_class != "PREFERRED":
                continue
            # as-converted payout if they convert
            if not take_pref[id(h)]:
                # They are currently in common_shares
                as_converted = remaining * (h.shares / common_shares) if common_shares > 0 else 0
            else:
                # Hypothetical: if they joined common
                as_converted = (remaining + h.investment) * (
                    h.shares / (common_shares + h.shares)
                ) if (common_shares + h.shares) > 0 else 0

            preference = h.investment
            wants_pref = preference > as_converted

            if wants_pref != take_pref[id(h)]:
                take_pref[id(h)] = wants_pref
                changed = True

        if not changed:
            break

    # Final allocation
    pref_payouts = 0.0
    for h in holders:
        if h.share_class == "PREFERRED" and take_pref[id(h)]:
            pref_payouts += h.investment
    remaining = max(exit_value - pref_payouts, 0.0)

    common_shares = 0.0
    for h in holders:
        if h.is_unconverted_safe():
            continue
        if h.share_class == "PREFERRED" and take_pref[id(h)]:
            continue
        common_shares += h.shares

    out = {}
    for h in holders:
        if h.is_unconverted_safe():
            out[h.name] = 0.0
        elif h.share_class == "PREFERRED" and take_pref[id(h)]:
            out[h.name] = h.investment
        else:
            out[h.name] = (
                remaining * (h.shares / common_shares) if common_shares > 0 else 0
            )
    return out
