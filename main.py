import requests

from authx.exceptions import MissingTokenError
from fastapi import FastAPI, Depends, Response, HTTPException,APIRouter
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from parser_wb import get_wb_data
from parser_aliexpress import get_aliexpress_data
import asyncio
from concurrent.futures import ThreadPoolExecutor
from DB import SessionLocal, create_product, Product as ProductModel, authenticate_user, create_user
import uvicorn
from authx import AuthX, AuthXConfig
from parser_ym import get_ym_data
from starlette import status
#from starlette.requests import Request
#import bcrypt
from urllib.parse import urlparse, parse_qs
from starlette.requests import Request

app = FastAPI()
executor = ThreadPoolExecutor(max_workers=5)

#config в другой файл?
config = AuthXConfig()
#Секретный токен
config.JWT_SECRET_KEY = "SECRET_KEY"
#Название токена
config.JWT_ACCESS_COOKIE_NAME = "my_access_token"
#JWT храниться в куках
config.JWT_TOKEN_LOCATION = ["cookies"]

security = AuthX(config=config)


origins = [
    "http://localhost",
    "http://localhost:5174",
    "http://localhost:5173"
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


class UserLoging(BaseModel):
    email: str
    password: str

@app.post("/login")
def loging(creds: UserLoging, response: Response,  db: Session = Depends(get_db)):
    user = authenticate_user(db, creds.email, creds.password)
    if not user:
        raise HTTPException(status_code=401)
    #if creds.email == "test" and creds.password == "test":
    token = security.create_access_token(uid="1234")
    response.set_cookie(config.JWT_ACCESS_COOKIE_NAME, token)
    return {"access_token": True}


@app.post("/register")
def register(creds: UserLoging, response: Response,  db: Session = Depends(get_db)):
    user = authenticate_user(db, creds.email, creds.password)
    if user:
        raise HTTPException(status_code=409)
    user = create_user(db, creds.email, creds.password)
    #if creds.email == "test" and creds.password == "test":
    token = security.create_access_token(uid="1234")
    response.set_cookie(config.JWT_ACCESS_COOKIE_NAME, token)
    return {"access_token": True}


@app.get("/protected", dependencies=[Depends(security.access_token_required)])
def protected():
    return {"data": "СЕКРЕТНАЯ КОНИНА"}


@app.exception_handler(MissingTokenError)
async def missing_access_token_exception_handler(request: Request, exc: MissingTokenError):
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=exc.args[0],
    )


@app.get("/parse/aliexpress", dependencies=[Depends(security.access_token_required)])
async def parse_aliexpress(url: str, db: Session = Depends(get_db)):
    loop = asyncio.get_event_loop()
    data = await loop.run_in_executor(executor, get_aliexpress_data, url)
    #Проверка на существующий продукт
    existing_product = db.query(ProductModel).filter(ProductModel.sku_id == int(data["sku_id"])).first()
    if existing_product:
        return {"message": "Продукт с таким sku_id уже существует.", "data": existing_product}
    create_product(db=db, sku_id=int(data['sku_id']), price=data['price'], name=data['name'], marketplace=data['marketplace'])
    return data

#GET http://localhost:8000/parse/wb?url=https://www.wildberries.ru/catalog/102855978760/detail.aspx
@app.get("/parse/wb", dependencies=[Depends(security.access_token_required)])
async def parse_wb(url: str, db: Session = Depends(get_db)):
    # Извлечение параметров из URL
    parsed_url = urlparse(url)
    path_parts = parsed_url.path.split('/')

    # Извлекаем nm_id из URL. Обычно он находится в пути, как последняя часть (например, /catalog/{nm_id}/detail.aspx)
    nm_id = path_parts[-2] if len(path_parts) > 1 else None

    if not nm_id:
        raise HTTPException(status_code=400, detail="Не удалось извлечь nm_id из URL")

    # Вызов парсера с nm_id
    loop = asyncio.get_event_loop()
    data = await loop.run_in_executor(executor, get_wb_data, nm_id)

    # Преобразуем данные перед их использованием
    # Да и до этого нормально работало
    nm_id_int = int(data["nm_id"])
    price_float = float(data["price"]) if data["price"] is not None else None

    # Проверка существующего продукта
    existing_product = db.query(ProductModel).filter(ProductModel.sku_id == nm_id_int).first()
    if existing_product:
        return {"message": "Продукт с таким nm_id уже существует.", "data": existing_product}

    # Запись в базу данных
    create_product(db=db, sku_id=nm_id_int, name=data['name'], price=price_float, marketplace=data['marketplace'])
    return data



#GET http://localhost:8000/parse/ym?url=https://market.yandex.ru/product--watch-pro-2/861347316?sku=103757197929&uniqueId=164019620&do-waremd5=7MWQCXC44b4uZevVEyURLA
# ... (остальные импорты остаются без изменений)
from urllib.parse import urlparse, parse_qs
import re


@app.get("/parse/ym", dependencies=[Depends(security.access_token_required)])
async def parse_ym(url: str, db: Session = Depends(get_db)):
    try:
        # Парсим URL напрямую без разворачивания
        parsed_url = urlparse(url)

        # Извлекаем sku из query-параметров
        query_params = parse_qs(parsed_url.query)
        sku = query_params.get('sku', [None])[0]

        # Извлекаем product_id через регулярное выражение (как в parser_ym.py)????
        product_id_match = re.search(r'/product--[^/]+/(\d+)', parsed_url.path)
        product_id = product_id_match.group(1) if product_id_match else None

        # Проверка на валидность параметров
        if not sku or not product_id:
            raise HTTPException(
                status_code=400,
                detail="URL должен содержать параметры sku и product_id"
            )

        # Проверяем, что product_id состоит из цифр
        if not product_id.isdigit():
            raise HTTPException(
                status_code=400,
                detail="Некорректный формат product_id"
            )

        # Запускаем парсер
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(executor, get_ym_data, sku, product_id)

        # Проверяем наличие ошибок в данных от парсера
        if "Ошибка" in data["name"]:
            raise HTTPException(
                status_code=404,
                detail=data["name"]
            )

        # Проверка на существующий продукт
        existing_product = db.query(ProductModel).filter(ProductModel.sku_id == data["nm_id"]).first()
        if existing_product:
            return {"message": "Продукт уже существует", "data": existing_product}

        # Сохраняем в БД
        create_product(
            db=db,
            sku_id=data["nm_id"],
            name=data["name"],
            price=data["price"],
            marketplace = data['marketplace']
        )

        return data

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Внутренняя ошибка сервера: {str(e)}"
        )
from auto_parser import router as auto_parser_router
app.include_router(auto_parser_router)


if __name__ == '__main__':
    uvicorn.run("main:app", host="localhost", port=8000, log_level="info")