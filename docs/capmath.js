// Dilution Lab — cap table math (ported from capmath.py)
// Track shares, not percentages. Post-money SAFE math. 1x non-participating preferred.

const INITIAL_SHARES = 10_000_000;

// ----- Holder factory -----
function makeHolder({ name, shareClass, shares = 0, investment = 0, safeCap = 0, roundOrigin = "" }) {
  return { name, shareClass, shares, investment, safeCap, roundOrigin };
}

function isUnconvertedSafe(h) {
  return h.shareClass === "SAFE";
}

function totalOutstandingShares(ct) {
  return ct.holders.reduce((s, h) => isUnconvertedSafe(h) ? s : s + h.shares, 0);
}

function holderPercent(ct, h) {
  if (isUnconvertedSafe(h)) return 0;
  const total = totalOutstandingShares(ct);
  return total === 0 ? 0 : h.shares / total;
}

function cloneCapTable(ct) {
  return { holders: ct.holders.map(h => ({ ...h })) };
}

// ----- Initialize -----
function initializeCapTable(founders, optionPoolPct) {
  const ct = { holders: [] };
  const poolShares = INITIAL_SHARES * optionPoolPct;
  const founderSharesTotal = INITIAL_SHARES - poolShares;
  const totalPct = founders.reduce((s, f) => s + f.pct, 0) || 1;

  for (const f of founders) {
    ct.holders.push(makeHolder({
      name: f.name,
      shareClass: "COMMON",
      shares: founderSharesTotal * (f.pct / totalPct),
      roundOrigin: "Founding",
    }));
  }
  if (poolShares > 0) {
    ct.holders.push(makeHolder({
      name: "Option Pool",
      shareClass: "OPTION_POOL",
      shares: poolShares,
      roundOrigin: "Founding",
    }));
  }
  return ct;
}

// ----- SAFE round: just add as unconverted -----
function applySafeRound(ct, rnd) {
  for (const safe of rnd.safes) {
    ct.holders.push(makeHolder({
      name: safe.name,
      shareClass: "SAFE",
      shares: 0,
      investment: Number(safe.amount),
      safeCap: Number(safe.cap),
      roundOrigin: rnd.name,
    }));
  }
}

// ----- Priced round: convert SAFEs, top up pool, issue new shares -----
function applyPricedRound(ct, rnd) {
  // 1. Convert all outstanding SAFEs (post-money math).
  const unconverted = ct.holders.filter(isUnconvertedSafe);
  const existingNonSafeShares = ct.holders.reduce(
    (s, h) => isUnconvertedSafe(h) ? s : s + h.shares, 0
  );

  if (unconverted.length > 0) {
    let totalSafePct = unconverted.reduce((s, x) => s + x.investment / x.safeCap, 0);
    if (totalSafePct >= 1) totalSafePct = 0.99;
    const newTotalAfterSafes = existingNonSafeShares / (1 - totalSafePct);
    for (const s of unconverted) {
      const pct = s.investment / s.safeCap;
      s.shares = newTotalAfterSafes * pct;
      s.shareClass = "PREFERRED";
    }
  }

  // 2. Option pool top-up (pre-money) sized to target post-round %.
  const preRoundShares = ct.holders.reduce((s, h) => s + h.shares, 0);
  const target = rnd.optionPoolPctPost;
  const r = rnd.preMoney > 0 ? rnd.raiseAmount / rnd.preMoney : 0;

  let pool = ct.holders.find(h => h.shareClass === "OPTION_POOL");
  const currentPool = pool ? pool.shares : 0;

  const denom = 1 - target * (1 + r);
  let topUp = 0;
  if (denom > 0) {
    topUp = (target * (1 + r) * preRoundShares - currentPool) / denom;
  }
  topUp = Math.max(topUp, 0);

  if (topUp > 0) {
    if (!pool) {
      pool = makeHolder({ name: "Option Pool", shareClass: "OPTION_POOL", shares: 0, roundOrigin: rnd.name });
      ct.holders.push(pool);
    }
    pool.shares += topUp;
  }

  // 3. New priced investors.
  const preMoneyShares = ct.holders.reduce((s, h) => s + h.shares, 0);
  if (rnd.preMoney > 0 && rnd.raiseAmount > 0) {
    const pricePerShare = rnd.preMoney / preMoneyShares;
    for (const inv of rnd.investors) {
      const invShares = inv.amount / pricePerShare;
      ct.holders.push(makeHolder({
        name: inv.name,
        shareClass: "PREFERRED",
        shares: invShares,
        investment: Number(inv.amount),
        roundOrigin: rnd.name,
      }));
    }
  }
}

function applyRound(ct, rnd) {
  if (rnd.kind === "SAFE") applySafeRound(ct, rnd);
  else if (rnd.kind === "PRICED") applyPricedRound(ct, rnd);
}

function simulate(founders, initialPoolPct, rounds) {
  const ct = initializeCapTable(founders, initialPoolPct);
  const snapshots = [cloneCapTable(ct)];
  for (const rnd of rounds) {
    applyRound(ct, rnd);
    snapshots.push(cloneCapTable(ct));
  }
  return snapshots;
}

// ----- Exit waterfall: all common (pro-rata) -----
function waterfallAllCommon(ct, exitValue) {
  const total = totalOutstandingShares(ct);
  const out = {};
  if (total === 0) {
    for (const h of ct.holders) out[h.name] = 0;
    return out;
  }
  for (const h of ct.holders) {
    out[h.name] = isUnconvertedSafe(h) ? 0 : exitValue * (h.shares / total);
  }
  return out;
}

// ----- Exit waterfall: 1x non-participating preferred -----
function waterfallWithPrefs(ct, exitValue) {
  const holders = ct.holders;
  const takePref = new Map();
  for (const h of holders) if (h.shareClass === "PREFERRED") takePref.set(h, false);

  for (let iter = 0; iter < 50; iter++) {
    let prefPayouts = 0;
    for (const h of holders) {
      if (h.shareClass === "PREFERRED" && takePref.get(h)) prefPayouts += h.investment;
    }
    const remaining = Math.max(exitValue - prefPayouts, 0);

    let commonShares = 0;
    for (const h of holders) {
      if (isUnconvertedSafe(h)) continue;
      if (h.shareClass === "PREFERRED" && takePref.get(h)) continue;
      commonShares += h.shares;
    }

    let changed = false;
    for (const h of holders) {
      if (h.shareClass !== "PREFERRED") continue;
      let asConverted;
      if (!takePref.get(h)) {
        asConverted = commonShares > 0 ? remaining * (h.shares / commonShares) : 0;
      } else {
        const denom = commonShares + h.shares;
        asConverted = denom > 0 ? (remaining + h.investment) * (h.shares / denom) : 0;
      }
      const wantsPref = h.investment > asConverted;
      if (wantsPref !== takePref.get(h)) {
        takePref.set(h, wantsPref);
        changed = true;
      }
    }
    if (!changed) break;
  }

  let prefPayouts = 0;
  for (const h of holders) {
    if (h.shareClass === "PREFERRED" && takePref.get(h)) prefPayouts += h.investment;
  }
  const remaining = Math.max(exitValue - prefPayouts, 0);

  let commonShares = 0;
  for (const h of holders) {
    if (isUnconvertedSafe(h)) continue;
    if (h.shareClass === "PREFERRED" && takePref.get(h)) continue;
    commonShares += h.shares;
  }

  const out = {};
  for (const h of holders) {
    if (isUnconvertedSafe(h)) out[h.name] = 0;
    else if (h.shareClass === "PREFERRED" && takePref.get(h)) out[h.name] = h.investment;
    else out[h.name] = commonShares > 0 ? remaining * (h.shares / commonShares) : 0;
  }
  return out;
}

// Export to global scope for browser
window.CapMath = {
  INITIAL_SHARES,
  initializeCapTable,
  applyRound,
  simulate,
  waterfallAllCommon,
  waterfallWithPrefs,
  totalOutstandingShares,
  holderPercent,
  isUnconvertedSafe,
};
