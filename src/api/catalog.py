from fastapi import APIRouter
import sqlalchemy
from src import database as db

router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """
    cat = []
    with db.engine.begin() as connection:    
        rows = connection.execute(sqlalchemy.text("""SELECT
                                                    potions.sku,
                                                    potions.name,
                                                    COALESCE(totals.amount, 0) as amount,
                                                    potions.red,
                                                    potions.green,
                                                    potions.blue,
                                                    potions.dark,
                                                    potions.gold
                                                    FROM
                                                    (
                                                        SELECT
                                                        CASE
                                                            WHEN item IN ('red') THEN 'red'
                                                            WHEN item IN ('green') THEN 'green'
                                                            WHEN item IN ('blue') THEN 'blue'
                                                            WHEN item IN ('white') THEN 'white'
                                                            WHEN item IN ('purple') THEN 'purple'
                                                            WHEN item IN ('yellow') THEN 'yellow'
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
                                                    RIGHT JOIN potions ON totals.pot = potions.sku"""))

        for row in rows:       
            if row.amount > 0:
                cat.append({
                    "sku": row.sku,
                    "name": row.name,
                    "quantity": row.amount,
                    "price": row.gold,
                    "potion_type": [row.red, row.green, row.blue, row.dark]
                })

    return cat
