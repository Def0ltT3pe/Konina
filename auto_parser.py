# auto_parser.py
from fastapi import APIRouter, HTTPException
from urllib.parse import urlparse, parse_qs
import asyncio

from parser_wb import get_wb_data
from parser_aliexpress import get_aliexpress_data
from parser_ym import get_ym_data

router = APIRouter()

@router.get("/parse/auto")
async def parse_auto(url: str):
    parsed_url = urlparse(url)
    netloc = parsed_url.netloc

    loop = asyncio.get_event_loop()

    # Wildberries
    if "wildberries.ru" in netloc:
        try:
            nm_id = parsed_url.path.split("/catalog/")[1].split("/")[0]
            data = await loop.run_in_executor(None, get_wb_data, nm_id)
            return data
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Ошибка при парсинге WB: {str(e)}")

    # AliExpress
    if "aliexpress" in netloc:
        try:
            data = await loop.run_in_executor(None, get_aliexpress_data, url)
            return data
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Ошибка при парсинге AliExpress: {str(e)}")

    # Яндекс.Маркет
    if "market.yandex" in netloc:
        try:
            query_params = parse_qs(parsed_url.query)
            sku = query_params.get("sku", [None])[0]
            product_id = parsed_url.path.split("/")[-1]
            if not sku or not product_id:
                raise ValueError("Невозможно извлечь sku и product_id из ссылки.")
            data = await loop.run_in_executor(None, get_ym_data, sku, product_id)
            return data
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Ошибка при парсинге Яндекс.Маркет: {str(e)}")

    raise HTTPException(status_code=400, detail="Неизвестный источник ссылки.")
