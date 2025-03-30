from .services.server_provider import ServiceProvider

import json

from fastapi import APIRouter


qdrant_server: ServiceProvider =None
qdrant_image_router = APIRouter(prefix="/qdrant_images_search", tags=["qdrant_image_search"])

@qdrant_image_router.get("/search/")
async def find_similar_image_by_description(request_data: dict):
  query_text=request_data['key_words']
  limit=request_data['limit']
  responce= await qdrant_server.qdrant_service.search_similar_description(query_text,limit=limit)
  if responce is None:
    message={
      "success" : False,
      "description" : None
    }
    return message
  else:
    message={
      "success" : True,
      "description" : json.loads(responce) 
    }
    return message
