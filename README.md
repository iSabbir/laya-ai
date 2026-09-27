# Laya AI by iSabbir

**Local-first AI decision tools for support triage and browser games.** This repository combines the Laya decision engine with practical demos for customer-support ticket classification, urgency and churn-risk scoring, and AI-guided Snake and road-avoidance games.

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache--2.0-green.svg)](LICENSE)
[![GitHub](https://img.shields.io/badge/GitHub-iSabbir-181717?logo=github)](https://github.com/iSabbir)

> **Attribution:** This is a personal derivative project built on [Laya](https://github.com/NandhaKishorM/laya), originally created by Nandakishor and contributors. The Laya engine, its existing source files, history, and copyright notices remain credited to their original authors. This repository preserves the upstream Apache-2.0 license. My additions and demos are identified below.

## About the author

**iSabbir** is a software engineer working with Python, Telegram bots, and SaaS, and is open to Software Engineer, Backend Engineer, and AI Engineer roles.

Contact: [sabbir@bdbots.org](mailto:sabbir@bdbots.org)

GitHub: [github.com/iSabbir](https://github.com/iSabbir)

## What is included

- **Support ticket triage:** Run five sample customer messages through Laya and inspect predicted department, urgency, churn risk, and routed model.
- **Snake game:** A browser-based game with safe local move planning and Laya prediction telemetry.
- **Road-avoidance game:** A browser game and Python prototype demonstrating lane decisions.
- **Laya engine:** The upstream local decision engine for typed `choice`, `score`, and `noul` predictions.

## Support ticket cases

The example runner is [`test_support_cases.py`](test_support_cases.py). It prints each message, the model's prediction, the expected reference values, and the routing checkpoint. Model output can vary with the checkpoint revision and inference environment; the printed `PASS` or `CHECK` compares predictions with the reference values in the script.

Run from Windows Command Prompt:

```cmd
cd /d D:\LAYA\laya
.venv\Scripts\activate.bat
python test_support_cases.py
```

The first run downloads the official English checkpoint from Hugging Face. A local checkpoint can be selected with:

```cmd
set LAYA_ENGLISH_MODEL=C:\path\to\english\checkpoint
python test_support_cases.py
```

## Install and run

Use Python 3.10 or newer. From the repository root in Windows Command Prompt:

```cmd
py -3 -m venv .venv
.venv\Scripts\activate.bat
python -m pip install -e ".[mcp]"
```

To run the routing and MCP test suites:

```cmd
python tests\test_router.py
python tests\test_mcp.py
```

The MCP extra is included in the install command above. The full model-backed end-to-end test also needs the English, multilingual, and typed-decision checkpoints:

```cmd
python tests\test_local_e2e.py
```

## Browser games

Start the local game server:

```cmd
python game_server.py
```

Then open the pages in a browser:

- Snake: <http://127.0.0.1:8000/snake.html>
- Road-avoidance game: <http://127.0.0.1:8000/>

The server uses the local Laya package. No hosted inference API is required by these demos.

## Use Laya for a decision

The Laya router loads the English checkpoint on first use and returns typed answers plus routing information:

```python
from laya import Router

router = Router()
questions = {
    "department": {
        "type": "choice",
        "instructions": "Which department should handle this support ticket?",
        "criteria": {
            "billing": "invoices, payments, duplicate charges, and refunds",
            "technical": "bugs, outages, login failures, and integrations",
        },
    },
    "urgency": {
        "type": "score",
        "instructions": "How urgent is the issue?",
        "criteria": ["routine", "needs attention soon", "blocks work or customers"],
    },
    "churn_risk": {
        "type": "noul",
        "instructions": "Does the customer indicate they may cancel or leave?",
    },
}

result = router.predict(
    {"message": "We were billed twice. Please refund the duplicate or we will cancel."},
    questions,
)
print(result["answers"]["department"]["choice"])
print(result["answers"]["urgency"]["score"])
print(result["answers"]["churn_risk"]["noul"])
print(result["routing"]["model"])
```

## Upstream project and license

- Original Laya repository: <https://github.com/NandhaKishorM/laya>
- Laya model: <https://huggingface.co/convaiinnovations/laya>
- Laya documentation: <https://nandhakishorm.github.io/laya/>
- License: [Apache License 2.0](LICENSE)

Laya is a local typed-decision engine. See the upstream project for its architecture, model details, benchmarks, and the complete API documentation. This personal repository focuses on the demos and support-ticket workflow added around that engine.
