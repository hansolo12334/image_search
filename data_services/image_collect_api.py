from .services.server_provider import ServiceProvider
from fastapi import APIRouter
from PIL import Image
import os
from pathlib import Path
from io import BytesIO
import uuid
import base64

from loguru import logger
import time
import requests
import json
import re

from data_services.config import app_config


image_collect_server: ServiceProvider =None
image_collect_router = APIRouter(prefix="/image_collect", tags=["image_collect"])


async def search_image(folder_path,recur=False):
  image_files = {}
  if recur:
      for root, _, files in os.walk(folder_path):
          for file in files:
              if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                file_path=Path(os.path.join(root, file)).as_posix()
                image_files.update({file : file_path})
              # image_files.append(os.path.join(root, file))
  else:
      for file in os.listdir(folder_path):
          if file.lower().endswith(('.png', '.jpg', '.jpeg')):
            file_path=Path(os.path.join(folder_path, file)).as_posix()
            image_files.update({file : file_path})
              
  return image_files

async def process_description_tags(description_tags:str)-> str:
  description=re.sub(r'\s+', ' ', description_tags)
  pattern = r'\d+\.\s*'
  description=re.sub(pattern, '', description)
  description=description.split()
  return description

async def process_description(description:str)-> str:
  description=description.strip().replace('\n', ' ')
  return description

async def generate_thumbnail_image(file_name,new_width=500):
  
  thumbnail_folder=app_config.thumbnail_folder
    
  image_name, ext = os.path.splitext(os.path.basename(file_name))
  
  namespace = uuid.NAMESPACE_URL
  file_uuid = uuid.uuid5(namespace, file_name)
  
  os.makedirs(thumbnail_folder, exist_ok=True)
      
  thumbnail_name = f"{file_uuid}{ext}"
  thumbnail_path = os.path.join(thumbnail_folder, thumbnail_name)
  with Image.open(file_name) as img:
    original_width, original_height = img.size
    # 计算按比例缩放后的新高度
    new_height = int((new_width / original_width) * original_height)
    
    # 调整分辨率
    resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    # print(resized_img.size)
    # 将图片保存到内存缓冲区
    buffered = BytesIO()
    # 如果图片有透明度(PNG),保持RGBA模式;否则转为RGB
    if resized_img.mode in ('RGBA', 'P'):
        resized_img.save(buffered, format="PNG")
    else:
        resized_img.convert('RGB').save(buffered, format="JPEG")
    base64_data = base64.b64encode(buffered.getvalue()).decode('utf-8')
    
    #生成缩略图
    if not os.path.exists(thumbnail_path):
        img.thumbnail((256,256))
      
        if img.mode in ('RGBA', 'P'):
            img.save(thumbnail_path, format="PNG",quality=85)
        else:
            img.convert('RGB').save(thumbnail_path, format="JPEG",quality=85)
    else:
        print(f"缩略图已存在，跳过创建: {thumbnail_path}")

    print("生成缩略图完成")
    return f"data:image/png;base64,{base64_data}",str(file_uuid),thumbnail_path
  
  

async def require_to_remote(image_base64: str,api_url:str, promot: str,max_retries=3,retry_delay=5,timeout=10):
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer token-abc123"
    }
    request_data = {
        "model": "./qwen2-vl",
          "messages": [
          {
              "role": "user",
              "content": [
                  {
                      "type": "text", #不要联想图片以外的事物,
                      "text": promot
                  },
                  {
                    "type": "image_url",
                     "image_url": {
                         "url": image_base64
                     },
                 
                  }
              ]
          }
        ]
      }
    # 发送 POST 请求
    for attempt in range(max_retries):
        try:
            logger.info(f"第 {attempt + 1} 次尝试向远程发送图片数据")
            response = requests.post(api_url, 
                                    data=json.dumps(request_data),  # 将字典转换为 JSON 字符串
                                    headers=headers,timeout=timeout)
            
            # 检查响应状态码
            response.raise_for_status()  # 如果状态码不是 200，会抛出异常

            # 解析响应
            result = response.json()
            # print("响应结果:", json.dumps(result, ensure_ascii=False, indent=2))
            return result["choices"][0]["message"]["content"]
        
        except requests.exceptions.Timeout:
            logger.warning(f"请求超时（{timeout}秒），将在 {retry_delay} 秒后重试")
            if attempt < max_retries - 1:  
                time.sleep(retry_delay)
            else:
                logger.error("达到最大重试次数，放弃请求")
                raise  #
        except requests.exceptions.RequestException as e:
            logger.error(f"请求失败: {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                logger.error("达到最大重试次数，放弃请求")
                raise  # 或返回 None
            
        except requests.exceptions.HTTPError as http_err:
            logger.error(f"HTTP 错误: {http_err}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                logger.error("达到最大重试次数，放弃请求")
                raise  # 或返回 None
            
        except json.JSONDecodeError:
            logger.error("响应不是有效的 JSON 格式:", response.text)
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                logger.error("达到最大重试次数，放弃请求")
                raise  # 
            # return ""
    

  
async def require_to_lm_studio(image_base64: str,api_url):
  # 6.xxx 7.xxx 8.xxx"
  request_data = {
      "model": "1@q4_k_m",
      "messages": [
          {
              "role": "user",
              "content": [
                  {
                      "type": "text", #不要联想图片以外的事物,
                      "text": "使用5个关键词总结这个图片,不要联想图片以外的事物,输出格式: 1.xxx 2.xxx 3.xxx 4.xxx 5.xxx" 
                  },
                  {
                      "type": "image_url",
                      "image_url": {
                          "url": image_base64
                        }
                  }
              ]
          }
      ],
      "temperature": 0.2,
      "max_tokens": -1,
      "stream": False,
  }

  # 设置请求头（通常需要指定 Content-Type）
  headers = {
      "Content-Type": "application/json",
      "Authorization": "Bearer lm-studio"
  }

  # 发送 POST 请求
  try:
      response = requests.post(api_url, 
                            data=json.dumps(request_data),  # 将字典转换为 JSON 字符串
                            headers=headers)
      
      # 检查响应状态码
      response.raise_for_status()  # 如果状态码不是 200，会抛出异常

      # 解析响应
      result = response.json()
      # print("响应结果:", json.dumps(result, ensure_ascii=False, indent=2))
      return result["choices"][0]["message"]["content"]
    
  except requests.exceptions.HTTPError as http_err:
      print(f"HTTP 错误: {http_err}")
  except requests.exceptions.RequestException as err:
      print(f"请求错误: {err}")
  except json.JSONDecodeError:
      print("响应不是有效的 JSON 格式:", response.text)
  return ""



@image_collect_router.get("/generate/")
async def generate_image_collection(request_data: dict):

  folder_path=request_data["folder_path"]
  recur=request_data["recur"]
  
  if not os.path.isdir(folder_path):
    return {"success": False}
  
  image_files=await search_image(folder_path,recur)
  for idx,image_name_kye in enumerate(image_files.keys()):
    
    logger.info(f"{idx}/{len(image_files.keys())} ---------------------------")
    image_path=image_files[image_name_kye]
    existing_desc = await image_collect_server.sql_service.get_description_path(image_path)
    if existing_desc:
      logger.warning(f"数据库中已有描述: {existing_desc}")
    else:
      start_time = time.time()
      image_base64,file_uuid,thumbnail_path = await generate_thumbnail_image(image_path)
      
      if app_config.use_remote:
        logger.info("use_remote")
        description=await require_to_remote(image_base64,app_config.remote_url,app_config.promot_descriptions)
        description_tags=await require_to_remote(image_base64,app_config.remote_url,app_config.promot_description_tag)
      else:
        description=await require_to_lm_studio(image_base64,"http://localhost:1234/v1/chat/completions")
      end_time = time.time()
      run_time = end_time - start_time
      
      if not isinstance(description, str):
          description = str(description)
              
 
      
      description=await process_description(description)
      description_tags=await process_description_tags(description_tags)
      
      print(description)
      print(description_tags)
      print(f"{round(run_time,1)}/s ---------------------------")
      # 保存到sql数据库
      await image_collect_server.sql_service.save_to_db( file_uuid,image_name_kye, image_path, thumbnail_path,description,description_tags)
      #保存到qdrant数据库
      if len(description)<=0:
          logger.warning("生成描述失败")
      else:
        await image_collect_server.qdrant_service.store_tags_in_qdrant(image_name_kye,file_uuid,image_path,thumbnail_path,description_tags)
        await image_collect_server.qdrant_service.store_into_qdrant(image_name_kye,file_uuid,image_path,thumbnail_path,description)
      
  return {"success": True}


@image_collect_router.get("/update_description/")
async def update_image_collection_description(request_data: dict):

  folder_path=request_data["folder_path"]
  recur=request_data["recur"]
  
  if not os.path.isdir(folder_path):
    return {"success": False}
  
  image_files=await search_image(folder_path,recur)
  for idx,image_name_kye in enumerate(image_files.keys()):
    
    logger.info(f"{idx}/{len(image_files.keys())} ---------------------------")
    image_path=image_files[image_name_kye]
    # existing_desc = await image_collect_server.sql_service.get_description_path(image_path)
    existing_desc=False
    if existing_desc:
      logger.warning(f"数据库中已有描述: {existing_desc}")
    else:
      start_time = time.time()
      image_base64,file_uuid,thumbnail_path = await generate_thumbnail_image(image_path)
      
      if app_config.use_remote:
        logger.info("use_remote")
        description=await require_to_remote(image_base64,app_config.remote_url,app_config.promot_descriptions)
      else:
        description=await require_to_lm_studio(image_base64,"http://localhost:1234/v1/chat/completions")
      end_time = time.time()
      run_time = end_time - start_time
      
      if not isinstance(description, str):
          description = str(description)
                    
      description=await process_description(description)
    
      
      print(description)
      
      print(f"{round(run_time,1)}/s ---------------------------")
     
      if len(description)<=0:
          logger.warning("生成描述失败")
      else:
        # 保存到sql数据库
        await image_collect_server.sql_service.update_to_db_with_description( file_uuid,image_name_kye, image_path, thumbnail_path,description)
         #保存到qdrant数据库
        if not await image_collect_server.check_qdrant_point_exit(file_uuid):
          await image_collect_server.qdrant_service.store_into_qdrant(image_name_kye,file_uuid,image_path,thumbnail_path,description)
      
  return {"success": True}