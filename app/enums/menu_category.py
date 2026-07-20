from enum import Enum


class MenuCategory(str, Enum):
    MAIN_COURSE = "Main Course"
    SNACK = "Snack"
    BEVERAGE = "Beverage"
    DESSERT = "Dessert"
    COMBO = "Combo"