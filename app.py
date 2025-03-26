from fastapi import FastAPI,APIRouter
from contextlib import asynccontextmanager

import interface.data_services.sql_api  as sql_api
import interface.data_services.qdrant_api  as qdrant_api

from interface.data_services.sql_server import SQLServer
from interface.data_services.qdrant_server import QdrantServer

@asynccontextmanager
async def lifespan(app: FastAPI):
  sql_server=SQLServer(r"D:\Qt_project\2024\image_search\image_descriptions.db")
  await sql_server.start()
  
  qdrant_server=QdrantServer()
  await qdrant_server.start()
  
  sql_api.sql_server=sql_server #注入
  qdrant_api.qdrant_server=qdrant_server
  yield
  
  await sql_server.close()
  await qdrant_server.close()
  
app=FastAPI(lifespan=lifespan,title="本地图像查询工具")

app.include_router(sql_api.sql_image_router)
app.include_router(qdrant_api.qdrant_image_router)

@app.get("/")
def test_server():
  return {"message" : "这是一个基本测试"}