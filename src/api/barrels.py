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
    totRedML = 0
    totBlueML = 0
    totGold = 0

    print(f"barrels delivered: {barrels_delivered} order_id: {order_id}")
    with db.engine.begin() as connection:
        currGreenML = connection.execute(sqlalchemy.text("SELECT num_green_ml from global_inventory")).scalar()
        currRedML = connection.execute(sqlalchemy.text("SELECT num_red_ml from global_inventory")).scalar()
        currBlueML = connection.execute(sqlalchemy.text("SELECT num_blue_ml from global_inventory")).scalar()
        currGold = connection.execute(sqlalchemy.text("SELECT gold from global_inventory")).scalar()
    
        for barrel in barrels_delivered:
            if (barrel.potion_type == [0, 1, 0, 0]):
                totGreenML += (barrel.quantity * barrel.ml_per_barrel)
                totGold += (barrel.quantity * barrel.price)

            if (barrel.potion_type == [1, 0, 0, 0]):
                totRedML += (barrel.quantity * barrel.ml_per_barrel)
                totGold += (barrel.quantity * barrel.price)

            if (barrel.potion_type == [0, 0, 1, 0]):
                totBlueML += (barrel.quantity * barrel.ml_per_barrel)
                totGold += (barrel.quantity * barrel.price)

        
        currGreenML += totGreenML
        currRedML += totRedML
        currBlueML += totBlueML
        currGold -= totGold

        with db.engine.begin() as connection:
            connection.execute(sqlalchemy.text(
                f"UPDATE global_inventory SET gold = {currGold}, num_green_ml = {currGreenML}, num_red_ml = {currRedML}, num_blue_ml = {currBlueML}"))

    return "OK"

# Gets called once a day big juice!!!!!!
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(wholesale_catalog)

    with db.engine.begin() as connection:
        numRedPotion = connection.execute(sqlalchemy.text("SELECT num_red_potions from global_inventory")).scalar()
        numGreenPotion = connection.execute(sqlalchemy.text("SELECT num_green_potions from global_inventory")).scalar()
        numBluePotion = connection.execute(sqlalchemy.text("SELECT num_blue_potions from global_inventory")).scalar()
        bank = connection.execute(sqlalchemy.text("SELECT gold from global_inventory")).scalar()
        
        """ Switch potion priority under here """
        redPots = [1, 0, 0, 0]
        greenPots = [0, 1, 0, 0]
        bluePots = [0, 0, 1, 0]

        """ modify code under here """
        potion1Type = redPots
        potion2Type = greenPots
        potion3Type = bluePots

        numPotion1 = numRedPotion
        numPotion2 = numGreenPotion
        numPotion3 = numBluePotion

        potion1min = 10
        potion2min = 5
        potion3min = 5

        """ End of modification area """
        plan = []
        
    for barrel in wholesale_catalog:
        if ((barrel.potion_type == potion1Type) and (numPotion1 < potion1min) and barrel.quantity and (bank > barrel.price)):
            bank -= barrel.price 
            plan.append({
                "sku": barrel.sku,
                "quantity": 1,
            })
        elif ((barrel.potion_type == potion2Type) and (numPotion2 < potion2min) and barrel.quantity and (bank > barrel.price)):
            bank -= barrel.price 
            plan.append({
                "sku": barrel.sku,
                "quantity": 1,
            })
        elif ((barrel.potion_type == potion3Type) and (numPotion3 < potion3min) and barrel.quantity and (bank > barrel.price)):
            bank -= barrel.price 
            plan.append({
                "sku": barrel.sku,
                "quantity": 1,
            })

    return plan

