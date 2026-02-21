import os
import telebot
from telebot import types

# Railway Variables bo'limidagi BOT_TOKEN-ni chaqiramiz
TOKEN = os.getenv('BOT_TOKEN')

# Botingizni yaratamiz
bot = telebot.TeleBot(TOKEN)

# /start buyrug'i uchun handler
@bot.message_handler(commands=['start'])
def welcome(message):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    item1 = types.KeyboardButton("Biz haqimizda")
    item2 = types.KeyboardButton("Bog'lanish")
    markup.add(item1, item2)
    
    bot.send_message(
        message.chat.id, 
        f"Salom {message.from_user.first_name}! Men Railway serverida ishlayapman. Menyu tanlang:", 
        reply_markup=markup
    )

# Tugmalar bosilganda yoki xabar yozilganda javob berish
@bot.message_handler(func=lambda message: True)
def answer(message):
    if message.text == "Biz haqimizda":
        bot.send_message(message.chat.id, "Bu bot Railway platformasiga muvaffaqiyatli yuklandi! ✅")
    elif message.text == "Bog'lanish":
        bot.send_message(message.chat.id, "Admin: @username")
    else:
        bot.reply_to(message, f"Siz yozdingiz: {message.text}")

# Botni doimiy yoqiq holatda ushlab turuvchi qator
if __name__ == "__main__":
    print("Bot ishga tushdi...")
    bot.polling(none_stop=True)
          
