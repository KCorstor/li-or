# Liquid Inference vs OpenRouter, top 30 by OpenRouter weekly tokens

Tick: 2026-10-17T17:44:43Z. Prices in USD per million tokens. Diff = Liquid minus OpenRouter (negative means Liquid is cheaper). Liquid latency figures are committed ceilings per offer, OpenRouter figures are measured when the API exposes them.
Blended = 75% input / 25% output. Cheapest offer/endpoint on each side is chosen by blended price. Cheaper column uses blended price.
Liquid signed-in view: off (set LIQUID_API_KEY).

| # | Model | OR in | OR out | OR blended | OR provider | LI in | LI out | LI blended | LI offers | Blended diff | Blended % | LI TTFT ceiling ms | LI completion ceiling ms | Cheaper | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | deepseek/deepseek-v4.1-flash | 0.09 | 0.18 | 0.1125 | Decart | 0.0012 | 0.0015 | 0.0013 | 11 | -0.1112 | -98.9% | 5000 | 300000 | liquid | ok |
| 2 | stepfun/step-5-preview | 1 | 2.7 | 1.425 | InferenceNet | 0.9995 | 2.6987 | 1.4243 | 1 | -0.0007 | -0% | 1500 | 30000 | liquid | ok |
| 3 | z-ai/glm-5.3-flash | 0.075 | 0.25 | 0.1187 | DeepInfra | 0.045 | 0.004 | 0.0348 | 6 | -0.084 | -70.7% | 10000 | 1800000 | liquid | ok |
| 4 | xiaomi/mimo-v2.6-flash | 0.1 | 0.28 | 0.145 | Darkbloom | 0.1401 | 0.2802 | 0.1751 | 2 | 0.0301 | 20.8% | 1500 | 30000 | openrouter | ok |
| 5 | tencent/hy4-preview | 0.7506 | 2.2509 | 1.1257 | Tencent | 1.0425 | 3.1263 | 1.5634 | 1 | 0.4378 | 38.9% | 20000 | 300000 | openrouter | ok |
| 6 | openai/gpt-6-luna | 0.05 | 0.25 | 0.1 | OpenAI | 0.1498 | 0.0193 | 0.1172 | 2 | 0.0172 | 17.2% | 20000 | 300000 | openrouter | ok |
| 7 | anthropic/claude-opus-5.5 | 4 | 20 | 8 | Amazon Bedrock | 3.9994 | 19.9971 | 7.9988 | 1 | -0.0012 | -0% | 1500 | 30000 | liquid | ok |
| 8 | nvidia/nemotron-3-ultra-550b-a55b:free | 0.4 | 1.76 | 0.74 | DeepInfra | 0.625 | 2.75 | 1.1562 | 1 | 0.4163 | 56.2% | 20000 | 300000 | openrouter | ok |
| 9 | z-ai/glm-5.3 | 0.5 | 1.505 | 0.7512 | Sail Research | 0.14 | 0.03 | 0.1125 | 10 | -0.6387 | -85% | 120000 | 600000 | liquid | ok |
| 10 | deepseek/deepseek-v4-flash-0731 | 0.0598 | 0.1795 | 0.0898 | Baidu | 0.045 | 0.0018 | 0.0342 | 6 | -0.0556 | -61.9% | 12500 | 300000 | liquid | ok |
| 11 | tencent/hy3 | 0.0825 | 0.33 | 0.1444 | Tencent | 0.0658 | 0.2594 | 0.1142 | 1 | -0.0301 | -20.9% | 1500 | 30000 | liquid | ok |
| 12 | meta/muse-spark-1.3-contributor | 0.1 | 0.2 | 0.125 | Meta | 0.1 | 0.1999 | 0.125 | 1 | -0 | -0% | 1500 | 30000 | liquid | ok |
| 13 | typesafe/jev-1.13 | 0.042 | 0 | 0.0315 | TypeSafe |  |  |  |  |  |  |  |  |  | not on Liquid |
| 14 | deepseek/deepseek-v4-flash | 0.016 | 0.0319 | 0.0199 | Baidu | 0.05 | 0.005 | 0.0388 | 3 | 0.0188 | 94.2% | 20000 | 600000 | openrouter | ok |
| 15 | anthropic/claude-sonnet-5.5 | 2 | 10 | 4 | Google | 1.9954 | 9.9771 | 3.9909 | 1 | -0.0091 | -0.2% | 1500 | 30000 | liquid | ok |
| 16 | moonshotai/kimi-k3 | 0.504 | 8.1 | 2.403 | Sail Research | 0.025 | 0.075 | 0.0375 | 8 | -2.3655 | -98.4% | 6000 | 600000 | liquid | ok |
| 17 | openai/gpt-6.1-sol | 1 | 5 | 2 | OpenAI | 2.9934 | 0.3 | 2.32 | 2 | 0.32 | 16% | 2000 | 300000 | openrouter | ok |
| 18 | anthropic/claude-haiku-5.5 | 0.1 | 0.5 | 0.2 | Google | 0.0998 | 0.499 | 0.1996 | 1 | -0.0004 | -0.2% | 1500 | 30000 | liquid | ok |
| 19 | google/gemini-3.8-flash | 0.375 | 1.875 | 0.75 | Google AI Studio | 0.7498 | 3.7489 | 1.4995 | 1 | 0.7495 | 99.9% | 1500 | 30000 | openrouter | ok |
| 20 | openai/gpt-5.6-luna | 0.1 | 0.6 | 0.225 | OpenAI |  |  |  |  |  |  |  |  |  | not on Liquid |
| 21 | xiaomi/mimo-v2.6-pro | 0.43 | 0.87 | 0.54 | DeepInfra | 0.434 | 0.8681 | 0.5425 | 2 | 0.0025 | 0.5% | 1500 | 30000 | openrouter | ok |
| 22 | minimax/minimax-m3 | 0.224 | 0.88 | 0.388 | DeepInfra | 0.5197 | 0.022 | 0.3953 | 2 | 0.0073 | 1.9% | 5000 | 300000 | openrouter | ok |
| 23 | nvidia/nemotron-3.5-lightning:free | 0.025 | 0.12 | 0.0488 | Darkbloom | 0.075 | 0.2 | 0.1062 | 1 | 0.0575 | 117.9% | 20000 | 300000 | openrouter | ok |
| 24 | poolside/laguna-s-2.1:free | 0.09 | 0.18 | 0.1125 | Poolside | 0.0999 | 0.1998 | 0.1249 | 1 | 0.0124 | 11% | 1500 | 30000 | openrouter | ok |
| 25 | z-ai/glm-5.2 | 0.189 | 0.594 | 0.2903 | Baidu | 0.155 | 0.035 | 0.125 | 3 | -0.1653 | -56.9% | 20000 | 600000 | liquid | ok |
| 26 | deepseek/deepseek-v4-pro-0813 | 0.1333 | 0.4 | 0.2 | Baidu | 0.6592 | 1.9776 | 0.9888 | 1 | 0.7888 | 394.5% | 1500 | 30000 | openrouter | ok |
| 27 | upstage/solar-mini4 | 0.05 | 0.2 | 0.0875 | Upstage | 0.05 | 0.2001 | 0.0875 | 1 | 0 | 0% | 1500 | 30000 | openrouter | ok |
| 28 | google/gemini-3-flash-preview | 0.25 | 1.5 | 0.5625 | Google AI Studio | 0.5008 | 3.005 | 1.1269 | 1 | 0.5644 | 100.3% | 1500 | 30000 | openrouter | ok |
| 29 | qwen/qwen3.6-35b-a3b | 0.05 | 0.7 | 0.2125 | Darkbloom | 0.112 | 0.02 | 0.089 | 3 | -0.1235 | -58.1% | 20000 | 300000 | liquid | ok |
| 30 | upstage/solar-pro4 | 0.09 | 0.36 | 0.1575 | Upstage | 0.03 | 0.1199 | 0.0525 | 1 | -0.105 | -66.7% | 1500 | 30000 | liquid | ok |
