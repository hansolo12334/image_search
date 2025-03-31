from .services.server_provider import ServiceProvider

import json

from fastapi import APIRouter

from data_services.search_params import SearchParams,FilterParams
from typing import Annotated
from fastapi import Depends


qdrant_server: ServiceProvider =None
qdrant_image_router = APIRouter(prefix="/qdrant_images_search", tags=["qdrant_image_search"])

@qdrant_image_router.post("/search")
async def find_similar_image_by_description(
                              search_params: SearchParams, 
                              filter_params: Annotated[FilterParams,Depends(FilterParams)]):
  

  responce= await qdrant_server.qdrant_service.search_similar_description(search_params,filter_params)

  if responce is None:
    message={
      "success" : False,
      "description" : None
    }
    return message
  else:
    message={
      "success" : True,
      "description" : responce
    }
    return message
