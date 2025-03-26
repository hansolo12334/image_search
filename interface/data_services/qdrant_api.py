from .qdrant_server import QdrantServer

import json

from fastapi import APIRouter


qdrant_server: QdrantServer =None
qdrant_image_router = APIRouter(prefix="/qdrant_images_search", tags=["qdrant_image_search"])

@qdrant_image_router.get("/search/{query_text}")
async def get_image_description(query_text : str):
  responce= await qdrant_server.search_similar_description(query_text)
  return {"description" : json.loads(responce)  }