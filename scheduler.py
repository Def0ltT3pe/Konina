from fastapi import FastAPI, Depends
from rocketry import Rocketry
from rocketry.conds import daily
import asyncio
from sqlalchemy.orm import Session
from DB import create_product, Product as ProductModel, SessionLocal, update_product
from parser_aliexpress import get_aliexpress_data
from concurrent.futures import ThreadPoolExecutor
app = Rocketry()
executor = ThreadPoolExecutor(max_workers=5)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create some tasks:


@app.task(daily.after("15:30"))
@app.get('/update/all_aliexpress')
async def update_all_aliexpress(db: Session = Depends(get_db)):
    # Получаем колонку sku_id
    sku_ids = db.query(ProductModel).with_entities(ProductModel.sku_id).all()
    # Список этой колонки
    products = [sku_id[0] for sku_id in sku_ids]
    update_results = []
    for product in products:
        sku_id = product.sku_id
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(executor, get_aliexpress_data, sku_id)
        
        if product.sku_id == int(data["sku_id"]):
            # Обновляем продукт
            updated_product = update_product(db=db, sku_id=int(data['sku_id']), price=data['price'], name=data['name'])
            if updated_product:
                update_results.append({"sku_id": product.sku_id, "status": "Обновлен"})
            else:
                update_results.append({"sku_id": product.sku_id, "status": "Не удалось обновить"})