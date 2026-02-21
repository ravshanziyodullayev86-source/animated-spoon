from telebot import types

@bot.message_handler(commands=['help'])
def help_command(message):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    item1 = types.KeyboardButton("Biz haqimizda")
    item2 = types.KeyboardButton("Bog'lanish")
    markup.add(item1, item2)
    bot.send_message(message.chat.id, "Menyu tanlang:", reply_markup=markup)
  
