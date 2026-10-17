#!/usr/bin/env python3
"""
Liquid Inference vs OpenRouter price and latency tracker.

Every tick (default 60 s) it:
  1. Pulls OpenRouter's public model list and per-model endpoints.
  2. Pulls Liquid Inference's public offers book.
  3. Optionally pulls Liquid's signed-in quotes and throughput views
     (set LIQUID_API_KEY; a key with the `list` scope is enough).
  4. Matches the configured top-30 models across both sites.
  5. Writes:
       out/history.csv      one row per model per tick (append only)
       out/latest.json      the full latest comparison
       out/latest.md        a readable table of the latest tick
       out/changes.log      a line whenever a model's price gap changes
       out/raw/<ts>/*.json  raw API responses for that tick

Prices are normalised to USD per million tokens.
Latency columns are NOT like for like:
  Liquid  ttft_ms / completion_ms are committed ceilings per offer.
  OpenRouter latency/throughput are measured p50s, when exposed.

Usage:
  python3 li_vs_or.py --once
  python3 li_vs_or.py --interval 60
  LIQUID_API_KEY=sk-... python3 li_vs_or.py --interval 60
"""

import argparse
import csv
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

OR_BASE = "https://openrouter.ai/api/v1"
LI_BASE = "https://router.inference.ai.exchange/v1"
HERE = Path(__file__).resolve().parent
OUT = HERE / "out"
MODELS_FILE = HERE / "models.json"

HISTORY_COLS = [
    "ts_utc", "rank", "openrouter_id", "liquid_model",
    "or_input_usd_mtok", "or_output_usd_mtok", "or_blended_usd_mtok", "or_cheapest_provider",
    "or_latency_p50_s", "or_throughput_tps", "or_endpoint_count",
    "li_input_usd_mtok", "li_output_usd_mtok", "li_blended_usd_mtok", "li_offer_count",
    "li_ttft_ms_ceiling", "li_completion_ms_ceiling", "li_region",
    "li_provider", "li_measured_tps",
    "input_diff_usd_mtok", "output_diff_usd_mtok", "blended_diff_usd_mtok",
    "input_pct_vs_or", "output_pct_vs_or", "blended_pct_vs_or", "cheaper_on", "status",
]


# ----------------------------------------------------------------- helpers

def now_utc():
    return datetime.now(timezone.utc)


def get_json(url, headers=None, timeout=30):
    req = urllib.request.Request(url, headers={
        "User-Agent": "li-vs-or-tracker/1.0",
        "Accept": "application/json",
        **(headers or {}),
    })
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def per_mtok(per_token_str):
    """OpenRouter prices are USD per token as strings. -1 means dynamic."""
    try:
        v = float(per_token_str)
    except (TypeError, ValueError):
        return None
    if v < 0:
        return None
    return v * 1_000_000


def norm(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def fmt(v, nd=4):
    if v is None:
        return ""
    if isinstance(v, float):
        return f"{v:.{nd}f}".rstrip("0").rstrip(".") if nd else f"{v:.0f}"
    return str(v)


def blended(inp, out, in_share):
    """Blended USD per million tokens at a given input share (0..1)."""
    if inp is None or out is None:
        return None
    return inp * in_share + out * (1 - in_share)


def pct(a, b):
    """(a - b) / b * 100, None if b is missing or zero."""
    if a is None or b in (None, 0):
        return None
    return (a - b) / b * 100.0


# ------------------------------------------------------------ data fetches

def fetch_openrouter(model_ids):
    models = get_json(f"{OR_BASE}/models")["data"]
    by_id = {m["id"]: m for m in models}
    endpoints = {}
    for mid in model_ids:
        slug = mid.split(":")[0]  # endpoints route ignores :free etc.
        try:
            endpoints[mid] = get_json(f"{OR_BASE}/models/{slug}/endpoints")["data"]
        except Exception as e:  # noqa: BLE001
            endpoints[mid] = {"error": str(e)}
    return by_id, endpoints


def fetch_liquid(api_key=None):
    offers = get_json(f"{LI_BASE}/exchange/offers")
    quotes, throughput = None, None
    if api_key:
        h = {"Authorization": f"Bearer {api_key}"}
        for name, url in (("quotes", f"{LI_BASE}/exchange/quotes?window_secs=3600"),
                          ("throughput", f"{LI_BASE}/exchange/throughput")):
            try:
                data = get_json(url, headers=h)
            except urllib.error.HTTPError as e:
                data = {"error": f"HTTP {e.code}"}
            except Exception as e:  # noqa: BLE001
                data = {"error": str(e)}
            if name == "quotes":
                quotes = data
            else:
                throughput = data
    return offers, quotes, throughput


# --------------------------------------------------------------- matching

def liquid_match(or_id, liquid_markets, overrides):
    """Return the Liquid market name for an OpenRouter id, or None."""
    if or_id in overrides:
        return overrides[or_id] or None
    base = or_id.split("/", 1)[1].split(":")[0]
    n = norm(base)
    for m in liquid_markets:
        if norm(m.split("/")[-1]) == n:
            return m
    return None


def best_liquid_offer(offers, market, in_share):
    """Cheapest non-synthetic chat offer by blended cost at in_share."""
    cands = [o for o in offers
             if o.get("market") == market
             and not o.get("synthetic")
             and (o.get("kind") in (None, "chat"))
             and o.get("rate_generation_usd_per_mtok") is not None]
    if not cands:
        return None, 0
    cands.sort(key=lambda o: blended(o.get("rate_uncached_input_usd_per_mtok") or 0,
                                     o["rate_generation_usd_per_mtok"], in_share))
    return cands[0], len(cands)


def best_or_endpoint(ep_data, in_share):
    """Cheapest live endpoint by blended cost at in_share."""
    eps = (ep_data or {}).get("endpoints") or []
    live = [e for e in eps if e.get("status", 0) in (0, None)]
    if not live:
        return None, len(eps)
    def key(e):
        p = e.get("pricing") or {}
        b = blended(per_mtok(p.get("prompt")), per_mtok(p.get("completion")), in_share)
        return b if b is not None else 1e9
    live.sort(key=key)
    return live[0], len(eps)


def liquid_signed_in_view(quotes, throughput, market):
    """Best-effort extraction of provider name and measured tok/s.

    The quotes/throughput schemas are undocumented, so this scans for rows
    whose model or market field matches and pulls common field names.
    Raw payloads are always saved, so nothing is lost if this misses.
    """
    provider, tps = None, None

    def rows(obj):
        if isinstance(obj, list):
            return obj
        if isinstance(obj, dict):
            for k in ("data", "quotes", "rows", "items", "models"):
                if isinstance(obj.get(k), list):
                    return obj[k]
        return []

    for src in (quotes, throughput):
        for r in rows(src):
            if not isinstance(r, dict):
                continue
            name = r.get("market") or r.get("model") or r.get("served_model")
            if name != market:
                continue
            provider = provider or r.get("provider") or r.get("provider_slug") \
                or r.get("provider_name")
            for k in ("tokens_per_second", "tps", "tok_s", "throughput_tps",
                      "generation_tps", "output_tps"):
                if r.get(k) is not None:
                    tps = r[k]
                    break
            if provider and tps is not None:
                return provider, tps
    return provider, tps


# ------------------------------------------------------------------ tick

def run_tick(cfg, api_key, keep_raw=True):
    ts = now_utc()
    ts_s = ts.strftime("%Y-%m-%dT%H:%M:%SZ")
    model_ids = cfg["models"]
    overrides = cfg.get("liquid_overrides", {})
    in_share = float(cfg.get("blend_input_share", 0.75))

    or_by_id, or_eps = fetch_openrouter(model_ids)
    li_offers, li_quotes, li_tp = fetch_liquid(api_key)
    li_markets = sorted({o["market"] for o in li_offers if o.get("market")})

    if keep_raw:
        raw_dir = OUT / "raw" / ts.strftime("%Y%m%dT%H%M%SZ")
        raw_dir.mkdir(parents=True, exist_ok=True)
        (raw_dir / "openrouter_models.json").write_text(json.dumps(or_by_id))
        (raw_dir / "openrouter_endpoints.json").write_text(json.dumps(or_eps))
        (raw_dir / "liquid_offers.json").write_text(json.dumps(li_offers))
        if li_quotes is not None:
            (raw_dir / "liquid_quotes.json").write_text(json.dumps(li_quotes))
        if li_tp is not None:
            (raw_dir / "liquid_throughput.json").write_text(json.dumps(li_tp))

    rows = []
    for rank, mid in enumerate(model_ids, 1):
        row = {c: None for c in HISTORY_COLS}
        row.update(ts_utc=ts_s, rank=rank, openrouter_id=mid)

        # OpenRouter side
        m = or_by_id.get(mid)
        if m:
            pr = m.get("pricing") or {}
            row["or_input_usd_mtok"] = per_mtok(pr.get("prompt"))
            row["or_output_usd_mtok"] = per_mtok(pr.get("completion"))
        ep, n_eps = best_or_endpoint(or_eps.get(mid), in_share)
        row["or_endpoint_count"] = n_eps
        if ep:
            row["or_cheapest_provider"] = ep.get("provider_name")
            epp = ep.get("pricing") or {}
            # endpoint prices win over the model-level list price
            if per_mtok(epp.get("completion")) is not None:
                row["or_input_usd_mtok"] = per_mtok(epp.get("prompt"))
                row["or_output_usd_mtok"] = per_mtok(epp.get("completion"))
            lat = ep.get("latency_last_30m")
            tp = ep.get("throughput_last_30m")
            row["or_latency_p50_s"] = (lat.get("p50") if isinstance(lat, dict) else lat)
            row["or_throughput_tps"] = (tp.get("p50") if isinstance(tp, dict) else tp)

        # Liquid side
        market = liquid_match(mid, li_markets, overrides)
        row["liquid_model"] = market
        if market:
            off, n_off = best_liquid_offer(li_offers, market, in_share)
            row["li_offer_count"] = n_off
            if off:
                row["li_input_usd_mtok"] = off.get("rate_uncached_input_usd_per_mtok")
                row["li_output_usd_mtok"] = off.get("rate_generation_usd_per_mtok")
                row["li_ttft_ms_ceiling"] = off.get("ttft_ms")
                row["li_completion_ms_ceiling"] = off.get("completion_ms")
                row["li_region"] = off.get("region")
            prov, tps = liquid_signed_in_view(li_quotes, li_tp, market)
            row["li_provider"] = prov
            row["li_measured_tps"] = tps

        # Diffs (Liquid minus OpenRouter; negative = Liquid cheaper)
        oi, oo = row["or_input_usd_mtok"], row["or_output_usd_mtok"]
        li_i, li_o = row["li_input_usd_mtok"], row["li_output_usd_mtok"]
        row["or_blended_usd_mtok"] = blended(oi, oo, in_share)
        row["li_blended_usd_mtok"] = blended(li_i, li_o, in_share)
        ob, lb = row["or_blended_usd_mtok"], row["li_blended_usd_mtok"]
        if None not in (ob, lb):
            row["blended_diff_usd_mtok"] = lb - ob
            row["blended_pct_vs_or"] = pct(lb, ob)
        if None not in (oi, li_i):
            row["input_diff_usd_mtok"] = li_i - oi
            row["input_pct_vs_or"] = pct(li_i, oi)
        if None not in (oo, li_o):
            row["output_diff_usd_mtok"] = li_o - oo
            row["output_pct_vs_or"] = pct(li_o, oo)

        if not m and not ep:
            row["status"] = "not on OpenRouter"
        elif not market:
            row["status"] = "not on Liquid"
        elif row["li_offer_count"] == 0:
            row["status"] = "no live Liquid offer"
        elif oo is None:
            row["status"] = "OpenRouter price dynamic/free"
        else:
            row["status"] = "ok"

        if row["status"] == "ok":
            if lb < ob:
                row["cheaper_on"] = "liquid"
            elif lb > ob:
                row["cheaper_on"] = "openrouter"
            else:
                row["cheaper_on"] = "same"
        rows.append(row)

    return ts_s, rows, {"liquid_signed_in": bool(api_key and li_quotes and "error" not in li_quotes),
                        "blend_input_share": in_share}


# --------------------------------------------------------------- outputs

def append_history(rows):
    OUT.mkdir(parents=True, exist_ok=True)
    f = OUT / "history.csv"
    new = not f.exists()
    with f.open("a", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=HISTORY_COLS)
        if new:
            w.writeheader()
        for r in rows:
            w.writerow({k: ("" if v is None else v) for k, v in r.items()})


def write_latest(ts_s, rows, meta):
    (OUT / "latest.json").write_text(json.dumps(
        {"ts_utc": ts_s, "meta": meta, "rows": rows}, indent=1))
    lines = [
        f"# Liquid Inference vs OpenRouter, top 30 by OpenRouter weekly tokens",
        f"",
        f"Tick: {ts_s}. Prices in USD per million tokens. Diff = Liquid minus OpenRouter "
        f"(negative means Liquid is cheaper). Liquid latency figures are committed ceilings "
        f"per offer, OpenRouter figures are measured when the API exposes them.",
        f"Blended = {int(meta.get('blend_input_share', 0.75) * 100)}% input / "
        f"{int(round((1 - meta.get('blend_input_share', 0.75)) * 100))}% output. Cheapest offer/endpoint "
        f"on each side is chosen by blended price. Cheaper column uses blended price.",
        f"Liquid signed-in view: {'on' if meta.get('liquid_signed_in') else 'off (set LIQUID_API_KEY)'}.",
        f"",
        "| # | Model | OR in | OR out | OR blended | OR provider | LI in | LI out | LI blended | LI offers | Blended diff | Blended % | LI TTFT ceiling ms | LI completion ceiling ms | Cheaper | Status |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        lines.append("| " + " | ".join([
            str(r["rank"]), r["openrouter_id"],
            fmt(r["or_input_usd_mtok"]), fmt(r["or_output_usd_mtok"]), fmt(r["or_blended_usd_mtok"]),
            r["or_cheapest_provider"] or "",
            fmt(r["li_input_usd_mtok"]), fmt(r["li_output_usd_mtok"]), fmt(r["li_blended_usd_mtok"]),
            fmt(r["li_offer_count"]),
            fmt(r["blended_diff_usd_mtok"]),
            (fmt(r["blended_pct_vs_or"], 1) + "%") if r["blended_pct_vs_or"] is not None else "",
            fmt(r["li_ttft_ms_ceiling"], 0), fmt(r["li_completion_ms_ceiling"], 0),
            r["cheaper_on"] or "", r["status"] or "",
        ]) + " |")
    (OUT / "latest.md").write_text("\n".join(lines) + "\n")


def log_changes(ts_s, rows, prev):
    """Append a line for every model whose diff moved since the last tick."""
    if not prev:
        return
    prev_by = {r["openrouter_id"]: r for r in prev}
    out = []
    for r in rows:
        p = prev_by.get(r["openrouter_id"])
        if not p:
            continue
        for col in ("blended_diff_usd_mtok", "cheaper_on", "status"):
            a, b = p.get(col), r.get(col)
            if isinstance(a, float) and isinstance(b, float):
                changed = abs(a - b) > 1e-9
            else:
                changed = a != b
            if changed:
                out.append(f"{ts_s} {r['openrouter_id']} {col}: {fmt(a)} -> {fmt(b)}")
    if out:
        with (OUT / "changes.log").open("a") as fh:
            fh.write("\n".join(out) + "\n")


# ------------------------------------------------------------------ main

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--once", action="store_true", help="run one tick and exit")
    ap.add_argument("--interval", type=int, default=60, help="seconds between ticks (default 60)")
    ap.add_argument("--no-raw", action="store_true", help="do not keep raw API responses")
    args = ap.parse_args()

    cfg = json.loads(MODELS_FILE.read_text())
    api_key = os.environ.get("LIQUID_API_KEY") or None
    OUT.mkdir(parents=True, exist_ok=True)
    prev_rows = None
    if (OUT / "latest.json").exists():
        try:
            prev_rows = json.loads((OUT / "latest.json").read_text())["rows"]
        except Exception:  # noqa: BLE001
            prev_rows = None

    while True:
        started = time.monotonic()
        try:
            ts_s, rows, meta = run_tick(cfg, api_key, keep_raw=not args.no_raw)
            append_history(rows)
            log_changes(ts_s, rows, prev_rows)
            write_latest(ts_s, rows, meta)
            prev_rows = rows
            ok = sum(1 for r in rows if r["status"] == "ok")
            cheaper_li = sum(1 for r in rows if r["cheaper_on"] == "liquid")
            print(f"{ts_s} tick ok: {ok}/{len(rows)} matched, Liquid cheaper on {cheaper_li}, "
                  f"signed-in={'yes' if meta['liquid_signed_in'] else 'no'}", flush=True)
        except Exception as e:  # noqa: BLE001
            print(f"{now_utc().isoformat()} tick failed: {e}", file=sys.stderr, flush=True)
        if args.once:
            break
        time.sleep(max(1, args.interval - (time.monotonic() - started)))


if __name__ == "__main__":
    main()
