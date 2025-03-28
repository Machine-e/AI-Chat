from flask import Flask, request, jsonify
import requests
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

SI_API_KEY = "your_api_key" # 替换为你的API密钥
SI_API_BASE_URL = "https://api.siliconflow.cn/v1/chat/completions" # 替换为你的API基础URL

# 使用全局变量存储当前选中的API模块
current_api_module = "deepseek-ai/DeepSeek-R1" 
history_module = "Qwen/QwQ-32B-Preview"


@app.route('/ModelSelect', methods=['POST'])
def modelselect():
    global current_api_module
    model_type = request.json.get('modelType')
    if not model_type:
        return jsonify({'error': '缺少模型API'}), 400
    print(f"模型选择已更新: {model_type}")
    current_api_module = model_type
    return jsonify({'status': 'success', 'model_type': model_type})

#历史记录
@app.route('/api/history', methods=['POST'])
def get_history():
    data = request.get_json()
    message = data.get('message', '')
    print(f"message: {message}")
    prompt = f"回复字数一定不能超过8个汉字，不能有标点符号，不能有空格，不能有换行,这是用户信息{message}请你对此内容做出简单概括，总结出一个标题"
    payload = {
        "model": history_module,
        "messages": [
            {
                "role": "user",
                "content":prompt
            }
        ],
    }
    headers = {
        "Authorization": f"Bearer {SI_API_KEY}",
        "Content-Type": "application/json"
    }
    try:
        response = requests.request("POST", SI_API_BASE_URL, json=payload, headers=headers)
        response.raise_for_status()
        
        response_data = response.json()
        history_topic = response_data["choices"][0]["message"]["content"]
        print(f"raw_history_topic: {history_topic}")
        if len(history_topic)>10:
            history_topic = history_topic[:10]+"..."
        print(f"history_topic: {history_topic}")
    except requests.exceptions.RequestException as e:
        print(f'Error calling Si API: {e}')
    except Exception as e:
        print(f'Error calling Si API: {e}')
    return jsonify({'history_topic': history_topic})


# 聊天接口
@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_message = data.get('message', '')
    
    payload = {
        "model": current_api_module,
        "messages": [
            {
                "role": "user",
                "content":user_message
            }
        ],
        "stream": False,
        "max_tokens": 512,
        "stop": None,
        "temperature": 0.7,
        "top_p": 0.7,
        "top_k": 50,
        "frequency_penalty": 0.5,
        "n": 1,
        "response_format": {"type": "text"},
        "tools": [
            {
                "type": "function",
                "function": {
                    "description": "<string>",
                    "name": "<string>",
                    "parameters": {},
                    "strict": False
                }
            }
        ]
    }
    
    try:
        headers = {
            "Authorization": f"Bearer {SI_API_KEY}",
            "Content-Type": "application/json"
        }
        response = requests.request("POST", SI_API_BASE_URL, json=payload, headers=headers)
        response.raise_for_status()
        response_data = response.json()
        ai_response = response_data["choices"][0]["message"]["content"]
        print(f"AI response: {ai_response}")
        
    except requests.exceptions.RequestException as e:
        print(f'Error calling Si API: {e}')
        ai_response = '抱歉，我暂时无法连接到服务器，请稍后再试。'
    except Exception as e:
        print(f'Error calling Si API: {e}')
        ai_response = "error-1"
    if not ai_response:
        ai_response="error-2"
    return jsonify({'message': ai_response})

if __name__ == '__main__':
    app.run(debug=True, port=5000)