import json
import os

class AppConfig:
  def __init__(self):
    self.lm_studio_url :str
    self.data_base_path:str
    self.thumbnail_image_path:str
    self.use_remote:bool
    self.remote_url:str
    self.init()
    
  def init(self):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(base_dir, "../app/config/app_config.json")
    config_path=os.path.abspath(config_path)
    
    with open(config_path) as f:
      data=json.load(f)
      self.lm_studio_url=data["lm_studio_url"]
      self.data_base_path=data["data_base_path"]
      self.thumbnail_image_path=data["thumbnail_image_path"]
      
      self.use_remote=data["use_remote"]
      self.remote_url=data["remote_url"]
      
 
    self.data_base_path = os.path.join(config_path, self.data_base_path)
    self.data_base_path=os.path.abspath(self.data_base_path)

    self.thumbnail_image_path=os.path.join(config_path,self.thumbnail_image_path)
    self.thumbnail_image_path=os.path.abspath(self.thumbnail_image_path)
    
    os.makedirs(self.thumbnail_image_path, exist_ok=True)
    
    
app_config=AppConfig()  


