import sqlite3
import pickle
import json
import re
from pathlib import Path
import requests
import base64

import asyncio
import aiosqlite

from .services.server_provider import ServiceProvider

from fastapi import APIRouter
from loguru import logger

sql_server: ServiceProvider =None
sql_image_router = APIRouter(prefix="/sql_images_search", tags=["sql_image_search"])

@sql_image_router.get("/uuid/{image_id}")
async def get_image_description(image_id : str):
  responce_description= await sql_server.sql_service.get_description_byUuid(image_id)
  if responce_description is None:
    message={
      "success" : False ,
      "description" : None
    }
    return message
  else:
    message={
      "success" : True ,
      "description" : json.loads(responce_description)
    }
    return message
 