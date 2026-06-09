# Cache key constants
CACHE_PRODUCT_LIST = "products:list:{}"  # page, filters
CACHE_PRODUCT_DETAIL = "products:detail:{}"  # product_id
CACHE_SELLER_DASHBOARD = "seller:dashboard:{}"  # user_id
CACHE_CATEGORY_LIST = "categories:list"
CACHE_HOMEPAGE = "homepage:data"

# Cache TTLs (seconds)
CACHE_TTL_PRODUCT_LIST = 300  # 5 minutes
CACHE_TTL_PRODUCT_DETAIL = 900  # 15 minutes
CACHE_TTL_SELLER_DASHBOARD = 600  # 10 minutes
CACHE_TTL_CATEGORIES = 3600  # 1 hour
