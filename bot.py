import telebot
from telebot import types
import sqlite3
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import io
import os

# ================== SOZLAMALAR ==================
TOKEN = os.getenv("8563362297:AAE7khkQUB2DnYAn-mA6vjB4WDZg37sEeAY")  # Railway-da environment variable orqali qo‘yiladi
ADMIN_ID = 7927679875  # o'zingning ID
SELLERS = [ADMIN_ID, 1089564557]  # akang ID

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# ================== DATABASE ==================
conn = sqlite3.connect("shop.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    price_uzs REAL,
    price_usd REAL,
    quantity INTEGER
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS sales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    seller_id INTEGER,
    product_name TEXT,
    qty INTEGER,
    total_uzs REAL,
    total_usd REAL,
    date TEXT
)
""")
conn.commit()

# ================== HELPER: RASM CHEK ==================
def create_receipt_image(sales_list, title="Bugungi savdolar"):
    height = 100 + len(sales_list) * 40
    img = Image.new('RGB', (600, max(height, 400)), color='white')
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()

    draw.text((10, 10), f"🧾 {title}", font=font, fill=(0,0,0))
    draw.text((10, 30), "------------------------------", font=font, fill=(0,0,0))

    y = 50
    for sale in sales_list:
        seller_name, product_name, qty, total_uzs, total_usd, date = sale
        line = f"👤 {seller_name} | {product_name} x{qty} | {total_uzs} UZS / ${total_usd} | {date}"
        draw.text((10, y), line, font=font, fill=(0,0,0))
        y += 30

    draw.text((10, y+10), "✅ Rahmat xaridingiz uchun!", font=font, fill=(0,0,0))

    bio = io.BytesIO()
    img.save(bio, format='PNG')
    bio.seek(0)
    return bio

# ================== START ==================
@bot.message_handler(commands=['start'])
def start(msg):
    if msg.from_user.id not in SELLERS:
        bot.send_message(msg.chat.id, "⛔ Sizga ruxsat yo‘q")
        return

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🔍 Qidirish", "🧾 Bugungi savdo")
    if msg.from_user.id == ADMIN_ID:
        kb.add("➕ Mahsulot qo‘shish")

    bot.send_message(msg.chat.id, "✅ Bot ishga tayyor", reply_markup=kb)

# ================== MAHSULOT QO‘SHISH ==================
@bot.message_handler(func=lambda m: m.text == "➕ Mahsulot qo‘shish")
def add_product_start(msg):
    if msg.from_user.id != ADMIN_ID:
        return
    bot.send_message(msg.chat.id, "Mahsulot nomini yozing:")
    bot.register_next_step_handler(msg, get_product_name)

def get_product_name(msg):
    name = msg.text
    bot.send_message(msg.chat.id, "Narx (UZS) ni yozing:")
    bot.register_next_step_handler(msg, get_price_uzs, name)

def get_price_uzs(msg, name):
    try:
        price_uzs = float(msg.text)
    except:
        bot.send_message(msg.chat.id, "❌ Raqam kiriting")
        return
    bot.send_message(msg.chat.id, "Narx (USD) ni yozing:")
    bot.register_next_step_handler(msg, get_price_usd, name, price_uzs)

def get_price_usd(msg, name, price_uzs):
    try:
        price_usd = float(msg.text)
    except:
        bot.send_message(msg.chat.id, "❌ Raqam kiriting")
        return
    bot.send_message(msg.chat.id, "Ombordagi sonini yozing:")
    bot.register_next_step_handler(msg, save_product, name, price_uzs, price_usd)

def save_product(msg, name, price_uzs, price_usd):
    try:
        qty = int(msg.text)
    except:
        bot.send_message(msg.chat.id, "❌ Butun son kiriting")
        return

    cursor.execute(
        "INSERT INTO products (name, price_uzs, price_usd, quantity) VALUES (?, ?, ?, ?)",
        (name, price_uzs, price_usd, qty)
    )
    conn.commit()
    bot.send_message(msg.chat.id, "✅ Mahsulot qo‘shildi")

# ================== QIDIRISH ==================
@bot.message_handler(func=lambda m: m.text == "🔍 Qidirish")
def search_start(msg):
    bot.send_message(msg.chat.id, "Mahsulot nomini yozing:")
    bot.register_next_step_handler(msg, search_product)

def search_product(msg):
    name = msg.text.lower()
    cursor.execute("SELECT * FROM products WHERE name LIKE ?", (f"%{name}%",))
    data = cursor.fetchone()
    if not data:
        bot.send_message(msg.chat.id, "❌ Topilmadi")
        return

    product_id, pname, puzs, pusd, qty = data
    text = f"📦 <b>{pname}</b>\n💰 {puzs} so‘m | ${pusd}\n📦 Ombor: {qty}"

    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🛒 Sotish", callback_data=f"sell_{product_id}"))
    bot.send_message(msg.chat.id, text, reply_markup=kb)

# ================== SOTISH ==================
@bot.callback_query_handler(func=lambda c: c.data.startswith("sell_"))
def sell_start(call):
    product_id = int(call.data.split("_")[1])
    msg = bot.send_message(call.message.chat.id, "Nechta sotildi?")
    bot.register_next_step_handler(msg, process_sale, product_id)

def process_sale(msg, product_id):
    try:
        qty_sell = int(msg.text)
    except:
        bot.send_message(msg.chat.id, "❌ Butun son kiriting")
        return

    cursor.execute("SELECT name, price_uzs, price_usd, quantity FROM products WHERE id=?",
                   (product_id,))
    data = cursor.fetchone()
    if not data:
        bot.send_message(msg.chat.id, "❌ Mahsulot topilmadi")
        return

    name, puzs, pusd, qty = data
    if qty_sell > qty:
        bot.send_message(msg.chat.id, "❌ Omborda yetarli emas")
        return

    new_qty = qty - qty_sell
    total_uzs = puzs * qty_sell
    total_usd = pusd * qty_sell
    now = datetime.now().strftime("%d.%m.%Y %H:%M")

    cursor.execute("UPDATE products SET quantity=? WHERE id=?", (new_qty, product_id))
    cursor.execute(
        "INSERT INTO sales (seller_id, product_name, qty, total_uzs, total_usd, date) VALUES (?, ?, ?, ?, ?, ?)",
        (msg.from_user.id, name, qty_sell, total_uzs, total_usd, now)
    )
    conn.commit()

    # Rasmli chek
    receipt_img = create_receipt_image([(msg.from_user.first_name, name, qty_sell, total_uzs, total_usd, now)],
                                       title="Sotuv Cheki")
    bot.send_photo(msg.chat.id, receipt_img)

# ================== BUGUNGI SAVDO ==================
@bot.message_handler(func=lambda m: m.text == "🧾 Bugungi savdo")
def today_sales(msg):
    today_date = datetime.now().strftime("%d.%m.%Y")
    cursor.execute("SELECT seller_id, product_name, qty, total_uzs, total_usd, date FROM sales")
    data = cursor.fetchall()

    sales_list = []
    for sale in data:
        seller_id, pname, qty, total_uzs, total_usd, date = sale
        if date.startswith(today_date):
            try:
                user = bot.get_chat(seller_id)
                seller_name = user.first_name
            except:
                seller_name = f"Sotuvchi {seller_id}"
            sales_list.append((seller_name, pname, qty, total_uzs, total_usd, date))

    if not sales_list:
        bot.send_message(msg.chat.id, "❌ Bugun savdo yo‘q")
        return

    receipt_img = create_receipt_image(sales_list, title=f"Bugungi savdolar ({today_date})")
    bot.send_photo(msg.chat.id, receipt_img)

# ================== ISHGA TUSHURISH ==================
print("Bot ishga tushdi...")
bot.infinity_polling(skip_pending=True)
