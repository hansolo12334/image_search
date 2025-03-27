from fastapi import FastAPI,APIRouter
from contextlib import asynccontextmanager

import data_services.sql_api  as sql_api
import data_services.qdrant_api  as qdrant_api
import data_services.image_collect_api as image_collect_api

from data_services.services.server_provider import ServiceProvider


@asynccontextmanager
async def lifespan(app: FastAPI):
  provider=ServiceProvider()
  await provider.start()
  
  
  sql_api.sql_server=provider #注入
  qdrant_api.qdrant_server=provider
  image_collect_api.image_collect_server=provider
  
  yield
  
  await provider.close()

  
app=FastAPI(lifespan=lifespan,title="本地图像查询工具")

app.include_router(sql_api.sql_image_router)
app.include_router(qdrant_api.qdrant_image_router)
app.include_router(image_collect_api.image_collect_router)

@app.get("/")
def test_server():
  
  return {"message" : "这是一个基本测试"}