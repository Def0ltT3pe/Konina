import uvicorn
from fastapi import FastAPI, HTTPException, Query
from parser_wb import get_wb_data
import asyncio
from concurrent.futures import ThreadPoolExecutor
from parser_ym import get_ym_data
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
executor = ThreadPoolExecutor(max_workers=5)

@app.get("/parse/wb")
async def parse_wb(nm_id: str = Query(..., pattern=r"^\d+$")):
    loop = asyncio.get_event_loop()
    try:
        result = await loop.run_in_executor(executor, get_wb_data, nm_id)
        if result.get("name") and "Ошибка" in result["name"]:
            raise ValueError(result["name"])
        if not result.get("name"):
            raise ValueError("Название товара не найдено")
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")
@app.get("/parse/ym")
async def parse_ym(sku: str = Query(..., pattern=r"^\d+$"), product_id: str = Query(..., pattern=r"^\d+$")):
    loop = asyncio.get_event_loop()
    try:
        result = await loop.run_in_executor(executor, get_ym_data, sku, product_id)
        if result.get("name") and "Ошибка" in result["name"]:
            raise ValueError(result["name"])
        if not result.get("name"):
            raise ValueError("Название товара не найдено")
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")


if __name__ == '__main__':
    uvicorn.run(app)