from pydantic import BaseModel, ConfigDict
from datetime import datetime, time

class FoodStallResponse(BaseModel):
    id: int
    name: str
    description: str
    location: str
    menu_image_url: str | None = None
    opening_time: time
    closing_time: time
    created_at: datetime
    updated_at: datetime
    

    model_config = ConfigDict(from_attributes=True)
