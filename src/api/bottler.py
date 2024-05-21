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
                                                  (:sku, :qty_amount)"""), 
                  [{"sku": stuff.sku, "qty_amount": pots.quantity}])
                
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
    total_pots = """ SELECT
                        potions.sku,
                        potions.potions_id,
                        COALESCE(totals.amount, 0) as amount,
                        potions.pot_min,
                        potions.pot_max,
                        potions.red,
                        potions.green,
                        potions.blue,
                        potions.dark,
                        potions.buy
                        FROM
                        (
                            SELECT
                            CASE
                                WHEN item IN ('red') THEN 'red'
                                WHEN item IN ('green') THEN 'green'
                                WHEN item IN ('blue') THEN 'blue'
                                WHEN item IN ('cyan') THEN 'cyan'
                                WHEN item IN ('white') THEN 'white'
                                WHEN item IN ('purple') THEN 'purple'
                                ELSE 'other sums'
                            END AS pot,
                            item,
                            COALESCE(SUM(amount), 0) AS amount
                            FROM
                            ledger
                            GROUP BY
                            pot,
                            item
                        ) as totals
                        RIGHT JOIN potions ON totals.pot = potions.sku
                        ORDER BY
                        amount, potions_id ASC """
    
    goldMl_inventory = sqlalchemy.text("""with red_ml as (
                                        SELECT COALESCE(SUM(amount), 0) as red_ml
                                        FROM ledger
                                        WHERE item = 'red_ml'
                                        ),
                                        green_ml as (
                                        SELECT COALESCE(SUM(amount), 0) as green_ml
                                        FROM ledger
                                        WHERE item = 'green_ml'
                                        ), 
                                        blue_ml as (
                                        SELECT COALESCE(SUM(amount), 0) as blue_ml
                                        FROM ledger
                                        WHERE item = 'blue_ml'
                                        ),
                                        dark_ml as (
                                        SELECT COALESCE(SUM(amount), 0) as dark_ml
                                        FROM ledger
                                        WHERE item = 'dark_ml'
                                        ),
                                        gold as (
                                        SELECT SUM(amount) as gold
                                        FROM ledger
                                        WHERE item = 'gold'
                                        )
                                        SELECT
                                        *
                                        FROM red_ml, green_ml, blue_ml, dark_ml, gold""")

    plan = []
    with db.engine.begin() as connection:
        tot_pots = connection.execute(sqlalchemy.text(total_pots))
        
        inventory= connection.execute(goldMl_inventory)
        
        for items in inventory:
            currRed = items.red_ml
            currGreen = items.green_ml
            currBlue = items.blue_ml
            currDark = items.dark_ml
            
            for pots in tot_pots:
                if (pots.amount <= pots.pot_min and 
                   (currRed >= (pots.red)) and 
                   (currGreen >= (pots.green)) and 
                   (currBlue >= (pots.blue)) and 
                   (currDark >= (pots.dark))):
                    
                    pots_qty = 1
                    while((currRed >= (pots.red * pots_qty)) and 
                          (currGreen >= (pots.green * pots_qty)) and 
                          (currBlue >= (pots.blue * pots_qty)) and 
                          (currDark >= (pots.dark * pots_qty)) and 
                          (pots.pot_max > pots_qty)):
                    
                            pots_qty += 1
                
                    currRed -= (pots.red * pots_qty) 
                    currGreen -= (pots.green * pots_qty) 
                    currBlue -= (pots.blue * pots_qty) 
                    currDark -= (pots.dark * pots_qty) 
                    
                    plan.append({
                    "potion_type": [pots.red, pots.green, pots.blue, pots.dark],
                    "quantity": pots_qty})

    return plan

if __name__ == "__main__":
    print(get_bottle_plan())