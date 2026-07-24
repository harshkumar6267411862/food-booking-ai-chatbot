from pathlib import Path

import pandas as pd
from sqlalchemy.orm import Session

from app.models.menu_item import MenuItem
from app.repositories.menu_item_repository import (
    create_menu_item,
    get_menu_item_by_name_and_stall,
    update_menu_item,
)
from app.repositories.stall_repository import get_food_stall_by_name

from scripts.parsers.helpers import (
    get_preparation_time,
    parse_price,
    resolve_category,
)


def parse_kitchen_ette_menu(
    db: Session,
    file_path: Path,
    stall_name: str,
) -> dict[str, int]:

    stall = get_food_stall_by_name(
        db=db,
        name=stall_name,
    )

    if stall is None:
        raise ValueError(
            f"Food stall '{stall_name}' not found."
        )

    # Row 2 contains the actual headers
    df = pd.read_excel(
        file_path,
        header=2,
    )
    
    df.columns = df.columns.str.strip()

    added = 0
    updated = 0
    skipped = 0

    for _, row in df.iterrows():

        if (
            pd.isna(row["Category"])
            or pd.isna(row["Item"])
        ):
            continue

        section = str(row["Category"]).strip()
        item = str(row["Item"]).strip()

        category = resolve_category(section)

        prices = []

        # Half price
        if pd.notna(row["Half (₹)"]):
            prices.append(
                (
                    f"{item} (Half)",
                    parse_price(row["Half (₹)"]),
                )
            )

        # Full price
        if pd.notna(row["Full (₹)"]):
            prices.append(
                (
                    f"{item} (Full)",
                    parse_price(row["Full (₹)"]),
                )
            )

        # Single price
        if pd.notna(row["Price (₹)"]):
            prices.append(
                (
                    item,
                    parse_price(row["Price (₹)"]),
                )
            )

        for item_name, current_price in prices:

            existing_item = get_menu_item_by_name_and_stall(
                db=db,
                stall_id=stall.id,
                name=item_name,
            )

            if existing_item:

                if (
                    existing_item.current_price != current_price
                    or existing_item.category != category
                    or existing_item.menu_section != section
                    or existing_item.preparation_time != get_preparation_time(category)
                    or not existing_item.is_available
                ):

                    existing_item.current_price = current_price
                    existing_item.category = category
                    existing_item.menu_section = section
                    existing_item.preparation_time = get_preparation_time(category)
                    existing_item.is_available = True

                    update_menu_item(
                        db=db,
                        menu_item=existing_item,
                    )

                    updated += 1

                else:
                    skipped += 1

                continue

            menu_item = MenuItem(
                stall_id=stall.id,
                name=item_name,
                description=None,
                category=category,
                menu_section=section,
                current_price=current_price,
                preparation_time=get_preparation_time(category),
                is_available=True,
            )

            create_menu_item(
                db=db,
                menu_item=menu_item,
            )

            added += 1

    return {
        "added": added,
        "updated": updated,
        "skipped": skipped,
    }