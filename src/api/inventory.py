from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import math
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/inventory",
    tags=["inventory"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.get("/audit")
def get_inventory():
    """ """
    sql_statement = sqlalchemy.text(""" with
                                        potions as (
                                            SELECT
                                            COALESCE(SUM(amount), 0) as potions
                                            from
                                            ledger
                                            where
                                            item = 'red'
                                            or item = 'green'
                                            or item = 'blue'
                                            or item = 'white'
                                            or item = 'yellow'
                                            or item = 'purple'
                                        ),
                                        ml as (
                                            SELECT
                                            COALESCE(SUM(amount), 0) as ml
                                            from
                                            ledger
                                            where
                                            item = 'red_ml'
                                            or item = 'green_ml'
                                            or item = 'blue_ml'
                                            or item = 'dark_ml'
                                        ),
                                        gold as(
                                            SELECT
                                            SUM(amount) as gold
                                            from
                                            ledger
                                            where
                                            item = 'gold'
                                        )
                                        select
                                        *
                                        from
                                        potions,
                                        ml, gold""")
    
    with db.engine.begin() as connection:
        inventory = connection.execute(sql_statement)
        for stuff in inventory:
        
            return {"num_of_potions": stuff.potions, 
                    "ml_in_barrels": stuff.ml, 
                    "gold": stuff.gold}

# Gets called once a day
@router.post("/plan")
def get_capacity_plan():
    """ 
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional 
    capacity unit costs 1000 gold.
    """
    
    pot_cap = 0
    ml_cap = 0
    
    """ with db.engine.begin() as connection:
        inventory = connection.execute(sql_statement)
        for stuff in inventory: 
            if(((stuff.potions - (stuff.potcap * 50)) > ((stuff.potcap * 50) * .8) or
               (stuff.ml - (stuff.mlcap * 10000)) > ((stuff.mlcap * 10000)* .2)) and 
               (stuff.gold - 1000 == 1000)
               ):
                pot_cap = 50
                ml_cap = 10000 """
             
    return {
        "potion_capacity": pot_cap,
        "ml_capacity": ml_cap
        }

class CapacityPurchase(BaseModel):
    potion_capacity: int
    ml_capacity: int

# Gets called once a day
@router.post("/deliver/{order_id}")
def deliver_capacity_plan(capacity_purchase : CapacityPurchase, order_id: int):
    """ 
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional 
    capacity unit costs 1000 gold.
    """
    
    

    return "OK"
