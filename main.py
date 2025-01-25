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
    ]
    for pattern in patterns:
        if re.match(pattern, url):
            return True
    return False

def get_file_info(file_id):
    """الحصول على معلومات الملف من جوجل درايف"""
    url = f'https://drive.google.com/uc?id={file_id}'
    response = requests.get(url, allow_redirects=True)
    
    if response.status_code == 200:
        # محاولة الحصول على اسم الملف من header
        content_disposition = response.headers.get('content-disposition')
        if content_disposition:
            fname = re.findall("filename=(.+)", content_disposition)
            if fname:
                # فك ترميز اسم الملف
                return urllib.parse.unquote(fname[0].strip('"'))
    
    # إذا لم نتمكن من الحصول على الاسم، نحاول طريقة أخرى
    url = f'https://drive.google.com/file/d/{file_id}/view'
    response = requests.get(url)
    if response.status_code == 200:
        title_match = re.search(r'<title>(.+?)</title>', response.text)
        if title_match:
            file_name = title_match.group(1)
            # إزالة " - Google Drive" من نهاية الاسم
            file_name = file_name.replace(' - Google Drive', '')
            return file_name
    
    return None

def extract_file_id(url):
    """استخراج معرف الملف من رابط جوجل درايف"""
    file_id = ""
    if "file/d/" in url:
        file_id = url.split("file/d/")[1].split("/")[0]
    elif "open?id=" in url:
        file_id = url.split("open?id=")[1].split("&")[0]
    return file_id

def get_direct_download_url(file_id):
    """تحويل رابط جوجل درايف إلى رابط تحميل مباشر"""
    return f'https://drive.google.com/uc?id={file_id}'

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
        file_name = get_file_info(file_id)
        
        if not file_name:
            file_name = f"file_{file_id}"
        
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
