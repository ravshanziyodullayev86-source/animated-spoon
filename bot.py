import telebot
from telebot import types
import sqlite3
import os
import time
from datetime import datetime, timedelta
from fpdf import FPDF

TOKEN = os.getenv('8282299399:AAEBOMxm2VvF2GXBAGCPAWS43bCsaSLvAjc')
bot = telebot.TeleBot(TOKEN)

def db_worker(query, params=()):
    with sqlite3.connect('sotuv.db') as conn:
        cur = conn.cursor()
        cur.execute(query, params)
        conn.commit()
        return cur.fetchall()

db_worker('CREATE TABLE IF NOT EXISTS savat (nomi TEXT, narxi REAL)')
db_worker('CREATE TABLE IF NOT EXISTS savdo (jami REAL, sana TEXT)')

@bot.message_handler(commands=['start'])
def start(m):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("➕ Mahsulot qo'shish", "📄 PDF Yuklab olish")
    markup.add("📊 Kunlik Savdo", "🗑 Savatni tozalash")
    bot.send_message(m.chat.id, "Sotuv boti!", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "➕ Mahsulot qo'shish")
def add_1(m):
    msg = bot.send_message(m.chat.id, "Mahsulot nomini yozing:")
    bot.register_next_step_handler(msg, add_2)

def add_2(m):
    nomi = m.text
    msg = bot.send_message(m.chat.id, f"'{nomi}' narxini kiriting:")
    bot.register_next_step_handler(msg, add_3, nomi)

def add_3(m, nomi):
    try:
        narxi = float(m.text)
        db_worker("INSERT INTO savat (nomi, narxi) VALUES (?, ?)", (nomi, narxi))
        bot.send_message(m.chat.id, f"✅ {nomi} savatga qo'shildi!")
    except:
        bot.send_message(m.chat.id, "❌ Faqat raqam kiriting!")

@bot.message_handler(func=lambda m: m.text == "📄 PDF Yuklab olish")
def get_pdf(m):
    items = db_worker("SELECT nomi, narxi FROM savat")
    if not items: return bot.send_message(m.chat.id, "Savat bo'sh!")
    
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="SOTUV CHEKI", ln=1, align='C')
    total = sum(p for n, p in items)
    for n, p in items:
        pdf.cell(200, 10, txt=f"{n}: {p} so'm", ln=1)
    pdf.cell(200, 10, txt=f"JAMI: {total} so'm", ln=1)
    
    fname = f"chek_{m.chat.id}.pdf"
    pdf.output(fname)
    with open(fname, 'rb') as f: bot.send_document(m.chat.id, f)
    
    sana = (datetime.now() + timedelta(hours=5)).strftime("%Y-%m-%d")
    db_worker("INSERT INTO savdo (jami, sana) VALUES (?, ?)", (total, sana))
    db_worker("DELETE FROM savat")
    os.remove(fname)

@bot.message_handler(func=lambda m: m.text == "📊 Kunlik Savdo")
def report(m):
    sana = (datetime.now() + timedelta(hours=5)).strftime("%Y-%m-%d")
    res = db_worker("SELECT SUM(jami) FROM savdo WHERE sana=?", (sana,))
    jami = res[0][0] if res[0][0] else 0
    bot.send_message(m.chat.id, f"Bugungi savdo: {jami} so'm")

@bot.message_handler(func=lambda m: m.text == "🗑 Savatni tozalash")
def clear(m):
    db_worker("DELETE FROM savat")
    bot.send_message(m.chat.id, "Savat tozalandi!")

while True:
    try:
        print("Bot ishga tushdi...")
        bot.polling(none_stop=True, timeout=90)
    except Exception as e:
        print(f"Xatolik: {e}")
        time.sleep(10)
