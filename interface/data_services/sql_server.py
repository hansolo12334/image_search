import sqlite3
import pickle
import json
import re
from pathlib import Path
import requests
import base64

import asyncio
import aiosqlite

from loguru import logger



class SQLServer():
  def __init__(self,db_path):
    self.db_path=db_path
    self.conn=None
    
  
  async def start(self):
    """启动并初始化连接"""
    self.conn=await aiosqlite.connect(self.db_path)
    
    await self.conn.execute('''
         CREATE TABLE IF NOT EXISTS image_descriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            image_uuid TEXT NOT NULL UNIQUE,
            image_name TEXT NOT NULL,
            image_path TEXT NOT NULL UNIQUE,
            thumbnail_path TEXT NOT NULL UNIQUE,
            description TEXT
        )
    ''')
    await self.conn.commit()
    logger.success("数据库初始化完成")
  
  
  async def save_to_db(self,image_uuid,image_name, image_path, thumbnail_path,description):
    json_description_str=json.dumps(description,ensure_ascii=False)
    await self.conn.execute('''
        INSERT OR REPLACE INTO image_descriptions (image_uuid,image_name ,image_path, thumbnail_path,description)
        VALUES (?, ?, ?,?,?)
    ''', (image_name, image_path, json_description_str))
    await self.conn.commit()
    
  async def get_description(self,image_uuid):
    # print(image_uuid)
    async with self.conn.execute('SELECT description FROM image_descriptions WHERE image_uuid = ?', (image_uuid,)) as cursor:
      result = await cursor.fetchone()
      # print(result)
    return result[0] if result else None 
  
  async def get_all_image_name(self):
    async with self.conn.execute('SELECT image_name FROM image_descriptions') as cursor:
      all_names = await cursor.fetchall()
    return all_names if all_names else None
    
  async def get_all_image_path(self):
    async with self.conn.execute('SELECT image_path FROM image_descriptions') as cursor:
      all_paths = await cursor.fetchall()
    return all_paths if all_paths else None
  
  async def close(self):
    """关闭连接"""
    if self.conn:
      await self.conn.close()
      logger.info("数据库连接已关闭")



async def main(server):
  

  await server.start()
  desp= await server.get_description("C:/Users/hansolo/Pictures/640.png")
  
  print(desp)
  names=await server.get_all_image_path()
  print(names)
  await server.close()
  
if __name__=="__main__":
  server=SQLServer(r"D:\Qt_project\2024\image_search\image_descriptions1.db")
  asyncio.run(main(server))
 
 
 
 
 
 
  # def process_description(description:str)-> str:
  #   description=re.sub(r'\s+', ' ', description)
  #   pattern = r'\d+\.\s*'
  #   description=re.sub(pattern, '', description)
  #   description=description.split()
  #   return description