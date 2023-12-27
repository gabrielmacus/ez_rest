from ez_rest.modules.mapper.services import mapper_services
from tests.modules.products.models import Product, ProductReadDTO, ProductSaveDTO
from ez_rest.modules.mapper.models import IgnoredAttr

mapper_services.register(
    Product,
    ProductReadDTO,
    {
        "name_category":lambda src: IgnoredAttr() if \
            "name" not in src or "category" not in src \
            else f'{src["name"]} {src['category'] or ''}'.strip(),
    }
)

mapper_services.register(
    ProductSaveDTO,
    Product,
    {
        "name":lambda src: src.get('product_name', IgnoredAttr()),
        "category":lambda src: src.get('product_category', IgnoredAttr()),
        "price":lambda src: src.get('product_price', IgnoredAttr()),
    }

)