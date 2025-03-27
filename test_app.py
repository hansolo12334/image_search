import requests

BASE_URL = "http://127.0.0.1:8000"

if __name__=="__main__":
  
  uuid="0a0d5949-b1f5-5168-ad0b-4b4475592944"
  url=f"{BASE_URL}/sql_images_search/uuid/{uuid}"

  re=requests.get(url=url)
  
  print(re.json())
  
  url=f"{BASE_URL}/"

  re=requests.get(url=url)
  
  text="白"
  url=f"{BASE_URL}/qdrant_images_search/search/{text}"
  re=requests.get(url=url)
  print(re.json())
  
  
  folder_path=r"C:/Users/hansolo/Pictures"
  message={
    "folder_path":folder_path,
    "recur" :False
  }
  url=f"{BASE_URL}/image_collect/generate/"
  re=requests.get(url=url,json=message)
  print(re.json())