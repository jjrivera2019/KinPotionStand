from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
from enum import Enum
import sqlalchemy
from src import database as db
from datetime import date
router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)

class search_sort_options(str, Enum):
    customer_name = "customer_name"
    item_sku = "item_sku"
    line_item_total = "line_item_total"
    timestamp = "timestamp"

class search_sort_order(str, Enum):
    asc = "asc"
    desc = "desc"   

@router.get("/search/", tags=["search"])
def search_orders(
    customer_name: str = "",
    potion_sku: str = "",
    search_page: str = "",
    sort_col: search_sort_options = search_sort_options.timestamp,
    sort_order: search_sort_order = search_sort_order.desc,
):
    """
    Search for cart line items by customer name and/or potion sku.

    Customer name and potion sku filter to orders that contain the 
    string (case insensitive). If the filters aren't provided, no
    filtering occurs on the respective search term.

    Search page is a cursor for pagination. The response to this
    search endpoint will return previous or next if there is a
    previous or next page of results available. The token passed
    in that search response can be passed in the next search request
    as search page to get that page of results.

    Sort col is which column to sort by and sort order is the direction
    of the search. They default to searching by timestamp of the order
    in descending order.

    The response itself contains a previous and next page token (if
    such pages exist) and the results as an array of line items. Each
    line item contains the line item id (must be unique), item sku, 
    customer name, line item total (in gold), and timestamp of the order.
    Your results must be paginated, the max results you can return at any
    time is 5 total line items.
    """

    return {
        "previous": "",
        "next": "",
        "results": [
            {
                "line_item_id": 1,
                "item_sku": "1 oblivion potion",
                "customer_name": "Scaramouche",
                "line_item_total": 50,
                "timestamp": "2021-01-01T00:00:00Z",
            }
        ],
    }


class Customer(BaseModel):
    customer_name: str
    character_class: str
    level: int

@router.post("/visits/{visit_id}")
def post_visits(visit_id: int, customers: list[Customer]):
    """
    Which customers visited the shop today?
    """
    

    print(customers)

    return "OK"


@router.post("/")
def create_cart(new_cart: Customer):
    """ """
    with db.engine.begin() as connection:
        #check if customer exists

        customer_id = connection.execute(sqlalchemy.text(
            "SELECT customer_id FROM customers WHERE name = (:name) AND class = (:class) AND level = (:level)"), 
            [{"name": new_cart.customer_name, "class": new_cart.character_class, "level": new_cart.level}]).scalar()
        
        if (customer_id is None):
            customer_id = connection.execute(sqlalchemy.text(
                "INSERT INTO customers (name, class, level) VALUES (:name, :class, :level) RETURNING customer_id"), 
                [{"name": new_cart.customer_name, "class": new_cart.character_class, "level": new_cart.level}]).scalar()

        cart_id = connection.execute(sqlalchemy.text(
            "INSERT INTO carts (customer_id) VALUES (:customer_id) RETURNING cart_id"), 
            [{"customer_id": customer_id}]).scalar()
        
    return {"cart_id": cart_id}

class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ """
    """ INSERT INTO cart_items (cart_id, quantity, catalog_id) 
        SELECT :cart_id, :quantity, catalog.id 
        FROM catalog WHERE catalog.sku = :item_sku """
        
    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text(
            "INSERT INTO cart_items (cart_id, item_sku, qty) VALUES (:cart_id, :sku, :qty)"), 
            [{"cart_id": cart_id, "sku": item_sku, "qty": cart_item.quantity}])
        
    return "OK"


class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """
    totalPots = 0
    totalGold = 0

    with db.engine.begin() as connection:
        potions = connection.execute(sqlalchemy.text("SELECT sku FROM potions"))
        
        items = connection.execute(sqlalchemy.text("SELECT item_sku,  FROM cart_items WHERE cart_id = :cart_id"),
                                   [{"cart_id": cart_id}])
        for potion in potions:
            for item in items:
                if item.item_sku == potion.sku:
                    connection.execute(sqlalchemy.text("UPDATE potions SET qty = potions.qty - :qty WHERE potions.sku = :potions_sku"),
                                       [{"qty": item.qty, "potions_sku": item.item_sku}])
                    
                    connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold = global_inventory.gold + :pot_gold"),
                                       [{"pot_gold": potion.gold * item.qty}])
                    
                    totalPots += item.qty
                    totalGold += potion.gold * item.qty                   

        
    return {"total_potions_bought": totalPots, "total_gold_paid": totalGold}
