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


def parse_standard_menu(
    db: Session,
    file_path: Path,
    stall_name: str,
) -> dict[str, int]:
    """
    Parses standard menu files having the format:

        NORTH INDIAN CUISINE

        Item            Rate (Rs.)
        Paneer          120
        Dal Makhani      90

        SOUTH INDIAN CUISINE

        Item            Rate (Rs.)
        Dosa             80

    Used for:
        - Vishal Dhaba
        - Gupta Canteen
    """

    stall = get_food_stall_by_name(
        db=db,
        name=stall_name,
    )

    if stall is None:
        raise ValueError(
            f"Food stall '{stall_name}' not found."
        )

    df = pd.read_excel(file_path)

    added = 0
    updated = 0
    skipped = 0

    current_section: str | None = None

    for _, row in df.iterrows():

        item = row.iloc[0]
        price = row.iloc[1]

        # Skip completely empty rows
        if pd.isna(item):
            continue

        item_name = str(item).strip()

        # Skip repeated table header
        if item_name.lower() == "item":
            continue

        # Section heading
        if pd.isna(price):
            current_section = item_name
            continue

        price_text = str(price).strip()

        # Skip repeated price header
        if price_text.lower() in {
            "rate",
            "rate (rs.)",
            "price",
            "amount",
        }:
            continue

        category = resolve_category(current_section)
        current_price = parse_price(price)

        existing_item = get_menu_item_by_name_and_stall(
            db=db,
            stall_id=stall.id,
            name=item_name,
        )

        if existing_item:

            if (
                existing_item.current_price != current_price
                or existing_item.category != category
                or existing_item.menu_section != current_section
                or existing_item.preparation_time
                != get_preparation_time(category)
                or not existing_item.is_available
            ):
                existing_item.current_price = current_price
                existing_item.category = category
                existing_item.menu_section = current_section
                existing_item.preparation_time = get_preparation_time(
                    category
                )
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
            menu_section=current_section,
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