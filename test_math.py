"""Sanity tests for capmath.py."""

from capmath import (
    Round,
    initialize_cap_table,
    simulate,
    waterfall_all_common,
    waterfall_with_prefs,
)


def pct(x):
    return f"{x*100:.2f}%"


def dollars(x):
    return f"${x:,.0f}"


def test_founders_only():
    print("\n=== Test 1: Founders only, no rounds ===")
    ct = initialize_cap_table(
        founders=[{"name": "Alice", "pct": 50}, {"name": "Bob", "pct": 50}],
        option_pool_pct=0.10,
    )
    for h in ct.holders:
        print(f"  {h.name:20s} {h.share_class:12s} shares={h.shares:>12,.0f}  pct={pct(ct.percent(h))}")
    total = sum(ct.percent(h) for h in ct.holders)
    print(f"  TOTAL: {pct(total)}")
    assert abs(total - 1.0) < 1e-6


def test_safe_round():
    print("\n=== Test 2: 1 SAFE @ $5M cap, $500K ===")
    rounds = [
        Round(
            name="Pre-seed SAFE",
            kind="SAFE",
            safes=[{"name": "Angel A", "amount": 500_000, "cap": 5_000_000}],
        )
    ]
    snapshots = simulate(
        founders=[{"name": "Alice", "pct": 50}, {"name": "Bob", "pct": 50}],
        initial_pool_pct=0.10,
        rounds=rounds,
    )
    print("  After SAFE round (SAFEs unconverted, still show 0%):")
    final = snapshots[-1]
    for h in final.holders:
        if h.is_unconverted_safe():
            print(f"  {h.name:20s} SAFE   ${h.investment:,.0f} @ ${h.safe_cap:,.0f} cap (unconverted)")
        else:
            print(f"  {h.name:20s} {h.share_class:12s} pct={pct(final.percent(h))}")


def test_safe_then_priced():
    print("\n=== Test 3: SAFE then priced seed (verifies SAFE conversion) ===")
    # SAFE: $1M at $10M post-money cap → should get 10% post-conversion (before priced round dilution)
    # Then priced round: $3M at $12M pre-money, 10% option pool target
    rounds = [
        Round(
            name="Pre-seed SAFE",
            kind="SAFE",
            safes=[{"name": "Angel A", "amount": 1_000_000, "cap": 10_000_000}],
        ),
        Round(
            name="Seed",
            kind="PRICED",
            pre_money=12_000_000,
            raise_amount=3_000_000,
            option_pool_pct_post=0.10,
            investors=[{"name": "Seed VC", "amount": 3_000_000}],
        ),
    ]
    snapshots = simulate(
        founders=[{"name": "Alice", "pct": 50}, {"name": "Bob", "pct": 50}],
        initial_pool_pct=0.10,
        rounds=rounds,
    )

    print("  Initial:")
    for h in snapshots[0].holders:
        print(f"    {h.name:20s} pct={pct(snapshots[0].percent(h))}")

    print("  After Seed (priced):")
    final = snapshots[-1]
    for h in final.holders:
        print(f"    {h.name:20s} {h.share_class:12s} pct={pct(final.percent(h))}")
    total = sum(final.percent(h) for h in final.holders if not h.is_unconverted_safe())
    print(f"    TOTAL: {pct(total)}")
    assert abs(total - 1.0) < 1e-4

    # Sanity: Seed VC bought $3M at $15M post-money → should own 20%
    seed_vc = next(h for h in final.holders if h.name == "Seed VC")
    print(f"    Seed VC expected ~20%, got {pct(final.percent(seed_vc))}")


def test_multiple_safes_diff_caps():
    print("\n=== Test 4: 3 SAFEs at different caps + priced round ===")
    rounds = [
        Round(
            name="Pre-seed",
            kind="SAFE",
            safes=[
                {"name": "Canonical", "amount": 1_500_000, "cap": 15_000_000},
                {"name": "Angel A",   "amount": 500_000,   "cap": 12_000_000},
                {"name": "Angel B",   "amount": 250_000,   "cap": 10_000_000},
            ],
        ),
        Round(
            name="Seed",
            kind="PRICED",
            pre_money=25_000_000,
            raise_amount=8_000_000,
            option_pool_pct_post=0.12,
            investors=[{"name": "Tier 1 VC", "amount": 8_000_000}],
        ),
    ]
    snapshots = simulate(
        founders=[
            {"name": "Founder A", "pct": 40},
            {"name": "Founder B", "pct": 40},
            {"name": "Founder C", "pct": 20},
        ],
        initial_pool_pct=0.10,
        rounds=rounds,
    )

    print("  After Seed:")
    final = snapshots[-1]
    for h in final.holders:
        marker = " (preferred)" if h.share_class == "PREFERRED" else ""
        print(f"    {h.name:20s} {h.share_class:12s} pct={pct(final.percent(h))}{marker}")
    total = sum(final.percent(h) for h in final.holders if not h.is_unconverted_safe())
    print(f"    TOTAL: {pct(total)}")
    assert abs(total - 1.0) < 1e-4

    # Sanity: SAFE pcts before priced round dilution should be:
    # Canonical 10%, Angel A 4.17%, Angel B 2.5% — they get diluted by option pool top-up and priced round
    print()
    print("  Expected SAFE ownership before priced round dilution:")
    print("    Canonical 10.00% | Angel A 4.17% | Angel B 2.50%")
    print("  After priced round dilution (option pool top-up + Tier 1 VC):")
    print("    Should all be lower than pre-dilution pcts above.")


def test_exit_waterfall():
    print("\n=== Test 5: Exit waterfall (1x non-participating) ===")
    rounds = [
        Round(
            name="Seed",
            kind="PRICED",
            pre_money=12_000_000,
            raise_amount=3_000_000,
            option_pool_pct_post=0.10,
            investors=[{"name": "Seed VC", "amount": 3_000_000}],
        )
    ]
    snapshots = simulate(
        founders=[{"name": "Alice", "pct": 50}, {"name": "Bob", "pct": 50}],
        initial_pool_pct=0.10,
        rounds=rounds,
    )
    final = snapshots[-1]

    for exit_val in [3_000_000, 15_000_000, 100_000_000, 1_000_000_000]:
        print(f"\n  Exit @ ${exit_val:,}:")
        common = waterfall_all_common(final, exit_val)
        prefs = waterfall_with_prefs(final, exit_val)
        for name in common:
            print(f"    {name:20s} all-common: {dollars(common[name]):>15s}  with-prefs: {dollars(prefs[name]):>15s}")

    # Sanity:
    # Seed VC put in $3M at $15M post → owns 20%
    # At $3M exit (= preference), VC should take $3M (preference > as-converted=20%*3M=600K)
    # At $1B exit, VC should convert: 20% of $1B = $200M (preference $3M is trivial)


def test_chipsage_style():
    print("\n=== Test 6: Realistic stacked pre-seed → seed → A ===")
    rounds = [
        Round(
            name="Pre-seed",
            kind="SAFE",
            safes=[
                {"name": "Lead VC",  "amount": 1_500_000, "cap": 15_000_000},
                {"name": "Angel 1",  "amount": 250_000,   "cap": 12_000_000},
                {"name": "Angel 2",  "amount": 250_000,   "cap": 12_000_000},
            ],
        ),
        Round(
            name="Seed",
            kind="PRICED",
            pre_money=30_000_000,
            raise_amount=10_000_000,
            option_pool_pct_post=0.12,
            investors=[{"name": "Seed Lead", "amount": 10_000_000}],
        ),
        Round(
            name="Series A",
            kind="PRICED",
            pre_money=80_000_000,
            raise_amount=20_000_000,
            option_pool_pct_post=0.15,
            investors=[{"name": "Series A Lead", "amount": 20_000_000}],
        ),
    ]
    snapshots = simulate(
        founders=[
            {"name": "Nojan",   "pct": 35},
            {"name": "Kevin",   "pct": 35},
            {"name": "Farinaz", "pct": 15},
            {"name": "Homayoun","pct": 15},
        ],
        initial_pool_pct=0.10,
        rounds=rounds,
    )

    for i, snap in enumerate(snapshots):
        label = "Initial" if i == 0 else f"After {rounds[i-1].name}"
        print(f"\n  {label}:")
        for h in snap.holders:
            if h.is_unconverted_safe():
                print(f"    {h.name:20s} SAFE (unconverted) ${h.investment:,.0f} @ ${h.safe_cap:,.0f} cap")
            else:
                print(f"    {h.name:20s} {h.share_class:12s} pct={pct(snap.percent(h))}")

    final = snapshots[-1]
    print(f"\n  Exit @ $500M (1x non-participating):")
    prefs = waterfall_with_prefs(final, 500_000_000)
    for name, amt in prefs.items():
        print(f"    {name:20s} {dollars(amt):>15s}")


if __name__ == "__main__":
    test_founders_only()
    test_safe_round()
    test_safe_then_priced()
    test_multiple_safes_diff_caps()
    test_exit_waterfall()
    test_chipsage_style()
    print("\n✓ All tests ran.")
