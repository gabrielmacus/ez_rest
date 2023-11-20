import math

class PaginationServices():
    def get_offset(self, page:int, limit:int) -> int:
        """Calculates pagination offset

        Args:
            page (int): Page number
            limit (int): Max number of items per page

        Returns:
            int: Number of items that should be ignored in pagination
        """
        return (page - 1) * limit

    def get_pages_count(
            self, 
            count:int, 
            limit:int
        ) -> int:
        """Calculates number of pages

        Args:
            count (int): Number of total items
            limit (int): Max number of items per page

        Returns:
            int: Total pages
        """
        return math.ceil(count / limit)