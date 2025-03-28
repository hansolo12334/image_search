import json
import os
import chardet

class AppConfig:
  def __init__(self):
    self.lm_studio_url : str
    self.data_base_path: str
    self.thumbnail_folder: str
    self.use_remote: bool
    self.remote_url: str
    self.promot_descriptions: str
    self.promot_description_tag: str
    
    self.init()
  
  def detect_encoding(self,file_path):
    with open(file_path, 'rb') as f:
        result = chardet.detect(f.read())
    return result['encoding']
  
  def init(self):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(base_dir, "../app/config/app_config.json")
    config_path=os.path.abspath(config_path)
    encoding = self.detect_encoding(config_path)
    with open(config_path,encoding=encoding) as f:
      data=json.load(f)
      self.lm_studio_url=data["lm_studio_url"]
      self.data_base_path=data["data_base_path"]
      self.thumbnail_folder=data["thumbnail_folder"]
      
      self.use_remote=data["use_remote"]
      self.remote_url=data["remote_url"]
      
      self.promot_descriptions=data["promot_descriptions"]
      self.promot_description_tag=data["promot_description_tag"]
      
      
    self.data_base_path = os.path.join(config_path, self.data_base_path)
    self.data_base_path=os.path.abspath(self.data_base_path)

    self.thumbnail_folder=os.path.join(config_path,self.thumbnail_folder)
    self.thumbnail_folder=os.path.abspath(self.thumbnail_folder)
    
    os.makedirs(self.thumbnail_folder, exist_ok=True)
    
    
app_config=AppConfig()  


