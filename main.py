from fastapi import FastAPI
from parser_wb1 import get_wb_price
from parser_aliexpress import get_aliexpress_data
import asyncio
from concurrent.futures import ThreadPoolExecutor

app = FastAPI()
executor = ThreadPoolExecutor(max_workers=5)

@app.get("/parse/wb")
async def parse_wb(nm_id: str):
    loop = asyncio.get_event_loop()
    price = await loop.run_in_executor(executor, get_wb_price, nm_id)
    return {"nm_id": nm_id,"price": price}


@app.get("/parse/aliexpress")
async def parse_aliexpress(url: str):
    loop = asyncio.get_event_loop()
    data = await loop.run_in_executor(executor, get_aliexpress_data, url)
    return data
