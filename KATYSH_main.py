from lib2to3.fixes.fix_input import context

import cv2
import telebot
from pyzbar.pyzbar import decode
import sqlite3
from telegram.ext import MessageHandler, ConversationHandler, CallbackContext, filters
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove

# Ініціалізація бота
bot = telebot.TeleBot('7059182423:AAGkjYejqkDEY3ZsIjOsAXDzYhCYbX3Zwoc')

# Початок роботи з базою даних
conn = sqlite3.connect('products.db')
cursor = conn.cursor()

# Створення таблиці товарів у базі даних
cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        barcode TEXT,
        description TEXT,
        quantity INTEGER,
        photo BLOB
    )
''')
conn.commit()


# Функція для додавання товару до бази даних
def add_product(name, barcode, description, quantity, photo):
    cursor.execute('''
        INSERT INTO products (name, barcode, description, quantity, photo) VALUES (?, ?, ?, ?, ?)
    ''', (name, barcode, description, quantity, photo))
    conn.commit()


# Функція для сканування штрих-кодів
def barcode_scanner(message):
    # Відправка повідомлення з запитом на відправку фото
    bot.send_message(message.chat.id, "Будь ласка, надішліть фото з штрих-кодом:")


# Функція для обробки отриманих фото з штрих-кодами
@bot.message_handler(content_types=['photo'])
def photo_handler(message):
    photo = message.photo[-1]
    file_id = photo.file_id
    file_info = bot.get_file(file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    with open('photo.jpg', 'wb') as new_file:
        new_file.write(downloaded_file)

    image = cv2.imread('photo.jpg')

    barcodes = decode(image)

    if barcodes:
        for barcode in barcodes:
            barcode_data = barcode.data.decode("utf-8")
            bot.send_message(message.chat.id, f"Штрих-код: {barcode_data}")
    else:
        bot.send_message(message.chat.id, "На зображенні не знайдено штрих-кодів")


# Функція для додавання товару
def add_product_handler(message):
    bot.send_message(message.chat.id, "Будь ласка, введіть назву товару:")
    return "WAITING_FOR_NAME"


def handle_name(message):
    context.user_data['name'] = message.text
    bot.send_message(message.chat.id, "Введіть штрих-код товару:")
    return "WAITING_FOR_BARCODE"


def handle_barcode(message):
    context.user_data['barcode'] = message.text
    bot.send_message(message.chat.id, "Введіть опис товару:")
    return "WAITING_FOR_DESCRIPTION"


def handle_description(message):
    context.user_data['description'] = message.text
    bot.send_message(message.chat.id, "Введіть кількість товару:")
    return "WAITING_FOR_QUANTITY"


def handle_quantity(message):
    name = context.user_data['name']
    barcode = context.user_data['barcode']
    description = context.user_data['description']
    quantity = int(message.text)

    add_product(name, barcode, description, quantity, None)
    bot.send_message(message.chat.id, "Товар додано до бази даних.")

    return ConversationHandler.END


def cancel(message):
    bot.send_message(message.chat.id, "Додавання товару скасовано.", reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END


# Реєстрація обробників
bot.add_message_handler(photo_handler)
bot.add_message_handler(barcode_scanner)

if __name__ == '__main__':
    bot.polling(none_stop=True)
