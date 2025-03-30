import requests

BASE_URL = "http://127.0.0.1:8000"

if __name__=="__main__":
  
  # uuid="0a0d5949-b1f5-5168-ad0b-4b4475592944"
  # url=f"{BASE_URL}/sql_images_search/uuid/{uuid}"

  # re=requests.get(url=url)
  
  # print(re.json())
  
  # url=f"{BASE_URL}/"
  # re=requests.get(url=url)
  # while True:
  #   print("输入描述:")
  #   text=input()
  #   # text="动漫 女生 紫色头发"
  #   url=f"{BASE_URL}/qdrant_images_search/search/{text}"
  #   re=requests.get(url=url)
  #   descriptions= re.json()['description']
  #   for description in descriptions:
  #     print(f"{description['image_name']} {description['description'][0:50]}, {description['image_path']}")
  
  
  # folder_path=r"C:/Users/hansolo/Pictures"
  folder_path=r"C:\Users\hansolo\Downloads\アズールレーン Second Anniversary Art Collection"
  message={
    "folder_path":folder_path,
    "recur" :True
  }
  url=f"{BASE_URL}/image_collect/generate/"
  re=requests.get(url=url,json=message)
  print(re.json())
  # url=f"{BASE_URL}/image_collect/update_description/"
  # re=requests.get(url=url,json=message)
  # print(re.json())