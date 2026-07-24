from pathlib import Path

from app.database import SessionLocal
from scripts.parsers.standard_parser import parse_standard_menu
from scripts.parsers.kitchen_ette_parser import parse_kitchen_ette_menu
from scripts.parsers.three_column_parser import parse_three_column_menu

MENU_DIRECTORY = Path("data/menus")


def seed_menus():
    db = SessionLocal()

    try:
        # ---------------- Standard Menus ---------------- #
        standard_menus = [
            ("Vishal Dhaba", "Vishal_Dhaba_Menu.xlsx"),
            ("Gupta Canteen", "Gupta_Canteen_Menu.xlsx"),
        ]

        print("\n🌱 Seeding Standard Menus...\n")

        for stall_name, file_name in standard_menus:
            print(f"📍 {stall_name}")

            result = parse_standard_menu(
                db=db,
                file_path=MENU_DIRECTORY / file_name,
                stall_name=stall_name,
            )

            print(f"   Added   : {result['added']}")
            print(f"   Updated : {result['updated']}")
            print(f"   Skipped : {result['skipped']}\n")

        print("✅ Standard Menus Seeded!\n")

        # ---------------- Kitchen Ette ---------------- #
        print("🌱 Seeding Kitchen Ette...\n")

        result = parse_kitchen_ette_menu(
            db=db,
            file_path=MENU_DIRECTORY / "Kitchen_Ette_CC_Menu.xlsx",
            stall_name="Kitchen Ette",
        )

        print("📍 Kitchen Ette")
        print(f"   Added   : {result['added']}")
        print(f"   Updated : {result['updated']}")
        print(f"   Skipped : {result['skipped']}\n")

        print("✅ Kitchen Ette Seeded!\n")

        # ---------------- Three Column Menus ---------------- #
        three_column_menus = [
            ("Ahuja", "Ahuja_Canteen_Menu.xlsx"),
            ("Chai Vyanjan", "Chai_Vyanjan_Menu.xlsx"),
        ]

        print("🌱 Seeding Three Column Menus...\n")

        for stall_name, file_name in three_column_menus:
            print(f"📍 {stall_name}")

            result = parse_three_column_menu(
                db=db,
                file_path=MENU_DIRECTORY / file_name,
                stall_name=stall_name,
            )

            print(f"   Added   : {result['added']}")
            print(f"   Updated : {result['updated']}")
            print(f"   Skipped : {result['skipped']}\n")

        print("✅ Three Column Menus Seeded!\n")

        print("🎉 All menus seeded successfully!")

    finally:
        db.close()


if __name__ == "__main__":
    seed_menus()