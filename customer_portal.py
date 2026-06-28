from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class Item(BaseModel):
    name: str
    description: str = None
    price: float
    tax: float = None

@app.post("/api/v1/virtual/items/", tags=["quantum-as-a-service"])
async def create_item(item: Item):
    return {
        **item.dict(),
        "claim_boundary": "This API path is a virtual/mathematical implementation.",
    }

@app.get("/api/v1/virtual/items/{item_id}", tags=["quantum-as-a-service"])
async def get_item(item_id: int):
    if item_id == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    return {
        "item_id": item_id,
        "name": "Sample Item",
        "claim_boundary": "This API path is a virtual/mathematical implementation.",
    }
