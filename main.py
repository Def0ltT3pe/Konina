from fastapi import FastAPI
from parser_wb import get_wb_price
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Инициализация FastAPI
app = FastAPI()

# Создание пула потоков
executor = ThreadPoolExecutor(max_workers=5)


@app.get("/parse/wb")
async def parse_wb(nm_id: str):
    loop = asyncio.get_event_loop()

    # Асинхронный вызов парсера в отдельном потоке
    price = await loop.run_in_executor(executor, get_wb_price, nm_id)
    return {"nm_id": nm_id, "price": price}
