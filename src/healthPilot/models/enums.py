import enum


class UserRole(str, enum.Enum):
    user = "user"
    admin = "admin"


class ProductCategory(str, enum.Enum):
    sleep = "sleep"
    fitness = "fitness"
    nutrition = "nutrition"
    mental_wellness = "mental_wellness"
    lifestyle = "lifestyle"


class VectorSyncStatus(str, enum.Enum):
    synced = "synced"
    pending = "pending"
    failed = "failed"


class EventType(str, enum.Enum):
    page_view = "page_view"
    product_view = "product_view"
    search = "search"
    category_filter = "category_filter"
    description_scroll = "description_scroll"
    product_return = "product_return"
    time_on_page = "time_on_page"
