from xml.dom import NotFoundErr

from connectGenAI import *
from flask import Flask, render_template, request
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import ConnectionError
import json


app = Flask(__name__)

with open("./config.json") as json_data_file:
    config = json.load(json_data_file)

es = Elasticsearch([{'host': config["es_host"], 'port': config["es_port"], 'scheme': 'http'}])
model = ConfigGenAI(config["api_key"])
index_name = config["index_name"]

@app.route("/")
def home():
    data = ""
    error_message = ""
    order_list = []

    try:
        # Kiểm tra xem index có tồn tại không
        if es.indices.exists(index=index_name):
            # Nếu tồn tại, thực hiện tìm kiếm
            data = es.search(index=index_name, body={"query": {"match_all": {}}})
        else:
            error_message = "Index not found in Elasticsearch."
    except ConnectionError as e:
        error_message = f"Failed to connect to Elasticsearch. Please check your connection and configuration.{e}"
        print(f"Connection error: {e}")
    except Exception as e:
        error_message = f"An unexpected error occurred with Elasticsearch. {e}"
        print(f"Unexpected error: {e}")

    # Nếu có dữ liệu, chuyển kết quả vào order_list
    if data and 'hits' in data:
        for i in data['hits']['hits']:
            order_list.append(i['_source'])

    return render_template("index.html", data=order_list, error_message=error_message)

@app.route("/search", methods=["GET", "POST"])
def search():
    error_message = ""  # Biến để lưu thông báo lỗi
    results = []  # Danh sách kết quả trả về từ Elasticsearch
    answer = ""
    corpus = ""
    if request.method == "POST":
        query = request.form.get("query")  # Lấy truy vấn từ form

        if query:
            print(f"Received query: {query}")

            # Tính toán embedding cho truy vấn

            # # Cấu trúc truy vấn Elasticsearch sử dụng multi_match
            # search_query = {
            #     "query": {
            #         "multi_match": {
            #             "query": query,
            #             "fields": ["title", "text"]
            #         }
            #     },
            #     "size": 10
            # }

            # Cấu trúc truy vấn Elasticsearch sử dụng match
            search_query = {
                "query": {
                    "match": {
                        "title": query  # Tìm kiếm trong trường 'title'
                    }
                },
                "size": 5  # Chỉ lấy 10 kết quả đầu tiên
            }

            try:
                response = es.search(index=index_name, body=json.dumps(search_query))
                hits = response['hits']['hits']  # Lấy các kết quả trả về từ Elasticsearch
                # Chuẩn bị dữ liệu để hiển thị
                for hit in hits:
                    passage = hit['_source']
                    score = hit['_score']  # Lấy điểm score từ Elasticsearch

                    result = {
                        'id': passage.get('id'),
                        'title': passage.get('title', 'No title'),
                        'context': passage.get('text', ''),  # Nội dung của tài liệu
                        'score': score  # Điểm score
                    }
                    results.append(result)
                    corpus += passage.get('text', '') + "."

                results = sorted(results, key=lambda x: x['score'], reverse=True)
                answer = generative_answer(model, corpus, query)

            except Exception as e:
                error_message = f"Error while querying Elasticsearch: {e}"  # Lưu thông báo lỗi vào biến
                print(f"Error while querying Elasticsearch: {e}")

    # Render lại giao diện với kết quả trả về từ Elasticsearch
    return render_template("index.html", query=query, results=results, error_message=error_message, answer=answer)


@app.route("/detail/<doc_id>")
def detail(doc_id):
    result = {}
    try:
        # Truy vấn tìm tài liệu dựa trên trường 'id'
        search_query = {
            "query": {
                "match": {
                    "id": doc_id  # Tìm kiếm tài liệu có giá trị 'id' bằng với doc_id
                }
            },
            "size": 1  # Chỉ lấy 1 kết quả
        }

        # Thực hiện tìm kiếm với Elasticsearch
        response = es.search(index=index_name, body=search_query)

        # Kiểm tra xem có tài liệu nào được trả về không
        if response['hits']['total']['value'] > 0:
            hit = response['hits']['hits'][0]  # Lấy tài liệu đầu tiên trong kết quả
            passage = hit['_source']  # Lấy phần dữ liệu của tài liệu
            score = hit['_score']  # Lấy điểm score

            # Cập nhật kết quả để hiển thị
            result = {
                'id': passage.get('id'),
                'title': passage.get('title', 'No title'),
                'context': passage.get('text', ''),  # Nội dung của tài liệu
                'score': score  # Điểm score
            }
        else:
            # Trường hợp không tìm thấy tài liệu
            return render_template("detail.html", result=result, error_message="Document not found."), 404

    except NotFoundErr:
        # Trả về trang chi tiết với thông báo tài liệu không tồn tại
        return render_template("detail.html", result=result, error_message="Document not found."), 404

    except Exception as e:
        # Trả về thông báo lỗi khi có vấn đề khác
        return render_template("detail.html", result=result, error_message=f"Error fetching document: {e}"), 500

    # Nếu tìm thấy tài liệu, render trang chi tiết với dữ liệu tài liệu
    return render_template("detail.html", result=result, error_message="")


if __name__ == "__main__":
    app.run(debug=True,host='0.0.0.0', port=5000)