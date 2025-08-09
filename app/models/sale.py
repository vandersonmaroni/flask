# app/models/sale.py
from pydantic import BaseModel, ConfigDict
from datetime import date, datetime

class Sale(BaseModel):
    sale_date: date
    product_id: str
    quantity: int
    total_value: float
    
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True
    )
