from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from sqlalchemy.sql import *
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
    print(f"potions delivered: {potions_delivered} order_id: {order_id}")
              
    metadata_obj = sqlalchemy.MetaData()
    ledger = sqlalchemy.Table("ledger", metadata_obj, autoload_with = db.engine)            
    delete_zeros = delete(ledger).where(ledger.c.amount == 0)
    
    with db.engine.begin() as connection:
        for pots in potions_delivered:
            connection.execute(sqlalchemy.text("""INSERT INTO ledger (item, amount) VALUES
                                                    (:red_ml, :red_ml_amount),
                                                    (:green_ml, :green_ml_amount),
                                                    (:blue_ml, :blue_ml_amount)"""), 
                  [{"red_ml": "red_ml", "red_ml_amount":-(pots.quantity * pots.potion_type[0]),
                    "green_ml": "green_ml", "green_ml_amount":-(pots.quantity * pots.potion_type[1]),
                    "blue_ml": "blue_ml", "blue_ml_amount":-(pots.quantity * pots.potion_type[2])}])
            
            catalog = connection.execute(sqlalchemy.text("""SELECT sku, gold FROM potions
                                                  WHERE red = :red AND green = :green AND blue = :blue"""),
                               [{"red": pots.potion_type[0], "green": pots.potion_type[1], "blue": pots.potion_type[2]}])
            
            for stuff in catalog:
                connection.execute(sqlalchemy.text("""INSERT INTO ledger (item, amount) VALUES
                                                  (:gold, :gold_amount),
                                                  (:sku, :qty_amount)"""), 
                  [{"gold": "gold", "gold_amount": -(stuff.gold * pots.quantity), 
                    "sku": stuff.sku, "qty_amount": pots.quantity}])
                
        connection.execute(delete_zeros)
            
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

    curr_red_ml = 0
    curr_green_ml = 0
    curr_blue_ml = 0
    curr_dark_ml = 0

    plan = []
    with db.engine.begin() as connection:
        potions = connection.execute(sqlalchemy.text("SELECT qty, red, green, blue, dark, pot_min, pot_max FROM potions ORDER BY qty ASC"))
        curr_red_ml = connection.execute(sqlalchemy.text("SELECT num_red_ml FROM global_inventory")).scalar()
        curr_green_ml = connection.execute(sqlalchemy.text("SELECT num_green_ml FROM global_inventory")).scalar()
        curr_blue_ml = connection.execute(sqlalchemy.text("SELECT num_blue_ml FROM global_inventory")).scalar()
        curr_dark_ml = connection.execute(sqlalchemy.text("SELECT num_dark_ml FROM global_inventory")).scalar()
        """ select sum of ledger """
        for potion in potions:
            if (potion.qty < potion.pot_min and 
               (curr_red_ml > potion.red * potion.pot_max - potion.qty) and 
               (curr_green_ml > potion.green * potion.pot_max - potion.qty) and
               (curr_blue_ml > potion.blue * potion.pot_max - potion.qty) and
               (curr_dark_ml > potion.dark * potion.pot_max - potion.qty)):
                
                curr_red_ml = curr_red_ml - (potion.red * potion.pot_max - potion.qty)
                curr_green_ml = curr_green_ml - (potion.green * potion.pot_max - potion.qty)
                curr_blue_ml = curr_blue_ml - (potion.blue * potion.pot_max - potion.qty)
                curr_dark_ml = curr_dark_ml - (potion.dark * potion.pot_max - potion.qty)

                plan.append({
                "potion_type": [potion.red, potion.green, potion.blue, potion.dark],
                "quantity": potion.pot_max - potion.qty
                })
    return plan

if __name__ == "__main__":
    print(get_bottle_plan())