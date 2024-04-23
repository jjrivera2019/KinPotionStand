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
        rows = connection.execute(sqlalchemy.text("SELECT * FROM potions"))

        for row in rows:       
            if row.qty > 0:
                cat.append({
                    "sku": row.sku,
                    "name": row.name,
                    "quantity": row.qty,
                    "price": row.gold,
                    "potion_type": [row.red, row.green, row.blue, row.dark]
                })

    return cat
