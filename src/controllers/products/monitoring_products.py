from fastapi import HTTPException, status
from src.model.product import Produto


class ProductInfo:
    """
    Retrieve stock information for a given user.

    Args:
        user_id (int): ID of the user whose stock will be queried.

    Attributes:
        products (list): List to store product data.
        quantity (int): Total number of products.
        total_stock_price (float): Sum of all product costs.
        user_id (int): The user ID used for queries.
    """

    def __init__(self, user_id: int) -> None:
        """Initialize empty values and store user_id."""
        self.products: list = []
        self.quantity: int = 0
        self.total_stock_price: float = 0.0
        self.user_id: int = user_id

    async def _get_products(self):
        """
        Query the database for all products of the given user.

        Returns:
            list: A list of Produto objects.
        """
        try:
            products = await Produto.filter(usuario_id=self.user_id).all()
            return products
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database query error: {e}",
            )

    async def count_products(self) -> int:
        """
        Count how many products exist in the user's stock.

        Returns:
            int: Quantity of products in stock.
        """
        products = await self._get_products()
        self.quantity = len(products)
        return self.quantity

    async def calculate_total_stock_price(self) -> float:
        """
        Calculate the total cost of all products in stock.

        Returns:
            float: Total stock cost.
        """
        products = await self._get_products()
        self.total_stock_price = sum(prod.cost_price for prod in products)
        return round(self.total_stock_price, 2)

    async def get_products_by_category(self) -> list[dict]:
        """
        Separate products by category and return their details.

        Returns:
            list[dict]: List of product data grouped by category.
        """
        products = await self._get_products()
        self.products = [
            {
                "name": prod.name,
                "category": prod.group,
                "stock": prod.stock,
                "sale_price": prod.sale_price,
                "active": prod.active,
            }
            for prod in products
        ]
        return self.products

    @property
    def stock_summary(self) -> dict:
        """
        Property to return a summarized view of the stock data.

        Returns:
            dict: Summary with quantity and total price.
        """
        return {
            "user_id": self.user_id,
            "quantity": self.quantity,
            "total_stock_price": self.total_stock_price,
        }
