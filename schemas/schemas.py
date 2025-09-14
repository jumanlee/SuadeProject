from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict

#like serailizers in Django

class UploadData(BaseModel):
#Dict mode: data["id"] or data["name"]
#Attribute mode: obj.id or obj.name
#use ConfigDict(from_attributes=True) so that when building this Pydantic model, allow it to pull values from object attributes instead of only dicts
#usually for ORM, which uses attributes, but UploadData is Pydantic, so not using attributes, but still defining ConfigDict(from_attributes=True) here even though not ORM, just to ensure consistency

    model_config = ConfigDict(from_attributes=True)
    row_count: int
    user_count: int
    product_count: int
    transaction_count: int
    duplicates_ignored: int


class Summary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    user_id: int
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    transaction_count: int
    mean: Optional[Decimal] = None
    maximum: Optional[Decimal] = None
    minimum: Optional[Decimal] = None
    
    

class ErrorResponse(BaseModel):
    detail: str
