from qdrant_client import AsyncQdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse
from qdrant_client.http import models
from loguru import logger
from sentence_transformers import SentenceTransformer 
import uuid
import json
from pydantic import ValidationError

from fastapi.params import Depends

from data_services.search_params import FilterParams,SearchParams

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
    await self.check_and_init_qdrant_client()
  
  async def check_and_init_qdrant_client(self):
    # 检查集合是否存在，如果不存在则创建
    if not await self.qdrant_client.collection_exists(self.collection_name):
      logger.warning(f"{self.collection_name} 不存在 创建qdrant集合")
      await self.qdrant_client.create_collection(
            collection_name=self.collection_name,
            vectors_config=models.VectorParams(size=self.embedder.get_sentence_embedding_dimension(), distance=models.Distance.COSINE)
        )
      
  async def check_qdrant_point_exit(self,image_uuid:str):
    point_id = str(image_uuid)
    existing_points = await self.qdrant_client.retrieve(
        collection_name=self.collection_name,
        ids=[point_id],
    )
    if existing_points:
      logger.warning(f"向量{point_id}已存在 跳过")
      return  True
    return False
  
  
  async def store_into_qdrant(self,image_name, image_uuid,image_path, thumbnail_path,descriptions):
    
    vectors=self.embedder.encode(descriptions, normalize_embeddings=True).tolist()
    # 检查集合是否存在，如果不存在则创建
    # if not await self.qdrant_client.collection_exists(self.collection_name):
    #   await self.qdrant_client.create_collection(
    #         collection_name=self.collection_name,
    #         vectors_config=models.VectorParams(size=self.embedder.get_sentence_embedding_dimension(), distance=models.Distance.COSINE)
    #     )
    
    
    
    points = []
    point_id = str(image_uuid)
    
    
    
    points.append(
      models.PointStruct(
          id=point_id,
          vector=vectors,
          payload={
              "image_name": image_name,
              "image_uuid":image_uuid,
              "image_path": image_path,
              "thumbnail_path": thumbnail_path,
              "description": descriptions,
          }
      ))
    
    response =  await self.qdrant_client.upsert(
        collection_name=self.collection_name,
        points=points
    )
    logger.info("插入qdrant向量完成 状态: {}", response.status)
    
    
  async def store_tags_in_qdrant(self,image_name, image_uuid,image_path, thumbnail_path,description_tags):
    
    vectors=self.embedder.encode(description_tags, normalize_embeddings=True).tolist()
    vector_size = len(vectors[0])  # 384（取决于嵌入模型）
    # 检查集合是否存在，如果不存在则创建
    if not await self.qdrant_client.collection_exists(self.collection_name):
      await self.qdrant_client.create_collection(
            collection_name=self.collection_name,
            vectors_config=models.VectorParams(size=vector_size, distance=models.Distance.COSINE)
        )
      
    points = []
    for vector,description in zip(vectors,description_tags):
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
    
  async def search_similar_description(self, search_param: SearchParams,filter_params:FilterParams):
    
    positive_query_vector =[self.embedder.encode(search_param.positive_descriptions,device="cuda",normalize_embeddings=True).tolist() ] if len(search_param.positive_descriptions)>0  else None
    
    
    negative_query_vector = [self.embedder.encode(search_param.negative_descriptions,device="cuda",normalize_embeddings=True).tolist()] if search_param.negative_descriptions is not None else None
    
    search_mod=models.RecommendStrategy.AVERAGE_VECTOR if search_param.search_mod=="average" else models.RecommendStrategy.BEST_SCORE
    try:
      logger.info("正在进行qdrant查询。。。")
      search_result = await self.qdrant_client.query_points(
                      collection_name="image_descriptions",
                      query=models.RecommendQuery(
                        recommend=models.RecommendInput(
                          positive=positive_query_vector,
                          negative=negative_query_vector,
                          strategy=search_mod
                        )
                        ),
                      query_filter=self.get_filters_by_params(filter_params),
                      limit=search_param.limit_num,
                      with_payload=True
                    )
    except ValidationError as e:
            logger.error(f"查询参数验证失败: {str(e)}")
            return None
    except UnexpectedResponse as e:
        logger.error(f"Qdrant 查询失败: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"未知错误: {str(e)}")
        return None
    
    messages=[]
    for point in search_result.points:
      message={
        "image_name" : point.payload["image_name"],
        "image_path" : point.payload["image_path"],
        "image_uuid" : point.payload["image_uuid"],
        "thumbnail_path": point.payload["thumbnail_path"],
        "description" : point.payload["description"],
        "score" : point.score
      }
      messages.append(message)
      
    return messages
  
  async def close(self):
    await self.qdrant_client.close()
    
    
    
  @staticmethod
  def get_filters_by_params(params:FilterParams | None)->models.Filter | None: 
    if params is None:
      return None
    
    positive_filters=[]
    negative_filters=[]
    
    if params.image_name is not None:
      positive_filters.append(models.FieldCondition(
        key="image_name",
        match=models.MatchAny(
          any=params.image_name
        )
      ))
    
    
      
    if len(positive_filters)<=0 and len(negative_filters)<=0:
      return None
    
    return models.Filter(
      must=positive_filters,
      must_not=negative_filters
    ) 
    
    