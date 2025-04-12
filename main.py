from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from parser_wb1 import get_wb_price
from parser_aliexpress import get_aliexpress_data
import asyncio
from concurrent.futures import ThreadPoolExecutor
from DB import SessionLocal, create_product
import uvicorn


app = FastAPI()
executor = ThreadPoolExecutor(max_workers=5)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/parse/aliexpress")
async def parse_aliexpress(url: str, db: Session = Depends(get_db)):
    loop = asyncio.get_event_loop()
    data = await loop.run_in_executor(executor, get_aliexpress_data, url)
    create_product(db=db, sku_id=data['sku_id'], price=data['price'], name=data['name'])
    return data


@app.get("/parse/wb1")
async def parse_wb(nm_id: str):
    loop = asyncio.get_event_loop()
    price = await loop.run_in_executor(executor, get_wb_price, nm_id)
    #create_product(db=db, nm_id=nm_id, price=price, source='wb')
    return {"nm_id": nm_id,"price": price}


if __name__ == '__main__':
    uvicorn.run("main:app", host="127.0.0.1", port=8000, log_level="info")