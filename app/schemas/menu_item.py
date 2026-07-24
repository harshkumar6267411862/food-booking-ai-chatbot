from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.enums.menu_category import MenuCategory


class MenuItemCreateRequest(BaseModel):
    stall_id: int
    name: str = Field(min_length=2, max_length=100)
    description: str | None = Field(None, max_length=500)
    category: MenuCategory
    current_price: Decimal = Field(gt=0, decimal_places=2)
    preparation_time: int = Field(gt=0, description="Preparation time in minutes")
    image_url: str | None = None


class MenuItemCreateResponse(BaseModel):
    id: int
    stall_id: int
    name: str
    description: str | None = None
    category: MenuCategory
    current_price: Decimal
    preparation_time: int
    image_url: str | None
    is_available: bool

    model_config = ConfigDict(
        from_attributes=True
    )


class MenuItemResponse(BaseModel):
    id: int
    stall_id: int
    name: str
    description: str | None = None
    category: MenuCategory
    current_price: Decimal
    preparation_time: int
    image_url: str | None = None
    is_available: bool

    model_config = ConfigDict(
        from_attributes=True
    )
    
class MenuItemSummary(BaseModel):
    name: str

    model_config = ConfigDict(from_attributes=True)