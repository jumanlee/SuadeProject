from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

#like serailizers in Django but these are for reponse values only

class UploadData(BaseModel):
#Dict mode: data["id"] or data["name"]
#Attribute mode: obj.id or obj.name
#use ConfigDict(from_attributes=True) so that when building this Pydantic model, allow it to pull values from object attributes instead of only dicts
#usually for ORM, which uses attributes, but UploadData is Pydantic, so not using attributes, but still defining ConfigDict(from_attributes=True) here even though not ORM, just to ensure consistency

#add extra="forbid" to reject any unexpected fields during validation
    model_config = ConfigDict(from_attributes=True, extra="forbid")
    row_count: int = Field(ge=0) #no -ve values!
    user_count: int = Field(ge=0)
    product_count: int = Field(ge=0)
    transaction_count: int = Field(ge=0)
    duplicates_ignored: int = Field(ge=0)


class Summary(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")
    user_id: int
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    transaction_count: int
    mean: Optional[Decimal] = None
    maximum: Optional[Decimal] = None
    minimum: Optional[Decimal] = None
    
    

class ErrorResponse(BaseModel):
    detail: str
