from .sql_server import SQLServer
from .qdrant_server import QdrantServer
from loguru import logger
from data_services.config import app_config



class ServiceProvider:
  def __init__(self):
    self.sql_service=SQLServer(app_config.data_base_path)
    self.qdrant_service=QdrantServer()
    
    
    
  async def start(self):
    await self.sql_service.start()
    logger.success("sql 初始化成功")
    await self.qdrant_service.start()
    logger.success("qdrant_client 初始化成功")
   
  async def close(self):
    await self.sql_service.close()
    logger.info("sql服务关闭")
    await self.qdrant_service.close()
    logger.info("qdrant服务关闭")