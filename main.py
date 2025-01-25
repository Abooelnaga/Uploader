import os
import telebot
import gdown
import re
import requests
import urllib.parse

# قم بتغيير هذا المفتاح إلى مفتاح البوت الخاص بك
BOT_TOKEN = "7806878555:AAFNpbXQjL7gmrT-xIkDIXg5xsPqWI5ADhs"

bot = telebot.TeleBot(BOT_TOKEN)

def clean_filename(filename):
    """تنظيف اسم الملف من الأحرف غير المسموح بها"""
    # إزالة الأحرف غير المسموح بها في أسماء الملفات
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename

def extract_file_id(url):
    """استخراج معرف الملف من رابط جوجل درايف"""
    file_id = None
    
    # نمط للتعرف على روابط drive.google.com
    patterns = [
        r'drive\.google\.com/file/d/([a-zA-Z0-9_-]+)',
        r'drive\.google\.com/open\?id=([a-zA-Z0-9_-]+)',
        r'drive\.google\.com/uc\?id=([a-zA-Z0-9_-]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            file_id = match.group(1)
            # إزالة أي معلمات إضافية
            file_id = file_id.split('&')[0]
            break
            
    return file_id

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
        file_id = extract_file_id(url)
        
        if not file_id:
            bot.reply_to(message, "عذراً، هذا ليس رابط جوجل درايف صالح! ❌")
            return
        
        # إرسال رسالة انتظار
        wait_msg = bot.reply_to(message, "جاري تحميل الملف... ⏳")
        
        # إنشاء مجلد للتحميلات إذا لم يكن موجوداً
        if not os.path.exists("downloads"):
            os.makedirs("downloads")
        
        # تجهيز عنوان URL للتحميل
        download_url = f'https://drive.google.com/uc?id={file_id}'
        output = f"downloads/file_{file_id}"
        
        # تحميل الملف
        try:
            success = gdown.download(download_url, output, quiet=False, fuzzy=True)
            
            if not success or not os.path.exists(output):
                bot.reply_to(message, "عذراً، فشل تحميل الملف. تأكد من أن الملف متاح للجميع! ❌")
                return
            
            # الحصول على الاسم الحقيقي للملف
            real_filename = os.path.basename(output)
            if os.path.exists(output):
                # إرسال الملف
                with open(output, 'rb') as file:
                    bot.send_document(
                        message.chat.id,
                        file,
                        caption=f"📁 تم التحميل بنجاح!"
                    )
                # حذف الملف بعد إرساله
                os.remove(output)
                
            bot.delete_message(message.chat.id, wait_msg.message_id)
            
        except Exception as download_error:
            print(f"Download error: {str(download_error)}")
            bot.reply_to(message, "عذراً، حدث خطأ أثناء تحميل الملف. تأكد من أن الملف متاح للجميع! ❌")
            return
            
    except Exception as e:
        print(f"Error: {str(e)}")
        bot.reply_to(message, f"حدث خطأ غير متوقع: {str(e)} ❌")
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
