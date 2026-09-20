"""Low-risk live smoke test for the TypeSafe sister node.

Requires:
- R3_TYPESAFE_URL (e.g. internal/private service URL)
- R3_API_TOKEN

The TypeSafe API key stays on the sister service; it is never passed by this client.
"""
from __future__ import annotations

import json
import os
import sys

import httpx

URL = os.environ["R3_TYPESAFE_URL"].rstrip("/")
TOKEN = os.environ["R3_API_TOKEN"]


def main() -> int:
    payload = {
        "state": {
            "message": "A backup check completed, but no independent restore proof exists yet.",
            "context": "R3 continuity status classification fixture",
        },
        "questions": {
            "route": {
                "type": "choice",
                "instructions": "Which bounded next action best matches the state?",
                "criteria": {
                    "continue_monitoring": "No blocker and no missing proof that requires action.",
                    "request_restore_test": "The state lacks an independent restore proof.",
                    "escalate_security": "There is evidence of a security compromise.",
                },
            },
            "restore_missing": {
                "type": "noul",
                "instructions": "Does the state explicitly lack independent restore proof?",
                "criteria": {
                    "true": "Independent restore proof is absent or pending.",
                    "false": "Independent restore proof is present and verified.",
                },
            },
            "priority": {
                "type": "score",
                "instructions": "How important is it to address the missing verification next?",
                "criteria": [
                    "No action needed.",
                    "Low priority.",
                    "Useful but not urgent.",
                    "Important next validation.",
                    "Critical blocker requiring immediate action.",
                ],
            },
        },
    }

    response = httpx.post(
        f"{URL}/judge",
        headers={"Authorization": f"Bearer {TOKEN}"},
        json=payload,
        timeout=45,
    )
    response.raise_for_status()
    print(json.dumps(response.json(), indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"status": "FAIL", "error": type(exc).__name__, "detail": str(exc)}), file=sys.stderr)
        raise
