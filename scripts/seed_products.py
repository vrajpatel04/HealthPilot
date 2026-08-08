"""
Seed sample wellness products into PostgreSQL and sync to Qdrant.

Usage:
    uv run python scripts/seed_products.py

Skips products whose title already exists (safe to re-run).
"""

from __future__ import annotations

import asyncio
import sys
from decimal import Decimal

from sqlalchemy import select

from healthPilot.core.database import AsyncSessionLocal, engine
from healthPilot.models.product import Product
from healthPilot.schemas.product import ProductCreateRequest
from healthPilot.services.product_service import ProductService

SAMPLE_PRODUCTS: list[ProductCreateRequest] = [
    ProductCreateRequest(
        title="Sleep Better in 21 Days",
        description=(
            "A structured 21-day program focused on building healthier sleep routines. "
            "Learn gradual habit changes for better rest, calmer nights, and more energy."
        ),
        category="sleep",
        price=Decimal("499.00"),
        metadata={"duration_days": 21, "difficulty": "beginner"},
    ),
    ProductCreateRequest(
        title="Beginner Walking Program",
        description=(
            "Start moving at your own pace with a gentle walking plan designed for "
            "office workers and beginners who want consistent daily activity."
        ),
        category="fitness",
        price=Decimal("299.00"),
        metadata={"duration_days": 14, "difficulty": "beginner"},
    ),
    ProductCreateRequest(
        title="Healthy Meal Planning",
        description=(
            "Build balanced meals with simple planning frameworks, grocery lists, "
            "and nutrition basics for sustainable eating habits."
        ),
        category="nutrition",
        price=Decimal("399.00"),
        metadata={"duration_days": 30, "difficulty": "beginner"},
    ),
    ProductCreateRequest(
        title="Stress Management",
        description=(
            "Practical techniques for managing daily stress through breathing, "
            "mindfulness, and structured recovery routines."
        ),
        category="mental_wellness",
        price=Decimal("449.00"),
        metadata={"duration_days": 21, "difficulty": "beginner"},
    ),
    ProductCreateRequest(
        title="Morning Routine Mastery",
        description=(
            "Design a morning routine that fits your schedule. Step-by-step guidance "
            "for hydration, movement, and focus before work."
        ),
        category="lifestyle",
        price=Decimal("349.00"),
        metadata={"duration_days": 14, "difficulty": "beginner"},
    ),
    ProductCreateRequest(
        title="7-Day Meal Plan",
        description=(
            "A ready-to-use 7-day meal plan with simple recipes and a shopping list "
            "for busy professionals."
        ),
        category="nutrition",
        price=Decimal("199.00"),
        metadata={"duration_days": 7, "difficulty": "beginner"},
    ),
    ProductCreateRequest(
        title="Morning Routine Guide",
        description=(
            "Digital guide covering morning habits for better energy, focus, and "
            "consistent sleep-wake timing."
        ),
        category="lifestyle",
        price=Decimal("149.00"),
        metadata={"format": "guide"},
    ),
    ProductCreateRequest(
        title="Sleep Improvement Program",
        description=(
            "A 30-day sleep improvement program combining wind-down rituals, "
            "screen-time boundaries, and weekly progress check-ins."
        ),
        category="sleep",
        price=Decimal("599.00"),
        metadata={"duration_days": 30, "difficulty": "intermediate"},
    ),
]


async def _title_exists(session, title: str) -> bool:
    result = await session.execute(select(Product.id).where(Product.title == title).limit(1))
    return result.scalar_one_or_none() is not None


async def seed_products() -> tuple[int, int]:
    created = 0
    skipped = 0

    async with AsyncSessionLocal() as session:
        service = ProductService(session)

        for product in SAMPLE_PRODUCTS:
            if await _title_exists(session, product.title):
                print(f"  skip  {product.title!r} (already exists)")
                skipped += 1
                continue

            result = await service.create(product)
            status = result.vector_sync_status.value
            print(f"  added {product.title!r} — sync: {status}")
            created += 1

    return created, skipped


async def main() -> None:
    print("Seeding HealthPilot sample products...\n")
    try:
        created, skipped = await seed_products()
    finally:
        await engine.dispose()

    print(f"\nDone: {created} created, {skipped} skipped.")
    if created == 0 and skipped == 0:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
