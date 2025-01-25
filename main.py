import os
import telebot
import requests
import re
import urllib.parse
from urllib.parse import urlparse, parse_qs

# قم بتغيير هذا المفتاح إلى مفتاح البوت الخاص بك
BOT_TOKEN = "7806878555:AAFNpbXQjL7gmrT-xIkDIXg5xsPqWI5ADhs"

bot = telebot.TeleBot(BOT_TOKEN)

def get_file_id_from_url(url):
    """استخراج معرف الملف من رابط جوجل درايف"""
    try:
        if 'drive.google.com' not in url:
            return None
            
        # التعامل مع روابط /file/d/
        if '/file/d/' in url:
            file_id = url.split('/file/d/')[1].split('/')[0]
            return file_id
            
        # التعامل مع روابط ?id=
        parsed = urlparse(url)
        if 'id' in parse_qs(parsed.query):
            return parse_qs(parsed.query)['id'][0]
            
        return None
    except:
        return None

def download_file(file_id, destination):
    """تحميل الملف من جوجل درايف"""
    try:
        # تجهيز headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # الحصول على cookies وتوكن التحميل
        session = requests.Session()
        response = session.get(f'https://drive.google.com/uc?id={file_id}&export=download', headers=headers)
        
        # التحقق من وجود ملف كبير يحتاج تأكيد
        for key, value in response.cookies.items():
            if key.startswith('download_warning'):
                token = value
                response = session.get(f'https://drive.google.com/uc?id={file_id}&export=download&confirm={token}', 
                                    headers=headers, stream=True)
                break
        else:
            # إذا لم يكن هناك تأكيد مطلوب
            response = session.get(f'https://drive.google.com/uc?id={file_id}&export=download', 
                                headers=headers, stream=True)
        
        # التحقق من نجاح الطلب
        response.raise_for_status()
        
        # حفظ الملف
        with open(destination, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        return True
    except Exception as e:
        print(f"Download error: {str(e)}")
        return False

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = """مرحباً! 👋
أنا بوت تحميل ملفات من جوجل درايف 📥
فقط أرسل لي رابط الملف وسأقوم بتحميله وإرساله لك.
تأكد من أن الملف متاح للجميع!"""
    bot.reply_to(message, welcome_text)

@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = """كيفية استخدام البوت:
1. تأكد من أن الملف في جوجل درايف متاح للجميع
2. انسخ رابط الملف
3. أرسل الرابط إلى البوت
4. انتظر حتى يتم تحميل وإرسال الملف إليك"""
    bot.reply_to(message, help_text)

@bot.message_handler(func=lambda message: True)
def handle_drive_link(message):
    url = message.text.strip()
    
    try:
        # استخراج معرف الملف
        file_id = get_file_id_from_url(url)
        
        if not file_id:
            bot.reply_to(message, "عذراً، هذا ليس رابط جوجل درايف صالح! ❌")
            return
        
        # إرسال رسالة انتظار
        wait_msg = bot.reply_to(message, "جاري تحميل الملف... ⏳")
        
        # إنشاء مجلد للتحميلات إذا لم يكن موجوداً
        if not os.path.exists("downloads"):
            os.makedirs("downloads")
        
        # تحديد مسار الملف
        output_file = f"downloads/file_{file_id}"
        
        # تحميل الملف
        if download_file(file_id, output_file):
            # إرسال الملف
            with open(output_file, 'rb') as file:
                bot.send_document(
                    message.chat.id,
                    file,
                    caption=f"📁 تم التحميل بنجاح!"
                )
            # حذف الملف بعد إرساله
            os.remove(output_file)
            bot.delete_message(message.chat.id, wait_msg.message_id)
        else:
            bot.reply_to(message, "عذراً، فشل تحميل الملف. تأكد من أن الملف متاح للجميع! ❌")
            
    except Exception as e:
        print(f"Error: {str(e)}")
        bot.reply_to(message, "عذراً، حدث خطأ أثناء تحميل الملف. تأكد من أن الملف متاح للجميع! ❌")
        return

def main():
    print("تم تشغيل البوت...")
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            print(f"Bot polling error: {e}")
            continue

if __name__ == "__main__":
    main()
