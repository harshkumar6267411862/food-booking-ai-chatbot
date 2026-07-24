from decimal import Decimal
import re

from app.enums.menu_category import MenuCategory

CATEGORY_MAPPING = {
    "north indian": MenuCategory.MAIN_COURSE,
    "south indian": MenuCategory.MAIN_COURSE,
    "chinese": MenuCategory.MAIN_COURSE,
    "rice": MenuCategory.MAIN_COURSE,
    "lunch": MenuCategory.MAIN_COURSE,
    "dinner": MenuCategory.MAIN_COURSE,

    "burger": MenuCategory.SNACK,
    "pizza": MenuCategory.SNACK,
    "sandwich": MenuCategory.SNACK,
    "roll": MenuCategory.SNACK,
    "momos": MenuCategory.SNACK,
    "fries": MenuCategory.SNACK,
    "maggi": MenuCategory.SNACK,

    "tea": MenuCategory.BEVERAGE,
    "coffee": MenuCategory.BEVERAGE,
    "shake": MenuCategory.BEVERAGE,
    "shakes": MenuCategory.BEVERAGE,
    "mojito": MenuCategory.BEVERAGE,
    "juice": MenuCategory.BEVERAGE,
    "soft drink": MenuCategory.BEVERAGE,

    "dessert": MenuCategory.DESSERT,
    "ice cream": MenuCategory.DESSERT,

    "combo": MenuCategory.COMBO,
}

PREPARATION_TIME = {
    MenuCategory.MAIN_COURSE: 20,
    MenuCategory.SNACK: 10,
    MenuCategory.BEVERAGE: 5,
    MenuCategory.DESSERT: 5,
    MenuCategory.COMBO: 25,
}

def resolve_category(section: str | None) -> MenuCategory:
    if not section:
        return MenuCategory.SNACK

    section = section.lower().strip()

    for keyword, category in CATEGORY_MAPPING.items():
        if keyword in section:
            return category

    return MenuCategory.SNACK


def parse_price(price) -> Decimal:
    if price is None:
        return Decimal("0.00")

    text = str(price).strip()

    match = re.search(r"\d+", text)

    if not match:
        return Decimal("0.00")

    return Decimal(match.group())

def get_preparation_time(
    category: MenuCategory,
) -> int:
    return PREPARATION_TIME.get(category, 10)