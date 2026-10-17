# Liquid Inference vs OpenRouter tracker

Checks both sites every minute and keeps a running list of the price gap on the 30 most-used OpenRouter models.

No dependencies beyond Python 3.9+. No API key needed for the price comparison.

## Run

```bash
# one check
python3 li_vs_or.py --once

# every minute, forever (Ctrl-C to stop)
python3 li_vs_or.py --interval 60

# with Liquid's signed-in views (provider names, measured tok/s)
export LIQUID_API_KEY=sk-liquid-...
python3 li_vs_or.py --interval 60

# keep it running after you close the terminal
nohup python3 li_vs_or.py --interval 60 > tracker.log 2>&1 &
```

Raw API responses are saved per tick (about 1.8 MB each, so roughly 2.6 GB a day). Add `--no-raw` to skip them.

## Outputs (in `out/`)

| File | What it is |
|---|---|
| `latest.md` | Readable table of the most recent check |
| `latest.json` | Same data, machine readable |
| `history.csv` | One row per model per check, append only. Open in a spreadsheet to chart gaps over time. |
| `changes.log` | A line each time a model's blended gap, cheaper side or status moves |
| `raw/<timestamp>/` | The raw JSON from each API call that tick |

## How to read the numbers

- All prices are USD per million tokens.
- **Blended** = 75% input + 25% output by default (3 input tokens per output token, a typical chat mix). Change `blend_input_share` in `models.json`. The cheapest offer on each side is picked by blended price, so the in/out columns show the prices of that one offer, not the min of each column separately.
- **Diff** = Liquid minus OpenRouter. Negative means Liquid is cheaper.
- **OR provider** is the cheapest live OpenRouter endpoint for that model, which is often not the model maker.
- **LI offers** is how many live, verified, non-synthetic offers Liquid had for that model.
- **LI TTFT / completion ceiling** are the deadlines the Liquid provider commits to for that offer, in ms. They are worst-case promises, not measured speed.
- **OR latency / throughput** columns in `history.csv` fill in only when OpenRouter's public API exposes them. At the time of writing they come back null.
- **LI provider / measured tps** fill in only with `LIQUID_API_KEY`. Those endpoints (`/v1/exchange/quotes`, `/v1/exchange/throughput`) are undocumented, so the parser is best-effort and the raw responses are always saved.

## Caveats

- Liquid is an auction. Its prices are live offers that can be withdrawn or repriced within minutes, which is the point of checking every minute.
- Very low Liquid offers (a few tenths of a cent per million) are real offers on the book, but say nothing about the provider's quality or capacity. Check `li_offer_count`: a model with one offer has no competition behind that price.
- Two of the 30 (`typesafe/jev-1.13`, `openai/gpt-5.6-luna`) are not on Liquid. OpenRouter's free variants are priced here at their cheapest paid endpoint, since the `:free` endpoint is $0 and not comparable.
- Model matching is by name with punctuation ignored. Override any pairing in `models.json` under `liquid_overrides`.

## Changing the model list

Edit the `models` array in `models.json`. The order is the rank shown in outputs. To refresh from OpenRouter's current top 30, use the weekly leaderboard at openrouter.ai/rankings (first 20) and openrouter.ai/models?order=top-weekly (the rest).
