import os
import telebot
import gdown
import re
import requests
import urllib.parse

# قم بتغيير هذا المفتاح إلى مفتاح البوت الخاص بك
BOT_TOKEN = "7806878555:AAFNpbXQjL7gmrT-xIkDIXg5xsPqWI5ADhs"

bot = telebot.TeleBot(BOT_TOKEN)

def is_valid_drive_link(url):
    """التحقق من صحة رابط جوجل درايف"""
    patterns = [
        r'https://drive\.google\.com/file/d/(.*?)/view',
        r'https://drive\.google\.com/open\?id=(.*?)(?:&|$)',
        r'https://drive\.google\.com/uc\?id=(.*?)(?:&|$)'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return True
    return False

def get_file_info(file_id):
    """الحصول على معلومات الملف من جوجل درايف"""
    try:
        session = requests.Session()
        
        # محاولة الحصول على معلومات الملف من الرابط المباشر
        url = f'https://drive.google.com/uc?id={file_id}&export=download'
        response = session.get(url, stream=True)
        
        # البحث عن اسم الملف في headers
        if 'content-disposition' in response.headers:
            content = response.headers['content-disposition']
            filename = re.findall('filename="(.+)"', content)
            if filename:
                return urllib.parse.unquote(filename[0])
        
        # إذا لم نجد في headers، نحاول من صفحة العرض
        view_url = f'https://drive.google.com/file/d/{file_id}/view'
        response = session.get(view_url)
        
        if response.status_code == 200:
            match = re.search(r'"title":"([^"]+)"', response.text)
            if match:
                return match.group(1)
                
        return f"file_{file_id}"
    except Exception as e:
        print(f"Error getting file info: {str(e)}")
        return f"file_{file_id}"

def extract_file_id(url):
    """استخراج معرف الملف من رابط جوجل درايف"""
    try:
        if "file/d/" in url:
            match = re.search(r'file/d/([^/]+)', url)
            if match:
                return match.group(1)
        elif "id=" in url:
            match = re.search(r'id=([^&]+)', url)
            if match:
                return match.group(1)
        return None
    except Exception as e:
        print(f"Error extracting file ID: {str(e)}")
        return None

def get_direct_download_url(file_id):
    """تحويل رابط جوجل درايف إلى رابط تحميل مباشر"""
    return f'https://drive.google.com/uc?id={file_id}&export=download'

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
    
    if not is_valid_drive_link(url):
        bot.reply_to(message, "عذراً، هذا ليس رابط جوجل درايف صالح! ❌")
        return
    
    try:
        # إرسال رسالة انتظار
        wait_msg = bot.reply_to(message, "جاري تحميل الملف... ⏳")
        
        # إنشاء مجلد للتحميلات إذا لم يكن موجوداً
        if not os.path.exists("downloads"):
            os.makedirs("downloads")
        
        # تحميل الملف
        file_id = extract_file_id(url)
        if not file_id:
            bot.reply_to(message, "عذراً، لم أتمكن من استخراج معرف الملف من الرابط! ❌")
            return
            
        file_name = get_file_info(file_id)
        output = f"downloads/{file_name}"
        download_url = get_direct_download_url(file_id)
        
        # تحميل الملف مع الاحتفاظ بالاسم الأصلي
        success = gdown.download(download_url, output, quiet=False, fuzzy=True)
        
        if not success:
            bot.reply_to(message, "عذراً، فشل تحميل الملف. تأكد من أن الملف متاح للجميع! ❌")
            return
            
        # إرسال الملف
        with open(output, 'rb') as file:
            bot.send_document(message.chat.id, file, caption=f"📁 {file_name}")
        
        # حذف الملف بعد إرساله
        os.remove(output)
        bot.delete_message(message.chat.id, wait_msg.message_id)
        
    except Exception as e:
        bot.reply_to(message, f"حدث خطأ أثناء تحميل الملف: {str(e)} ❌")
        return

def main():
    print("تم تشغيل البوت...")
    bot.polling(none_stop=True)

if __name__ == "__main__":
    main()
