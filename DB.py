from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import sessionmaker, Session, declarative_base
import os

# Получаем абсолютный путь к файлу базы данных
absolute_path = os.path.abspath('./data_base.db')
print(absolute_path)


DATABASE_URL = "sqlite:///" + absolute_path  # Замените на ваш URL базы данных

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Product(Base):
    __tablename__ = "products"

    sku_id = Column(Integer, primary_key=True, index=True)
    #source = Column(String) # Вб или алик
    name = Column(String)
    price = Column(Float)


class User(Base):
    __tablename__ = "users"
    user_email = Column(String, primary_key=True, index=True)
    password = Column(String)

# Создайте таблицы в базе данных
Base.metadata.create_all(bind=engine)


def get_product(db: Session, sku_id: str):
    return db.query(Product).filter(Product.sku_id == sku_id).first()


def create_product(db: Session, sku_id: str, price: float, name: str):
    db_product = Product(sku_id=sku_id, name=name, price=price)
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product