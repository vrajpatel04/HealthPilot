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
