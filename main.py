from authx.exceptions import MissingTokenError
from fastapi import FastAPI, Depends, Response, HTTPException
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
from starlette.requests import Request
import bcrypt

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
        return data
    create_product(db=db, sku_id=int(data['sku_id']), price=data['price'], name=data['name'])
    return data


@app.get("/parse/wb", dependencies=[Depends(security.access_token_required)])
async def parse_wb(nm_id: str, db: Session = Depends(get_db)):
    loop = asyncio.get_event_loop()
    data = await loop.run_in_executor(executor, get_wb_data, nm_id)
    existing_product = db.query(ProductModel).filter(ProductModel.sku_id == data["nm_id"]).first()
    if existing_product:
        return data
    create_product(db=db, sku_id=data['nm_id'],  name=data['name'], price=data['price'])
    return data


@app.get("parse/ym", dependencies=[Depends(security.access_token_required)])
async def parse_ym(sku: str, product_id: str, db: Session = Depends(get_db)):
    loop = asyncio.get_event_loop()
    data = await loop.run_in_executor(executor, get_ym_data,  sku, product_id)
    existing_product = db.query(ProductModel).filter(ProductModel.sku_id == data["nm_id"]).first()
    if existing_product:
        return data
    create_product(db=db, sku_id=data['nm_id'], name = data['name'], price=data['price'])
    return data


if __name__ == '__main__':
    uvicorn.run("main:app", host="localhost", port=8000, log_level="info")