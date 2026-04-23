from pydantic import BaseModel

class CategoryBase(BaseModel):
    name: str

class CategoryCreate(CategoryBase):
    pass

class CategorySchema(CategoryBase):
    id: int
    
    class Config:
        from_attributes = True


class BookBase(BaseModel):
    title: str
    url: str
    price: float
    in_stock: bool
    rating: int
    category_id: int | None = None

class BookCreate(BookBase):
    pass

class BookUpdate(BaseModel):
    title: str | None = None
    url: str | None = None
    price: float | None = None
    in_stock: bool | None = None
    rating: int | None = None
    category_id: int | None = None
    
class BookSchema(BookBase):
    id: int
    category: CategorySchema | None = None
    
    class Config:
        from_attributes = True