from __future__ import annotations

import os

from agents.llm_client import call_llm


def main() -> None:
    if not (os.getenv("MCTSCODER_API_KEY") or os.getenv("OPENAI_API_KEY")):
        raise RuntimeError("Set MCTSCODER_API_KEY (or OPENAI_API_KEY) before running.")
    response = call_llm("Hello?", temperature=0.2, max_tokens=256)
    print(response)


if __name__ == "__main__":
    main()
