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
    print(f"barrels delivered: {barrels_delivered} order_id: {order_id}")
    with db.engine.begin() as connection:
        currGreenML = connection.execute(sqlalchemy.text("SELECT num_green_ml from global_inventory")).scalar()
        currGold = connection.execute(sqlalchemy.text("SELECT gold from global_inventory")).scalar()
    
        for barrel in barrels_delivered:
            if (barrel.sku == "green"):
                totGreenML += (barrel.quantity * barrel.ml_per_barrel)
                totGold += (barrel.quantity * barrel.price)

        currGreenML += totGreenML
        currGold -= totGold

        with db.engine.begin() as connection:
            connection.execute(sqlalchemy.text(
                f"UPDATE global_inventory SET gold = {currGold}"))
            
            connection.execute(sqlalchemy.text(
                f"UPDATE global_inventory SET mum_green_ml = {currGreenML}"))

    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(wholesale_catalog)
    wantGreenBarrels = 0
    with db.engine.begin() as connection:
        numGreenPotion = connection.execute(sqlalchemy.text("SELECT num_green_potions from global_inventory")).scalar()
        if (numGreenPotion < 10):
            wantGreenBarrels = 1
        else:
            return []

    for barrel in wholesale_catalog:
        if (barrel.potion_type == [0, 1, 0, 0]):
            sku = barrel.sku
        else:
            sku = 0
    return [
        {
            "sku": sku,
            "quantity": wantGreenBarrels,
        }
    ]

