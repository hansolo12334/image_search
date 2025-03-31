from PyQt5.QtCore import QThread,QObject,pyqtSignal
import requests
import sys
from data_services.config import app_config
import typing

from data_services.search_params import FilterParams,SearchParams


class ImageInfo:
  def __init__(self,idx: typing.Optional[int] =0,
               image_name :typing.Optional[str]='',
               image_path:typing.Optional[str]='',
               thumbnail_image_paths:typing.Optional[str]='',
               description:typing.Optional[str]='',
               score:typing.Optional[float]=0.0):
    self.idx=idx
    self.image_name=image_name
    self.thumbnail_image_paths=thumbnail_image_paths
    self.image_path=image_path
    self.description=description
    self.score=score
    
class ServiceConnection(QThread):
  images_info=pyqtSignal(list)
  finished=pyqtSignal()
  
  def __init__(self, 
               parent:typing.Optional[QObject] = None,
               positive_key_words:typing.Optional[str]=None,
               negative_key_words:typing.Optional[str]=None,
               limit: typing.Optional[int]=5,
               search_mod: typing.Optional[str]=None,
               image_name: typing.Optional[str]=None,
               positive_description_tags: typing.Optional[str]=None,
               negative_description_tags: typing.Optional[str]=None
               ):
    super().__init__(parent)
    self.fast_api_url=app_config.fast_api_url
    self.positive_key_words=positive_key_words
    self.negative_key_words=negative_key_words
    self.limit=limit
    self.search_mod=search_mod
    
    self.image_name=image_name
    self.positive_description_tags=positive_description_tags
    self.negative_description_tags=negative_description_tags
    
    
  def run(self):
    
    search_json={
      "positive_descriptions": self.positive_key_words,
      "negative_descriptions": self.negative_key_words if len(self.negative_key_words) else '',
      "search_mod": self.search_mod if self.search_mod else "average",
      "limit_num": self.limit
    }
    
    filter_param={
      "image_name": self.image_name,
      "positive_description_tags": self.positive_description_tags,
      "negative_description_tags": self.negative_description_tags,
    }

    # print(search_json)
    # print(filter_param)
    url=f"{self.fast_api_url}/qdrant_images_search/search"
    try:
      re=requests.post(url=url,json=search_json,params=filter_param)
      re.raise_for_status()
      print(re.text)
      descriptions= re.json()['description']
      image_data=[]
      for idx,description in enumerate(descriptions):
        image_data.append(ImageInfo(
          idx+1,
          description['image_name'],
          description['image_path'],
          description['thumbnail_path'],
          description['description'],
          description['score']
        ))
      self.images_info.emit(image_data)
    except requests.exceptions.HTTPError as e:
      print(f"{e}")
      print(f"Response text: {re.text}")
      
    