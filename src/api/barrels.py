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

potion_type_to_color = {(1,0,0,0): "red_ml",
                        (0,1,0,0): "green_ml",
                        (0,0,1,0): "blue_ml",
                        (0,0,0,1): "dark_ml"}

@router.post("/deliver/{order_id}")
def post_deliver_barrels(barrels_delivered: list[Barrel], order_id: int):
    """ """
    print(f"barrels delivered: {barrels_delivered} order_id: {order_id}")
    
    insertion = """   INSERT INTO ledger 
                      (item, amount)
                      VALUES 
                      (:ml_color, :ml_amount),
                      (:gold, :gold_amount) """
    
    ledger_insert = []
    for barrel in barrels_delivered:
        ledger_insert.append({
            "ml_color": potion_type_to_color[(barrel.potion_type[0], barrel.potion_type[1], barrel.potion_type[2], barrel.potion_type[3])],
            "ml_amount": (barrel.ml_per_barrel * barrel.quantity),
            "gold": "gold",
            "gold_amount": -(barrel.price * barrel.quantity)
        })

    with db.engine.begin() as connection:
            connection.execute(sqlalchemy.text(insertion), ledger_insert)
            
    return "OK"

# Gets called once a day big juice!!!!!!

@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(wholesale_catalog)
    gold_inventory = sqlalchemy.text(""" 
    SELECT SUM(amount) as gold
    FROM ledger WHERE item = 'gold'
    """)
    
    ml_inventory = sqlalchemy.text("""SELECT
  COALESCE(totals.amount, 0) as amount,
  barrel_minmax.name,
  barrel_minmax.sku,
  barrel_minmax.red,
  barrel_minmax.green,
  barrel_minmax.blue,
  barrel_minmax.dark,
  barrel_minmax.min,
  barrel_minmax.max,
  barrel_minmax.num_barrels_to_buy
FROM
  (
    SELECT
      CASE
        WHEN item IN ('red_ml') THEN 'red_ml'
        WHEN item IN ('green_ml') THEN 'green_ml'
        WHEN item IN ('blue_ml') THEN 'blue_ml'
        ELSE 'other sums'
      END AS ml_color,
      item,
      COALESCE(SUM(amount), 0) AS amount
    FROM
      ledger
    GROUP BY
      ml_color,
      item
  ) AS totals
  RIGHT JOIN barrel_minmax ON totals.ml_color = barrel_minmax.name
WHERE name = 'red_ml' or name = 'green_ml' or name = 'blue_ml'
ORDER BY
  amount ASC""")
    
    plan = []
    
    with db.engine.begin() as connection:
        curr_gold = connection.execute(gold_inventory).scalar()
        ml_totals = connection.execute(ml_inventory)
        
        for totals in ml_totals:
            for barrel in wholesale_catalog:
                if ((barrel.potion_type == [totals.red, totals.green, totals.blue, totals.dark]) and
                    (totals.amount < totals.min) and 
                    (totals.sku == barrel.sku) and
                     barrel.quantity > 0 and (curr_gold >= barrel.price * totals.num_barrels_to_buy)):
                    
                    newamount = totals.amount
                    barrels_to_buy = 0
                    
                    while (newamount + barrel.ml_per_barrel < totals.max and
                           curr_gold > barrel.price and 
                           barrel.quantity >= barrels_to_buy + 1):
                        
                        newamount += barrel.ml_per_barrel
                        barrels_to_buy += 1
                        curr_gold -= barrel.price 
                        
                    plan.append({
                            "sku": barrel.sku,
                            "quantity": barrels_to_buy
                    })
    return plan

