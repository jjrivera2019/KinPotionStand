from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/barrels",
    tags=["barrels"],
    dependencies=[Depends(auth.get_api_key)],
)

class Barrel(BaseModel):
    sku: str

    ml_per_barrel: int
    potion_type: list[int]
    price: int

    quantity: int

@router.post("/deliver/{order_id}")
def post_deliver_barrels(barrels_delivered: list[Barrel], order_id: int):
    """ """
    totGreenML = 0
    totGold = 0
    print(f"barrels delievered: {barrels_delivered} order_id: {order_id}")
    with db.engine.begin() as connection:
        currGreenML = connection.execute(sqlalchemy.text("SELECT from num_green_ml from global_inventory")).scalar()
        currGold = connection.execute(sqlalchemy.text("SELECT from gold from global_inventory")).scalar()
    
        for Barrel in barrels_delivered:
            totGreenML += (Barrel.quantity * Barrel.ml_per_barrel)
            totGold += (Barrel.quantity * Barrel.price)

        currGreenML += totGreenML
        currGold -= totGold

        with db.engine.begin() as connection:
            connection.execute(sqlalchemy.text(
                f"UPDATE global_inventory SET gold = {currGold}, num_green_ml = {currGreenML}"))
    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(wholesale_catalog)
    wantGreenBarrels = 0
    with db.engine.begin() as connection:
        numGreenPotion = connection.execute(sqlalchemy.text("SELECT from num_green_potions from global_inventory")).scalar
        if (numGreenPotion < 10):
            wantGreenBarrels = 1
        i = 0
    for barrel in wholesale_catalog:
        if wholesale_catalog[i].potion_type == [0, 100, 0, 0]:
            newSku = wholesale_catalog[i].sku
        i += 1 
    return [
        {
            "sku": newSku,
            "quantity": wantGreenBarrels,
        }
    ]

