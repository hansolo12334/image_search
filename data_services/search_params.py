
from typing import Annotated
from fastapi.params import Query
from pydantic import BaseModel,Field


class FilterParams:
  def __init__(self,
               positive_description_tags: Annotated[str | None, Query(
                                                description="图片标签的正面描述"
                                              )] =None,
               negative_description_tags: Annotated[str | None, Query(
                                                description="图片标签的反向描述"
                                              )] =None,
               image_name: Annotated[str| None ,Query(
                                                description="图片名称"
                                              )]=None
              
               ):
  
    self.positive_description_tags=[positive_description_tags] if positive_description_tags is not None else None
    self.negative_description_tags=[negative_description_tags] if negative_description_tags is not None else None
    self.image_name=[image_name] if image_name is not None else None
  
 
    

class SearchParams(BaseModel):
  positive_descriptions: str =Field(None,description="图片的正向描述")
  
  negative_descriptions: str | None=Field(None,description="图片的反向描述")
 
  search_mod: str = Field("average",description="搜索方式 average 或者 best")
  
  limit_num: int =Field(50,description="返回的搜索数量")