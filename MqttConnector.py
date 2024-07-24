from dotenv import load_dotenv
import base64
import requests
import os
import paho.mqtt.client as mqtt
from flask import Flask, jsonify

app = Flask(__name__)

# Load .env
load_dotenv()

# OpenAI API Key
api_key = os.environ.get('OPENAI_API_KEY')
if not api_key:
    raise ValueError("OpenAI API key not found in environment variables")

# Path to the single image file
image_path = "received_image.jpg"

# 전역 변수 선언
project_response = ""
z_info = 0

# Function to encode the image
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

# 브로커 접속 시도 결과 처리 콜백 함수
def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    if rc == 0:
        client.subscribe("PICTURE")  # 첫 번째 토픽 구독
        client.subscribe("bssm/seonguk/project")  # 두 번째 토픽 구독
    else:
        print('연결 실패 : ', rc)

# 첫 번째 토픽 메시지 수신 콜백 함수
def on_message_picture(client, userdata, msg):
    try:
        # 메시지 페이로드를 JPEG 형식으로 저장
        image_data = msg.payload
        with open(image_path, "wb") as image_file:
            image_file.write(image_data)
        print(f"Image received and saved to '{image_path}'")
        # 첫 번째 토픽에 대한 추가 로직 처리
        process_picture(image_path)
    except Exception as e:
        print(f"Error processing message: {e}")

# 두 번째 토픽 메시지 수신 콜백 함수
def on_message_project(client, userdata, msg):
    global project_response
    try:
        # 메시지 페이로드를 문자열로 변환
        message = msg.payload.decode("utf-8")
        # X, Y, Z 좌표값 파싱
        x, y, z = map(float, message.split(","))
        print(f"Received coordinates: X={x}, Y={y}, Z={z}")
        # 두 번째 토픽에 대한 추가 로직 처리 및 GPT에게 질문
        project_response = process_project(x, y, z)

    except Exception as e:
        print(f"Error processing message: {e}")

# 첫 번째 토픽에 대한 추가 로직 처리 함수
def process_picture(filename):
    global z_info
    print(f"Processing picture from {filename}")
    # 이미지 파일을 인코딩
    base64_image = encode_image(filename)
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    payload = {
        "model": "gpt-4o",
        "messages": [
            {
                "role": "user",
                "content": f"""
현재 기울기 정보는 다음과 같아:

Z축 : {z_info}

기울기 센서 축 값은 다음과 같이 읽어:

- Z 축: 센서가 수평축(좌/우) 방향으로 회전할 때 값이 변화합니다.
- 센서가 시계 방향으로 회전하면 Z 축 값이 양수(+)가 됩니다.
- 센서가 반시계 방향으로 회전하면 Z 축 값이 음수(-)가 됩니다.

기울기 센서는 네모난 20*20(단위 cm)인 통의 정가운데에 고정되어 있으며, 통 아래쪽을 향해 설치되어 있습니다.
센서의 기울기에 따라 물체들의 상대적 위치가 달라집니다.

이미지를 분석하여 다음을 수행해줘:
1. 이미지에서 노란색 물체는 쓰레기이고 초록색 물체는 해양 생물로 식별해줘.
2. 이미지에서 각 물체의 좌표를 식별하여 알려줘. 좌표는 0,0에서 20,20 범위로 정해줘.
3. Z축을 분석하여서 부표가 회전되어도 사진과 Z축 정보만으로 쓰레기와 해양 생물의 위치를 알려줘
다른 말은 하지 말고 오직 JSON으로만 응답해줘.
쓰레기들의 각각의 좌표
해양 생물들의 각각의 좌표
""",
                "image_url": f"data:image/jpeg;base64,{base64_image}"
            }
        ],
        "max_tokens": 300
    }

    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    response_json = response.json()

    # 응답이 유효한지 확인하고 project_response에 저장
    choices = response_json.get("choices", [])
    if choices:
        project_response = choices[0].get("message", {}).get("content", "")
    else:
        project_response = "Invalid response from GPT API"
    print("Response from GPT API for picture:", project_response)

# 두 번째 토픽에 대한 추가 로직 처리 함수
def process_project(x, y, z):
    global z_info
    print(f"Processing project coordinates: X={x}, Y={y}, Z={z}")
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    payload = {
        "model": "gpt-4o",
        "messages": [
            {
                "role": "user",
                "content": f"""
현재 기울기 정보는 다음과 같아:

X축: {x}
Y축: {y}
Z축: {z}
기울기 센서 축 값은 다음과 같이 읽어:

X 축: 센서가 앞뒤로 기울어질 때 값이 변화합니다.
센서가 앞으로 기울면 X 축 값이 -가 됩니다.
센서가 뒤로 기울면 X 축 값이 +가 됩니다.
Y 축: 센서가 좌우로 기울어질 때 값이 변화합니다.
센서가 왼쪽으로 기울면 Y 축 값이 -가 됩니다.
센서가 오른쪽으로 기울면 Y 축 값이 +가 됩니다.
Z 축: 센서가 수평축(좌/우) 방향으로 회전할 때 값이 변화합니다.
센서가 시계 방향으로 회전하면 Z 축 값이 양수(+)가 됩니다.
센서가 반시계 방향으로 회전하면 Z 축 값이 음수(-)가 됩니다.
기울기 센서는 네모난 20*20(단위 cm)인 통의 정가운데에 있으며, 통 아래쪽을 향해 설치되어 있습니다.
기울기 센서의 Z축을 기준으로 센서가 바라보는 방향을 찾고, X축과 Y축을 통해 파도의 방향을 구합니다.

X축과 Y축 값의 변경이 작으면 '잔잔함'이라고 판단합니다. X축과 Y축 값의 변경 폭이 엄청 크지 않으면 웬만하면 '잔잔함'으로 판단합니다.
만약 파도가 여러 방향에서 나타나면 세기가 더 센 방향 하나만 알려줍니다.

너의 응답은 JSON 형식으로만 알려줘. 다른 말은 필요없어. 이유나 설명 등 다른 말은 하지 말아줘 파도의 방향 정보 하나만 알려줘 파도의 방향을 다음 중 하나로만 말해줘:

왼쪽에서 오른쪽
오른쪽에서 왼쪽
위쪽에서 아래쪽
아래쪽에서 위쪽
대각선 오른쪽 위에서 대각선 왼쪽 아래
대각선 왼쪽 위에서 대각선 오른쪽 아래
대각선 오른쪽 아래에서 대각선 왼쪽 위로
대각선 왼쪽 아래에서 대각선 오른쪽 위로
잔잔함
아래는 응답하는 형식이야
"파도의 방향": "여기에 방향을 입력" 이 문장 딱 하나만 출력해줘
"""
            }
        ],
        "max_tokens": 300
    }

    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    response_json = response.json()

    # 응답이 유효한지 확인하고 project_response에 저장
    choices = response_json.get("choices", [])
    if choices:
        project_response = choices[0].get("message", {}).get("content", "")
    else:
        project_response = "Invalid response from GPT API"
    z_info = z
    print(f"*** Response from GPT API   x : {x}, y : {y}, z : {z}    for project coordinates:", project_response)

    return project_response

# 1. MQTT 클라이언트 객체 인스턴스화
client = mqtt.Client()

# 2. 관련 이벤트에 대한 콜백 함수 등록
client.on_connect = on_connect

# 메시지 수신 시 각 토픽에 대한 콜백 함수를 등록
def on_message(client, userdata, msg):
    if msg.topic == "PICTURE":
        on_message_picture(client, userdata, msg)
    elif msg.topic == "bssm/seonguk/project":
        on_message_project(client, userdata, msg)

client.on_message = on_message

try:
    # 3. 브로커 연결
    client.connect("broker.mqtt-dashboard.com")

    # 4. 메시지 루프 - 이벤트 발생 시 해당 콜백 함수 호출됨
    client.loop_start()

except Exception as err:
    print('에러 : %s' % err)

@app.route('/api/project_response', methods=['GET'])
def get_project_response():
    global project_response
    # Return only the direction string without any surrounding characters or JSON formatting
    return project_response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
