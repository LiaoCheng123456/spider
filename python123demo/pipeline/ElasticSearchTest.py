from elasticsearch import Elasticsearch
es = Elasticsearch(hosts="192.168.136.151:9200")

prarms = {
    "doc": {
  "recommend": "3",
  "abstract": "大家一起来学习Java",
  "sort": "202",
  "title": "pyth2on基础",
  "content": "东西",
  "article_id": "12345225",
  "titel": "新闻2",
  "updata_time": "2019-02-25",
  "thum": "www.baidu.com4",
  "id": "12233",
  "tag": "Array",
  "time": "2019-02-24",
  "username": "廖程",
  "status": "1"
}
}


# result =es.create(index="mynote", id="test", doc_type="article", body=prarms)
# print(result)
# es.update(index="mynote", doc_type="article", id= "test", body=prarms)
result = es.get("mynote", "article", "test1")
print(result)