import re
import asyncio
import aiohttp
import os
import shutil
from telethon import TelegramClient, events, utils
from telethon.tl.functions.account import UpdateProfileRequest
from telethon.tl.types import (
    MessageEntityBold, MessageEntityItalic, MessageEntityUnderline, 
    MessageEntityCode, MessageEntitySpoiler,
    InputMediaUploadedPhoto, InputMediaUploadedDocument,
    DocumentAttributeFilename, MessageMediaPhoto, MessageMediaDocument,
    PeerUser, PeerChat, PeerChannel
)
from datetime import datetime, timedelta
import jdatetime
import calendar
import logging
from PIL import Image, ImageDraw, ImageFont, ImageSequence
import io
import textwrap
from bs4 import BeautifulSoup
import json
import math
import tempfile
from pathlib import Path
import random
from urllib.parse import urlparse, quote, urljoin
import traceback
import sys
import time

# اطلاعات API
api_id = 20182995
api_hash = '228e9fd91b46a98388b4e173880ccd68'

# کلاینت تلگرام
client = TelegramClient('session', api_id, api_hash, connection_retries=5, retry_delay=5, request_retries=5)

# آی‌دی تلگرام شما
allowed_user_id = 928758237

# لیست دشمنان و دوستان
enemies = {}
friends = {}

# لیست آیدی‌های مسدود شده در سکوت پیوی
silent_pv_users = set()

# تنظیمات
time_enabled = False
silent_pv_enabled = False
current_font_style = "classic"
message_log_enabled = False
delete_log_enabled = False
edit_log_enabled = False
auto_text_style = None

# اطلاعات کارت بانکی
card_info = {
    "number": "",
    "name": "",
    "gateway": ""
}

# انواع فونت‌های اعداد (بدون حروف انگلیسی)
fonts = {
    "classic": {
        "map": str.maketrans('0123456789:', '0123456789:'),
        "sample": "12:34"
    },
    "modern": {
        "map": str.maketrans('0123456789:', '𝟬𝟭𝟮𝟯𝟰𝟱𝟲𝟳𝟴𝟵:'),
        "sample": "𝟭𝟮:𝟯𝟰"
    },
    "mono": {
        "map": str.maketrans('0123456789:', '𝟶𝟷𝟸𝟹𝟺𝟻𝟼𝟽𝟾𝟿:'),
        "sample": "𝟷𝟸:𝟹𝟺"
    },
    "bold": {
        "map": str.maketrans('0123456789:', '𝟬𝟭𝟮𝟯𝟰𝟱𝟲𝟳𝟴𝟵:'),
        "sample": "𝟭𝟮:𝟯𝟰"
    },
    "fancy": {
        "map": str.maketrans('0123456789:', '𝟘𝟙𝟚𝟛𝟜𝟝𝟞𝟟𝟠𝟡:'),
        "sample": "𝟙𝟚:𝟛𝟜"
    },
    "double": {
        "map": str.maketrans('0123456789:', '𝟘𝟙𝟚𝟛𝟜𝟝𝟞𝟟𝟠𝟡:'),
        "sample": "𝟙𝟚:𝟛𝟜"
    },
    "code": {
        "map": str.maketrans('0123456789:', '𝟶𝟷𝟸𝟹𝟺𝟻𝟼𝟽𝟾𝟿:'),
        "sample": "𝟷𝟸:𝟹𝟺"
    },
    "roman": {
        "map": str.maketrans('0123456789:', 'ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ:'),
        "sample": "ⅠⅡ:ⅢⅣ"
    },
    "circle": {
        "map": str.maketrans('0123456789:', '⓪①②③④⑤⑥⑦⑧⑨:'),
        "sample": "①②:③④"
    },
    "square": {
        "map": str.maketrans('0123456789:', '🄋➀➁➂➃➄➅➆➇➈:'),
        "sample": "➀➁:➂➃"
    },
    "math": {
        "map": str.maketrans('0123456789:', '𝟎𝟏𝟐𝟑𝟒𝟓𝟔𝟕𝟖𝟗:'),
        "sample": "𝟏𝟐:𝟑𝟒"
    },
    "subscript": {
        "map": str.maketrans('0123456789:', '₀₁₂₃₄₅₆₇₈₉:'),
        "sample": "₁₂:₃₄"
    },
    "superscript": {
        "map": str.maketrans('0123456789:', '⁰¹²³⁴⁵⁶⁷⁸⁹:'),
        "sample": "¹²:³⁴"
    },
    "fullwidth": {
        "map": str.maketrans('0123456789:', '０１２３４５６７８９：'),
        "sample": "１２：３４"
    },
    "currency": {
        "map": str.maketrans('0123456789:', '₀₁₂₃₄₅₆₇₈₉:'),
        "sample": "₁₂:₃₄"
    },
    "outline": {
        "map": str.maketrans('0123456789:', '①②③④⑤⑥⑦⑧⑨⓪:'),
        "sample": "①②:③④"
    },
    "shadow": {
        "map": str.maketrans('0123456789:', '🄋➀➁➂➃➄➅➆➇➈:'),
        "sample": "➀➁:➂➃"
    },
    "typewriter": {
        "map": str.maketrans('0123456789:', '𝟶𝟷𝟸𝟹𝟺𝟻𝟼𝟽𝟾𝟿:'),
        "sample": "𝟷𝟸:𝟹𝟺"
    },
    "decorative": {
        "map": str.maketrans('0123456789:', '🄀➊➋➌➍➎➏➐➑➒:'),
        "sample": "➊➋:➌➍"
    },
    "black_circle": {
        "map": str.maketrans('0123456789:', '⓿❶❷❸❹❺❻❼❽❾:'),
        "sample": "❶❷:❸❹"
    },
    "parenthesis": {
        "map": str.maketrans('0123456789:', '⑴⑵⑶⑷⑸⑹⑺⑻⑼⑽:'),
        "sample": "⑴⑵:⑶⑷"
    },
    "double_circle": {
        "map": str.maketrans('0123456789:', '⓪①②③④⑤⑥⑦⑧⑨:'),
        "sample": "①②:③④"
    },
    "filled_circle": {
        "map": str.maketrans('0123456789:', '⓿❶❷❸❹❺❻❼❽❾:'),
        "sample": "❶❷:❸❹"
    },
    "dotted": {
        "map": str.maketrans('0123456789:', '⓿⓿➊➋➌➍➎➏➐➑:'),
        "sample": "➊➋:➌➍"
    },
    "small_numbers": {
        "map": str.maketrans('0123456789:', '⁰¹²³⁴⁵⁶⁷⁸⁹:'),
        "sample": "¹²:³⁴"
    },
    "large_numbers": {
        "map": str.maketrans('0123456789:', '𝟬𝟭𝟮𝟯𝟰𝟱𝟲𝟳𝟴𝟵:'),
        "sample": "𝟭𝟮:𝟯𝟰"
    },
    "fraction": {
        "map": str.maketrans('0123456789:', '½⅓⅔¼¾⅕⅖⅗⅘⅙:'),
        "sample": "½⅓:⅔¼"
    }
}

# لیست متون فان و طنز برای پاسخ به دوستان (با حال و هوای فشی)
friend_responses = [
    "کیرتم مشتی",
    "بشاش شنا کنم",
    "شق کن بارفیکس برم",
    "کیرتو بخورم ستون",
    "جات رو کیرمه مشتی",
    "کیرتو بده لیس بزنیم",
    "خایه هام مال خودت مشتی",
    "داشمی",
    "تاج سری ستونم",
    "کیرت تو کسمادر بدخات",
    "مادر بدخاتو گاییدم",
    "ایدی بدخا بده ننشو بگام",
    "کیر تو ناموس کسی که ازت بدش بیاد",
    "خایتو بخورم ستونم",
    "بمولا که عشقمی",
    "دوست دارم داپشی",
    "ناموس بدخاتو گاییدم",
    "کیرت تو دنیا",
    "بکش پایین بکنمت",
    "رفاقت ابدی داپش",
    "کیرتو الکسیس بخوره",
    "امار ننه بدخاتو دربیارم؟",
    "بدخات ننش شب خوابه",
    "کیرت تو هرچی ادم مادرجندس",
    "کیرمون تو کسمادر بدخات",
    "کسخار دنیا داپش",
    "هعی مشتی کیر تو روزگار",
    "رفاقت پابرجا",
    "گاییدن کونت بهترین لذته",
    "کیرم به کونت بیب",
    "بخار عنتم تف کن شنا کنیم",
    "گوزیدم واست ارکستر زدم",
    "باسنمو ببینی سکته میکنی",
    "کیرم و ننتم واست شعر میخونن",
    "باسنم قارچ گرفته مشتی",
    "عن کردم واست کباب کوپده",
    "گوزیدم رنگین کمان شد",
    "بخار کونمو بخور کبابت میشه",
    "عنتم واست تخم مرغ دزدید",
    "باسنم واست جوک میگه",
    "کیرمو ببین یاد میفتیم",
    "ننتم گفته بهت سلام برسونم",
    "خایمالی کن مشتی",
    "کیرم وایساده واست",
    "باسنمو دیدی غش کن",
    "عنتم واست فندق شور کرده",
    "گوزیدم بادکنکی شد",
    "کیرم واست شعر حافظ میخونه",
    "ننتم گفته بیا خایه مال",
    "باسنم واست کتاب نوشت",
    "عنتم واست کتلت درست کرد",
    "گوزیدم آهنگ ساخت",
    "کیرم و ننتم رفیقن",
    "بخار کونمو قلیون بکش",
    "باسنم واست نقاشی کشید",
    "عنتم واست پیتزا پخت",
    "گوزیدم هواپیما شد",
    "کیرم واست لالایی میخونه",
    "ننتم واست شیرینی پخت",
    "باسنم واست فیلم بازی کرد",
    "عنتم واست دمنوش درست کرد",
    "گوزیدم فشفشه ای شد",
    "کیرم و باسنم رفیقن",
    "بخار کونمو بخور بهش میگن عطر",
    "ننتم گفته باسنت خوشگله",
    "باسنم واست جوک تعریف کرد",
    "عنتم واست ساندویچ درست کرد",
    "گوزیدم ترقه بازی درآوردم",
    "کیرم واست پادکست ضبط کرد",
    "بخار باسنم واست بخور",
    "ننتم واست نون بربری پخت"
]

# لیست متون سنگین برای پاسخ به دشمنان
enemy_responses = [
    "یا الله کیرم به قلب مادرت",
    "مادرتو میدم سگ بگاد",
    "با کیرم ناموستو پاره میکنم",
    "کیرمو حلقه میکنم دور گردن مادرت",
    "کسخارتو بتن ریزی کردم",
    "ننتو تو پورن هاب دیدم",
    "کیر و خایه هام به کل اجدادت",
    "فیلم ننت فروشی",
    "کسننت پدرتم",
    "میرم تو کسمادرت با بیل پارش میکنم",
    "کیر به ناموس گشادت",
    "خسته نشدی ننتو گاییدم؟",
    "کیرم شلاقی به ناموس جندت",
    "با ناموست تریسام زدم",
    "برج خلیفه تو مادرت",
    "دو پایی میرم تو کسمادرت",
    "داگی استایل ننتو گاییدم",
    "هندل زدم به کون مادرت گاییدمش",
    "یگام دو گام ننتو میگام",
    "کیرمو نکن تو کسمادرت",
    "کیر و خایم به توان دو تو کسمادرت",
    "قمه تو کسمادرت",
    "نود ننتو دارم مادرکسده",
    "با کله میرم تو کسمادرت",
    "دستام تو کسمادرت",
    "کیرم به استخون های ننت",
    "مادرتو حراج زدم مادرجنده",
    "بریم برای راند بعد با ننت",
    "کیرم به رحم نجس ننت",
    "کیرم به چش و چال ننت",
    "کیروم به فرق سر ناموست",
    "مادرجنده کیری ناموس",
    "با کون ننت ناگت درست کردم",
    "خایه هام به کسمادرت",
    "برج میلاد تو کسمادرت",
    "یخچال تو کسمادرت",
    "کیرم به پوزه مادرت",
    "مادرتو زدم به سیخ",
    "کسمادرت",
    "کیر شتر تو ناموست",
    "نودا ننت فروشی",
    "خایه با پرزش تو ننت", 
    "چشای ننت تو کون خارت بره",
    "ننتو ریدم",
    "لال شو مادرجنده اوبنه ای", 
    "اوب از کون ننت میباره",
    "ماهی تو کسمادرت",
    "کیر هرچی خره تو کسمادرت", 
    "کیر رونالدو به کس خار و مادرت",
    "مادرت زیر کیرم شهید شد", 
    "اسپنک زدم به کون مادر جندت",
    "کیرم یهویی به مردع و زندت",
    "کیر به فیس ننت", 
    "برو مادرجنده بی غیرت",
    "استخون های مرده هات تو کسمادرت",
    "اسپرمم تو نوامیست", 
    "مادرتو با پوزیشن های مختلف گاییدم",
    "میز و صندلی تو کسمادرت",
    "کیر به ناموس دلقکت", 
    "دمپایی تو کون ننت"
]

user_response_queue = {}
message_edit_log = {}
message_delete_log = {}  # ذخیره پیام‌ها برای لاگ حذف

# نگاشت روزها و ماه‌ها
day_names_fa = {
    "Sunday": "یکشنبه", "Monday": "دوشنبه", "Tuesday": "سه‌شنبه",
    "Wednesday": "چهارشنبه", "Thursday": "پنج‌شنبه", "Friday": "جمعه", "Saturday": "شنبه"
}

jalali_months_fa = {
    1: 'فروردین', 2: 'اردیبهشت', 3: 'خرداد', 4: 'تیر', 5: 'مرداد', 6: 'شهریور',
    7: 'مهر', 8: 'آبان', 9: 'آذر', 10: 'دی', 11: 'بهمن', 12: 'اسفند'
}

def get_jalali_month_days(year, month):
    is_leap_year = jdatetime.datetime(year, 1, 1).isleap()
    if month in [1, 2, 3, 4, 5, 6]:
        return 31
    elif month in [7, 8, 9, 10, 11]:
        return 30
    else:
        return 30 if is_leap_year else 29

def get_remaining_days_in_year(year, current_month, current_day):
    remaining_days = 0
    remaining_days_in_current_month = get_jalali_month_days(year, current_month) - current_day
    for month in range(current_month + 1, 13):
        remaining_days += get_jalali_month_days(year, month)
    return remaining_days_in_current_month + remaining_days

def get_date_time_info():
    now = jdatetime.datetime.now()
    current_day = now.day
    total_days_in_month = get_jalali_month_days(now.year, now.month)
    remaining_days_in_month = total_days_in_month - current_day
    remaining_days_in_year = get_remaining_days_in_year(now.year, now.month, current_day)
    day_name_en = now.togregorian().strftime("%A")
    day_name_fa = day_names_fa.get(day_name_en, '')
    jalali_month_name_fa = jalali_months_fa.get(now.month, '')
    
    return {
        'time_now': now.strftime("%H:%M:%S"),
        'jalali_date': now.strftime("%Y/%m/%d"),
        'gregorian_date': now.togregorian().strftime("%Y/%m/%d"),
        'day_name_fa': day_name_fa,
        'day_name_en': day_name_en,
        'jalali_month_name_fa': jalali_month_name_fa,
        'month_name_en': now.togregorian().strftime("%B"),
        'utc_date': now.togregorian().strftime("%Y-%m-%d %H:%M:%S"),
        'remaining_days_in_month': remaining_days_in_month,
        'remaining_days_in_year': remaining_days_in_year
    }

async def send_with_style(event, text, style="normal"):
    try:
        entities = []
        if style == "bold":
            entities = [MessageEntityBold(0, len(text))]
        elif style == "italic":
            entities = [MessageEntityItalic(0, len(text))]
        elif style == "underline":
            entities = [MessageEntityUnderline(0, len(text))]
        elif style == "mono":
            entities = [MessageEntityCode(0, len(text))]
        elif style == "spoiler":
            entities = [MessageEntitySpoiler(0, len(text))]
        
        await event.reply(text, formatting_entities=entities)
    except Exception as e:
        print(f"خطا در send_with_style: {e}")

async def send_random_reply(event, responses_list):
    """ارسال پاسخ رندوم از لیست"""
    try:
        if responses_list:
            random_response = random.choice(responses_list)
            await send_with_style(event, random_response, "normal")
    except Exception as e:
        print(f"خطا در send_random_reply: {e}")

async def save_media_with_dot(event):
    """ذخیره مدیا وقتی ریپلای شده و متن با نقطه تموم میشه - بدون حذف پیام"""
    try:
        if event.is_reply and event.sender_id == allowed_user_id:
            text = event.raw_text.strip()
            
            # اگه متن با نقطه تموم بشه
            if text.endswith('.'):
                replied_message = await event.get_reply_message()
                
                if replied_message and replied_message.media:
                    # دریافت اطلاعات فرستنده
                    sender = await replied_message.get_sender()
                    sender_id = replied_message.sender_id
                    sender_name = "ناشناس"
                    sender_username = ""
                    
                    if sender:
                        sender_name = getattr(sender, 'first_name', '') or getattr(sender, 'title', 'ناشناس')
                        sender_username = getattr(sender, 'username', '')
                    
                    # دانلود مدیا
                    media = await client.download_media(replied_message.media, file=tempfile.gettempdir())
                    
                    if media and os.path.exists(media):
                        # ارسال به سیو مسیج
                        await client.send_file('me', media)
                        
                        # پاک کردن فایل موقت
                        os.remove(media)
                        
                        # ارسال تایید به سیو مسیج با اطلاعات فرستنده
                        caption = f"✅ مدیا با موفقیت ذخیره شد\n👤 فرستنده: {sender_name} (آیدی: {sender_id})\n📝 متن شما: {text}\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                        if sender_username:
                            caption += f"\n📱 یوزرنیم: @{sender_username}"
                        
                        await client.send_message('me', caption)
                        
                        # پیام فرمان حذف نمیشه
                        print(f"مدیا با نقطه ذخیره شد از {sender_name}")
    except Exception as e:
        print(f"خطا در save_media_with_dot: {e}")

async def handle_name_change(event):
    try:
        match = re.match(r"اسم عوض بشه به (.+)", event.raw_text)
        if match:
            new_name = match.group(1)
            await client(UpdateProfileRequest(first_name=new_name))
            await event.message.edit("✅ اسم مورد نظر با موفقیت عوض شد")
    except Exception as e:
        print(f"خطا در handle_name_change: {e}")
        try:
            await event.message.edit(f"❌ خطا: {str(e)}")
        except:
            pass

async def send_command_list(event):
    try:
        # ساخت نمونه فونت‌ها (فقط اعداد)
        font_samples = ""
        font_counter = 0
        font_list = [
            ("کلاسیک", "classic"),
            ("مدرن", "modern"),
            ("مونو", "mono"),
            ("بولد", "bold"),
            ("فانسی", "fancy"),
            ("دوبل", "double"),
            ("کد", "code"),
            ("رومن", "roman"),
            ("دایره", "circle"),
            ("مربع", "square"),
            ("ریاضی", "math"),
            ("زیرنویس", "subscript"),
            ("بالانویس", "superscript"),
            ("پهن", "fullwidth"),
            ("ارزی", "currency"),
            ("حاشیه‌دار", "outline"),
            ("سایه‌دار", "shadow"),
            ("ماشین تحریر", "typewriter"),
            ("تزیینی", "decorative"),
            ("دایره سیاه", "black_circle"),
            ("پرانتزدار", "parenthesis"),
            ("دایره دوتایی", "double_circle"),
            ("دایره پر", "filled_circle"),
            ("نقطه‌چین", "dotted"),
            ("ریز", "small_numbers"),
            ("درشت", "large_numbers"),
            ("کسری", "fraction")
        ]
        
        for persian_name, font_key in font_list:
            if font_key in fonts:
                font_samples += f"• `فونت {persian_name}` - نمونه: {fonts[font_key]['sample']}\n"
                font_counter += 1
                if font_counter % 7 == 0:
                    font_samples += "\n"
        
        command_list = f"""
📋 **لیست دستورات سلف @l37Pl**

**⚡ مدیریت دشمن و دوست:**
• `تنظیم بدخا` (ریپلای) - اضافه به لیست بدخا (پاسخ رندوم)
• `حذف بدخا` (ریپلای) - حذف از لیست بدخا
• `تنظیم مشتی` (ریپلای) - اضافه به لیست مشتی (پاسخ رندوم)
• `حذف مشتی` (ریپلای) - حذف از لیست مشتی

**⏰ مدیریت زمان:**
• `تایم روشن` - فعال‌سازی ساعت زنده (فقط اسم)
• `تایم خاموش` - غیرفعال‌سازی ساعت

**🎨 فونت‌های اعداد ({len(font_list)} نوع):**
{font_samples}

**🎨 استایل خودکار متن (سراسری):**
• `تنظیم استایل بولد` - فعال‌سازی استایل بولد خودکار
• `تنظیم استایل ایتالیک` - فعال‌سازی استایل ایتالیک خودکار
• `تنظیم استایل آندرلاین` - فعال‌سازی استایل آندرلاین خودکار
• `تنظیم استایل مونو` - فعال‌سازی استایل مونو خودکار
• `تنظیم استایل اسپویلر` - فعال‌سازی استایل اسپویلر خودکار
• `تنظیم استایل عادی` - غیرفعال‌سازی استایل خودکار

**🔇 مدیریت سکوت پیوی:**
• `سکوت پیوی روشن` - فعال‌سازی سکوت برای همه
• `سکوت پیوی خاموش` - غیرفعال‌سازی سکوت برای همه
• `سکوت آیدی [آیدی عددی]` - اضافه کردن آیدی به لیست سکوت
• `حذف سکوت آیدی [آیدی عددی]` - حذف آیدی از لیست سکوت

**💳 مدیریت کارت بانکی:**
• `تنظیم کارت شماره‌کارت نام [درگاه]` - تنظیم اطلاعات کارت
• `حذف کارت` - حذف اطلاعات کارت
• `کارت` - دریافت اطلاعات کارت

**🛒 جستجو در دیجی‌کالا:**
• `سرچ دیجی [نام محصول]` - جستجوی محصول و نمایش قیمت‌های دقیق (به تومان)

**ℹ اطلاعات کاربری:**
• `آیدی من` - دریافت آیدی عددی خودتان
• `آیدی [یوزرنیم]` - دریافت آیدی عددی کاربر/گروه/کانال
• `آیدی ریپلای` - دریافت آیدی عددی کاربر ریپلای شده

**💾 ذخیره مدیا:**
• ریپلای روی هر مدیا + نوشتن هر متنی که با `.` تموم بشه - ذخیره خودکار در سیومسیج

**📝 لاگ پیام:**
• `لاگ پیام روشن` - فعال‌سازی ثبت پیام‌های پیوی
• `لاگ پیام خاموش` - غیرفعال‌سازی ثبت

**ℹ اطلاعات:**
• `تاریخ و ساعت` - نمایش تاریخ و ساعت
• `اسم عوض بشه به [اسم]` - تغییر نام پروفایل
• `لیست دستورات` - نمایش این راهنما
"""
        await event.message.edit(command_list)
    except Exception as e:
        print(f"خطا در send_command_list: {e}")

async def handle_silent_pv(event):
    global silent_pv_enabled
    
    try:
        # حالت سکوت برای آیدی‌های خاص
        if event.is_private and event.sender_id != allowed_user_id and event.sender_id in silent_pv_users:
            await event.message.delete()
            if event.is_reply:
                replied = await event.get_reply_message()
                if replied and replied.sender_id == allowed_user_id:
                    await replied.delete()
            return
        
        # حالت عادی سکوت برای همه
        if silent_pv_enabled and event.is_private and event.sender_id != allowed_user_id:
            await event.message.delete()
            if event.is_reply:
                replied = await event.get_reply_message()
                if replied and replied.sender_id == allowed_user_id:
                    await replied.delete()
    except Exception as e:
        print(f"خطا در سکوت پیوی: {e}")

async def log_message_action(event, action_type):
    global message_log_enabled, delete_log_enabled, edit_log_enabled
    
    # فقط برای پیوی
    if not hasattr(event, 'is_private') or not event.is_private:
        return
    
    try:
        if action_type == "edit" and edit_log_enabled:
            if hasattr(event, 'message') and event.message:
                message = event.message
                sender = await message.get_sender()
                
                sender_id = message.sender_id
                sender_name = "ناشناس"
                sender_username = "ندارد"
                
                if sender:
                    sender_name = getattr(sender, 'first_name', '') or getattr(sender, 'title', 'ناشناس')
                    sender_username = getattr(sender, 'username', 'ندارد')
                
                old_text = message_edit_log.get(message.id, "پیام جدید")
                new_text = message.text if message.text else "مدیا"
                
                message_edit_log[message.id] = new_text
                
                log_text = f"""
✏️ **پیام ادیت شد (پیوی)**

👤 **فرستنده:**
   • آیدی: `{sender_id}`
   • نام: {sender_name}
   • یوزرنیم: @{sender_username}

📝 **متن قبلی:**
{old_text[:300]}{'...' if len(old_text) > 300 else ''}

📄 **متن جدید:**
{new_text[:300]}{'...' if len(new_text) > 300 else ''}

⏰ **زمان:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
                await client.send_message('me', log_text)
                print(f"لاگ ادیت ارسال شد برای پیوی {event.chat_id}")
                
        elif action_type == "delete" and delete_log_enabled:
            deleted_count = len(event.deleted_ids) if hasattr(event, 'deleted_ids') else 1
            
            # جمع‌آوری اطلاعات پیام‌های حذف شده
            deleted_messages_info = []
            
            # دریافت اطلاعات چت
            chat_id = event.chat_id if hasattr(event, 'chat_id') else "نامشخص"
            
            # تلاش برای دریافت اطلاعات فرستنده از چت
            sender_info = {}
            try:
                if chat_id != "نامشخص" and chat_id != allowed_user_id:
                    # اگر چت پیوی هست، خود فرستنده همون چت هست
                    if chat_id and chat_id > 0:  # آیدی مثبت یعنی کاربر عادی
                        try:
                            sender_entity = await client.get_entity(chat_id)
                            sender_info = {
                                'id': chat_id,
                                'name': getattr(sender_entity, 'first_name', '') or getattr(sender_entity, 'title', 'ناشناس'),
                                'username': getattr(sender_entity, 'username', 'ندارد')
                            }
                        except:
                            sender_info = {
                                'id': chat_id,
                                'name': 'ناشناس',
                                'username': 'ندارد'
                            }
            except:
                pass
            
            # جمع‌آوری اطلاعات از دیکشنری message_delete_log
            if hasattr(event, 'messages') and event.messages:
                for msg_id in event.messages:
                    if msg_id in message_delete_log:
                        msg_info = message_delete_log[msg_id]
                        # اگر اطلاعات فرستنده نداریم، از اطلاعات چت استفاده کنیم
                        if 'sender_id' not in msg_info and sender_info:
                            msg_info['sender_id'] = sender_info.get('id', 'نامشخص')
                            msg_info['sender_name'] = sender_info.get('name', 'ناشناس')
                            msg_info['sender_username'] = sender_info.get('username', 'ندارد')
                        deleted_messages_info.append(msg_info)
            
            # اگر هیچ اطلاعاتی از لاگ نگرفته بودیم ولی آیدی چت رو داریم
            if not deleted_messages_info and sender_info:
                deleted_messages_info.append({
                    'sender_id': sender_info.get('id', 'نامشخص'),
                    'sender_name': sender_info.get('name', 'ناشناس'),
                    'sender_username': sender_info.get('username', 'ندارد'),
                    'text': 'بدون متن (مدیا یا نامشخص)',
                    'time': datetime.now()
                })
            
            # ساخت متن لاگ
            if deleted_messages_info:
                log_text = f"""
🗑 **پیام حذف شد (پیوی)**

💬 **چت:** پیوی
🔢 **تعداد پیام‌ها:** {deleted_count}
⏰ **زمان:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📋 **جزئیات پیام‌های حذف شده:**
"""
                for i, info in enumerate(deleted_messages_info[:5], 1):  # حداکثر 5 پیام
                    sender_id = info.get('sender_id', 'نامشخص')
                    sender_name = info.get('sender_name', 'ناشناس')
                    sender_username = info.get('sender_username', 'ندارد')
                    text = info.get('text', 'بدون متن')
                    msg_time = info.get('time', datetime.now())
                    
                    if isinstance(msg_time, datetime):
                        time_str = msg_time.strftime('%H:%M:%S')
                    else:
                        time_str = 'نامشخص'
                    
                    log_text += f"\n{i}. 👤 **فرستنده:** {sender_name}"
                    log_text += f"\n   🆔 آیدی: `{sender_id}`"
                    if sender_username and sender_username != 'ندارد':
                        log_text += f"\n   📱 یوزرنیم: @{sender_username}"
                    log_text += f"\n   ⏰ زمان ارسال: {time_str}"
                    log_text += f"\n   📝 متن: {text[:150]}{'...' if len(text) > 150 else ''}\n"
            else:
                # اگر هیچ اطلاعاتی نداریم
                chat_name = "پیوی"
                try:
                    if chat_id != "نامشخص" and chat_id > 0:
                        try:
                            entity = await client.get_entity(chat_id)
                            chat_name = getattr(entity, 'first_name', '') or getattr(entity, 'title', 'کاربر ناشناس')
                        except:
                            chat_name = f"کاربر {chat_id}"
                except:
                    pass
                
                log_text = f"""
🗑 **پیام حذف شد (پیوی)**

💬 **چت:** {chat_name}
🔢 **تعداد پیام‌ها:** {deleted_count}
⏰ **زمان:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

⚠️ **توجه:** اطلاعات دقیق پیام‌ها در دسترس نیست.
"""
            await client.send_message('me', log_text)
            print(f"لاگ حذف ارسال شد برای پیوی {chat_id}")
            
    except Exception as e:
        print(f"خطا در لاگ {action_type}: {e}")
        try:
            await client.send_message('me', f"❌ خطا در لاگ {action_type}: {str(e)}")
        except:
            pass

def apply_font(text, font_style):
    if font_style in fonts:
        return text.translate(fonts[font_style]["map"])
    return text

async def update_profile_name():
    global time_enabled, current_font_style
    while True:
        try:
            if time_enabled:
                now = datetime.now()
                time_now = f"{now.hour}:{now.minute:02d}"
                time_formatted = apply_font(time_now, current_font_style)

                me = await client.get_me()
                current_name = me.first_name if me.first_name else ""
                
                # الگوهای پاک کردن همه انواع فونت اعداد
                patterns = [
                    r'\s*[𝟬𝟭𝟮𝟯𝟰𝟱𝟲𝟳𝟴𝟵]{1,2}:[𝟬𝟭𝟮𝟯𝟰𝟱𝟲𝟳𝟴𝟵]{2}\s*$',
                    r'\s*[𝟶𝟷𝟸𝟹𝟺𝟻𝟼𝟽𝟾𝟿]{1,2}:[𝟶𝟷𝟸𝟹𝟺𝟻𝟼𝟽𝟾𝟿]{2}\s*$',
                    r'\s*[𝟘𝟙𝟚𝟛𝟜𝟝𝟞𝟟𝟠𝟡]{1,2}:[𝟘𝟙𝟚𝟛𝟜𝟝𝟞𝟟𝟠𝟡]{2}\s*$',
                    r'\s*\d{1,2}:\d{2}\s*$',
                    r'\s*[ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ]{1,2}:[ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ]{2}\s*$',
                    r'\s*[⓪①②③④⑤⑥⑦⑧⑨]{1,2}:[⓪①②③④⑤⑥⑦⑧⑨]{2}\s*$',
                    r'\s*[🄋➀➁➂➃➄➅➆➇➈]{1,2}:[🄋➀➁➂➃➄➅➆➇➈]{2}\s*$',
                    r'\s*[𝟎𝟏𝟐𝟑𝟒𝟓𝟔𝟕𝟖𝟗]{1,2}:[𝟎𝟏𝟐𝟑𝟒𝟓𝟔𝟕𝟖𝟗]{2}\s*$',
                    r'\s*[₀₁₂₃₄₅₆₇₈₉]{1,2}:[₀₁₂₃₄₅₆₇₈₉]{2}\s*$',
                    r'\s*[⁰¹²³⁴⁵⁶⁷⁸⁹]{1,2}:[⁰¹²³⁴⁵⁶⁷⁸⁹]{2}\s*$',
                    r'\s*[０１２３４５６７８９]{1,2}:[０１２３４５６７۸９]{2}\s*$',
                    r'\s*[❶❷❸❹❺❻❼❽❾❿]{1,2}:[❶❷❸❹❺❻❼❽❾❿]{2}\s*$',
                    r'\s*[➊➋➌➍➎➏➐➑➒➓]{1,2}:[➊➋➌➍➎➏➐➑➒➓]{2}\s*$',
                    r'\s*[⑴⑵⑶⑷⑸⑹⑺⑻⑼⑽]{1,2}:[⑴⑵⑶⑷⑸⑹⑺⑻⑼⑽]{2}\s*$',
                    r'\s*[½⅓⅔¼¾⅕⅖⅗⅘⅙]{1,2}:[½⅓⅔¼¾⅕⅖⅗⅘⅙]{2}\s*$'
                ]
                
                for pattern in patterns:
                    current_name = re.sub(pattern, '', current_name)
                
                new_name = f"{current_name.strip()} {time_formatted}"
                
                await client(UpdateProfileRequest(first_name=new_name.strip()))
        except Exception as e:
            print(f"خطا در به‌روزرسانی نام پروفایل: {e}")
        
        await asyncio.sleep(35)

async def digikala_search(query):
    """جستجو در دیجی‌کالا و نمایش قیمت دقیق به تومان"""
    try:
        async with aiohttp.ClientSession() as session:
            search_url = f"https://api.digikala.com/v1/search/?q={quote(query)}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json'
            }
            
            async with session.get(search_url, headers=headers, timeout=15) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get('status') == 200 and data.get('data', {}).get('products'):
                        products = data['data']['products'][:5]  # حداکثر 5 محصول
                        
                        result_text = f"🛒 **نتایج جستجو برای: {query}**\n\n"
                        
                        for i, product in enumerate(products, 1):
                            product_id = product['id']
                            title = product['title_fa']
                            if not title:
                                title = product['title_en']
                            
                            # دریافت قیمت دقیق
                            price_data = product.get('price', {})
                            selling_price = price_data.get('selling_price', 0)
                            rrp_price = price_data.get('rrp_price', 0)
                            is_available = price_data.get('is_available', False)
                            
                            # تبدیل ریال به تومان (تقسیم بر 10)
                            selling_price_toman = selling_price // 10
                            rrp_price_toman = rrp_price // 10
                            
                            # اگر قیمت فروشنده صفر بود، از قیمت اصلی استفاده کن
                            if selling_price_toman == 0 and rrp_price_toman > 0:
                                selling_price_toman = rrp_price_toman
                            
                            # قیمت به تومان
                            if selling_price_toman > 0:
                                price_text = f"{selling_price_toman:,} تومان"
                                if rrp_price_toman > selling_price_toman:
                                    discount = int((1 - selling_price/rrp_price) * 100)
                                    price_text += f"\n      💰 قیمت اصلی: {rrp_price_toman:,} تومان"
                                    price_text += f"\n      🔻 تخفیف: {discount}%"
                                if is_available:
                                    price_text += f"\n      ✅ موجود"
                                else:
                                    price_text += f"\n      ⚠️ ناموجود"
                            else:
                                # تلاش برای دریافت قیمت از روش دیگر
                                default_variant = product.get('default_variant', {})
                                if default_variant:
                                    price = default_variant.get('price', {})
                                    selling_price = price.get('selling_price', 0)
                                    selling_price_toman = selling_price // 10
                                    if selling_price_toman > 0:
                                        price_text = f"{selling_price_toman:,} تومان"
                                    else:
                                        price_text = "❌ ناموجود"
                                else:
                                    price_text = "❌ ناموجود"
                            
                            rating = product.get('rating', {}).get('rate', 0)
                            rate_count = product.get('rating', {}).get('count', 0)
                            
                            # لینک محصول
                            url = f"https://www.digikala.com/product/dkp-{product_id}"
                            
                            result_text += f"{i}. **{title}**\n"
                            result_text += f"   🆔 شناسه: `{product_id}`\n"
                            result_text += f"   💵 قیمت: {price_text}\n"
                            if rating > 0:
                                result_text += f"   ⭐ امتیاز: {rating}/5 (از {rate_count} نفر)\n"
                            result_text += f"   🔗 لینک: {url}\n\n"
                        
                        return result_text
                    else:
                        return f"❌ محصولی با نام '{query}' یافت نشد"
                else:
                    return f"❌ خطا در ارتباط با دیجی‌کالا (کد {response.status})"
    except Exception as e:
        print(f"خطا در جستجوی دیجی‌کالا: {e}")
        return f"❌ خطا در جستجو: {str(e)}"

async def get_user_id_info(event, target=None):
    """دریافت آیدی عددی کاربر/گروه/کانال"""
    try:
        if target:
            # اگر یوزرنیم وارد شده
            if target.startswith('@'):
                target = target[1:]
            
            try:
                entity = await client.get_entity(target)
                user_id = entity.id
                user_type = "کاربر"
                
                if hasattr(entity, 'title'):
                    user_type = "کانال/گروه"
                    name = entity.title
                else:
                    name = f"{entity.first_name or ''} {entity.last_name or ''}".strip()
                
                username = getattr(entity, 'username', None)
                
                result = f"""
👤 **اطلاعات {user_type}**

🆔 آیدی عددی: `{user_id}`
📝 نام: {name}
"""
                if username:
                    result += f"📱 یوزرنیم: @{username}"
                
                return result
            except Exception as e:
                return f"❌ موجودی با شناسه '{target}' یافت نشد"
        
        else:
            # آیدی خودم
            me = await client.get_me()
            return f"""
👤 **اطلاعات شما**

🆔 آیدی عددی: `{me.id}`
📝 نام: {me.first_name or ''} {me.last_name or ''}
📱 یوزرنیم: @{me.username if me.username else 'ندارد'}
"""
    except Exception as e:
        return f"❌ خطا: {str(e)}"

def is_command(text):
    """بررسی اینکه متن یک دستور است یا نه"""
    commands = [
        "تایم روشن", "تایم خاموش",
        "سکوت پیوی روشن", "سکوت پیوی خاموش", "سکوت آیدی", "حذف سکوت آیدی",
        "لاگ پیام روشن", "لاگ پیام خاموش",
        "تاریخ و ساعت", "آیدی من", "آیدی ریپلای", "آیدی ",
        "سرچ دیجی ",
        "لیست دستورات",
        "کارت", "تنظیم کارت", "حذف کارت",
        "اسم عوض بشه به",
        "تنظیم بدخا", "حذف بدخا", "تنظیم مشتی", "حذف مشتی"
    ]
    
    # بررسی دستورات فونت
    font_commands = ["فونت کلاسیک", "فونت مدرن", "فونت مونو", "فونت بولد", "فونت فانسی",
                     "فونت دوبل", "فونت کد", "فونت رومن", "فونت دایره", "فونت مربع",
                     "فونت ریاضی", "فونت زیرنویس", "فونت بالانویس", "فونت پهن", "فونت ارزی",
                     "فونت حاشیه‌دار", "فونت سایه‌دار", "فونت ماشین تحریر", "فونت تزیینی",
                     "فونت دایره سیاه", "فونت پرانتزدار", "فونت دایره دوتایی", "فونت دایره پر",
                     "فونت نقطه‌چین", "فونت ریز", "فونت درشت", "فونت کسری"]
    
    # بررسی دستورات استایل
    style_commands = ["تنظیم استایل بولد", "تنظیم استایل ایتالیک", "تنظیم استایل آندرلاین",
                      "تنظیم استایل مونو", "تنظیم استایل اسپویلر", "تنظیم استایل عادی"]
    
    # بررسی دستورات ارسال با استایل
    if text.startswith("ارسال "):
        return True
    
    # بررسی دستورات فونت
    for cmd in font_commands:
        if text == cmd:
            return True
    
    # بررسی دستورات استایل
    for cmd in style_commands:
        if text == cmd:
            return True
    
    # بررسی دستورات عادی
    for cmd in commands:
        if text == cmd or text.startswith(cmd + " "):
            return True
    
    return False

async def handle_commands(event):
    global time_enabled, current_font_style, silent_pv_enabled
    global message_log_enabled, delete_log_enabled, edit_log_enabled
    global card_info, auto_text_style
    global silent_pv_users
    
    try:
        text = event.raw_text.strip()
        
        # دستورات فونت با نمونه (فقط اعداد)
        font_commands = {
            "فونت کلاسیک": "classic",
            "فونت مدرن": "modern",
            "فونت مونو": "mono",
            "فونت بولد": "bold",
            "فونت فانسی": "fancy",
            "فونت دوبل": "double",
            "فونت کد": "code",
            "فونت رومن": "roman",
            "فونت دایره": "circle",
            "فونت مربع": "square",
            "فونت ریاضی": "math",
            "فونت زیرنویس": "subscript",
            "فونت بالانویس": "superscript",
            "فونت پهن": "fullwidth",
            "فونت ارزی": "currency",
            "فونت حاشیه‌دار": "outline",
            "فونت سایه‌دار": "shadow",
            "فونت ماشین تحریر": "typewriter",
            "فونت تزیینی": "decorative",
            "فونت دایره سیاه": "black_circle",
            "فونت پرانتزدار": "parenthesis",
            "فونت دایره دوتایی": "double_circle",
            "فونت دایره پر": "filled_circle",
            "فونت نقطه‌چین": "dotted",
            "فونت ریز": "small_numbers",
            "فونت درشت": "large_numbers",
            "فونت کسری": "fraction"
        }
        
        for cmd, style in font_commands.items():
            if text == cmd:
                current_font_style = style
                sample = fonts[style]["sample"]
                await event.message.edit(f"✅ فونت به {cmd.replace('فونت ', '')} تغییر کرد\n📝 نمونه: {sample}")
                return
        
        # دستورات استایل خودکار
        style_commands = {
            "تنظیم استایل بولد": "bold",
            "تنظیم استایل ایتالیک": "italic",
            "تنظیم استایل آندرلاین": "underline",
            "تنظیم استایل مونو": "mono",
            "تنظیم استایل اسپویلر": "spoiler",
            "تنظیم استایل عادی": None
        }
        
        for cmd, style in style_commands.items():
            if text == cmd:
                if style:
                    auto_text_style = style
                    await event.message.edit(f"✅ استایل خودکار سراسری به {cmd.replace('تنظیم استایل ', '')} تغییر کرد")
                else:
                    auto_text_style = None
                    await event.message.edit("✅ استایل خودکار غیرفعال شد")
                return
        
        # ارسال با استایل
        if text.startswith("ارسال بولد "):
            await send_with_style(event, text[11:], "bold")
            await event.message.delete()
            return
        elif text.startswith("ارسال ایتالیک "):
            await send_with_style(event, text[14:], "italic")
            await event.message.delete()
            return
        elif text.startswith("ارسال آندرلاین "):
            await send_with_style(event, text[15:], "underline")
            await event.message.delete()
            return
        elif text.startswith("ارسال مونو "):
            await send_with_style(event, text[11:], "mono")
            await event.message.delete()
            return
        elif text.startswith("ارسال اسپویلر "):
            await send_with_style(event, text[14:], "spoiler")
            await event.message.delete()
            return
        
        # مدیریت کارت بانکی
        if text.startswith("تنظیم کارت "):
            parts = text[11:].strip().split(maxsplit=2)
            if len(parts) >= 2:
                card_number = parts[0].replace(' ', '').replace('-', '')
                card_name = parts[1]
                card_gateway = parts[2] if len(parts) > 2 else ""
                
                if len(card_number) == 16 and card_number.isdigit():
                    card_info = {
                        "number": card_number,
                        "name": card_name,
                        "gateway": card_gateway
                    }
                    await event.message.edit("✅ اطلاعات کارت با موفقیت ذخیره شد")
                else:
                    await event.message.edit("❌ شماره کارت باید 16 رقم باشد")
            else:
                await event.message.edit("❌ فرمت صحیح: تنظیم کارت شماره‌کارت نام [درگاه]")
            return
        
        elif text == "حذف کارت":
            card_info = {"number": "", "name": "", "gateway": ""}
            await event.message.edit("✅ اطلاعات کارت حذف شد")
            return
        
        elif text == "کارت":
            if card_info and card_info.get("number"):
                card_number = card_info["number"]
                formatted_card = ' '.join([card_number[i:i+4] for i in range(0, 16, 4)])
                
                result = f"""
💳 **اطلاعات کارت بانکی**

📌 شماره کارت: `{formatted_card}`
👤 به نام: {card_info['name']}
"""
                if card_info.get('gateway'):
                    result += f"🔗 درگاه پرداخت: {card_info['gateway']}"
                await event.message.edit(result)
            else:
                await event.message.edit("❌ اطلاعات کارتی ثبت نشده است")
            return
        
        # دستورات زمان
        elif text == "تایم روشن":
            time_enabled = True
            await event.message.edit("✅ تایم فعال شد (فقط در کنار اسم)")
            return
        elif text == "تایم خاموش":
            time_enabled = False
            await event.message.edit("❌ تایم غیرفعال شد")
            me = await client.get_me()
            current_name = me.first_name or ""
            
            # الگوهای پاک کردن همه انواع فونت اعداد
            patterns = [
                r'\s*[𝟬𝟭𝟮𝟯𝟰𝟱𝟲𝟳𝟴𝟵]{1,2}:[𝟬𝟭𝟮𝟯𝟰𝟱𝟲𝟳𝟴𝟵]{2}\s*$',
                r'\s*[𝟶𝟷𝟸𝟹𝟺𝟻𝟼𝟽𝟾𝟿]{1,2}:[𝟶𝟷𝟸𝟹𝟺𝟻𝟼𝟽𝟾𝟿]{2}\s*$',
                r'\s*[𝟘𝟙𝟚𝟛𝟜𝟝𝟞𝟟𝟠𝟡]{1,2}:[𝟘𝟙𝟚𝟛𝟜𝟝𝟞𝟟𝟠𝟡]{2}\s*$',
                r'\s*\d{1,2}:\d{2}\s*$',
                r'\s*[ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ]{1,2}:[ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ]{2}\s*$',
                r'\s*[⓪①②③④⑤⑥⑦⑧⑨]{1,2}:[⓪①②③④⑤⑥⑦⑧⑨]{2}\s*$',
                r'\s*[🄋➀➁➂➃➄➅➆➇➈]{1,2}:[🄋➀➁➂➃➄➅➆➇➈]{2}\s*$',
                r'\s*[𝟎𝟏𝟐𝟑𝟒𝟓𝟔𝟕𝟖𝟗]{1,2}:[𝟎𝟏𝟐𝟑𝟒𝟓𝟔𝟕𝟖𝟗]{2}\s*$',
                r'\s*[₀₁₂₃₄₅₆₇₈₉]{1,2}:[₀₁₂₃₄₅₆₇₈₉]{2}\s*$',
                r'\s*[⁰¹²³⁴⁵⁶⁷⁸⁹]{1,2}:[⁰¹²³⁴⁵⁶⁷⁸⁹]{2}\s*$',
                r'\s*[０１２３４５６７８９]{1,2}:[０１２３４５６７８９]{2}\s*$',
                r'\s*[❶❷❸❹❺❻❼❽❾❿]{1,2}:[❶❷❸❹❺❻❼❽❾❿]{2}\s*$',
                r'\s*[➊➋➌➍➎➏➐➑➒➓]{1,2}:[➊➋➌➍➎➏➐➑➒➓]{2}\s*$',
                r'\s*[⑴⑵⑶⑷⑸⑹⑺⑻⑼⑽]{1,2}:[⑴⑵⑶⑷⑸⑹⑺⑻⑼⑽]{2}\s*$',
                r'\s*[½⅓⅔¼¾⅕⅖⅗⅘⅙]{1,2}:[½⅓⅔¼¾⅕⅖⅗⅘⅙]{2}\s*$'
            ]
            
            for pattern in patterns:
                current_name = re.sub(pattern, '', current_name)
            await client(UpdateProfileRequest(first_name=current_name.strip()))
            return
        
        # دستورات سکوت پیوی
        elif text == "سکوت پیوی روشن":
            silent_pv_enabled = True
            await event.message.edit("✅ سکوت پیوی برای همه فعال شد")
            return
        elif text == "سکوت پیوی خاموش":
            silent_pv_enabled = False
            await event.message.edit("❌ سکوت پیوی برای همه غیرفعال شد")
            return
        
        # اضافه کردن آیدی به لیست سکوت
        elif text.startswith("سکوت آیدی "):
            try:
                user_id = int(text[10:].strip())
                silent_pv_users.add(user_id)
                await event.message.edit(f"✅ آیدی {user_id} به لیست سکوت اضافه شد\nاز این به بعد پیام‌های این کاربر در پیوی حذف میشود")
            except ValueError:
                await event.message.edit("❌ لطفاً آیدی عددی معتبر وارد کنید")
            return
        
        # حذف آیدی از لیست سکوت
        elif text.startswith("حذف سکوت آیدی "):
            try:
                user_id = int(text[14:].strip())
                if user_id in silent_pv_users:
                    silent_pv_users.remove(user_id)
                    await event.message.edit(f"✅ آیدی {user_id} از لیست سکوت حذف شد")
                else:
                    await event.message.edit(f"❌ آیدی {user_id} در لیست سکوت نیست")
            except ValueError:
                await event.message.edit("❌ لطفاً آیدی عددی معتبر وارد کنید")
            return
        
        # دستورات لاگ
        elif text == "لاگ پیام روشن":
            message_log_enabled = True
            delete_log_enabled = True
            edit_log_enabled = True
            await event.message.edit("✅ لاگ پیام فعال شد (فقط پیوی - ارسال به سیومسیج)")
            return
        elif text == "لاگ پیام خاموش":
            message_log_enabled = False
            delete_log_enabled = False
            edit_log_enabled = False
            await event.message.edit("❌ لاگ پیام غیرفعال شد")
            return
        
        # تاریخ و ساعت
        elif text == "تاریخ و ساعت":
            info = get_date_time_info()
            response = f"""
📅 **تاریخ و ساعت**

⏰ ساعت: `{info['time_now']}`
📆 تاریخ شمسی: `{info['jalali_date']}` - {info['day_name_fa']}
🌍 تاریخ میلادی: `{info['gregorian_date']}` - {info['day_name_en']}
📌 ماه شمسی: {info['jalali_month_name_fa']}
📌 ماه میلادی: {info['month_name_en']}

⏳ روزهای باقیمانده:
   • تا پایان ماه: {info['remaining_days_in_month']} روز
   • تا پایان سال: {info['remaining_days_in_year']} روز

🌐 UTC: `{info['utc_date']}`
"""
            await event.message.edit(response)
            return
        
        # آیدی من
        elif text == "آیدی من":
            result = await get_user_id_info(event)
            await event.message.edit(result)
            return
        
        # آیدی ریپلای
        elif text == "آیدی ریپلای" and event.is_reply:
            replied = await event.get_reply_message()
            sender = await replied.get_sender()
            user_id = sender.id
            name = getattr(sender, 'first_name', '') or getattr(sender, 'title', '')
            username = getattr(sender, 'username', None)
            
            result = f"""
👤 **اطلاعات کاربر ریپلای شده**

🆔 آیدی عددی: `{user_id}`
📝 نام: {name}
"""
            if username:
                result += f"📱 یوزرنیم: @{username}"
            
            await event.message.edit(result)
            return
        
        # آیدی با یوزرنیم
        elif text.startswith("آیدی "):
            target = text[5:].strip()
            result = await get_user_id_info(event, target)
            await event.message.edit(result)
            return
        
        # جستجو در دیجی‌کالا
        elif text.startswith("سرچ دیجی "):
            query = text[9:].strip()
            await event.message.edit(f"🛒 در حال جستجوی '{query}' در دیجی‌کالا...")
            result = await digikala_search(query)
            await event.message.edit(result)
            return
        
        # لیست دستورات
        elif text == "لیست دستورات":
            await send_command_list(event)
            return
            
    except Exception as e:
        print(f"خطا در handle_commands: {e}")
        traceback.print_exc()

@client.on(events.NewMessage)
async def new_message_handler(event):
    try:
        # ذخیره مدیا با نقطه (بدون حذف پیام)
        await save_media_with_dot(event)
        
        # ذخیره متن برای لاگ حذف
        if event.is_private and event.sender_id != allowed_user_id:
            sender = await event.get_sender()
            sender_name = getattr(sender, 'first_name', '') or getattr(sender, 'title', 'ناشناس')
            sender_username = getattr(sender, 'username', '')
            message_delete_log[event.id] = {
                'sender_id': event.sender_id,
                'sender_name': sender_name,
                'sender_username': sender_username,
                'text': event.raw_text if event.raw_text else "مدیا",
                'time': datetime.now()
            }
        
        if event.sender_id != allowed_user_id:
            if event.sender_id in enemies:
                await send_random_reply(event, enemy_responses)  # رندوم
            elif event.sender_id in friends:
                await send_random_reply(event, friend_responses)  # رندوم
            
            await handle_silent_pv(event)
            return
        
        # بررسی اینکه آیا پیام یک دستور است یا خیر
        text = event.raw_text.strip()
        
        # اگر استایل خودکار فعال باشه و پیام دستور نباشه، استایل رو اعمال کن
        if auto_text_style and text and not is_command(text):
            style = auto_text_style
            entities = []
            if style == "bold":
                entities = [MessageEntityBold(0, len(text))]
            elif style == "italic":
                entities = [MessageEntityItalic(0, len(text))]
            elif style == "underline":
                entities = [MessageEntityUnderline(0, len(text))]
            elif style == "mono":
                entities = [MessageEntityCode(0, len(text))]
            elif style == "spoiler":
                entities = [MessageEntitySpoiler(0, len(text))]
            
            await event.message.edit(text, formatting_entities=entities)
            return
        
        # اجرای دستورات
        await handle_commands(event)
        await manage_lists_via_reply(event)
        await handle_name_change(event)
        
    except Exception as e:
        print(f"خطا در new_message_handler: {e}")

@client.on(events.MessageEdited)
async def message_edit_handler(event):
    try:
        if edit_log_enabled:
            await log_message_action(event, "edit")
    except Exception as e:
        print(f"خطا در message_edit_handler: {e}")

@client.on(events.MessageDeleted)
async def message_delete_handler(event):
    try:
        if delete_log_enabled:
            await log_message_action(event, "delete")
        
        # پاک کردن از لاگ
        if hasattr(event, 'messages') and event.messages:
            for msg_id in event.messages:
                if msg_id in message_delete_log:
                    del message_delete_log[msg_id]
    except Exception as e:
        print(f"خطا در message_delete_handler: {e}")

async def manage_lists_via_reply(event):
    try:
        if event.is_reply and event.sender_id == allowed_user_id:
            replied = await event.get_reply_message()
            if replied:
                sender_id = replied.sender_id
                
                if 'تنظیم بدخا' in event.raw_text:
                    enemies[sender_id] = 'دشمن'
                    await event.message.edit(f"✅ کاربر {sender_id} به لیست بدخا اضافه شد (پاسخ رندوم)")
                elif 'تنظیم مشتی' in event.raw_text:
                    friends[sender_id] = 'دوست'
                    await event.message.edit(f"✅ کاربر {sender_id} به لیست مشتی اضافه شد (پاسخ رندوم)")
                elif 'حذف بدخا' in event.raw_text:
                    if sender_id in enemies:
                        del enemies[sender_id]
                        await event.message.edit(f"✅ کاربر {sender_id} از لیست بدخا حذف شد")
                    else:
                        await event.message.edit("❌ کاربر در لیست بدخا نیست")
                elif 'حذف مشتی' in event.raw_text:
                    if sender_id in friends:
                        del friends[sender_id]
                        await event.message.edit(f"✅ کاربر {sender_id} از لیست مشتی حذف شد")
                    else:
                        await event.message.edit("❌ کاربر در لیست مشتی نیست")
    except Exception as e:
        print(f"خطا در manage_lists_via_reply: {e}")

async def main():
    try:
        await client.start()
        me = await client.get_me()
        print("✅ ربات با موفقیت راه‌اندازی شد!")
        print(f"👤 اکانت: {me.first_name}")
        print("📋 برای مشاهده دستورات، 'لیست دستورات' را بفرستید")
        
        asyncio.create_task(update_profile_name())
        await client.run_until_disconnected()
    except Exception as e:
        print(f"خطای اصلی: {e}")
        traceback.print_exc()
        print("🔄 ربات در حال راه‌اندازی مجدد...")
        await asyncio.sleep(5)
        await main()

if __name__ == "__main__":
    while True:
        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            print("❌ ربات متوقف شد")
            break
        except Exception as e:
            print(f"خطای بحرانی: {e}")
            traceback.print_exc()
            print("🔄 ربات در حال راه‌اندازی مجدد بعد از 10 ثانیه...")
            time.sleep(10)
