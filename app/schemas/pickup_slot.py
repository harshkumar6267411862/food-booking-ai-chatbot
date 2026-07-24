from datetime import date, time

from pydantic import BaseModel, ConfigDict, Field, model_validator

class PickupSlotResponse(BaseModel):
    id: int
    slot_date: date
    start_time: time
    end_time: time
    estimated_wait_minutes: int
    available: bool

    model_config = ConfigDict(
        from_attributes=True
    )
    
    #ConfigDict tells pydantic "Hey.. the thing i am giving is not a dict, its a python object..."
    #ConfigDict is simply a configuration object that stores settings for how the model should behave.
    #SQLAlchemy is an ORM--> Object Relational Mapper
    
    '''
    ConfigDict(from_attributes=True) tells Pydantic to create the response model from an object's attributes (like a SQLAlchemy model) instead of expecting a dictionary.
    '''
    
class PickupSlotCreateRequest(BaseModel):
    slot_date: date
    start_time: time
    end_time: time
    max_orders: int = Field(gt=0)
    estimated_wait_minutes: int = Field(ge=0)
    
    @model_validator(mode='after')
    def check_time_range(self):
        if self.start_time >= self.end_time:
            raise ValueError("end_time must be after start_time")
        return self
    
class PickupSlotCreateResponse(BaseModel):
    id: int
    slot_date: date
    start_time: time
    end_time: time
    max_orders: int
    current_orders: int
    estimated_wait_minutes: int
    is_active: bool

    model_config = ConfigDict(
        from_attributes = True
    )
    
from datetime import date, time

class GeneratePickupSlotsRequest(BaseModel):
    slot_date: date
