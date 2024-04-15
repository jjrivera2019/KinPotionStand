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
        currGreenPots = connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory")).scalar()

        if currGreenPots > 0:
            [
            {
                "sku": "GREEN_POTION_0",
                "name": "green potion",
                "quantity": 1,
                "price": 50,
                "potion_type": [0, 1, 0, 0]
            }
        ]

    return cat
