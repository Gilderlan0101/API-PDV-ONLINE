
from pydantic import BaseModel
from typing import Optional

class EditCartItem(BaseModel):
    product_id: int
    quantity: Optional[int] = None
    discount: Optional[float] = None
    addition: Optional[float] = None
