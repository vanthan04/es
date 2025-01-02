from elasticsearch import Elasticsearch
from elasticsearch.exceptions import RequestError

# Initialize Elasticsearch client
client = Elasticsearch([{'host': 'localhost', 'port': 9200, 'scheme': 'http'}])

# Kiểm tra kết nối
if client.ping():
    print("Kết nối Elasticsearch thành công!")
else:
    print("Không thể kết nối Elasticsearch.")
    exit(1)

# Define settings and mapping with custom analyzer for stopwords
index_name = "tvtt"
settings_and_mapping = {
    "settings": {
        "analysis": {
            "analyzer": {
                "custom_analyzer": {
                    "type": "standard",
                    "stopwords": "_vietnamese_"  # Sử dụng stopwords cho tiếng Việt
                }
            }
        }
    },
    "mappings": {
        "properties": {
            "id": {"type": "text"},
            "title": {
                "type": "text",
                "analyzer": "custom_analyzer"  # Áp dụng custom analyzer cho field 'title'
            },
            "text": {
                "type": "text",
            }
        }
    }
}

# Xóa chỉ mục cũ nếu có
if client.indices.exists(index=index_name):
    try:
        client.indices.delete(index=index_name)
        print(f"Chỉ mục '{index_name}' đã được xóa.")
    except RequestError as e:
        print(f"Đã xảy ra lỗi khi xóa chỉ mục: {e}")
        exit(1)

# Tạo chỉ mục mới với custom analyzer và mapping
try:
    client.indices.create(index=index_name, body=settings_and_mapping)
    print(f"Chỉ mục '{index_name}' đã được tạo với stopwords.")
except RequestError as e:
    print(f"Đã xảy ra lỗi khi tạo chỉ mục: {e}")
    exit(1)
