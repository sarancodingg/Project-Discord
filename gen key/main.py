import requests
import time
from bs4 import BeautifulSoup

base_url = "https://konoro.sogod.online/"
login_url = base_url
generate_key_url = "https://konoro.sogod.online/keys/generate"

session = requests.Session()

# เข้าสู่ระบบ
initial_page = session.get(base_url)
soup = BeautifulSoup(initial_page.content, 'html.parser')

csrf_token = soup.find('input', {'name': 'csrf_test_name'})['value']

payload = {
    "csrf_test_name": csrf_token,
    "username": "bangrus",
    "password": "bangsaran"
}

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    "Content-Type": "application/x-www-form-urlencoded",
    "Referer": base_url,
    "Origin": base_url
}

response = session.post(login_url, data=payload, headers=headers, allow_redirects=False)

if response.status_code == 303 and 'location' in response.headers and '/dashboard' in response.headers['location']:
    print("Login successful!")

    # รับข้อมูลการสร้างคีย์จากผู้ใช้
    max_devices = input("maxdevice > ")
    duration = input("day > ")
    num_keys = int(input("numkey >"))

# วนลูปตามจำนวนคีย์ที่ผู้ใช้ต้องการ
for i in range(num_keys):
    generate_page = session.get(generate_key_url)
    soup = BeautifulSoup(generate_page.content, 'html.parser')
    
    # ดึง CSRF token สำหรับสร้างคีย์
    csrf_token_generate = soup.find('input', {'name': 'csrf_test_name'})['value']
    
    key_payload = {
        "csrf_test_name": csrf_token_generate,
        "game": "ROV",
        "max_devices": max_devices,
        "duration": duration,
        "loopcount": 1,  # สร้างคีย์ 1 คีย์ต่อครั้ง
        "custominput": ""  
    }

    # ส่งคำร้องขอสร้างคีย์
    response_generate = session.post(generate_key_url, data=key_payload, headers=headers)

    if response_generate.status_code == 200:
        print(f"Key generation request {i + 1} successful!")

        soup_generate = BeautifulSoup(response_generate.text, 'html.parser')
        # ดึงคีย์แรกที่พบ
        key_element = soup_generate.find('strong', class_='key-sensi')

        if key_element:
            key = key_element.text.strip()  # ดึงข้อความของคีย์
            print(f"Generated key {i + 1}: {key}")

            # บันทึกคีย์ลงในไฟล์
            with open('keys.txt', 'a') as f:
                f.write(key + '\n')
            print("Key saved successfully!")
        else:
            print(f"Key not found in response for request {i + 1}.")
    else:
        print(f"Key generation request {i + 1} failed.")
        print(response_generate.status_code)
        print(response_generate.text)

    # เพิ่มการหน่วงเวลา (ปรับตามต้องการ)
    time.sleep(2)

else:
    print("Login failed.")
