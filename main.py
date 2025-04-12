from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from parser_wb import get_wb_data
from parser_aliexpress import get_aliexpress_data
import asyncio
from concurrent.futures import ThreadPoolExecutor
from DB import SessionLocal, create_product
import uvicorn

from parser_ym import get_ym_data

app = FastAPI()
executor = ThreadPoolExecutor(max_workers=5)

origins = [
    "http://localhost",
    "http://localhost:5174",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


@app.get("/parse/wb")
async def parse_wb(nm_id: str, db: Session = Depends(get_db)):
    loop = asyncio.get_event_loop()
    data = await loop.run_in_executor(executor, get_wb_data, nm_id)
    create_product(db=db, sku_id=data['nm_id'],  name=data['name'], price=data['price'])
    return data


@app.get("parse/ym")
async def parse_ym(sku: str, product_id: str, db: Session = Depends(get_db)):
    loop = asyncio.get_event_loop()
    data = await loop.run_in_executor(executor, get_ym_data,  sku, product_id)
    create_product(db=db, sku_id=data['nm_id'], name = data['name'], price=data['price'])
    return data


if __name__ == '__main__':
    uvicorn.run("main:app", host="localhost", port=8000, log_level="info")