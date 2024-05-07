from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
import sqlalchemy 
from sqlalchemy.sql import *
from src import database as db

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.post("/reset")
def reset():
    """
    Reset the game state. Gold goes to 100, all potions are removed from
    inventory, and all barrels are removed from inventory. Carts are all reset.
    """
    metadata_obj = sqlalchemy.MetaData()
    ledger = sqlalchemy.Table("ledger", metadata_obj, autoload_with = db.engine)
    
    metadata_obj1 = sqlalchemy.MetaData()
    carts = sqlalchemy.Table("carts", metadata_obj1, autoload_with = db.engine)
    
    metadata_obj2 = sqlalchemy.MetaData()
    cart_items = sqlalchemy.Table("cart_items", metadata_obj2, autoload_with = db.engine)
    
    subquery = select(ledger.c.id).offset(3)
    delete_ledger = delete(ledger).where(ledger.c.id.in_(subquery))
    
    delete_cart = delete(carts).where(carts.c.cart_id > 0)
    delete_cart_items = delete(cart_items).where(cart_items.c.cart_id > 0)


    with db.engine.begin() as connection:
        connection.execute(delete_ledger)
        connection.execute(delete_cart)
        connection.execute(delete_cart_items)
    
    return "OK"

