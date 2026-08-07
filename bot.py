from telebot import TeleBot, types
import requests
import json

# ضع التوكن الخاص ببوتك هنا من BotFather
TOKEN = "YOUR_TELEGRAM_BOT_TOKEN_HERE"
bot = TeleBot(TOKEN)

# قاموس لتخزين بيانات العميل المؤقتة أثناء الخطوات
user_data = {}

# 1. دالة تسجيل الدخول الخاصة بك
def login(number, password):
    url1 = 'https://mobile.vodafone.com.eg/auth/realms/vf-realm/protocol/openid-connect/token'
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Connection": "keep-alive",
        "silentLogin": "true",
        "x-agent-operatingsystem": "13",
        "clientId": "AnaVodafoneAndroid",
        "Accept-Language": "en",
        "x-agent-device": "Xiaomi M2102J20SG",
        "x-agent-version": "2025.11.1",
        "x-agent-build": "1063",
        "digitalId": "244BQYOGFM0IM",
        "device-id": "b83aab2d8fa633da",
        "Content-Type": "application/x-www-form-urlencoded",
        "Host": "mobile.vodafone.com.eg",
        "Accept-Encoding": "gzip",
        "User-Agent": "okhttp/4.12.0"
    }
    data = {
        "username": number,
        "password": password,
        "grant_type": "password",
        "client_secret": "95fd95fb-7489-4958-8ae6-d31a525cd20a",
        "client_id": "ana-vodafone-app"
    }
    response = requests.post(url1, data=data, headers=headers)
    if response.status_code != 200:
        raise Exception(f"فشل تسجيل الدخول (كود {response.status_code})")
    return response.json()['access_token']

# 2. دالة تغيير كلمة المرور الخاصة بك
def change_pass(number, token, password, newPass):
    url = "https://web.vodafone.com.eg/services/dxl/sam/serviceAccountManagement/v1/serviceAccount"
    payload = {
        "@type": "userPrefsUpdate",
        "customerAccount": {
            "authentication": {
                "password": password,
                "newPassword": newPass
            }
        },
        "resources": [{"resourceType": "MSISDN", "IDs": [{"value": number}]}]
    }
    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Mobile Safari/537.36",
        'Accept': "application/json",
        'Accept-Encoding': "gzip, deflate, br, zstd",
        'Content-Type': "application/json",
        'sec-ch-ua-platform': "\"Android\"",
        'Authorization': f"Bearer {token}",
        'Accept-Language': "AR",
        'msisdn': number,
        'clientId': "WebsiteConsumer",
        'Origin': "https://web.vodafone.com.eg",
        'Referer': "https://web.vodafone.com.eg/spa/profile",
    }
    response = requests.patch(url, data=json.dumps(payload), headers=headers)
    return response

# استقبال أمر البدء /start
@bot.message_handler(commands=['start'])
def start_cmd(message):
    chat_id = message.chat.id
    user_data[chat_id] = {}
    bot.send_message(chat_id, "مرحباً بك! 👋\nيرجى إرسال **رقم فودافون** الخاص بك:")
    bot.register_next_step_handler(message, get_number)

def get_number(message):
    chat_id = message.chat.id
    user_data[chat_id]['number'] = message.text.strip()
    bot.send_message(chat_id, "🔐 أرسل الآن **كلمة المرور الحالية**:")
    bot.register_next_step_handler(message, get_password)

def get_password(message):
    chat_id = message.chat.id
    user_data[chat_id]['password'] = message.text.strip()
    bot.send_message(chat_id, "✨ أرسل الآن **كلمة المرور الجديدة**:")
    bot.register_next_step_handler(message, process_change)

def process_change(message):
    chat_id = message.chat.id
    new_pass = message.text.strip()
    number = user_data[chat_id]['number']
    password = user_data[chat_id]['password']
    
    bot.send_message(chat_id, "⏳ جاري الاتصال والتغيير، انتظر لحظات...")
    
    try:
        token = login(number, password)
        res = change_pass(number, token, password, new_pass)
        
        try:
            data = res.json()
            if data.get("reason") == "Repeated Password":
                bot.send_message(chat_id, "❌ فشل التغيير: كلمة المرور الجديدة مستخدمة من قبل.")
            elif data.get("state") == "updated":
                bot.send_message(chat_id, "✅ تم تغيير كلمة المرور بنجاح!")
            else:
                bot.send_message(chat_id, f"⚠️ استجابة الخادم: {data}")
        except:
            bot.send_message(chat_id, f"⚠️ استجابة غير متوقعة: {res.text}")
            
    except Exception as e:
        bot.send_message(chat_id, f"❌ حدث خطأ أثناء العملية: {e}")
        
    # مسح البيانات المؤقتة لضمان الأمان
    user_data.pop(chat_id, None)

# تشغيل البوت
bot.infinity_polling()
