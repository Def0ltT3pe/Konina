from fastapi import FastAPI, Depends
import uvicorn
from pydantic import BaseModel
from sqlalchemy.orm import DeclarativeBase, Mapped
from sqlalchemy.sql.annotation import Annotated

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.testing.schema import mapped_column

engine = create_async_engine('sqlite+aiosqlite:///data_base.db')

new_session = async_sessionmaker(engine, expire_on_commit=False)

async def get_session():
    async with new_session() as session:
        yield session

class Base(DeclarativeBase):
    pass

class User(Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str]
    password: Mapped[str]

#app = FastAPI()

#if __name__ == '__main__':
#    uvicorn.run("main:app", reload=True)
