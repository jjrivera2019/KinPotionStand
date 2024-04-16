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
    
    totRedML = 0
    newRedPot = 0

    totGreenML = 0
    newGreenPot = 0

    totBlueML = 0
    newBluePot = 0

    print(f"potions delievered: {potions_delivered} order_id: {order_id}")

    with db.engine.begin() as connection:
        currRedML = connection.execute(sqlalchemy.text("SELECT num_red_ml from global_inventory")).scalar()
        currRedPot = connection.execute(sqlalchemy.text("SELECT num_red_potions from global_inventory")).scalar()
    
        currGreenML = connection.execute(sqlalchemy.text("SELECT num_green_ml from global_inventory")).scalar()
        currGreenPot = connection.execute(sqlalchemy.text("SELECT num_green_potions from global_inventory")).scalar()
    
        currBlueML = connection.execute(sqlalchemy.text("SELECT num_blue_ml from global_inventory")).scalar()
        currBluePot = connection.execute(sqlalchemy.text("SELECT num_blue_potions from global_inventory")).scalar()
    
        for pots in potions_delivered:
            if pots.potion_type == [100, 0, 0, 0]:
                newRedPot += pots.quantity
                totRedML += (pots.quantity * 100)
                
            if pots.potion_type == [0, 100, 0, 0]:
                newGreenPot += pots.quantity
                totGreenML += (pots.quantity * 100)
                
            if pots.potion_type == [0, 0, 100, 0]:
                newBluePot += pots.quantity
                totBlueML += (pots.quantity * 100)
                
        currRedML -= totRedML
        currRedPot += newRedPot
    
        currGreenML -= totGreenML
        currGreenPot += newGreenPot

        currBlueML -= totBlueML
        currBluePot += newBluePot

        with db.engine.begin() as connection:
            connection.execute(sqlalchemy.text(
                f"UPDATE global_inventory SET num_red_ml = {currRedML}, num_red_potions = {currRedPot}"))
            
            connection.execute(sqlalchemy.text(
                f"UPDATE global_inventory SET num_green_ml = {currGreenML}, num_green_potions = {currGreenPot}"))
            
            connection.execute(sqlalchemy.text(
                f"UPDATE global_inventory SET num_blue_ml = {currBlueML}, num_green_potions = {currBluePot}"))
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

    bottleToRedBarrel = 0
    bottleToGreenBarrel = 0
    bottleToBlueBarrel = 0

    plan = []
    with db.engine.begin() as connection:
        currRedML = connection.execute(sqlalchemy.text("SELECT num_red_ml FROM global_inventory")).scalar()
        currGreenML = connection.execute(sqlalchemy.text("SELECT num_green_ml FROM global_inventory")).scalar()
        currBlueML = connection.execute(sqlalchemy.text("SELECT num_blue_ml FROM global_inventory")).scalar()

        while (currRedML >= 100):
            bottleToBarrel += 1 
            currRedML -= 100
        
        while (currGreenML >= 100):
            bottleToBarrel += 1 
            currGreenML -= 100
        
        while (currBlueML >= 100):
            bottleToBarrel += 1 
            currBlueML -= 100
        

        if bottleToRedBarrel != 0:
            plan.append({
                "potion_type": [0, 100, 0, 0],
                "quantity": bottleToRedBarrel,
            })

        if bottleToGreenBarrel != 0:
            plan.append({
                "potion_type": [0, 100, 0, 0],
                "quantity": bottleToGreenBarrel,
            })

        if bottleToBlueBarrel != 0:
            plan.append({
                "potion_type": [0, 100, 0, 0],
                "quantity": bottleToBlueBarrel,
            })
    
    return plan

if __name__ == "__main__":
    print(get_bottle_plan())