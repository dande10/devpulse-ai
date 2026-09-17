"""One-off backfill: reprocess every stored update with the current
processor logic (summary/category/impact) instead of whatever version of
that logic was live when it was first ingested.

Spends zero Tavily credits — the original Tavily Extract payload is already
saved in raw_metadata.tavily, so this just re-runs clean_content/
create_summary/classify_category/classify_impact against it and updates the
row in place.

Run inside the backend container:
    python -m app.scripts.reprocess_updates
"""

from app.database.session import SessionLocal
from app.ingestion import processor
from app.models import DeveloperUpdate


def main() -> None:
    db = SessionLocal()
    updated = 0
    unchanged = 0
    skipped = 0
    try:
        for update in db.query(DeveloperUpdate).all():
            tavily_result = (update.raw_metadata or {}).get("tavily")
            if not tavily_result:
                skipped += 1
                continue

            processed = processor.process(tavily_result, published_at=update.published_at)
            if not processed:
                skipped += 1
                continue

            changed = (
                update.summary != processed.summary
                or update.extracted_content != processed.extracted_content
                or update.category != processed.category
                or update.impact_level != processed.impact_level
            )
            if not changed:
                unchanged += 1
                continue

            update.summary = processed.summary
            update.extracted_content = processed.extracted_content
            update.category = processed.category
            update.impact_level = processed.impact_level
            updated += 1

        db.commit()
    finally:
        db.close()

    print(f"Reprocessed: {updated} updated, {unchanged} already clean, {skipped} had no raw Tavily payload to reprocess.")


if __name__ == "__main__":
    main()
