#!/usr/bin/env python3
"""Seed wellness knowledge documents into Qdrant."""

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from healthPilot.rag.ingest import ingest_markdown_dir


async def main() -> None:
    knowledge_dir = ROOT / "data" / "knowledge"
    if not knowledge_dir.exists():
        print(f"Knowledge directory not found: {knowledge_dir}")
        sys.exit(1)
    count = await ingest_markdown_dir(knowledge_dir)
    print(f"Upserted {count} new knowledge chunks into Qdrant.")


if __name__ == "__main__":
    asyncio.run(main())
