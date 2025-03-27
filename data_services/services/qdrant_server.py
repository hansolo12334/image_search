from qdrant_client import AsyncQdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse
from qdrant_client.http import models

from loguru import logger
from sentence_transformers import SentenceTransformer 
import uuid
import json

class QdrantServer():
  def __init__(self):
    self.qdrant_client=None
    self.collection_name = "image_descriptions"
    self.embedder=None
    
    
  async def start(self):
    self.qdrant_client=AsyncQdrantClient(host="localhost",port=6333)
    
    self.collection_name = "image_descriptions"
    
    self.embedder=SentenceTransformer("BAAI/bge-base-zh-v1.5",device="cuda",cache_folder="D:\Qt_project/2024\image_search\BAAI_bge_base_zh_v1_5/1",local_files_only=True)  # 轻量级嵌入模型，输出 384 维向量
    
    # logger.success("qdrant_client 初始化成功")
    
  async def store_into_qdrant(self,image_name, image_uuid,image_path, thumbnail_path,descriptions):
    
    vectors=self.embedder.encode(descriptions, normalize_embeddings=True).tolist()
    vector_size = len(vectors[0])  # 384（取决于嵌入模型）
    # 检查集合是否存在，如果不存在则创建
    if not await self.qdrant_client.collection_exists(self.collection_name):
      await self.qdrant_client.create_collection(
            collection_name=self.collection_name,
            vectors_config=models.VectorParams(size=vector_size, distance=models.Distance.COSINE)
        )
      
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
    response =  await self.qdrant_client.upsert(
        collection_name=self.collection_name,
        points=points
    )
    logger.info("插入qdrant向量完成 状态: {}", response.status)
    
    
    
  async def search_similar_description(self,query_text, limit=4):
    query_vector = self.embedder.encode(query_text,device="cuda",normalize_embeddings=True).tolist()
    try:
      search_result = await self.qdrant_client.query_points(
                      collection_name="image_descriptions", query=query_vector, limit=limit,with_payload=True
                    )
    except UnexpectedResponse as e: 
      if e.status_code == 404:
        logger.error("qdrant不存在集合: image_descriptions")
        return None
    
    messages=[]
    for point in search_result.points:
      message={
        "image_name" : point.payload["image_name"],
        "image_uuid" : point.payload["image_uuid"],
        "description" : point.payload["description"],
        "score" : point.score
      }
      messages.append(message)
      
    return json.dumps(messages)
  
  async def close(self):
    await self.qdrant_client.close()