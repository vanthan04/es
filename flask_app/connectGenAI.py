import google.generativeai as genai

def ConfigGenAI(api_key):
    # Configure API key
    genai.configure(api_key=api_key)

    # Create GenerativeModel instance
    model = genai.GenerativeModel('gemini-1.5-flash-8b')

    return model

def generative_answer(model, corpus, question):
    # Gửi yêu cầu tới mô hình
    response = model.generate_content(f"Câu hỏi: {question} Nội dung: {corpus}")

    # In kết quả trả về
    return response.text