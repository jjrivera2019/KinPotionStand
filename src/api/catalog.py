from fastapi import APIRouter
import sqlalchemy
from src import database as db

router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """

    """ modify prices here """
    redPrice = 50
    greenPrice = 50
    bluePrice = 50

    redQty = 1
    greenQty = 1
    blueQty = 1

    """ End of modification """
    cat = []
    with db.engine.begin() as connection:
        currRedPots = connection.execute(sqlalchemy.text("SELECT num_red_potions FROM global_inventory")).scalar()
        currGreenPots = connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory")).scalar()
        currBluePots = connection.execute(sqlalchemy.text("SELECT num_blue_potions FROM global_inventory")).scalar()

        if currRedPots > 0:
            cat.append({
                "sku": "RED_POTION",
                "name": "red potion",
                "quantity": redQty,
                "price": redPrice,
                "potion_type": [1, 0, 0, 0]
            })

        if currGreenPots > 0:
            cat.append({
                "sku": "GREEN_POTION",
                "name": "green potion",
                "quantity": greenQty,
                "price": greenPrice,
                "potion_type": [0, 1, 0, 0]
            })

        if currBluePots > 0:
            cat.append({
                "sku": "BLUE_POTION",
                "name": "blue potion",
                "quantity": blueQty,
                "price": bluePrice,
                "potion_type": [0, 0, 1, 0]
            })

    return cat
