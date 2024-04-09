from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/bottler",
    tags=["bottler"],
    dependencies=[Depends(auth.get_api_key)],
)

class PotionInventory(BaseModel):
    potion_type: list[int]
    quantity: int

@router.post("/deliver/{order_id}")
def post_deliver_bottles(potions_delivered: list[PotionInventory], order_id: int):
    """ """
    totGreenML = 0
    newGreenPot = 0
    print(f"potions delievered: {potions_delivered} order_id: {order_id}")

    with db.engine.begin() as connection:
        currGreenML = connection.execute(sqlalchemy.text("SELECT from num_green_ml from global_inventory")).scalar()
        currGreenPot = connection.execute(sqlalchemy.text("SELECT from num_green_potions from global_inventory")).scalar()
    
        for pots in potions_delivered:
            if pots.potion_type == [0, 100, 0, 0]:
                newGreenPot += pots.quantity
                totGreenML += (pots.quantity * 100)
                
        currGreenML -= totGreenML
        currGreenPot += newGreenPot

        with engine.begin() as connection:
            connection.execute(sqlalchemy.text(
                f"UPDATE global_inventory SET num_green_ml = {currGreenML}, num_green_potions = {currGreenPot}"))
    return "OK"

@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """

    # Each bottle has a quantity of what proportion of red, blue, and
    # green potion to add.
    # Expressed in integers from 1 to 100 that must sum up to 100.

    # Initial logic: bottle all barrels into red potions.

    bottleToBarrel = 0
    with engine.begin() as connection:
        currGreenML = connection.execute(sqlalchemy.text("SELECT num_green_ml FROM global_inventory")).scalar()

        while currGreenML >= 100:
            bottleToBarrel += 1 
            currGreenML -= 100

    return [
            {
                "potion_type": [0, 100, 0, 0],
                "quantity": bottleToBarrel,
            }
        ]

if __name__ == "__main__":
    print(get_bottle_plan())