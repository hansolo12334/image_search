from PyQt5.QtCore import QThread,QObject,pyqtSignal
import requests
import sys
from data_services.config import app_config
import typing


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
               key_words:typing.Optional[str]='',
               limit: typing.Optional[int]=5):
    super().__init__(parent)
    self.fast_api_url=app_config.fast_api_url
    self.key_words=key_words
    self.limit=limit
    
    
  def run(self):
    message={
    "key_words":self.key_words,
    "limit" :self.limit
  }
    url=f"{self.fast_api_url}/qdrant_images_search/search/"
    re=requests.get(url=url,json=message)
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