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
    print(f"barrels delivered: {barrels_delivered} order_id: {order_id}")
    insertion = """   INSERT INTO ledger 
                      (item, amount)
                      VALUES 
                      (:ml_color, :ml_amount),
                      (:gold, :gold_amount) """
              
    with db.engine.begin() as connection:
        for barrel in barrels_delivered:
            connection.execute(sqlalchemy.text(insertion), 
                           [{"ml_color": barrel.sku, "ml_amount": (barrel.ml_per_barrel * barrel.quantity),
                             "gold": "gold", "gold_amount": -(barrel.price * barrel.quantity)}])
            
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
                                        (SELECT 
                                            CASE 
                                            WHEN item IN ('red_ml') THEN 'red_ml'
                                            WHEN item IN ('green_ml') THEN 'green_ml'
                                            WHEN item IN ('blue_ml') THEN 'blue_ml'
                                            ELSE 'other sums' 
                                            END AS ml_color,
                                            item,
                                            COALESCE(SUM(amount), 0) AS amount
                                        FROM ledger
                                        GROUP BY ml_color, item) AS totals
                                        RIGHT JOIN barrel_minmax ON totals.ml_color = barrel_minmax.name
                                        ORDER BY amount DESC""")
    
    
    plan = []
    with db.engine.begin() as connection:
        curr_gold = connection.execute(gold_inventory).scalar()
        ml_totals = connection.execute(ml_inventory)
        
        for totals in ml_totals:
            for barrel in wholesale_catalog:
                if ((barrel.potion_type == [totals.red, totals.green, totals.blue, totals.dark]) and
                   (totals.amount < totals.min) and 
                   (totals.sku == barrel.sku) and
                   barrel.quantity > 0 and (curr_gold > barrel.price * totals.num_barrels_to_buy)):
                    
                    curr_gold -= barrel.price * totals.num_barrels_to_buy
                    plan.append({
                            "sku": barrel.sku,
                            "quantity": totals.num_barrels_to_buy
                    })
    return plan

