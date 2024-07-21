#파일을 직접 업로드 하기
import base64
import requests
import os

# OpenAI API Key
#api_key = "YOUR_OPENAI_API_KEY"
api_key = os.environ.get('OPENAI_API_KEY')
print(api_key)

# Function to encode the image
def encode_image(image_path):
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')

# Path to your image
image_path = "images/received_image_33.jpg"

# Getting the base64 string
base64_image = encode_image(image_path)

headers = {
  "Content-Type": "application/json",
  "Authorization": f"Bearer {api_key}"
}

payload = {
  #"model": "gpt-4-vision-preview",
  "model": "gpt-4o",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          #"text": "What’s in this image?"
          "text": "이 이미지에서 초록색과 노란색 버튼이 보일거야 이 버튼들의 위치와 각각 이 사진을 찍은 곳으로부터 어느 정도의"
        },
        {
          "type": "image_url",
          "image_url": {
            "url": f"data:image/jpeg;base64,{base64_image}"
          }
        }
      ]
    }
  ],
  "max_tokens": 300
}
 
response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)

print(response.json())