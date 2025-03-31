import os
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

from qdrant_client import QdrantClient
from qdrant_client.http import models
from sentence_transformers import SentenceTransformer 
import uuid
import numpy as np

import requests
import base64


import time

from PIL import Image
from io import BytesIO

import sqlite3
import pickle
import json
import re
from pathlib import Path

import cv2
import ffmpeg
import numpy as np
from PIL import Image
from io import BytesIO

import subprocess
import base64
import time
import os
import math
from pathlib import Path
import shutil
import io
from tqdm import tqdm
# 初始化 Qdrant 客户端
# qdrant_client = QdrantClient("localhost", port=6333)
# # 初始化嵌入模型
# embedder = SentenceTransformer("BAAI/bge-base-zh-v1.5",device="cuda",cache_folder="D:\Qt_project/2024\image_search\BAAI_bge_base_zh_v1_5/1",local_files_only=True)  # 轻量级嵌入模型，输出 384 维向量



class VideoConfig:
  #最大分辨率
  MAX_SIZE = (360,420)
  # 目标宽度（像素）
  TARGET_WIDTH = 460   #420
  
  # 目标高度（像素）
  TARGET_HEIGHT = 360  
  
  #采样帧率
  TARGET_PFS=1.0
  #关键帧最小间隔
  MIN_KEYFRAME_INTERVAL=5
  #最大处理帧数
  MAX_FRAMES=30
  
  
class LocalEmbedding():
    def __init__(self, text, data=None):
        self.text = text#text必须是一个list：['文本1','文本2']
        self.data = data#list 
#查询时：搜索关键词+官方给定的instruction
    def achieve_emb(self):
        try:
            # MODELBGE = SentenceTransformer("BAAI/bge-base-zh-v1.5",device="cuda")
            instruction = "为这个句子生成表示以用于检索相关文章："
            q_embeddings = embedder.encode([instruction + self.text], normalize_embeddings=True).tolist()
            self.data.extend(q_embeddings)
            return self.data
          
        except Exception as e:
            print('本地embedding错误', e)
            return self.data
#入库文本的向量化
    def achieve_emb_txt(self):
        try:
            p_embeddings = embedder.encode(self.text, normalize_embeddings=True).tolist()
            return p_embeddings
        except Exception as e:
            print('本地embedding错误', e)
            return self.data
          
# 将描述存入 Qdrant
def store_in_qdrant(qdrant_client, image_name, image_uuid,image_path, thumbnail_path,descriptions):
    # 将描述转换为向量

   
    # vector = embedder.encode([instruction+descriptions],device="cuda",normalize_embeddings=True).tolist()  
    
    vectors=embedder.encode(descriptions, normalize_embeddings=True).tolist()
  
    # 
    # 集合名称
    collection_name = "image_descriptions"
    vector_size = len(vectors[0])  # 384（取决于嵌入模型）
   
    # 检查集合是否存在，如果不存在则创建
    if not qdrant_client.collection_exists(collection_name):
        qdrant_client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(size=vector_size, distance=models.Distance.COSINE)
        )

    # 存储向量和元数据
    

    points = []
    for vector,description in zip(vectors,descriptions):
      point_id = str(uuid.uuid4())
      points.append(
        models.PointStruct(
            id=point_id,
            vector=vector,
            payload={
                "image_name": image_name,
                "image_uuid":image_uuid,
                "image_path": image_path,
                "thumbnail_path": thumbnail_path,
                "description": description,
            }
        )
    )
 
    qdrant_client.upsert(
        collection_name=collection_name,
        points=points
    )
    
# 查询相似描述
def search_similar_description(qdrant_client, query_text, limit=2):
    instruction = "为这个句子生成表示以用于检索相关文章："
    query_vector = embedder.encode(query_text,device="cuda",normalize_embeddings=True).tolist()
    search_result = qdrant_client.query_points(
                    collection_name="image_descriptions", query=query_vector, limit=limit,with_payload=True
                    )
    # search_result = qdrant_client.search(
    #     collection_name="image_descriptions",
    #     query_vector=query_vector,
    #     limit=limit
    # )
    return search_result
  


def image_to_base64_data_uri(file_path,new_width=500):
    
    
    with Image.open(file_path) as img:
        # 获取原始尺寸
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
        return f"data:image/png;base64,{base64_data}"
    
def require_to_remote(image_base64: str,api_url :str):
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
                      # "text": "使用10个关键词总结这个图片,不要联想图片以外的事物,输出格式: 1.xxx 2.xxx 3.xxx 4.xxx 5.xxx 6.xxx 7.xxx 8.xxx 9.xxx 10.xxx"
                      "text": "详细描述这张图片" 
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
  
def require_to_lm_studio(image_base64: str,api_url):
  # 6.xxx 7.xxx 8.xxx"
  request_data = {
      "model": "1@q4_k_m",
      "messages": [
          {
              "role": "user",
              "content": [
                  {
                      "type": "text", #不要联想图片以外的事物,
                      # "text": "使用5个关键词总结这个图片,不要联想图片以外的事物,输出格式: 1.xxx 2.xxx 3.xxx 4.xxx 5.xxx" 
                      "text": "详细描述这张图片"
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
      "temperature": 0.1,
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

def search_image(folder_path,recur=False):
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



# 数据库初始化函数
def init_db(db_path="image_descriptions.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS image_descriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            image_uuid TEXT NOT NULL UNIQUE,
            image_name TEXT NOT NULL,
            image_path TEXT NOT NULL UNIQUE,
            thumbnail_path TEXT NOT NULL UNIQUE,
            description TEXT
        )
    ''')
    conn.commit()
    return conn, cursor
  
# 保存描述到数据库
def save_to_db(cursor, conn, image_uuid,image_name, image_path, thumbnail_path,description):
    json_description_str=json.dumps(description,ensure_ascii=False)
    cursor.execute('''
        INSERT OR REPLACE INTO image_descriptions (image_uuid,image_name ,image_path, thumbnail_path,description)
        VALUES (?, ?, ?,?,?)
    ''', (image_uuid,image_name,image_path, thumbnail_path,json_description_str))
    conn.commit()
    
# 从数据库查询描述
def get_description(cursor, image_path):
    print(image_path)
    cursor.execute('SELECT description FROM image_descriptions WHERE image_path = ?', (image_path,))
    result = cursor.fetchone()
    return result[0] if result else None 
  
def process_description(description:str)-> str:

  # description.strip().replace('\\n', ' ')
  
  description=re.sub(r'\s+', ' ', description)
  pattern = r'\d+\.\s*'
  description=re.sub(pattern, '', description)
  
  
  # description=re.sub(pattern, '', description)
  description=description.split()
  # if "1." in description:
  #   description.strip().replace("1.","")
  # elif "2." in description:
  #   description.strip().replace("2.","")
  # elif "3." in description:
  #   description.strip().replace("3.","")
  # elif "4." in description:
  #   description.strip().replace("4.","")
  # elif "5." in description:
  #   description.strip().replace("5.","")

  return description

def generate_thumbnail_image(file_name,new_width=500):
    
    thumbnail_path="./thumbnail"
    
    image_name, ext = os.path.splitext(os.path.basename(file_name))
    
    namespace = uuid.NAMESPACE_URL
    file_uuid = uuid.uuid5(namespace, file_name)
    
    os.makedirs(thumbnail_path, exist_ok=True)
        
    thumbnail_name = f"{file_uuid}{ext}"
    thumbnail_path = os.path.join(thumbnail_path, thumbnail_name)

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



def extract_key_frame_by_ffmpeg(video_path :str):
  
  base_dir = os.path.dirname(os.path.abspath(__file__))
  output_folder=os.path.join(base_dir,"./ffmpeg_output")
  output_folder=Path(output_folder).as_posix()
  
  if os.path.exists(output_folder):
    shutil.rmtree(output_folder)
    
  os.makedirs(output_folder,exist_ok=True)
  try:
    start_time=time.time()
    probe=ffmpeg.probe(video_path)
    video_duration=float(probe["streams"][0]["duration"])
    
    frame_interval=video_duration/VideoConfig.MAX_FRAMES
    
    stream=ffmpeg.input(video_path)
    
    stream=ffmpeg.output(
      stream,
      # os.path.join(output_folder, "frame_%06d.jpg"),
      'pipe:',
      vf=f"fps=1/{frame_interval},scale={VideoConfig.TARGET_WIDTH}:-1",
      vframes=VideoConfig.MAX_FRAMES,
      format="image2pipe",
      vcodec='mjpeg',
      
    )
    out, _=ffmpeg.run(stream,capture_stdout=True, capture_stderr=True)
    
    frames_base64=[]
    bufferd=BytesIO(out)
    # base64_encoded = base64.b64encode(out).decode('utf-8')
    current_frame = bytearray()
    while True:
      byte = bufferd.read(1)
      if not byte:
        if current_frame:
          frames_base64.append(base64.b64encode(current_frame).decode('utf-8'))
        break
      current_frame.extend(byte)
      
      if len(current_frame) > 2 and current_frame[-2:] == b'\xFF\xD9':  # JPEG 结束标记
        frames_base64.append(base64.b64encode(bytes(current_frame)).decode('utf-8'))
        current_frame = bytearray()
      
    print(f"成功从视频中抽取了 {math.ceil(video_duration * VideoConfig.TARGET_PFS)} 帧, 一共耗时{time.time() - start_time}s")
    return frames_base64
    
  except ffmpeg.Error as e:
    print(f"发生错误{e.stderr}")
      
  
  
  
  # start_time=time.time()
  
  # base_dir = os.path.dirname(os.path.abspath(__file__))
  # output_folder=os.path.join(base_dir,"./ffmpeg_output")
  # os.makedirs(output_folder,exist_ok=True)
  
  # command = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
  #              "default=nokey=1:noprint_wrappers=1", video_path]
  # result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  # if result.returncode != 0:
  #     raise ValueError("Failed to get video duration.")
    
  # duration = float(result.stdout.decode().strip())
  # duration=round(duration)
  
  # print(f"视频长度 {duration}")
  # command = [
  #       "ffmpeg",
  #       "-i", video_path,
  #       "-vf", f"fps={VideoConfig.TARGET_PFS}",
  #       "-frames:v", "%d" % (math.ceil(duration * VideoConfig.TARGET_PFS)),
  #       os.path.join(output_folder, "frame_%06d.jpg")
  #   ]
  # subprocess.run(command, check=True)
 
  # print(f"成功从视频中抽取了 {math.ceil(duration * VideoConfig.TARGET_PFS)} 帧, 一共耗时{time.time() - start_time}s")

if __name__=="__main__":
  
    
    api_url = "http://127.0.0.1:1234/v1/chat/completions"
    # conn, cursor = init_db()
    # image_path2="D:\BaiduNetdiskDownload/NSFW/facefusion3.1/facefusion-3.1.0/2024-12-25 175234.png"
    
    # image_base64=  image_to_base64_data_uri(image_path2)
    video_path=r"C:\Users\hansolo\Videos\京都动画\1、轻音少女！+NCED.mp4"

    base64_frames=extract_key_frame_by_ffmpeg(video_path=video_path)
   
 
  
    start_time = time.time()
    description=require_to_lm_studio(f"data:image/jpeg;base64,{base64_frames[14]}",api_url)
    end_time = time.time()
    run_time = end_time - start_time
    print(f"{round(run_time,1)}/s ---------------------------")
    print(description)
    
    # image_files=search_image(r"C:/Users/hansolo/Pictures")
    
    # for idx,image_name_kye in enumerate(image_files.keys()):
    #   print(f"{idx}/{len(image_files.keys())} ---------------------------")
    #   image_path=image_files[image_name_kye]
    #   existing_desc = get_description(cursor, image_path)
    #   if existing_desc:
    #     print(f"数据库中已有描述: {existing_desc}")
    #   else:
    #     start_time = time.time()
    #     image_base64,file_uuid,thumbnail_path = generate_thumbnail_image(image_path)
     
    #     description=require_to_lm_studio(image_base64)
    #     end_time = time.time()
    #     run_time = end_time - start_time
        
    #     if not isinstance(description, str):
    #         description = str(description)
                
    #     print(description)
        
    #     description=process_description(description)
     
        
    #     print(description)
        
    #     print(f"{round(run_time,1)}/s ---------------------------")
    #     # 保存到sql数据库
    #     save_to_db(cursor, conn, file_uuid,image_name_kye, image_path, thumbnail_path,description)
    #     #保存到qdrant数据库
    #     store_in_qdrant(qdrant_client,image_name_kye,file_uuid,image_path,thumbnail_path,description)
        
    # conn.close()
    
    
    # while(True):
    #   print("查询")
    #   text=input()
    
    #   re=search_similar_description(qdrant_client,text,limit=3)
    #   print(re)
    #   for point in re.points:
    #     print(f"{point.score} ---{point.payload}")
    
    
