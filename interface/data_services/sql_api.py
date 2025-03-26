import sqlite3
import pickle
import json
import re
from pathlib import Path
import requests
import base64

import asyncio
import aiosqlite

from .sql_server import SQLServer

from fastapi import APIRouter

from loguru import logger

sql_server: SQLServer =None
sql_image_router = APIRouter(prefix="/sql_images_search", tags=["sql_image_search"])

@sql_image_router.get("/uuid/{image_id}")
async def get_image_description(image_id : str):
  responce_description= await sql_server.get_description(image_id)
  return {"description" : json.loads(responce_description) }