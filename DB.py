from typing import Optional

from passlib.context import CryptContext
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import sessionmaker, Session, declarative_base
import os

# Получаем абсолютный путь к файлу базы данных
absolute_path = os.path.abspath('./data_base.db')
print(absolute_path)


DATABASE_URL = "sqlite:///" + absolute_path

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Product(Base):
    __tablename__ = "products"

    sku_id = Column(Integer, primary_key=True, index=True)
    #source = Column(String) # Вб или алик
    name = Column(String)
    price = Column(Float)
    marketplace = Column(String)


class User(Base):
    __tablename__ = "users"
    user_email = Column(String, primary_key=True, index=True)
    password = Column(String)

# Создайте таблицы в базе данных
Base.metadata.create_all(bind=engine)


def get_product(db: Session, sku_id: str):
    return db.query(Product).filter(Product.sku_id == sku_id).first()


def create_product(db: Session, sku_id: int, price: float, name: str, marketplace: str):
    db_product = Product(sku_id=sku_id, name=name, price=price, marketplace=marketplace)
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


def update_product(db: Session, sku_id: int, price: float, name: str):
    # Найти
    db_product = db.query(Product).filter(Product.sku_id == sku_id).one()

    # Обновление полей
    db_product.name = name
    db_product.price = price
    db.commit()
    db.refresh(db_product)
    return db_product

###

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str):
    return pwd_context.hash(password)

# Функции для работы с пользователями
def get_user(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.user_email == email).first()

def authenticate_user(db: Session, email: str, password: str):
    user = get_user(db, email)
    if not user:
        return False
    if not verify_password(password, user.password):
        return False
    return user

def create_user(db: Session, email: str, password: str):
    hashed_password = get_password_hash(password)
    db_user = User(user_email=email, password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user