from .services.server_provider import ServiceProvider

import json

from fastapi import APIRouter


qdrant_server: ServiceProvider =None
qdrant_image_router = APIRouter(prefix="/qdrant_images_search", tags=["qdrant_image_search"])

@qdrant_image_router.get("/search/{query_text}")
async def get_image_description(query_text : str):
  responce= await qdrant_server.qdrant_service.search_similar_description(query_text)
  if responce is None:
    message={
      "success" : False,
      "description" : None
    }
    return message
  else:
    message={
      "success" : False,
      "description" : json.loads(responce) 
    }
    return message
