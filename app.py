from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import List
from pydantic import BaseModel, Field, validator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship

app = FastAPI()

SQLALCHEMY_DATABASE_URI = "mysql://root:root@localhost:3306/new_schema"
engine = create_engine(SQLALCHEMY_DATABASE_URI)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password = Column(String(100), nullable=False)

    def __repr__(self):
        return f'<User {self.first_name} {self.last_name}>'

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500), nullable=False)
    price = Column(Float, nullable=False)

    def __repr__(self):
        return f'<Product {self.name}>'

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    order_date = Column(DateTime, nullable=False)
    status = Column(String(20), nullable=False, default="pending")

    user = relationship("User", backref="orders")
    product = relationship("Product", backref="orders")

    def __repr__(self):
        return f'<Order {self.id}>'

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class UserSchema(BaseModel):
    first_name: str = Field(..., title="Имя", max_length=100)
    last_name: str = Field(..., title="Фамилия", max_length=100)
    email: str = Field(..., title="Email", max_length=100)
    password: str = Field(..., title="Пароль", max_length=100)

    @validator("email")
    def email_must_be_valid(cls, value):
        if "@" not in value or "." not in value:
            raise ValueError("Неверный формат email")
        return value

class ProductSchema(BaseModel):
    name: str = Field(..., title="Название", max_length=100)
    description: str = Field(..., title="Описание", max_length=500)
    price: float = Field(..., title="Цена")

class OrderSchema(BaseModel):
    user_id: int = Field(..., title="ID пользователя")
    product_id: int = Field(..., title="ID товара")
    status: str = Field("pending", title="Статус заказа")

# CRUD operations for Users
@app.get("/users", response_model=List[UserSchema])
async def get_users(db: SessionLocal = Depends(get_db)):
    users = db.query(User).all()
    users_data = [
        {
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
        }
        for user in users
    ]
    return JSONResponse(content=users_data)

@app.get("/users/{user_id}", response_model=UserSchema)
async def get_user(user_id: int, db: SessionLocal = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return JSONResponse(content=user.dict())

@app.post("/users", response_model=UserSchema, status_code=201)
async def create_user(user: UserSchema, db: SessionLocal = Depends(get_db)):
    db_user = User(
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        password=user.password,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return JSONResponse(content=user.dict())

@app.put("/users/{user_id}", response_model=UserSchema)
async def update_user(user_id: int, user: UserSchema, db: SessionLocal = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    db_user.first_name = user.first_name
    db_user.last_name = user.last_name
    db_user.email = user.email
    db_user.password = user.password
    db.commit()
    db.refresh(db_user)
    return JSONResponse(content=user.dict())

@app.delete("/users/{user_id}", status_code=204)
async def delete_user(user_id: int, db: SessionLocal = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    db.delete(db_user)
    db.commit()
    return JSONResponse(content=None)

# CRUD operations for Products
@app.get("/products", response_model=List[ProductSchema])
async def get_products(db: SessionLocal = Depends(get_db)):
    products = db.query(Product).all()
    products_data = [
        {
            "id": product.id,
            "name": product.name,
            "description": product.description,
            "price": product.price,
        }
        for product in products
    ]
    return JSONResponse(content=products_data)

@app.get("/products/{product_id}", response_model=ProductSchema)
async def get_product(product_id: int, db: SessionLocal = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Товар не найден")
    return JSONResponse(content=product.dict())

@app.post("/products", response_model=ProductSchema, status_code=201)
async def create_product(product: ProductSchema, db: SessionLocal = Depends(get_db)):
    db_product = Product(
        name=product.name, description=product.description, price=product.price
    )
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return JSONResponse(content=product.dict())

@app.put("/products/{product_id}", response_model=ProductSchema)
async def update_product(
    product_id: int, product: ProductSchema, db: SessionLocal = Depends(get_db)
):
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if db_product is None:
        raise HTTPException(status_code=404, detail="Товар не найден")
    db_product.name = product.name
    db_product.description = product.description
    db_product.price = product.price
    db.commit()
    db.refresh(db_product)
    return JSONResponse(content=product.dict())

@app.delete("/products/{product_id}", status_code=204)
async def delete_product(product_id: int, db: SessionLocal = Depends(get_db)):
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if db_product is None:
        raise HTTPException(status_code=404, detail="Товар не найден")
    db.delete(db_product)
    db.commit()
    return JSONResponse(content=None)

# CRUD operations for Orders
@app.get("/orders", response_model=List[OrderSchema])
async def get_orders(db: SessionLocal = Depends(get_db)):
    orders = db.query(Order).all()
    orders_data = [
        {
            "id": order.id,
            "user_id": order.user_id,
            "product_id": order.product_id,
            "order_date": order.order_date.isoformat(),
            "status": order.status,
        }
        for order in orders
    ]
    return JSONResponse(content=orders_data)

@app.get("/orders/{order_id}", response_model=OrderSchema)
async def get_order(order_id: int, db: SessionLocal = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if order is None:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    return JSONResponse(content=order.dict())

@app.post("/orders", response_model=OrderSchema, status_code=201)
async def create_order(order: OrderSchema, db: SessionLocal = Depends(get_db)):
    db_order = Order(
        user_id=order.user_id, product_id=order.product_id, status=order.status
    )
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    return JSONResponse(content=order.dict())

@app.put("/orders/{order_id}", response_model=OrderSchema)
async def update_order(
    order_id: int, order: OrderSchema, db: SessionLocal = Depends(get_db)
):
    db_order = db.query(Order).filter(Order.id == order_id).first()
    if db_order is None:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    db_order.user_id = order.user_id
    db_order.product_id = order.product_id
    db_order.status = order.status
    db.commit()
    db.refresh(db_order)
    return JSONResponse(content=order.dict())

@app.delete("/orders/{order_id}", status_code=204)
async def delete_order(order_id: int, db: SessionLocal = Depends(get_db)):
    db_order = db.query(Order).filter(Order.id == order_id).first()
    if db_order is None:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    db.delete(db_order)
    db.commit()
    return JSONResponse(content=None)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)