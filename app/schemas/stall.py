from pydantic import BaseModel, ConfigDict
from datetime import datetime

class FoodStallResponse(BaseModel):
    id: int
    name: str
    description: str
    location: str
    menu_image_url: str | None = None
    is_open: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
