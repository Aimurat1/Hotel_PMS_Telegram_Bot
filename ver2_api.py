from telegram import ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup, Update, ForceReply, KeyboardButton, ReplyKeyboardMarkup,InputMediaPhoto, ParseMode
from telegram.ext import Defaults, InvalidCallbackData, PicklePersistence, CallbackQueryHandler, Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler
from typing import Dict
import json
import requests
import re
import firebase_with_api as firebase
import datetime
import sendemail, asyncio, time
import calendar_inline.telegramcalendar as telegramcalendar
import calendar_inline.utils as utils
from admin import Admin, set_morning_notification, set_evening_notification, set_daily_evening_notification, set_daily_morning_notification, set_nightly_no_ota, notifications_menu, set_daily_convert
from components.adminRequests import adminRequests
import logging
import os
from constants.admin_id import admin_id_arr
from utils.number_to_emoji import number_to_emoji
from utils.delete_message import delete_message, set_delete_message
from ptbcontrib.ptb_sqlalchemy_jobstore import PTBSQLAlchemyJobStore

from admin import admin_notification_evening, admin_notification_morning
import pytz
import flag 

import wubook_functions as wubook
import google_currency as currency #pip install google-currency

from components.admin_help import *
from components.guest_payment import *
from components.assign_room import *

# Enable logging
logging.basicConfig(
    filename = "eva.log",
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)



# logging.basicConfig(filename="logfilename.log", level=logging.INFO)

admin = Admin()




SELECT_LANGUAGE, LANGUAGE_MENU, MAIN_MENU, GET_COURSE, ABOUT_HOTEL, ADDRESS_CALLBACK = range(6)
LEVEL1, LEVEL2, LEVEL3, LEVEL3_ABOUT_HOTEL, LEVEL3_EVENTS, LEVEL4_ABOUT_HOTEL, LEVEL5_ABOUT_HOTEL, LEVEL3_BOOKING, LEVEL34_BOOKING, LEVEL4_BOOKING, LEVEL5_BOOKING, LEVEL6_BOOKING, LEVEL1_VERIFY, LEVEL2_VERIFY, LEVEL3_VERIFY,LEVEL7_CHECKIN, LEVEL7_CHECKOUT, LEVEL7_BOOKING, LEVEL1_CHECKOUT, LEVEL1_PAYMENT, LEVEL2_PAYMENT, LEVEL1_NEW_BOOKING, LEVEL2_NEW_BOOKING, LEVEL3_NEW_BOOKING, LEVEL4_NEW_BOOKING, LEVEL34_SELECT_BOOKING= range(26)


botChatID = 0

#start menu
start_menu = [
    ["Мероприятия"],
    ["О гостинице"], ['Бронирование'],
    ["Язык"]
]
start_menu_markup = ReplyKeyboardMarkup(start_menu, resize_keyboard=True, one_time_keyboard=True)

language_select_menu = [
    ["Русский"],
    ["English"],
]
language_select_menu_markup = ReplyKeyboardMarkup(language_select_menu, resize_keyboard=True, one_time_keyboard=True)


btn1 = InlineKeyboardButton("Мероприятия", callback_data="EVENTS")
btn2 = InlineKeyboardButton("О гостинице", callback_data="ABOUTHOTEL")
btn3 = InlineKeyboardButton("Бронирование", callback_data="BOOKING")
btn4 = InlineKeyboardButton("Язык", callback_data="LANGUAGE_SELECT")
btn5 = InlineKeyboardButton("🔙 Назад", callback_data="BACK")


async def deleteMessage(update: Update, context: CallbackContext, chatID, messageID):
    await asyncio.sleep(2)
    await context.bot.delete_message(chatID, messageID)

# Define a few command handlers. These usually take the two arguments update and
# context.
          
def main_end_conversation(update: Update, context: CallbackContext) -> None:
    return ConversationHandler.END
    
def start(update: Update, context: CallbackContext) -> None:
 

    chat_id = update.message.chat_id
    
    try:
        # # args[0] should contain the time for the timer in seconds
        print(context.args[0])
        
        firestore_id = context.args[0]
        firebase.add_maid_details(firestore_id, {"telegram_id": update.message.from_user.id, "telegram_username": update.message.from_user.username})
        
        print("Successfully add maid")
        
    except:
        pass
        
    sticker_message = context.bot.send_sticker(chat_id = chat_id, sticker = "CAACAgIAAxkBAAEfc1pkMa_AzLtlqH2rC5yT9NywVWFneQAC1CoAAhw2kUmDB2FYe2N1Gy8E")
    context.user_data['sticker_message_id'] = sticker_message.message_id
    
    set_delete_message(context, "sticker_delete_message", 60, sticker_message.chat_id, sticker_message.message_id)
    
    context.bot.send_message(chat_id, text = f"""
Привет! Я Eva – ваш помощник из гостиницы Eva at Home. Я много что умею 😉 Вместе со мной можно заселиться в номер, узнать детали бронирования, забронировать номер или изменить бронирование. Я могу рассказать про гостиницу и город, познакомить с мероприятиями или турами. Нам будет интересно вместе!
                             """)
    
    context.bot.send_message(chat_id = chat_id, text = f"""Давай расскажу по меню:
Кнопка Бронирование - тут ты можешь забронировать номер и зарегистрироваться, или же посмотреть свое бронирование. 

Кнопка О гостинице - здесь я подскажу как добраться, ознакомлю с услугами гостиницы и скину фотографии. 

Кнопка Мероприятия - мы пока работаем над ней
                                """,
                            reply_markup = InlineKeyboardMarkup([
                                [btn1],
                                [btn2], [btn3],
                                [btn4],
                                [InlineKeyboardButton(text="Я приехал, хочу заселиться", callback_data="CHECKIN_MAIN_MENU")],
                                [InlineKeyboardButton(text="Я уезжаю, сдать номер", callback_data="CHECKOUT_MAIN_MENU")],
                            ]))
    
    
    context.user_data["lang"] = "rus"
    context.user_data["chat_id"] = update.message.chat_id
    print(f"USERNAME: {update.message.from_user.username} ID: {update.message.chat_id}")
    
    if str(update.message.from_user.id) in admin_id_arr:
        print("works")
        keyboard = [
            ["Меню администратора"]
        ]
        
    
def asks_for_name(update: Update, context: CallbackContext):
    
    
    name = update.message.text 
    context.user_data['name'] = name
    
    context.bot.send_message(chat_id = update.message.chat_id, text = f"""
Приятно познакомится, {name} :)
И так давай расскажу по меню: 

Кнопка Бронирование - тут ты можешь забронировать номер и зарегистрироваться, или же посмотреть свое бронирование. 

Кнопка О гостинице - здесь я подскажу как добраться, ознакомлю с услугами гостиницы и скину фотографии. 

Кнопка Мероприятия - мы пока работаем над ней
                             """,  reply_markup = InlineKeyboardMarkup([
                                [btn1],
                                [btn2], [btn3],
                                [btn4],
                                [InlineKeyboardButton(text="Я приехал, хочу заселиться", callback_data="CHECKIN_MAIN_MENU")],
                                [InlineKeyboardButton(text="Я уезжаю, сдать номер", callback_data="CHECKOUT_MAIN_MENU")],
                            ]) )
    
    return ConversationHandler.END
    


def main_menu(update: Update, context: CallbackContext) -> None:
 
    query = update.callback_query
    query.answer()

    try:
        query.edit_message_text(text = "Выберите нужный раздел",
                            reply_markup = InlineKeyboardMarkup([
                                [btn1],
                                [btn2], [btn3],
                                [btn4],
                                [InlineKeyboardButton(text="Я приехал, хочу заселиться", callback_data="CHECKIN_MAIN_MENU")],
                                [InlineKeyboardButton(text="Я уезжаю, сдать номер", callback_data="CHECKOUT_MAIN_MENU")],

                            ]))
    except:
        context.bot.delete_message(chat_id = query.message.chat_id, message_id = query.message.message_id)
        context.bot.send_message(chat_id = query.message.chat_id, text = "Выберите нужный раздел",
                            reply_markup = InlineKeyboardMarkup([
                                [btn1],
                                [btn2], [btn3],
                                [btn4],
                                [InlineKeyboardButton(text="Я приехал, хочу заселиться", callback_data="CHECKIN_MAIN_MENU")],
                                [InlineKeyboardButton(text="Я уезжаю, сдать номер", callback_data="CHECKOUT_MAIN_MENU")],

                            ]))
        
    context.user_data["lang"] = "rus"
    
    return LEVEL2

def main_menu_send_message(update: Update, context: CallbackContext) -> None:
 
    context.bot.send_message(chat_id = context.user_data["chat_id"], text = "Выберите нужный раздел",
                        reply_markup = InlineKeyboardMarkup([
                            [btn1],
                            [btn2], [btn3],
                            [btn4],
                            [InlineKeyboardButton(text="Я приехал, хочу заселиться", callback_data="CHECKIN_MAIN_MENU")],
                            [InlineKeyboardButton(text="Я уезжаю, сдать номер", callback_data="CHECKOUT_MAIN_MENU")],

                        ]))
        
    context.user_data["lang"] = "rus"
    
    return LEVEL2



def checkin_main_menu(update: Update, context: CallbackContext, *args, **kwargs):
    try:
        query = update.callback_query
        query.answer()
        chat_id = query.message.chat_id
    except:
        chat_id = update.message.chat_id
    
    try:
        context.bot.delete_message(chat_id, query.message.message_id)
    except:
        pass
    
    message = context.bot.send_message(chat_id, text="Так, давай поищем твое бронирование")
    
    try:
        if query.data == "OTHER_PHONE":
            del context.user_data['phone_number']
            del context.user_data['booking']
    except:
        pass
    
    if "phone_number" in context.user_data.keys()  or ("rcode" in kwargs.keys() and kwargs['rcode'] == True):
        
        if ("rcode" in kwargs.keys() and kwargs['rcode'] == True):
            bookings = context.user_data['bookings']
        else:
            bookings = firebase.getBookingByPhoneNumber(context.user_data["phone_number"])
        
        if "booking" in context.user_data.keys():
            del context.user_data['booking']
            
        
        if len(bookings) == 1:
            context.user_data['booking'] = bookings[0]
            
        # print(bookings)

        bookings_list = [
            [],
            [InlineKeyboardButton(text = "Поискать для другого номера", callback_data="OTHER_PHONE")]
        ]
        message_text = f""
        for i in range(len(bookings)):
            # print(i)
            # if type(bookings[i]['room_number']) == list:
            #     room_number = ""
            #     for room_type in bookings[i]['room_number']:
            #         room_number += f"{room_type} "
                    
            bookings_list[0].append(InlineKeyboardButton(text = (i+1), callback_data=f"SELECTED_BOOKING | {i}"))
            message_text += f"""Бронирование №{i+1}
Дата заселения: {bookings[i]["checkin_date"].strftime("%d/%m/%Y")}
Дата выселения: {bookings[i]["checkout_date"].strftime("%d/%m/%Y")}
Ваша комната: {bookings[i]['room_number'] }
Вид комнаты: {bookings[i]['room_type']}
        
"""
            
            
        message.edit_text(text = f"""
Я нашла ваши бронирования. Выберите необходимое бронирование:

{message_text}
""", reply_markup = InlineKeyboardMarkup(bookings_list))

        return "LEVEL4_CHECKIN"

    else:
        if "booking" in context.user_data.keys():
            del context.user_data['booking']
        
        keyboard = [
            [InlineKeyboardButton(text = "Подтвердить через Telegram", callback_data="VERIFY_PHONE")],
            [InlineKeyboardButton(text = "Поиск по номеру телефона", callback_data="VERIFY_JUST_NUMBER")],
            [InlineKeyboardButton(text = "Поиск по номеру бронирования", callback_data="VERIFY_JUST_RCODE")],

            # [InlineKeyboardButton(text = "Подтвердить по почте", callback_data="VERIFY_EMAIL")],
            [btn5]
        ]
        
        
        message.edit_text(text=f"""
Отлично, мне нужно подтвердить твою личность, чтобы получить доступ к твоим бронированиям.
Ты можешь подтвердить через Telegram, если бронирование сделано на тот же номер телефона, как и твой номер в Telegram.
Или же через почту, если ты указал другой номер при регистрации.
                                """, reply_markup=InlineKeyboardMarkup(keyboard))
        return "LEVEL1_CHECKIN"

    
def checkin_selected_booking(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer("Секундочку")
    
    
    if "booking" in context.user_data.keys():
        booking = context.user_data['booking']
    else:

        callbackArr = query.data.split(" | ")
        # print(callbackArr)

        bookings = firebase.getBookingByPhoneNumber(context.user_data["phone_number"])
        
        context.user_data["booking"] = bookings[int(callbackArr[1])]
        booking = bookings[int(callbackArr[1])]
        
        context.user_data['selected_booking'] = {"user_id": booking['user_id'], "booking_id": booking['id']}
    
    today_datetime = datetime.datetime.now(tz = pytz.timezone("Asia/Almaty"))
    
    # today_datetime = booking["checkin_date"]
    
    if booking["checkin_date"].date() < today_datetime.date():
        query.edit_message_text(text = f"""
Ваша дата заезда {booking["checkin_date"].strftime("%d/%m/%Y")}, а сегодня {datetime.datetime.today().strftime("%d/%m/%Y")}. Я смогу вас зарегистрировать только в день заезда...
""", reply_markup=InlineKeyboardMarkup([[btn5]]))  
        return "LEVEL5_CHECKIN"  
    
    status = firebase.getStatusFromGuestBookingID(booking['user_id'], booking['id'])
    
    # datetime.datetime.today().date()
    
    if status['checked_in'] == False:
        
        context.user_data['assign_room_final'] = {
            "next_state": "NEXT_CHECKIN",
            "next_func": "ver2_api.checkin_payment(update, context)"
        }
        
        context.user_data['guest_payment_final'] = {
            "next_state": "NEXT_CHECKIN",
            "next_func": "ver2_api.checkin_actions_after_payment(update, context)"
        }
        
        
        
        keyboard = [
            [InlineKeyboardButton(text = "🔑 Получить ключ от номера", callback_data="ASSIGN_ROOM")],
            [InlineKeyboardButton(text = "💵 Оплатить проживание", callback_data="GUEST_PAYMENT")],
            [InlineKeyboardButton(text = "📷 Посмотреть номер", callback_data="AAA")],
            [InlineKeyboardButton(text = "🧭 Экскурсия по гостинице", callback_data="AAA")],
            [InlineKeyboardButton(text = "🔔 Раннее заселение (до 14:00)", callback_data="AAA")],
            [btn5]
        ]
        
        message_text = f"""Ваше бронирование:
Дата заселения: {booking["checkin_date"].strftime("%d/%m/%Y")}
Дата выселения: {booking["checkout_date"].strftime("%d/%m/%Y")}
Ваша комната: {booking['room_number'] }
Вид комнаты: {booking['room_type']}

Что будем делать дальше?
"""
        query.edit_message_text(text = message_text, reply_markup=InlineKeyboardMarkup(keyboard))
        
        return "LEVEL5_CHECKIN"
    
    else:
        
        keyboard = [
            # [InlineKeyboardButton(text = "🔑 Получить ключ от номера", callback_data="ASSIGN_ROOM")],
            [InlineKeyboardButton(text = "💵 Оплатить проживание", callback_data="GUEST_PAYMENT")],
            # [InlineKeyboardButton(text = "📷 Посмотреть номер", callback_data="AAA")],
            # [InlineKeyboardButton(text = "🧭 Экскурсия по гостинице", callback_data="AAA")],
            # [InlineKeyboardButton(text = "🔔 Раннее заселение (до 14:00)", callback_data="AAA")],
            [btn5]
        ]
                
        query.edit_message_text(text = f"""
Ваше бронирование:
Дата заселения: {booking["checkin_date"].strftime("%d/%m/%Y")}
Дата выселения: {booking["checkout_date"].strftime("%d/%m/%Y")}
Ваша комната: {booking['room_number'] }
Вид комнаты: {booking['room_type']}
                                
Я вижу, что вы уже зарегистрированы. Вы можете сделать оплату, если у вас есть долг или же вернуться назад.""", reply_markup=InlineKeyboardMarkup(keyboard))
        # time.sleep(0.5)
        
        return "LEVEL5_CHECKIN"
        
        # return main_menu(update, context)


def checkin_payment(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    context.user_data['guest_payment_final'] = {
            "next_state": "NEXT_CHECKIN",
            "next_func": "ver2_api.checkin_actions_after_payment(update, context)"
    }
    
    keyboard = [
            [InlineKeyboardButton(text = "💵 Оплатить проживание", callback_data="GUEST_PAYMENT")],
        ]
    
    query.edit_message_text(text = "Отлично, теперь тебе необходимо оплатить проживание. Для этого нажми на кнопку!", reply_markup=InlineKeyboardMarkup(keyboard))
    
    return "LEVEL6_CHECKIN"

def checkin_actions_after_payment(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    user_id, booking_id = context.user_data['booking']['user_id'], context.user_data['booking']['id']
    
    status = firebase.getStatusFromGuestBookingID(user_id, booking_id)
    
    booking = context.user_data['booking']
    
    checkin_date_bool = booking["checkin_date"].date() == booking["checkin_date"].date()
    
    if "guest_payment_wait_approve" in context.user_data.keys() and context.user_data['guest_payment_wait_approve'] == True:
        context.user_data['guest_payment_wait_approve'] = False
        
        keyboard = [
                [InlineKeyboardButton(text = "🧭 Экскурсия по гостинице", callback_data="aaaa")],
                [InlineKeyboardButton(text = "🗺️ Мой гид по Бишкек", callback_data="aaaa")],
                [InlineKeyboardButton(text = "🌐 Вернуться в главное меню", callback_data="MAIN_MENU")],
            ]
        
        query.edit_message_text(text = "Что ты хочешь сделать дальше?", reply_markup=InlineKeyboardMarkup(keyboard))
    elif status['checked_in'] == False and checkin_date_bool == True:
        
        context.user_data['assign_room_final'] = {
            "next_state": "NEXT_CHECKIN_FINAL",
            "next_func": "ver2_api.checkin_actions_after_payment(update, context)"
        }
        
        keyboard = [
                [InlineKeyboardButton(text = "🔑 Получить ключ от комнаты", callback_data="ASSIGN_ROOM")],
                # [InlineKeyboardButton(text = "🗺️ Мой гид по Бишкек", callback_data="aaaa")],
                [InlineKeyboardButton(text = "🌐 Вернуться в главное меню", callback_data="MAIN_MENU")],
        ]
        
        query.edit_message_text(text = "Я вижу, что ты еще не получил комнату, давай это исправим", reply_markup = InlineKeyboardMarkup(keyboard))
    else:
    
        keyboard = [
                [InlineKeyboardButton(text = "🧭 Экскурсия по гостинице", callback_data="aaaa")],
                [InlineKeyboardButton(text = "🗺️ Мой гид по Бишкек", callback_data="aaaa")],
                [InlineKeyboardButton(text = "🌐 Вернуться в главное меню", callback_data="MAIN_MENU")],
            ]
        
        query.edit_message_text(text = "Молодец, ты выполнил все пункты регистрации. Что ты хочешь сделать дальше?", reply_markup=InlineKeyboardMarkup(keyboard))

    return "LEVEL7_CHECKIN"

#Номер телефона без подтверждения
def checkin_verify_just_phone_number(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    query.edit_message_text(text="Напиши номер телефона, на который был забронирован номер. Обязательно в международном формате (+ххххххххххх)!")

    return "LEVEL2_CHECKIN_JUST_PHONENUMBER"

def checkin_verify_just_phone_number_incorrect_format(update: Update, context: CallbackContext):
    context.bot.send_message(update.message.chat_id, text = f"Вы ввели некорректный номер телефона, попробуйте снова. В формате: +xxxxxxxxxxx (начинается с '+' и максимум 15 цифр)")
    return "LEVEL2_CHECKIN_JUST_PHONENUMBER"


def checkin_verify_just_phone_number_get_phone(update: Update, context: CallbackContext):
    phone_number = update.message.text
    context.bot.send_message(chat_id = update.message.chat_id, text = "Ищу ваше бронирование...")
    
    bookings = firebase.getBookingByPhoneNumber(phone_number)
    
    if(bookings is None or len(bookings) == 0):
        keyboard = [
            [InlineKeyboardButton(text = "❌ Отменить и вернуться назад", callback_data="BACK")]
        ]
        context.bot.send_message(chat_id = update.message.chat_id, text = "Я не нашла ваше бронирование, проверьте номер телефона и отправьте еще раз или вернитесь назад", reply_markup = InlineKeyboardMarkup(keyboard))
        return "LEVEL2_CHECKIN_JUST_PHONENUMBER"
    else:
        context.user_data["phone_number"] = phone_number
        return checkin_main_menu(update, context)

#Номер бронирования без подтверждения
def checkin_verify_just_rcode(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    query.edit_message_text(text="Введи номер бронирования.")

    return "LEVEL2_CHECKIN_JUST_RCODE"

def checkin_verify_just_rcode_incorrect_format(update: Update, context: CallbackContext):
    context.bot.send_message(update.message.chat_id, text = f"Вы ввели некорректный номер бронирования, попробуйте снова. Номер бронирования зачастую представлен в виде числа из 10 цифр")
    return "LEVEL2_CHECKIN_JUST_RCODE"


def checkin_verify_just_rcode_get_rcode(update: Update, context: CallbackContext):
    rcode = update.message.text
    context.bot.send_message(chat_id = update.message.chat_id, text = "Ищу ваше бронирование...")
    
    bookings = firebase.getBookingByRcode(rcode)
    
    if(bookings is None or len(bookings) == 0):
        keyboard = [
            [InlineKeyboardButton(text = "❌ Отменить и вернуться назад", callback_data="BACK")]
        ]
        context.bot.send_message(chat_id = update.message.chat_id, text = "Я не нашла ваше бронирование, проверьте номер бронирования и отправьте еще раз или вернитесь назад", reply_markup = InlineKeyboardMarkup(keyboard))
        return "LEVEL2_CHECKIN_JUST_RCODE"
    else:
        context.user_data['bookings'] = bookings
        return checkin_main_menu(update, context, rcode = True)  
        
def checkin_verify_email(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    query.edit_message_text(text="Напиши номер телефона, на который был забронирован номер. Обязательно в международном формате (+ххххххххххх)!")
    
    return "LEVEL2_CHECKIN"

def checkin_get_phone_number_and_send_email(update: Update, context: CallbackContext):
    try:
        if update.callback_query.data == "SEND_CODE_AGAIN":
            phone_number = context.user_data['checkin_phone']
    except:
        phone_number = update.message.text
        context.user_data['checkin_phone'] = phone_number
       
    user = firebase.getUserByPhoneNumber(phone_number)
    if user is not None:
        email = user['email']
        generated_code = sendemail.send_email(email)
        context.user_data['generated_code'] = generated_code
        context.user_data['not_verified_phone_number'] = user['phone_number']
    
        keyboard = [
            [InlineKeyboardButton(text = "Отправить заново", callback_data="SEND_CODE_AGAIN")]
        ]
        
        context.bot.send_message(update.message.from_user.id, text="На почту, на которую был забронирован номер должен прийти код подтверждения. Введи его")
        
        return "LEVEL3_CHECKIN"
    else:
        context.bot.send_message(update.message.from_user.id, text="Мы не нашли бронирование на ваш номер, попробуйте еще раз")
        return "LEVEL2_CHECKIN"

def checkin_get_code_from_user(update: Update, context: CallbackContext):
    code_from_user = update.message.text
    # while(code_from_user != context.user_data['generated_code']):
    #     context.bot.send_message(update.message.from_user.id, text="Вы неправильно ввели код подтверждения, попробуйте еще раз")
    # context.bot.send_message(update.message.from_user.id, text="Все правильно!")
    
    if(code_from_user == context.user_data['generated_code']):
        messageToDelete = context.bot.send_message(update.message.from_user.id, text="Все правильно!")
        time.sleep(2)
        context.bot.delete_message(update.message.from_user.id, messageToDelete.message_id)
        context.user_data["phone_number"] = context.user_data['not_verified_phone_number']

    else:
        context.bot.send_message(update.message.from_user.id, text="Вы неправильно ввели код подтверждения, попробуйте еще раз")
        return "LEVEL3_CHECKIN"
    # booking_contact(update, context)
    return checkin_main_menu(update, context)

def checkin_verify_phone(update: Update, context: CallbackContext):
    
    query = update.callback_query
    query.answer()
    
    if "phone_number" not in context.user_data.keys():
        
        keyboard = [KeyboardButton(text="Подтвердите свой номер", request_contact=True)]
        
        context.bot.send_message(chat_id = query.from_user.id,text="Нам необходимо подтвердить ваш номер телефона, чтобы получить доступ к бронированиям", 
                                reply_markup=ReplyKeyboardMarkup(keyboard=[keyboard], resize_keyboard=True, one_time_keyboard=True))
        
        return "LEVEL2_CHECKIN"
    
def checkin_verified_with_contact(update: Update, context: CallbackContext):
    if "phone_number" not in context.user_data.keys():
        #Если номера телефона еще нет в user_data
        phone_number_from_bot = update.message.contact.phone_number
        arr = [c for c in phone_number_from_bot]
        # print(arr)
        if arr[0] != "+":
            phone_number_from_bot = '+'+phone_number_from_bot
            # print(phone_number_from_bot)
            
        
        phone_number = phone_number_from_bot
        get_booking = firebase.getBookingByPhoneNumber(phone_number)
        
        if get_booking is None:
            context.bot.send_message(chat_id = context.user_data["chat_id"], text = "Я не нашла бронирование на твой номер, попробуйте еще раз")
            return checkin_request_contact_again(update, context)

        
        booking = get_booking[0]
        if booking is not None:
            #Если бронирование найдено
            # print("Бронирование найдено")
            context.user_data["phone_number"] = phone_number_from_bot
            # context.user_data['booking'] = booking
            return checkin_main_menu(update, context)
        else:
            #Если бронирование не найдено
            context.bot.send_message(chat_id = context.user_data["chat_id"], text = "Я не нашла бронирование на твой номер, попробуйте еще раз")
            return checkin_request_contact_again(update, context)
    
    else:
        phone_number = context.user_data["phone_number"]
        
        get_booking = firebase.getBookingByPhoneNumber(phone_number)
        
        
        booking = get_booking[0]
        
        if get_booking is None:
            context.bot.send_message(chat_id = context.user_data["chat_id"], text = "Я не нашла бронирование на твой номер, попробуйте еще раз")
            return checkin_request_contact_again(update, context)
        
        if booking is not None:
            # print("Бронирование найдено")
            # context.user_data['booking'] = booking
            return checkin_main_menu(update, context)
        else:
            try:
                update.callback_query.edit_message_text(text = "Я не нашла бронирование на твой номер, попробуйте еще раз")
            except:
                context.bot.send_message(chat_id = context.user_data["chat_id"], text = "Я не нашла бронирование на твой номер, попробуйте еще раз")
                
            return checkin_request_contact_again(update, context)
 
def checkin_request_contact_again(update, context):
    
    
    keyboard = [KeyboardButton(text="Подтвердите свой номер", request_contact=True)]
    
    context.bot.send_message(chat_id = context.user_data["chat_id"],text="Нам необходимо подтвердить ваш номер телефона, чтобы получить доступ к бронированиям", 
                            reply_markup=ReplyKeyboardMarkup(keyboard=[keyboard], resize_keyboard=True, one_time_keyboard=True))
    
    return LEVEL4_BOOKING



def checkout_main_menu(update: Update, context: CallbackContext):
    try:
        query = update.callback_query
        query.answer()
        chat_id = query.message.chat_id
    except:
        chat_id = update.message.chat_id
    
    try:
        context.bot.delete_message(chat_id, query.message.message_id)
    except:
        pass
    
    message = context.bot.send_message(chat_id, text="Так, давай поищем твое бронирование")
    
    try:
        if query.data == "OTHER_PHONE":
            del context.user_data['phone_number']
    except:
        pass
    
    if "phone_number" not in context.user_data.keys():
        keyboard = [
            [InlineKeyboardButton(text = "Подтвердить через Telegram", callback_data="VERIFY_PHONE")],
            [InlineKeyboardButton(text = "Подтвердить по почте", callback_data="VERIFY_EMAIL")],
            [btn5]
        ]
        
        
        message.edit_text(text=f"""
Отлично, мне нужно подтвердить твою личность, чтобы получить доступ к твоим бронированиям.
Ты можешь подтвердить через Telegram, если бронирование сделано на тот же номер телефона, как и твой номер в Telegram.
Или же через почту, если ты указал другой номер при регистрации.
                                """, reply_markup=InlineKeyboardMarkup(keyboard))
        return "LEVEL1_MAIN_MENU_CHECKOUT"
    else:
        bookings = firebase.getBookingByPhoneNumber(context.user_data["phone_number"])

        bookings_list = [
            [],
            [InlineKeyboardButton(text = "Поискать для другого номера", callback_data="OTHER_PHONE")]
        ]
        message_text = f""
        for i in range(len(bookings)):
            # print(i)
            if type(bookings[i]['room_number']) == list:
                room_number = ""
                for room_type in bookings[i]['room_number']:
                    room_number += f"{room_type} "
                    
            bookings_list[0].append(InlineKeyboardButton(text = (i+1), callback_data=f"SELECTED_BOOKING | {i}"))
            message_text += f"""Бронирование №{i+1}
Дата заселения: {bookings[i]["checkin_date"].strftime("%d/%m/%Y")}
Дата выселения: {bookings[i]["checkout_date"].strftime("%d/%m/%Y")}
Ваша комната: {room_number if room_number is not None else bookings[i]['room_number'] }
        
"""
            
            
        message.edit_text(text = f"""
Я нашла ваши бронирования. Выберите необходимое бронирование:

{message_text}
""", reply_markup = InlineKeyboardMarkup(bookings_list))

    return "LEVEL4_MAIN_MENU_CHECKOUT"
    
        
def checkout_verify_email(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    query.edit_message_text(text="Напиши номер телефона, на который был забронирован номер. Обязательно в международном формате (+ххххххххххх)!")
    
    return "LEVEL2_MAIN_MENU_CHECKOUT"

def checkout_get_phone_number_and_send_email(update: Update, context: CallbackContext):
    phone_number = update.message.text
    user = firebase.getUserByPhoneNumber(phone_number)
    if user is not None:
        email = user['email']
        generated_code = sendemail.send_email(email)
        context.user_data['generated_code'] = generated_code
        context.user_data['not_verified_phone_number'] = user['phone_number']
        
        context.bot.send_message(update.message.from_user.id, text="На почту, на которую был забронирован номер должен прийти код подтверждения. Введи его")
        
        return "LEVEL3_MAIN_MENU_CHECKOUT"
    else:
        context.bot.send_message(update.message.from_user.id, text="Мы не нашли бронирование на ваш номер, попробуйте еще раз")
        return "LEVEL2_MAIN_MENU_CHECKOUT"

def checkout_get_code_from_user(update: Update, context: CallbackContext):
    code_from_user = update.message.text
    # while(code_from_user != context.user_data['generated_code']):
    #     context.bot.send_message(update.message.from_user.id, text="Вы неправильно ввели код подтверждения, попробуйте еще раз")
    # context.bot.send_message(update.message.from_user.id, text="Все правильно!")
    
    if(code_from_user == context.user_data['generated_code']):
        messageToDelete = context.bot.send_message(update.message.from_user.id, text="Все правильно!")
        time.sleep(2)
        context.bot.delete_message(update.message.from_user.id, messageToDelete.message_id)
        context.user_data["phone_number"] = context.user_data['not_verified_phone_number']

    else:
        context.bot.send_message(update.message.from_user.id, text="Вы неправильно ввели код подтверждения, попробуйте еще раз")
        return "LEVEL3_MAIN_MENU_CHECKOUT"
    # booking_contact(update, context)
    return checkout_main_menu(update, context)

def checkout_verify_phone(update: Update, context: CallbackContext):
    
    query = update.callback_query
    query.answer()
    
    if "phone_number" not in context.user_data.keys():
        
        keyboard = [KeyboardButton(text="Подтвердите свой номер", request_contact=True)]
        
        context.bot.send_message(chat_id = query.from_user.id,text="Нам необходимо подтвердить ваш номер телефона, чтобы получить доступ к бронированиям", 
                                reply_markup=ReplyKeyboardMarkup(keyboard=[keyboard], resize_keyboard=True, one_time_keyboard=True))
        
        return "LEVEL2_MAIN_MENU_CHECKOUT"
    
def checkout_verified_with_contact(update: Update, context: CallbackContext):
    if "phone_number" not in context.user_data.keys():
        #Если номера телефона еще нет в user_data
        phone_number_from_bot = update.message.contact.phone_number
        arr = [c for c in phone_number_from_bot]
        # print(arr)
        if arr[0] != "+":
            phone_number_from_bot = '+'+phone_number_from_bot
            # print(phone_number_from_bot)
            
        
        phone_number = phone_number_from_bot
        get_booking = firebase.getBookingByPhoneNumber(phone_number)
        
        if get_booking is None:
            context.bot.send_message(chat_id = context.user_data["chat_id"], text = "Я не нашла бронирование на твой номер, попробуйте еще раз")
            return checkin_request_contact_again(update, context)

        
        booking = get_booking[0]
        if booking is not None:
            #Если бронирование найдено
            # print("Бронирование найдено")
            context.user_data["phone_number"] = phone_number_from_bot
            # context.user_data['booking'] = booking
            return checkout_main_menu(update, context)
        else:
            #Если бронирование не найдено
            context.bot.send_message(chat_id = context.user_data["chat_id"], text = "Я не нашла бронирование на твой номер, попробуйте еще раз")
            return checkout_request_contact_again(update, context)
    
    else:
        phone_number = context.user_data["phone_number"]
        
        get_booking = firebase.getBookingByPhoneNumber(phone_number)
        
        
        booking = get_booking[0]
        
        if get_booking is None:
            context.bot.send_message(chat_id = context.user_data["chat_id"], text = "Я не нашла бронирование на твой номер, попробуйте еще раз")
            return checkout_request_contact_again(update, context)
        
        if booking is not None:
            # print("Бронирование найдено")
            # context.user_data['booking'] = booking
            return checkout_main_menu(update, context)
        else:
            try:
                update.callback_query.edit_message_text(text = "Я не нашла бронирование на твой номер, попробуйте еще раз")
            except:
                context.bot.send_message(chat_id = context.user_data["chat_id"], text = "Я не нашла бронирование на твой номер, попробуйте еще раз")
                
            return checkout_request_contact_again(update, context)
 
def checkout_request_contact_again(update, context):
    
    
    keyboard = [KeyboardButton(text="Подтвердите свой номер", request_contact=True)]
    
    context.bot.send_message(chat_id = context.user_data["chat_id"],text="Нам необходимо подтвердить ваш номер телефона, чтобы получить доступ к бронированиям", 
                            reply_markup=ReplyKeyboardMarkup(keyboard=[keyboard], resize_keyboard=True, one_time_keyboard=True))
    
    return "LEVEL4_MAIN_MENU_CHECKOUT"


def checkout_selected(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    if "booking" in context.user_data.keys():
        booking = context.user_data['booking']
    else:

        callbackArr = query.data.split(" | ")
        # print(callbackArr)
        bookings = firebase.getBookingByPhoneNumber(context.user_data["phone_number"])
        context.user_data["booking"] = bookings[int(callbackArr[1])]
        booking = bookings[int(callbackArr[1])]
        
    if type(booking['room_number']) == list:
        room_number = ""
        for room_type in booking['room_number']:
            room_number += f"{room_type} "
            
    message = f"""
Ваше бронирование:

Дата заселения: {booking["checkin_date"].strftime("%d/%m/%Y")}
Дата выселения: {booking["checkout_date"].strftime("%d/%m/%Y")}
Ваша комната: {room_number if room_number is not None else booking['room_number'] }
"""
    
    query.edit_message_text(text = message)
    
    
    context.bot.send_message(context.user_data['chat_id'], text="Просим вас оставить ключи у администратора)")

    rating = [
        [InlineKeyboardButton(text="1", callback_data="1"), 
         InlineKeyboardButton(text="2", callback_data="2"), 
         InlineKeyboardButton(text="3", callback_data="3"), 
         InlineKeyboardButton(text="4", callback_data="4"), 
         InlineKeyboardButton(text="5", callback_data="5")]
    ]
    
    context.bot.send_message(context.user_data['chat_id'], text="Оцените наш сервис от 1 до 5", reply_markup=InlineKeyboardMarkup(rating))

    return "LEVEL5_MAIN_MENU_CHECKOUT"

def checkout_rated_main_menu(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    context.user_data["rating"] = query.data
    query.edit_message_reply_markup(reply_markup=None)
    context.bot.send_message(context.user_data["chat_id"], text="Спасибо за вашу оценку!", reply_markup = ReplyKeyboardRemove())
    context.bot.send_message(context.user_data["chat_id"], text="Есть ли у вас какие-либо комментарии по нашему сервису?", reply_markup = ReplyKeyboardRemove())
    return "LEVEL5_MAIN_MENU_CHECKOUT"
    
def checkout_comments_main_menu(update: Update, context: CallbackContext):
    comment = update.message
    context.bot.send_message(context.user_data["chat_id"], text="Спасибо, мы передали ваши комментарии администратору. Надеюсь увидимся еще!")
    
    user = update.message.from_user
    booking = context.user_data["booking"]
    user_from_booking = firebase.getUserByPhoneNumber(context.user_data["phone_number"])
    
    for adminID in admin_id_arr:
        context.bot.send_message(chat_id = adminID, text = f"""
Гость выселился из номера:
    Логин в Telegram: @{user.username}
    Имя и Фамилия: {user_from_booking['name']} {user_from_booking['lastname']}
    Номер телефона: {user_from_booking["phone_number"]}
    Дата заселения: {booking["checkin_date"].strftime("%d-%m-%Y")}
    Дата выселения: {booking["checkout_date"].strftime("%d-%m-%Y")}
    Комната: {booking["room_number"]}
    _________________________________________
    Комментарии: {comment.text}
    Оценка: {context.user_data["rating"]}/5
                             """)
        
    
    firebase.check_room_occupancy_if_delete(booking['user_id'], booking['id'], booking['reservation_code'])
    
    firebase.updateBookingWithId(booking['user_id'], booking['id'], {"checked_out": True})
    firebase.approveStatusFromGuestBookingID(booking['user_id'], booking['id'], 'checked_out', True)
     
    del context.user_data['booking']
    return main_menu_send_message(update, context)
    # return my_booking_options(update, context)
    
# def main_menu(update: Update, context: CallbackContext, chat_id, message_id) -> None:
#     if(context.user_data["lang"] == "rus"):
#         context.bot.send_message(chat_id = chat_id, text="Russian")
#         context.bot.delete_message(chat_id, message_id)
#     else:
#         context.bot.send_message(chat_id = chat_id, text="English")
#         context.bot.delete_message(chat_id, message_id)
        

        
def select_language(update: Update, context: CallbackContext):
    
    query = update.callback_query
    query.answer()
    

    lang_select_keyboard = [
        [InlineKeyboardButton(text="Русский", callback_data=f"LANG | rus")],
        [InlineKeyboardButton(text="English", callback_data=f"LANG | eng")],
        [btn5]
    ]
    
    query.edit_message_text(
        text = "Выберите язык",
        reply_markup=InlineKeyboardMarkup(lang_select_keyboard)
    )
    # context.bot.sendMessage(chat_id = update.message.chat_id, text = "Выберите язык", 
    #     reply_markup=InlineKeyboardMarkup(lang_select_keyboard))
    
    
    return LEVEL2

def language_select_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    
    try:
        callbackArr = (query.data).split(" | ")
        context.user_data["lang"] = callbackArr[1]
    except:
        pass

    query.answer()
    
    
    lang_select_keyboard = [
        [btn5]
    ]

    query.edit_message_text(
        text = "Успешно!",
        reply_markup=InlineKeyboardMarkup(lang_select_keyboard)
    )
    
    return LEVEL2
    
        
    
def language_select_rus(update: Update, context: CallbackContext) -> None:
    # print(update.message.text)
    context.user_data["lang"] = "rus"
    main_menu(update, context)

def language_select_eng(update: Update, context: CallbackContext) -> None:
    context.user_data["lang"] = "eng"
    main_menu(update, context)
    
# About Hotel
    
def about_hotel(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    # about_hotel_keyboard = [
    #     [InlineKeyboardButton(text = "Адрес" if context.user_data["lang"] == "rus" else "Address", callback_data=f"AboutHotel | address | {update.message.message_id}")],
    #     [InlineKeyboardButton(text = "Время заезда" if context.user_data["lang"] == "rus" else "Check-in time", callback_data=f"AboutHotel | checkinTime | {update.message.message_id}")],
    #     [InlineKeyboardButton(text = "Время выезда" if context.user_data["lang"] == "rus" else "Check-out time", callback_data=f"AboutHotel | checkoutTime | {update.message.message_id}")],
    #     [InlineKeyboardButton(text = "Услуги в отеле" if context.user_data["lang"] == "rus" else "Hotel services", callback_data=f"AboutHotel | hotelServices | {update.message.message_id}")],
    #     [InlineKeyboardButton(text = "Код вайфай" if context.user_data["lang"] == "rus" else "WIFI password", callback_data=f"AboutHotel | WIFIpass | {update.message.message_id}")],
    #     [InlineKeyboardButton(text = "Парковка" if context.user_data["lang"] == "rus" else "Parking", callback_data=f"AboutHotel | parking | {update.message.message_id}")],
    # ]
    
    
    about_hotel_keyboard = [
        [InlineKeyboardButton(text = "Адрес", callback_data="ADDRESS")],
        # [InlineKeyboardButton(text = "Время заезда", callback_data="CHECKIN_TIME"), InlineKeyboardButton(text = "Время выезда", callback_data="CHECKOUT_TIME")],
        [InlineKeyboardButton(text = "Заселение", callback_data="CHECKIN"), InlineKeyboardButton(text = "Номера", callback_data="ROOMS")],
        [InlineKeyboardButton(text = "Услуги в отеле", callback_data="HOTEL_SERVICES"), InlineKeyboardButton(text = "Отзывы", callback_data="REVIEWS")],
        # [InlineKeyboardButton(text = "Парковка", callback_data="PARKING")],
        [btn5]
    ]
    
    try:
        query.edit_message_text(text = "Информация о отеле", reply_markup = InlineKeyboardMarkup(about_hotel_keyboard))
    except:
        context.bot.delete_message(chat_id = query.message.chat_id, message_id = query.message.message_id)
        context.bot.send_message(chat_id = query.message.chat_id, text = "Информация о отеле", reply_markup = InlineKeyboardMarkup(about_hotel_keyboard))
    
    return LEVEL3_ABOUT_HOTEL

def about_hotel_address(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer("Секундочку")
    
    address_inline_keyboard = [
        [InlineKeyboardButton(text = "Как добраться до гостиницы", callback_data="AddressCallback")],
        # [InlineKeyboardButton(text = "Как добраться из вокзала", callback_data="AddressCallback | train_station")],
        # [InlineKeyboardButton(text = "Как добраться из автовокзала", callback_data="AddressCallback | car_station")],
        # [InlineKeyboardButton(text = "Такси в городе", callback_data="AddressCallback | taxi")],
        [btn5]
    ]
    
    if(context.user_data["lang"] == "rus"):
        photo = InputMediaPhoto(media=open('media/address/12.png', 'rb'))
        context.bot.delete_message(chat_id = query.message.chat_id, message_id = int(query.message.message_id))
        context.bot.send_photo(chat_id = query.message.chat_id, photo=open('media/address/12.png', 'rb'), caption=f"""
Наша гостиница находится в самом центре города, по адресу ул. Московская 262. Бизнес-центр "Айтур" 

Можешь кликнуть по ссылке и посмотреть на карте:
https://goo.gl/maps/xy6yySj7hjh42eLX6 
 
или в 2gis: 
https://go.2gis.com/nuncx 
                                """,
                                reply_markup=InlineKeyboardMarkup(address_inline_keyboard)) 
    
    return LEVEL4_ABOUT_HOTEL

def about_hotel_address_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    try:
        context.bot.delete_message(chat_id = query.message.chat_id, message_id = context.user_data['sticker_message_id'])
    except:
        pass

    callbackArr = (query.data).split(" | ")
    
    if(context.user_data["lang"] == "rus"):
        context.bot.delete_message(chat_id = query.message.chat_id, message_id = query.message.message_id)
        context.bot.send_message(chat_id = query.message.chat_id, text = f"""
Добро пожаловать в наш прелестный Бишкек. 
Надеюсь, что тебя не сильно трясло при посадке.""")
        context.bot.send_sticker(chat_id = query.message.chat_id, sticker = "CAACAgIAAxkBAAEfc3xkMbbysyo0eQwAAQOZNKpYMhEQdAsAAoEpAAKlOolJd66xMFKyB_svBA")
        context.bot.send_message(chat_id = query.message.chat_id, text = f"""
Из аэропорта Манас в нашу гостиницу можно доехать на Яндекс такси.
Посадка обойдётся от 59 сомов, а за километр заплатишь примерно от 10 до 13 сомов.
Заказать можно только в приложении.

Ну, а если у тебя проблемы с интернетом, то можешь позвонить. Например в такси "Удача", посадка от 69 сомов, за километр от 12 сомов. 

Номера телефонов:
0773061816
0552154000
короткий номер 5454
                                 """, reply_markup = InlineKeyboardMarkup([[btn5]]))
    
    return "LEVEL5_ABOUT_HOTEL_ADDRESS"


# def about_hotel_callback(update: Update, context: CallbackContext):
#     query = update.callback_query
#     callbackArr = (query.data).split(" | ")

#     query.answer()
    
#     address_inline_keyboard = [
#         [InlineKeyboardButton(text = "Как добраться из аэропорта", callback_data="AddressCallback | airport")],
#         [InlineKeyboardButton(text = "Как добраться из вокзала", callback_data="AddressCallback | train_station")],
#         [InlineKeyboardButton(text = "Как добраться из автовокзала", callback_data="AddressCallback | car_station")],
#         [InlineKeyboardButton(text = "Такси в городе", callback_data="AddressCallback | taxi")],
#     ]
    
#     if(context.user_data["lang"] == "rus"):
#         if(callbackArr[1] == "address"):
#             context.bot.send_message(chat_id = query.from_user.id, text = "Lorem ipsum", reply_markup = InlineKeyboardMarkup(address_inline_keyboard))
#             context.bot.delete_message(query.from_user.id, query.message.message_id)
#             return ADDRESS_CALLBACK
#         elif(callbackArr[1] == "checkinTime"):
#             context.bot.send_message(chat_id = query.from_user.id, text = "Lorem ipsum")
#         elif(callbackArr[1] == "checkoutTime"):
#             context.bot.send_message(chat_id = query.from_user.id, text = "Lorem ipsum")
#         elif(callbackArr[1] == "hotelServices"):
#             context.bot.send_message(chat_id = query.from_user.id, text = "Lorem ipsum")
#         elif(callbackArr[1] == "WIFIpass"):
#             context.bot.send_message(chat_id = query.from_user.id, text = "Lorem ipsum")
#         elif(callbackArr[1] == "parking"):
#             context.bot.send_message(chat_id = query.from_user.id, text = "Lorem ipsum")
                
        
                
#     elif(context.user_data["lang"] == "eng"):
#         match callbackArr[1]:
#             case "Address":
#                 context.bot.send_message(chat_id = query.from_user.id, text = "Lorem ipsum")
#             case "Check-in time":
#                 context.bot.send_message(chat_id = query.from_user.id, text = "Lorem ipsum")
#             case "Check-out time":
#                 context.bot.send_message(chat_id = query.from_user.id, text = "Lorem ipsum")
#             case "Hotel services":
#                 context.bot.send_message(chat_id = query.from_user.id, text = "Lorem ipsum")
#             case "WIFI password":
#                 context.bot.send_message(chat_id = query.from_user.id, text = "Lorem ipsum")
#             case "Parking":
#                 context.bot.send_message(chat_id = query.from_user.id, text = "Lorem ipsum")
    
#Checkin time
def about_hotel_checkin(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    query.edit_message_text(text = f"""
Заехать можно с 14:00.
Твоя кровать будет теплой и готовой к твоему приезду.

А выехать можно после 12:00.
                            """, reply_markup=InlineKeyboardMarkup(
        [[btn5]]
    ))
    
    return LEVEL4_ABOUT_HOTEL
    
# #Checkout time
# def checkout_time(update: Update, context: CallbackContext):
#     query = update.callback_query
#     query.answer()
    
#     query.edit_message_text(text = "Время выезда - **:**", reply_markup=InlineKeyboardMarkup(
#         [[btn5]]
#     ))
    
#     return LEVEL4_ABOUT_HOTEL

#About Hotel - Rooms
def about_hotel_rooms(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    keyboard = [
        [InlineKeyboardButton(text = "Премиальный номер", callback_data="PHOTOS_OF_ROOMS | deluxe")],
        [InlineKeyboardButton(text = "Двухместный номер с отдельными кроватями", callback_data="PHOTOS_OF_ROOMS | twins")],
        [InlineKeyboardButton(text = "Стандартный двухместный номер с большой кроватью", callback_data="PHOTOS_OF_ROOMS | double")],
        [InlineKeyboardButton(text = "Кровать в общем шестиместном номере", callback_data="PHOTOS_OF_ROOMS | shared")],
        [InlineKeyboardButton(text = "Все номера сразу", callback_data="PHOTOS_OF_ROOMS | all")],
        [btn5]
    ]
    
    query.edit_message_text(text = f"""
У нас ты можешь забронировать:
    🔵 Премиальный номер с одной большой двуспальной кроватью и собственной ванной комнатой.
    🔵 Двухместный номер с отдельными кроватями и общей ванной комнатой.
    🔵 Стандартный двухместный номер с одной кроватью и общей ванной комнатой.
    🔵 Кровать в общем шестиместном номере.

Мы придаем большое значение чистоте. Все постельное белье стирается при каждом новом проживании, а все поверхности и предметы часто дезинфицируются.
                            
Чтобы просмотреть фотографии номеров, нажми на кнопку ниже
                            """, reply_markup=InlineKeyboardMarkup(keyboard))
    
    return LEVEL4_ABOUT_HOTEL


def about_hotel_rooms_photos(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer("Секундочку")
    
    room_type = query.data.split(" | ")[1]
    
    print(room_type)
    
    shared = [
        InputMediaPhoto(media=open('media/room_types/shared/1.jpg', 'rb'), caption="Кровать в общем номере"),
        InputMediaPhoto(media=open('media/room_types/shared/2.jpg', 'rb')),
        InputMediaPhoto(media=open('media/room_types/shared/3.jpg', 'rb')),
        InputMediaPhoto(media=open('media/room_types/shared/4.jpg', 'rb')),
    ]
    
    double = [
        InputMediaPhoto(media=open('media/room_types/double/1.jpg', 'rb'), caption="Комната с большой кроватью и общей ванной комнатой"),
        InputMediaPhoto(media=open('media/room_types/double/2.jpg', 'rb')),
        InputMediaPhoto(media=open('media/room_types/double/3.jpg', 'rb'))
    ]
    
    twins = [
        InputMediaPhoto(media=open('media/room_types/twins/1.jpg', 'rb'), caption="Комната с двумя отдельными кроватями и общей ванной комнатой"),
        InputMediaPhoto(media=open('media/room_types/twins/2.jpg', 'rb')),
        InputMediaPhoto(media=open('media/room_types/twins/3.jpg', 'rb')),
    ]
    
    deluxe = [
        InputMediaPhoto(media=open('media/room_types/deluxe/1.jpg', 'rb'), caption="Улучшенный номер с собственной ванной комнатой"),
        InputMediaPhoto(media=open('media/room_types/deluxe/2.jpg', 'rb')),
        InputMediaPhoto(media=open('media/room_types/deluxe/3.jpg', 'rb')),
        InputMediaPhoto(media=open('media/room_types/deluxe/4.jpg', 'rb')),
        InputMediaPhoto(media=open('media/room_types/deluxe/5.jpg', 'rb')),
        InputMediaPhoto(media=open('media/room_types/deluxe/6.jpg', 'rb')),
    ]
    
    if room_type == "deluxe":
        context.bot.send_media_group(query.from_user.id, deluxe)
    elif room_type == "double":
        context.bot.send_media_group(query.from_user.id, double)
    elif room_type == "twins":
        context.bot.send_media_group(query.from_user.id, twins)
    elif room_type == "shared":
        context.bot.send_media_group(query.from_user.id, shared)
    elif room_type == "all":    
        context.bot.send_media_group(query.from_user.id, shared)
        context.bot.send_media_group(query.from_user.id, double)
        context.bot.send_media_group(query.from_user.id, twins)
        context.bot.send_media_group(query.from_user.id, deluxe)
    
    context.bot.send_message(chat_id = query.message.chat_id, text = "Вернуться назад", reply_markup = InlineKeyboardMarkup([[btn5]]))
    
    return "LEVEL5_ABOUT_HOTEL_PHOTOS"

#About Hotel - Hotel services
def hotel_services(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    keyboard = [
        [InlineKeyboardButton(text="Фотографии", callback_data="PHOTOS_OF_SERVICES"), InlineKeyboardButton(text="Пароль WI-FI", callback_data="WIFI_PASSWORD")],
        [InlineKeyboardButton(text="Заказать стирку", callback_data="ORDER_LAUNDRY"),
        InlineKeyboardButton(text="Заказать уборку в комнате", callback_data="ORDER_ROOM_CLEANING")],
        [btn5]
    ]
    
    query.edit_message_text(text = f"""
Мы предлагаем удобные простыни, подушки и чистые полотенца. 

Ботинки нельзя носить внутри гостиницы. Мы дадим тебе домашние тапочки.

В душе есть ароматный шампунь и мыло. Фен можно взять у администратора. 

Общая кухня оборудована микроволновкой, кофемашиной, холодильником, чайником и фильтром для воды.
Плитки на кухне нет, можешь заказать доставку еды. Доставляют обычно быстро от 20 до 60 минут. Или можешь прогуляться до ближайшего кафе, пешком можно добраться за 3-5 минут.
 
При необходимости, можешь заказать стирку вещей. Тебе их постирают, высушат и погладят. 
 
А ещё прямо в гостинице ты можешь обменять валюту и даже арендовать велосипед  … представляешь?! 
                            """, reply_markup=InlineKeyboardMarkup(
       keyboard
    ))
    
    return LEVEL4_ABOUT_HOTEL
    
#Wifi password
def about_hotel_wifi_password(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    # query.edit_message_text(text = "Wifi пароль", reply_markup=InlineKeyboardMarkup(
    #     [[btn5]]
    # ))
    
    query.edit_message_text(text = "тссс ... тот самый секретный пароль 123123123", reply_markup=InlineKeyboardMarkup(
        [[btn5]]
    ))
    
    return LEVEL5_ABOUT_HOTEL
    
def about_hotel_photos_of_services(update: Update, context: CallbackContext):

    query = update.callback_query
    query.answer("Загружаю...")
    
    query.delete_message()
    
    services = [
        InputMediaPhoto(media=open('media/services/service1.png', 'rb'), caption="Фотографии удобств нашего отеля"),
        InputMediaPhoto(media=open('media/services/service2.png', 'rb')),
        InputMediaPhoto(media=open('media/services/service3.png', 'rb')),
        InputMediaPhoto(media=open('media/services/service4.png', 'rb')),
        InputMediaPhoto(media=open('media/services/service5.png', 'rb')),
        InputMediaPhoto(media=open('media/services/service6.png', 'rb')),
        InputMediaPhoto(media=open('media/services/service7.jpg', 'rb')),
        InputMediaPhoto(media=open('media/services/service8.jpg', 'rb')),
        InputMediaPhoto(media=open('media/services/service9.jpg', 'rb')),
        InputMediaPhoto(media=open('media/services/service10.jpg', 'rb')),
    ]
        
    context.bot.send_media_group(query.from_user.id, services)
    
    context.bot.send_message(query.message.chat_id, text = "Вернуться назад", reply_markup = InlineKeyboardMarkup([[btn5]]))

    return LEVEL5_ABOUT_HOTEL
    
def about_hotel_order_laundry(update: Update, context):
    query = update.callback_query
    query.answer("В разработке")
    
def about_hotel_order_cleaning(update: Update, context):
    query = update.callback_query
    query.answer("В разработке")
    
    
#About Hotel - reviews
def about_hotel_review(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    reviews = [
        InputMediaPhoto(media=open('media/reviews/1.png', 'rb'), caption = "Отзывы настоящие, не поддельные :)"),
        InputMediaPhoto(media=open('media/reviews/2.png', 'rb')),
        InputMediaPhoto(media=open('media/reviews/3.png', 'rb')),
        
    ]
    
    keyboard = [
        [InlineKeyboardButton(text = "Просмотреть все отзывы", url = "https://www.booking.com/hotel/kg/eva-at-home-bishkek.ru.html#tab-reviews")],
        [btn5]
    ]
    
    query.delete_message() 
    
    context.bot.send_media_group(query.message.chat_id, reviews)
    
    context.bot.send_message(query.message.chat_id, text = "Ещё больше отзывов можешь посмотреть по ссылке. Жми на кнопку", reply_markup = InlineKeyboardMarkup(keyboard))
    
    return LEVEL4_ABOUT_HOTEL
    
    
#Parking
def parking(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    query.edit_message_text(text = "Паркинг", reply_markup=InlineKeyboardMarkup(
        [[btn5]]
    ))
    
    return LEVEL4_ABOUT_HOTEL

#events
def events(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    query.edit_message_text(text = "Мероприятия в городе", reply_markup = InlineKeyboardMarkup([
        [btn5]
    ]))
    
    return LEVEL3_EVENTS

#booking
def booking(update: Update, context: CallbackContext):
    
    is_query = False
    try:
        query = update.callback_query
        query.answer()
        is_query = True
        chat_id = update.callback_query.message.chat_id
        
    except:
        is_query = False
        chat_id = update.message.chat_id
    
    
    booking_inline_keyboard = [
        [InlineKeyboardButton(text = f"{number_to_emoji(1)} Забронировать номер", callback_data="BOOK")],
        [InlineKeyboardButton(text = f"{number_to_emoji(2)} Мое бронирование", callback_data="MY_BOOKING")],
        # [InlineKeyboardButton(text = f"Admin help", callback_data="ADMIN_HELP")],
        # [InlineKeyboardButton(text = f"Оплата", callback_data="GUEST_PAYMENT")],
        # [InlineKeyboardButton(text = f"Назначить комнату", callback_data="ASSIGN_ROOM")],
        [btn5]
    ]
    
    context.user_data['assign_room_final'] = {
        'next_state': "NEXT_BOOKING",
        'next_func': "ver2_api.booking(update, context)"
    }
    
    message = f"""
Я рада, что ты захотел забронировать, а может и уже забронировал номер в нашей гостинице. 

Выбери, пожалуйста, что ты хочешь сделать?

{number_to_emoji(1)} Забронировать номер

{number_to_emoji(2)} Узнать о своём бронировании, если ты уже забронировал номер.                         
                            """
    
    if is_query:
        query.edit_message_text(text = message, reply_markup = InlineKeyboardMarkup(booking_inline_keyboard))
    else:
        context.bot.send_message(chat_id, text = message, reply_markup = InlineKeyboardMarkup(booking_inline_keyboard))
        
    return LEVEL3_BOOKING

def verify_options(update: Update, context: CallbackContext):
    if(update.callback_query.data == str("OTHER_PHONE")):
        if "phone_number" in context.user_data.keys(): del context.user_data["phone_number"]
        try:
            del context.user_data["booking"]
        except:
            pass
        
    if "phone_number" not in context.user_data.keys():
        query = update.callback_query
        query.answer()
        
        keyboard = [
            [InlineKeyboardButton(text = "Подтвердить через Telegram", callback_data="VERIFY_PHONE")],
            [InlineKeyboardButton(text = "Поиск по номеру телефона", callback_data="VERIFY_JUST_NUMBER")],
            [InlineKeyboardButton(text = "Поиск по номеру бронирования", callback_data="VERIFY_JUST_RCODE")],
            # [InlineKeyboardButton(text = "Подтвердить по почте", callback_data="VERIFY_EMAIL")],
            # [InlineKeyboardButton(text = "Тестовый вход", callback_data="VERIFY_TEST")],
            [btn5]
        ]
        
        message = f"""
Отлично, мне нужно подтвердить твою личность, чтобы получить доступ к твоим бронированиям.
Ты можешь подтвердить через Telegram, если бронирование сделано на тот же номер телефона, как и твой Telegram.
Или же просто ввести номер телефона или бронирования
                                """
        
        query.edit_message_text(text=message, reply_markup=InlineKeyboardMarkup(keyboard))

        return LEVEL1_VERIFY
    else:
        # booking_contact(update, context)
        # update.callback_query.edit_message_reply_markup(reply_markup=None)
        return my_booking_options(update, context)
       
#Тестовый вход
def verify_test(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    query.edit_message_text(text="Напиши номер телефона, на который был забронирован номер. Обязательно в международном формате (+ххххххххххх)!")
    
    return "LEVEL2_VERIFY_TEST"

def verify_test_get_phone(update: Update, context: CallbackContext):
    phone_number = update.message.text
    context.user_data["phone_number"] = phone_number
    return my_booking_options(update, context)

#Номер телефона без подтверждения
def verify_just_phone_number(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    query.edit_message_text(text="Напиши номер телефона, на который был забронирован номер. Обязательно в международном формате (+ххххххххххх)!")

    return "LEVEL2_JUST_PHONENUMBER"

def verify_just_phone_number_incorrect_format(update: Update, context: CallbackContext):
    context.bot.send_message(update.message.chat_id, text = f"Вы ввели некорректный номер телефона, попробуйте снова. В формате: +xxxxxxxxxxx (начинается с '+' и максимум 15 цифр)")
    return "LEVEL2_JUST_PHONENUMBER"


def verify_just_phone_number_get_phone(update: Update, context: CallbackContext):
    phone_number = update.message.text
    context.bot.send_message(chat_id = update.message.chat_id, text = "Ищу ваше бронирование...")
    
    bookings = firebase.getBookingByPhoneNumber(phone_number)
    
    if(bookings is None or len(bookings) == 0):
        keyboard = [
            [InlineKeyboardButton(text = "❌ Отменить и вернуться назад", callback_data="BACK")]
        ]
        context.bot.send_message(chat_id = update.message.chat_id, text = "Я не нашла ваше бронирование, проверьте номер телефона и отправьте еще раз или вернитесь назад", reply_markup = InlineKeyboardMarkup(keyboard))
        return "LEVEL2_JUST_PHONENUMBER"
    else:
        context.user_data["phone_number"] = phone_number
        return my_booking_options(update, context)
    
#Номер бронирования без подтверждения
def verify_just_rcode(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    query.edit_message_text(text="Введи номер бронирования.")

    return "LEVEL2_JUST_RCODE"

def verify_just_rcode_incorrect_format(update: Update, context: CallbackContext):
    context.bot.send_message(update.message.chat_id, text = f"Вы ввели некорректный номер бронирования, попробуйте снова. Номер бронирования зачастую представлен в виде числа из 10 цифр")
    return "LEVEL2_JUST_RCODE"


def verify_just_rcode_get_rcode(update: Update, context: CallbackContext):
    rcode = update.message.text
    context.bot.send_message(chat_id = update.message.chat_id, text = "Ищу ваше бронирование...")
    
    bookings = firebase.getBookingByRcode(rcode)
    
    if(bookings is None or len(bookings) == 0):
        keyboard = [
            [InlineKeyboardButton(text = "❌ Отменить и вернуться назад", callback_data="BACK")]
        ]
        context.bot.send_message(chat_id = update.message.chat_id, text = "Я не нашла ваше бронирование, проверьте номер бронирования и отправьте еще раз или вернитесь назад", reply_markup = InlineKeyboardMarkup(keyboard))
        return "LEVEL2_JUST_RCODE"
    else:
        context.user_data['bookings'] = bookings
        return my_booking_options(update, context, rcode = True)
    
def verify_email(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    query.edit_message_text(text="Напиши номер телефона, на который был забронирован номер. Обязательно в международном формате (+ххххххххххх)!")
    
    return LEVEL2_VERIFY

def get_phone_number_and_send_email(update: Update, context: CallbackContext):
    phone_number = update.message.text
    user = firebase.getUserByPhoneNumber(phone_number)
    if user is not None:
        email = user['email']
        generated_code = sendemail.send_email(email)
        context.user_data['generated_code'] = generated_code
        context.user_data['not_verified_phone_number'] = user['phone_number']
        
        context.bot.send_message(update.message.from_user.id, text="На почту, на которую был забронирован номер должен прийти код подтверждения. Введи его")
        
        return LEVEL3_VERIFY
    else:
        context.bot.send_message(update.message.from_user.id, text="Мы не нашли бронирование на ваш номер, попробуйте еще раз")
        return LEVEL2_VERIFY

def get_code_from_user(update: Update, context: CallbackContext):
    code_from_user = update.message.text
    # while(code_from_user != context.user_data['generated_code']):
    #     context.bot.send_message(update.message.from_user.id, text="Вы неправильно ввели код подтверждения, попробуйте еще раз")
    # context.bot.send_message(update.message.from_user.id, text="Все правильно!")
    
    if(code_from_user == context.user_data['generated_code']):
        messageToDelete = context.bot.send_message(update.message.from_user.id, text="Все правильно!")
        time.sleep(2)
        context.bot.delete_message(update.message.from_user.id, messageToDelete.message_id)
        context.user_data["phone_number"] = context.user_data['not_verified_phone_number']

    else:
        context.bot.send_message(update.message.from_user.id, text="Вы неправильно ввели код подтверждения, попробуйте еще раз")
        return LEVEL3_VERIFY
    # booking_contact(update, context)
    return my_booking_options(update, context)

def my_booking_options(update: Update, context: CallbackContext, **kwargs):
    
    if "set_telegram_details" not in context.user_data.keys() or context.user_data['set_telegram_details'] != True:
        try:
            user = update.message.from_user
        except:
            user = update.callback_query.from_user
        firebase.setTelegramDetailsToUser(context.user_data["phone_number"], user.username, user.id)
        context.user_data['set_telegram_details'] = True
    
    try:
        callback = update.callback_query.data
        if callback == str("OTHER_BOOKING"):
            del context.user_data["booking"]
    except:
        pass
        
    if "rcode" in kwargs.keys() and kwargs['rcode'] == True:
        bookings = context.user_data['bookings']
        context.user_data['login_with_rcode'] = True
    else:
        bookings = firebase.getBookingByPhoneNumber(context.user_data["phone_number"])
        
    for booking in bookings:
        firebase.approveStatusFromGuestBookingID(booking['user_id'], booking['id'], "connection", True)
    
    bookings_list = [
        [],
        [InlineKeyboardButton(text = "Поискать для другого номера", callback_data="OTHER_PHONE")]
    ]
    
    # print(context.user_data["booking"])
    
    if len(bookings) == 1:
        if "send_message" not in kwargs.keys():
            return my_booking_selected_one(update, context)
        else:
            return my_booking_selected_one(update, context, send_message = True)
        
    if "booking" in context.user_data.keys():
        if "send_message" not in kwargs.keys():
            return my_booking_selected(update, context)
        else:
            return my_booking_selected(update, context, send_message = True)
    
    message = f""
    for i in range(len(bookings)):
        # print(i)
        bookings_list[0].append(InlineKeyboardButton(text = (i+1), callback_data=f"SELECTED_BOOKING | {i}"))
        message += f"""Бронирование №{i+1}
Дата заселения: {bookings[i]["checkin_date"].strftime("%d/%m/%Y")}
Дата выселения: {bookings[i]["checkout_date"].strftime("%d/%m/%Y")}
Ваша комната: {bookings[i]["room_number"]}
        
"""
 
    try:
        query = update.callback_query
        query.answer()
        query.edit_message_text(text = f"""
Я нашла несколько бронирований на ваше имя. Выберите необходимое бронирование:

{message}
""", reply_markup = InlineKeyboardMarkup(bookings_list))
    except:
        context.bot.send_message(context.user_data["chat_id"], text = f"""
Я нашла несколько бронирований на ваше имя. Выберите необходимое бронирование:

{message}
""", reply_markup = InlineKeyboardMarkup(bookings_list))
        
    return LEVEL34_SELECT_BOOKING


def my_booking_selected_one(update: Update, context:CallbackContext, **kwargs):
    booking_options = [
        [InlineKeyboardButton(text = "Подробнее о бронировании", callback_data="LEARN_MORE")],
        [InlineKeyboardButton(text = "Изменить бронирование", callback_data="EDIT")],
        [InlineKeyboardButton(text = "Зарегистрироваться", callback_data="REGISTER"),
         InlineKeyboardButton(text = "Выезд", callback_data="CHECKOUT")],
        [InlineKeyboardButton(text = "Оплата", callback_data="PAYMENT")],
        [InlineKeyboardButton(text = "Поискать для другого номера", callback_data="OTHER_PHONE")],
        [btn5]
    ]
    
        
    if "login_with_rcode" in context.user_data.keys() and context.user_data['login_with_rcode'] == True:
        bookings = context.user_data['bookings']
        del context.user_data['login_with_rcode']
    else:
        bookings = firebase.getBookingByPhoneNumber(context.user_data["phone_number"])
    
    
    context.user_data["booking"] = bookings[0]
    booking = bookings[0]
    context.user_data['selected_booking'] = {"user_id": booking['user_id'], "booking_id": booking['id']}

    
    if type(booking['room_number']) == list:
        room_number = ""
        for room_type in booking['room_number']:
            room_number += f"{room_type} "
    
    message = f"""
Найдено бронирование на ваше имя!
Дата заселения: {booking["checkin_date"].strftime("%d/%m/%Y")}
Дата выселения: {booking["checkout_date"].strftime("%d/%m/%Y")}
Ваша комната: {room_number if room_number is not None else booking['room_number'] }
Тип комнаты: {" ".join(booking['room_type'])}
Стоимость: {booking['price']} {booking['currency']} | {convert_currency(booking['currency'], "KGS", booking['price'])} | {convert_currency(booking['currency'], "RUB", booking['price'])}
"""
    
    today = datetime.datetime.now().date()
    status = firebase.getStatusFromGuestBookingID(booking['user_id'], booking['id'])
    if status['approve_booking'] == False and booking['checkin_date'].date() >= today:
        callbackDict = {"callback": "APPROVE_BOOKING", "user_id": booking['user_id'], "booking_id": booking['id']}
        
        approve_booking = [InlineKeyboardButton(text = "Подтвердить бронирование", callback_data=callbackDict)]
        message += "\nВсе еще собираетесь приехать в наш отель? Подтвердите бронирование"
        booking_options.insert(0, approve_booking)
    
    if "send_message" in kwargs.keys():
        
        context.bot.send_message(context.user_data["chat_id"], text = message, reply_markup = InlineKeyboardMarkup(booking_options))
        return LEVEL34_BOOKING
        
    try:
        query = update.callback_query
        query.answer()
        query.edit_message_text(text = message, reply_markup = InlineKeyboardMarkup(booking_options))
    except:
        context.bot.send_message(context.user_data["chat_id"], text = message, reply_markup = InlineKeyboardMarkup(booking_options))

    # print("works!")
    return LEVEL34_BOOKING

def my_booking_selected(update: Update, context:CallbackContext, **kwargs):
    booking_options = [
        [InlineKeyboardButton(text = "Подробнее о бронировании", callback_data="LEARN_MORE")],
        [InlineKeyboardButton(text = "Изменить бронирование", callback_data="EDIT")],
        [InlineKeyboardButton(text = "Зарегистрироваться", callback_data="REGISTER"),
         InlineKeyboardButton(text = "Выезд", callback_data="CHECKOUT")],
        [InlineKeyboardButton(text = "Оплата", callback_data="PAYMENT")],
        
        [InlineKeyboardButton(text = "Выбрать другое бронирование", callback_data="OTHER_BOOKING")],
        [btn5]
    ]
    
    if "booking" in context.user_data.keys():
        booking = context.user_data['booking']
    else:
        query = update.callback_query
        query.answer()
        callbackArr = query.data.split(" | ")
        # print(callbackArr)
        if "login_with_rcode" in context.user_data.keys() and context.user_data['login_with_rcode'] == True:
            bookings = context.user_data['bookings']
            del context.user_data['login_with_rcode']
        else:
            bookings = firebase.getBookingByPhoneNumber(context.user_data["phone_number"])
        
        context.user_data["booking"] = bookings[int(callbackArr[1])]
        booking = bookings[int(callbackArr[1])]
        context.user_data['selected_booking'] = {"user_id": booking['user_id'], "booking_id": booking['id']}

        
    if type(booking['room_number']) == list:
        room_number = ""
        for room_type in booking['room_number']:
            room_number += f"{room_type} "
            
        
    message = f"""
Найдено бронирование на ваше имя!
Дата заселения: {booking["checkin_date"].strftime("%d/%m/%Y")}
Дата выселения: {booking["checkout_date"].strftime("%d/%m/%Y")}
Ваша комната: {room_number if room_number is not None else booking['room_number'] }
Тип комнаты: {" ".join(booking['room_type'])}
Стоимость: {booking['price']} {booking['currency']} | {convert_currency(booking['currency'], "KGS", booking['price'])} | {convert_currency(booking['currency'], "RUB", booking['price'])}
"""
    
    status = firebase.getStatusFromGuestBookingID(booking['user_id'], booking['id'])
    
    today = datetime.datetime.now().date()
    
    if status['approve_booking'] == False and booking['checkin_date'].date() >= today:
        callbackDict = {"callback": "APPROVE_BOOKING", "user_id": booking['user_id'], "booking_id": booking['id']}
        
        approve_booking = [InlineKeyboardButton(text = "Подтвердить бронирование", callback_data=callbackDict)]
        message += "\nВсе еще собираетесь приехать в наш отель? Подтвердите бронирование"
        booking_options.insert(0, approve_booking)

    if "send_message" in kwargs.keys():
        context.bot.send_message(context.user_data["chat_id"], text = message, reply_markup = InlineKeyboardMarkup(booking_options))
        return LEVEL34_BOOKING
 
    try:
        query = update.callback_query
        query.answer()
        query.edit_message_text(text = message, reply_markup = InlineKeyboardMarkup(booking_options))
    except:
        context.bot.send_message(context.user_data["chat_id"], text = message, reply_markup = InlineKeyboardMarkup(booking_options))

    # print("works!")
    return LEVEL34_BOOKING

def approve_booking_status(update: Update, context: CallbackContext):
    query = update.callback_query
    callback = query.data
    
    booking_options = [
        [InlineKeyboardButton(text = "Подробнее о бронировании", callback_data="LEARN_MORE")],
        [InlineKeyboardButton(text = "Изменить бронирование", callback_data="EDIT")],
        [InlineKeyboardButton(text = "Выезд", callback_data="CHECKOUT"),
        InlineKeyboardButton(text = "Оплата", callback_data="PAYMENT")],
        [InlineKeyboardButton(text = "Зарегистрироваться", callback_data="REGISTER")],
        [InlineKeyboardButton(text = "Поискать для другого номера", callback_data="OTHER_PHONE")],
        [btn5]
    ]
    
    firebase.approveStatusFromGuestBookingID(callback['user_id'], callback['booking_id'], 'approve_booking', True)
    query.answer(text="Вы подтвердили бронирование")
    
    message = query.message.text
    message = message.replace("\nВсе еще собираетесь приехать в наш отель? Подтвердите бронирование", "")
    query.edit_message_text(text=message, reply_markup=InlineKeyboardMarkup(booking_options))
    # query.edit_message_reply_markup(InlineKeyboardMarkup(booking_options))
    

def my_booking_learn_more(update: Update, context: CallbackContext):
    
    query = update.callback_query
    query.answer()
    
    query.edit_message_text(text = f"""Адрес нашего отеля:
что то что то
                            """)
    
    return my_booking_options(update, context, send_message = True)

def verify_phone(update: Update, context: CallbackContext):
    
    query = update.callback_query
    query.answer()
    
    if "phone_number" not in context.user_data.keys():
        
        keyboard = [KeyboardButton(text="Подтвердите свой номер", request_contact=True)]
        
        context.bot.send_message(chat_id = query.from_user.id,text="Нам необходимо подтвердить ваш номер телефона, чтобы получить доступ к бронированиям", 
                                reply_markup=ReplyKeyboardMarkup(keyboard=[keyboard], resize_keyboard=True, one_time_keyboard=True))
        
        return LEVEL4_BOOKING
    
    else:
        booking_contact(update, context)
        return LEVEL4_BOOKING
    
def request_contact_again(update, context):
    
    
    keyboard = [KeyboardButton(text="Подтвердите свой номер", request_contact=True)]
    
    context.bot.send_message(chat_id = context.user_data["chat_id"],text="Нам необходимо подтвердить ваш номер телефона, чтобы получить доступ к бронированиям", 
                            reply_markup=ReplyKeyboardMarkup(keyboard=[keyboard], resize_keyboard=True, one_time_keyboard=True))
    
    return LEVEL4_BOOKING


def verified_with_contact(update: Update, context: CallbackContext):
    if "phone_number" not in context.user_data.keys():
        #Если номера телефона еще нет в user_data
        phone_number_from_bot = update.message.contact.phone_number
        arr = [c for c in phone_number_from_bot]
        # print(arr)
        if arr[0] != "+":
            phone_number_from_bot = '+'+phone_number_from_bot
            # print(phone_number_from_bot)
            
        
        phone_number = phone_number_from_bot
        get_booking = firebase.getBookingByPhoneNumber(phone_number)
        
        if get_booking is None:
            context.bot.send_message(chat_id = context.user_data["chat_id"], text = "Я не нашла бронирование на твой номер, попробуйте еще раз")
            return request_contact_again(update, context)

        
        booking = get_booking[0]
        if booking is not None:
            #Если бронирование найдено
            # print("Бронирование найдено")
            context.user_data["phone_number"] = phone_number_from_bot
            # context.user_data['booking'] = booking
            return my_booking_options(update, context)
        else:
            #Если бронирование не найдено
            context.bot.send_message(chat_id = context.user_data["chat_id"], text = "Я не нашла бронирование на твой номер, попробуйте еще раз")
            return request_contact_again(update, context)
    
    else:
        phone_number = context.user_data["phone_number"]
        
        get_booking = firebase.getBookingByPhoneNumber(phone_number)
        
        
        booking = get_booking[0]
        
        if get_booking is None:
            context.bot.send_message(chat_id = context.user_data["chat_id"], text = "Я не нашла бронирование на твой номер, попробуйте еще раз")
            return request_contact_again(update, context)
        
        if booking is not None:
            # print("Бронирование найдено")
            # context.user_data['booking'] = booking
            return my_booking_options(update, context)
        else:
            try:
                update.callback_query.edit_message_text(text = "Я не нашла бронирование на твой номер, попробуйте еще раз")
            except:
                context.bot.send_message(chat_id = context.user_data["chat_id"], text = "Я не нашла бронирование на твой номер, попробуйте еще раз")
                
            return request_contact_again(update, context)

#Checkin

def booking_checkin(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer("Секундочку")
        
    booking = context.user_data['booking']
    
    status = firebase.getStatusFromGuestBookingID(booking['user_id'], booking['id'])
    
    # datetime.datetime.today().date()
    
    if status['checked_in'] == False:
    
        # datetime.datetime.today().date()
        if(booking["checkin_date"].date() != datetime.datetime.today().date()):
            query.edit_message_text(text = "Извините, но регистрация возможна только в день заезда")
            del context.user_data['booking']
            time.sleep(1.5)
            return checkin_main_menu(update, context)
            
        if type(booking['room_number']) == list:
            room_number = ""
            for room_type in booking['room_number']:
                room_number += f"{room_type} "    
    
        context.bot.send_message(query.message.chat_id, f"""
Очень серьёзно сейчас, хорошо? Я понимаю твоё волнение, но твои данные будут надежно защищены. 

Фотография паспорта нужна для того, чтобы уже в гостинице убедиться, что приехал ты, а не кто-то, кто прикрылся твоим именем.

Отправь фотографию своего паспорта, но только проследи, чтобы фотография была без бликов. Нам нужна страничка, с твоим лицом. 

Спасибо за понимание!
                                """)
        
        return "LEVEL4_BOOKING_CHECKIN"
    
    else:
        context.bot.send_message(query.message.chat_id, "Вы уже зарегистрированы")
        # time.sleep(0.5)
        # return my_booking_selected(update, context)

def booking_checkin_get_passport_photo(update: Update, context: CallbackContext):
    photo = update.message.photo
    
    booking = context.user_data['booking']
    
    filename = f"passport_{booking['user_id']}_{booking['id']}.jpg"
    
    newFile = update.message.effective_attachment[-1].get_file()
    
    directory = "media/passports"
    os.makedirs(directory, exist_ok=True)
    
    newFile.download(custom_path = f"./media/passports/{filename}")

    public_url = firebase.upload_photo_to_cloud_storage(f"{filename}")
    
    firebase.put_link_passport_to_booking(booking['user_id'], booking['id'], f"{public_url}")
    
    keyboard = [
        [btn5]
    ]
    
    #Присвоение номера   
    
    context.bot.send_message(update.message.chat_id, text = "Отлично, ищу вам номер")
    
                
    assigned_room_number = firebase.assignGuestToRoom(booking, booking['room_type_id'][0])
        
    # context.user_data["booking"]['checkin_date'] = datetime.datetime.strptime(booking['checkin_date'], "%Y-%m-%d")
    # context.user_data["booking"]['checkout_date'] = datetime.datetime.strptime(booking['checkout_date'], "%Y-%m-%d")

    user_id, booking_id = context.user_data['selected_booking']['user_id'], context.user_data['selected_booking']['booking_id']
    booking = firebase.getBookingById(user_id, booking_id)['booking']
    booking['checkin_date'] = datetime.datetime.strptime(booking['checkin_date'], "%d-%m-%Y")
    booking['checkout_date'] = datetime.datetime.strptime(booking['checkout_date'], "%d-%m-%Y")

    context.user_data["booking"] = booking
    
    
    if(assigned_room_number is None):
        message = "Почему то все комнаты заняты, сообщите администратору"
        context.bot.send_message(update.message.chat_id, text = message, reply_markup = InlineKeyboardMarkup(keyboard))
        
        return "LEVEL4_BOOKING_CHECKIN"
    else:
        return my_booking_selected(update, context)
#         room_number = booking['room_number']
#         message = f"""
# Ваше бронирование:

# Дата заселения: {booking["checkin_date"].strftime("%d/%m/%Y")}
# Дата выселения: {booking["checkout_date"].strftime("%d/%m/%Y")}
# Ваша комната: {room_number}
#     """

    
    
    
    # context.bot.send_message(update.message.chat_id, text = "Отлично, давай проверим оплату...")
    # time.sleep(1)
    
    # keyboard = [
    #     [InlineKeyboardButton(text="Перевод 📱", callback_data="PEREVOD")],
    #     [InlineKeyboardButton(text="Наличные 💵", callback_data="CASH")],
        
    # ]
    
    # if(booking['channel_name'] == "Airbnb"):
    #     context.bot.send_message(update.message.chat_id, text = "Я вижу, что ты оплатил")
    # else:
    #     context.bot.send_message(update.message.chat_id, text = "Что-то я не вижу оплаты, какой способ оплаты тебе удобнее?", reply_markup = InlineKeyboardMarkup(keyboard))

   

def booking_contact(update: Update, context: CallbackContext):
    # print("booking contact")

    phone_number = context.user_data["phone_number"]
    
    booking = context.user_data["booking"]
    
    channel_name = booking['channel_name']
    
    if booking is not None:
        # print("Бронирование найдено")
        booking_found_keyboard = [
            [InlineKeyboardButton(text="Отменить бронирование", callback_data="CANCEL_BOOKING")],
            # [InlineKeyboardButton(text="Изменить даты", callback_data="EDIT_DATES")],
            [InlineKeyboardButton(text="Изменить номер", callback_data="CHANGE_ROOM")],
            [btn5]
        ]
        
        if type(booking['room_number']) == list:
            room_number = ""
            for room_type in booking['room_number']:
                room_number += f"{room_type} "
                
        if(channel_name != "WooDoo"):
            try:
                update.callback_query.edit_message_text(text = f"К сожалению, мы не можем изменять бронирования с {channel_name} напрямую :(",
                                                    reply_markup=InlineKeyboardMarkup([[btn5]]))
            except:
                context.bot.send_message(update.message.chat_id, text = f"К сожалению, мы не можем изменять бронирования с {channel_name} напрямую :(",
                                                        reply_markup=InlineKeyboardMarkup([[btn5]]))
        else:      
            try:
                update.callback_query.edit_message_text(text = f"""
Найдено бронирование на ваше имя!
Дата заселения: {booking["checkin_date"].strftime("%d/%m/%Y")}
Дата выселения: {booking["checkout_date"].strftime("%d/%m/%Y")}
Ваша комната: {room_number if room_number is not None else booking['room_number'] }
""", reply_markup = InlineKeyboardMarkup(booking_found_keyboard))
            except:
                context.bot.send_message(update.message.from_user.id, text = f"""
Найдено бронирование на ваше имя!
Дата заселения: {booking["checkin_date"].strftime("%d/%m/%Y")}
Дата выселения: {booking["checkout_date"].strftime("%d/%m/%Y")}
Ваша комната: {room_number if room_number is not None else booking['room_number'] }
""", reply_markup = InlineKeyboardMarkup(booking_found_keyboard))

        return LEVEL5_BOOKING

    
def cancel_booking(update: Update, context: CallbackContext):
    
    query = update.callback_query
    query.answer()
    
    keyboard = [
        [InlineKeyboardButton(text="Подтверждаю", callback_data="CONFIRM_CANCEL")],
        [btn5]
    ]
    
    query.edit_message_text(text=f"""
Поменялись планы? Не беда. 

Подтверди, пожалуйста, что ты точно отменяшь бронирование.

Не волнуйся, отмена бронирования у нас бесплатная.
""", reply_markup=InlineKeyboardMarkup(keyboard))
    
    
    return LEVEL6_BOOKING

def approve_cancel_booking(update: Update, context: CallbackContext):
    query = update.callback_query
    # query.answer("Отменяю бронирование...")
    
    rcode = context.user_data['booking']['reservation_code']
    print(rcode)
    res = wubook.cancel_booking(rcode)
    
    time.sleep(1)
    
    if res:
        query.answer("Я отменила бронирование. Надеюсь, что мы ещё свидимся. Пока.")
        del context.user_data["phone_number"]
        del context.user_data["booking"]
        time.sleep(1)
        return main_menu(update, context)
    else:
        query.answer("Произошла ошибка")
    
 #Edit dates
    
def edit_dates(update: Update, context: CallbackContext):
    
    
    query = update.callback_query
    query.answer()
    
    keyboard = [
        [btn5]
    ]
    
    booking = context.user_data["booking"]
    
    edit_dates_requests = firebase.getBookingRequests(context.user_data['phone_number'], booking['id'], "edit_dates")
    
    if len(edit_dates_requests) == 0 or edit_dates_requests[0]['approved'] == True:
        query.edit_message_text(text = f"""
Текущие даты:
    Дата заселения: {booking["checkin_date"].strftime("%d/%m/%Y")}
    Дата выселения: {booking["checkout_date"].strftime("%d/%m/%Y")}
                                """)

        context.bot.send_message(context.user_data["chat_id"], text="Новая дата заезда? Или введите старую дату, чтобы оставить как есть. (В формате ДД/ММ/ГГГГ)", 
                                 reply_markup = telegramcalendar.create_calendar())
    
        return LEVEL6_BOOKING
    elif edit_dates_requests[0]['approved'] == False:
        query.edit_message_text(text = """
Мы уже получили вашу заявку. Вы получите уведомление о вашей заявке!
                                """)
        return booking_contact(update, context)


def edit_checkin_dates(update: Update, context: CallbackContext):
    selected,date = telegramcalendar.process_calendar_selection(update, context)
    if selected:
        context.bot.send_message(chat_id=update.callback_query.from_user.id,
                        text=(date.strftime("%d/%m/%Y")),
                        reply_markup=ReplyKeyboardRemove())
    
        context.user_data["new_checkin_date"] = date
        context.bot.send_message(update.callback_query.message.chat_id, text="Новая дата выезда? Или введите старую дату, чтобы оставить как есть. (В формате ДД/ММ/ГГГГ)", reply_markup = telegramcalendar.create_calendar())
        return LEVEL7_CHECKOUT


def edit_checkout_dates(update: Update, context: CallbackContext):
    selected,date = telegramcalendar.process_calendar_selection(update, context)
    if selected:
        
        if(context.user_data["new_checkin_date"] > date):
            context.bot.send_message(update.callback_query.from_user.id, 
                                     text = "Дата выселения раньше чем дата заселения, выберите еще раз")
            return edit_dates(update, context)
        
        context.bot.send_message(chat_id=update.callback_query.from_user.id,
                        text=(date.strftime("%d/%m/%Y")),
                        reply_markup=ReplyKeyboardRemove())
        
        
    
        # context.user_data["new_checkout_date"] = datetime.datetime.strptime(update.message.text, "%d/%m/%Y") 
        context.user_data["new_checkout_date"] = date 

        context.bot.send_message(update.callback_query.from_user.id, text = f"""
Я уведомила администратора, что вы хотите изменить даты в вашем бронировании. Вы получите уведомление, когда бронь будет изменена.
Вы выбрали:
    Дата и время заезда: {context.user_data['new_checkin_date'].strftime("%d/%m/%Y")}
    Дата выезда: {context.user_data['new_checkout_date'].strftime("%d/%m/%Y")}
                                """)
        
        user = update.callback_query.from_user
        booking = context.user_data["booking"]
        user_from_booking = firebase.getUserByPhoneNumber(context.user_data["phone_number"])
        
        new_dates = {}
        new_dates["checkin_date"] = f"{context.user_data['new_checkin_date'].strftime('%Y-%m-%d')}"
        new_dates["checkout_date"] = context.user_data['new_checkout_date'].strftime('%Y-%m-%d')
        
        firebase.addEditDatesBookingRequest(context.user_data["phone_number"], booking, new_dates)
        context.user_data['new_dates_for_edit'] = new_dates 
        
        admin_keyboard = [
            [InlineKeyboardButton(text="Подтвердить изменение даты бронирования", callback_data=f"ADMIN_EDIT_DATES_BOOKING | {context.user_data['chat_id']}")]
        ]
        
        
        for adminID in admin_id_arr:
            context.bot.send_message(chat_id = adminID, text = f"""
Поступила заявка на изменение даты:
    Логин в Telegram: @{user.username}
    Имя и Фамилия: {user_from_booking['name']} {user_from_booking['lastname']}
    Номер телефона: {user_from_booking["phone_number"]}
    Старая дата заселения: {booking["checkin_date"].strftime("%d/%m/%Y %H:%M")}
    Старая дата выселения: {booking["checkout_date"].strftime("%d/%m/%Y")}
    Комната: {booking["room_number"]}
    ____________________________________
    Новая дата заселения: {context.user_data['new_checkin_date'].strftime("%d/%m/%Y")}
    Новая дата выселения: {context.user_data['new_checkout_date'].strftime("%d/%m/%Y")}
                            """, reply_markup = InlineKeyboardMarkup(admin_keyboard))
        
        return booking_contact(update, context)

#Change room

def change_room(update: Update, context: CallbackContext):
    
    query = update.callback_query
    query.answer()
    
    keyboard = [
        [InlineKeyboardButton(text="Посмотреть фотографии всех номеров", callback_data="PHOTOS_OF_ROOMS")],
        [btn5]
    ]
    
    dfrom = context.user_data['booking']["checkin_date"]
    dto = context.user_data['booking']["checkout_date"]
    
    number_of_people = context.user_data['booking']['adults']
    
    avail = wubook.get_availability_for_all(dfrom, dto)
    i = 0
    for room_name in avail:
        if (room_name != "shared" or number_of_people == 1) and avail[room_name] > 0:
            keyboard.insert(i, 
                [InlineKeyboardButton(text=room_names_dict[room_name]['name'], callback_data=f"SELECT_ROOM | {room_names_dict[room_name]['callback']}")]
                            )
            i+=1
        if room_name == "shared" and number_of_people > 1 and avail[room_name] >= number_of_people:
            keyboard.insert(i, 
                [InlineKeyboardButton(text=room_names_dict[room_name]['name'], callback_data=f"SELECT_ROOM | {room_names_dict[room_name]['callback']}")]
                            )
            i+=1
    
    message = f"Перед вами все доступные номера на ваши даты. Какой номер вы хотите?"
    
    if context.user_data["booking"]['adults'] > 1:
        message += f"""

<b>Имейте ввиде, если вы выберите 'Кровать в общем номере', то вы забронируете сразу {number_of_people} номера</b>
Так как у вас в бронировании {number_of_people} гостя        
"""
    
    query.edit_message_text(text = message, parse_mode=ParseMode.HTML, reply_markup = InlineKeyboardMarkup(keyboard))
    
    
    return LEVEL6_BOOKING
    
def photos_of_rooms(update: Update, context: CallbackContext):
    
    query = update.callback_query
    query.answer()
    
    query.delete_message()
    
    shared = [
        InputMediaPhoto(media=open('media/room_types/shared/1.jpg', 'rb'), caption="Кровать в общем номере"),
        InputMediaPhoto(media=open('media/room_types/shared/2.jpg', 'rb')),
        InputMediaPhoto(media=open('media/room_types/shared/3.jpg', 'rb')),
        InputMediaPhoto(media=open('media/room_types/shared/4.jpg', 'rb')),
    ]
    
    double = [
        InputMediaPhoto(media=open('media/room_types/double/1.jpg', 'rb'), caption="Комната с большой кроватью и общей ванной комнатой"),
        InputMediaPhoto(media=open('media/room_types/double/2.jpg', 'rb')),
        InputMediaPhoto(media=open('media/room_types/double/3.jpg', 'rb'))
    ]
    
    twins = [
        InputMediaPhoto(media=open('media/room_types/twins/1.jpg', 'rb'), caption="Комната с двумя отдельными кроватями и общей ванной комнатой"),
        InputMediaPhoto(media=open('media/room_types/twins/2.jpg', 'rb')),
        InputMediaPhoto(media=open('media/room_types/twins/3.jpg', 'rb')),
    ]
    
    deluxe = [
        InputMediaPhoto(media=open('media/room_types/deluxe/1.jpg', 'rb'), caption="Улучшенный номер с собственной ванной комнатой"),
        InputMediaPhoto(media=open('media/room_types/deluxe/2.jpg', 'rb')),
        InputMediaPhoto(media=open('media/room_types/deluxe/3.jpg', 'rb')),
        InputMediaPhoto(media=open('media/room_types/deluxe/4.jpg', 'rb')),
        InputMediaPhoto(media=open('media/room_types/deluxe/5.jpg', 'rb')),
        InputMediaPhoto(media=open('media/room_types/deluxe/6.jpg', 'rb')),
    ]
    
    context.bot.send_media_group(query.from_user.id, shared)
    context.bot.send_media_group(query.from_user.id, double)
    context.bot.send_media_group(query.from_user.id, twins)
    context.bot.send_media_group(query.from_user.id, deluxe)
    
    keyboard = [
        [btn5]
    ]
    
    dfrom = context.user_data['booking']["checkin_date"]
    dto = context.user_data['booking']["checkout_date"]
    
    number_of_people = context.user_data['booking']['adults']
    
    avail = wubook.get_availability_for_all(dfrom, dto)
    i = 0
    for room_name in avail:
        if (room_name != "shared" or number_of_people == 1) and min(avail[room_name]) > 0:
            keyboard.insert(i, 
                [InlineKeyboardButton(text=room_names_dict[room_name]['name'], callback_data=f"SELECT_ROOM | {room_names_dict[room_name]['callback']}")]
                            )
            i+=1
        if room_name == "shared" and number_of_people > 1 and min(avail[room_name]) >= number_of_people:
            keyboard.insert(i, 
                [InlineKeyboardButton(text=room_names_dict[room_name]['name'], callback_data=f"SELECT_ROOM | {room_names_dict[room_name]['callback']}")]
                            )
            i+=1
            
    message = f"Перед вами все доступные номера на ваши даты. Какой номер вы хотите?"
    
    if context.user_data["booking"]['adults'] > 1:
        message += f"""

<b>Имейте ввиде, если вы выберите 'Кровать в общем номере', то вы забронируете сразу {number_of_people} номера</b>
Так как у вас в бронировании {number_of_people} гостя        
"""    
    context.bot.send_message(update.callback_query.from_user.id, text = message, parse_mode=ParseMode.HTML, reply_markup = InlineKeyboardMarkup(keyboard))

    return LEVEL7_BOOKING

def select_room_type(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    room_type = ""
    
    callback_data = query.data.split(" | ")
        
    if callback_data[1] == "ROOM_SHARED":
        room_type="shared"
    elif callback_data[1] == "ROOM_DOUBLE":
        room_type = "double"
    elif callback_data[1] == "ROOM_TWINS":
        room_type = "twins"
    elif callback_data[1] == "ROOM_DELUXE":
        room_type = "deluxe"

    context.user_data['selected_room_type'] = room_type
    
        
    names_of_rooms = {
        'shared' : "Кровать в общем номере",
        'double' : "Комната с большой кроватью и общей ванной комнатой",
        'twins': "Комната с двумя отдельными кроватями и общей ванной комнатой",
        'deluxe': "Улучшенный номер с собственной ванной комнатой"
    }
    
    booking = context.user_data["booking"]
    user = firebase.getUserByPhoneNumber(context.user_data["phone_number"])
    
    number_of_people = booking['adults']
    
    booking_dict = {
        'rcode': booking['reservation_code'],
        'room_type': room_type,
        'name': user['name'],
        'surname': user['lastname'],
        'email': user['email'],
        'phonenumber': context.user_data["phone_number"],
        'number_of_people': number_of_people,
        'dfrom': booking["checkin_date"],
        'dto': booking["checkout_date"]
    }
    
    if(room_type == "shared" and number_of_people > 1):
        booking_dict['room_amount'] = number_of_people
    else:
        booking_dict['room_amount'] = 1
        
    
    keyboard = [
        [InlineKeyboardButton(text = "Все правильно, изменяем ✅", callback_data=booking_dict)],
        [btn5]
    ]
    
    price = wubook.price_for_room(room_type)
    
    delta = booking["checkout_date"] - booking["checkin_date"]
    number_of_nights = delta.days
    
    total_price = number_of_nights * price * int(booking_dict['room_amount'])
    
    context.bot.send_message(update.callback_query.message.chat_id, text = f"""
Все ли верно?
<b>Даты</b>: c {booking["checkin_date"].strftime("%d/%m/%Y")} по {booking["checkout_date"].strftime("%d/%m/%Y")} | {number_of_nights} {"ночь" if number_of_nights == 1 else "ночей"}
<b>Номер</b>: {names_of_rooms[room_type]}
<b>Количество номеров</b>: {booking_dict['room_amount']}
<b>Количество гостей</b>: {number_of_people} {"гость" if number_of_people == 1 else "гостей"}

<b>Общая стоимость</b>: ${total_price} 
                             """, parse_mode=ParseMode.HTML, reply_markup = InlineKeyboardMarkup(keyboard))

    
    # print(booking_dict)
    
    return "LEVEL8_BOOKING"


def change_room_type(update: Update, context: CallbackContext):
    query = update.callback_query
    
    booking_details = query.data
    
    room_type = booking_details['room_type']
    dfrom = booking_details['dfrom']
    dto = booking_details['dto']
    avail = wubook.get_availability_for_single(room_type, dfrom, dto)
    if avail == 0 or (booking_details['room_type'] == "shared" and avail < booking_details['room_amount']):
        query.answer("Сожалею, но на данную дату мест нет. Попробуйте выбрать другие даты")
    
    res = wubook.change_room(query.data)
    
    if(res):
        query.answer("Ваш номер изменен. Вам нужно будет выбрать войти еще раз.")
        time.sleep(1)
        del context.user_data["booking"]
        return my_booking_options(update, context)
    else:
        query.answer("Что-то сломалось")
        
#Checkout

def checkout(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    
    query.edit_message_text(text="Просим вас оставить ключи у администратора)")

    rating = [
        [InlineKeyboardButton(text="1", callback_data="1"), 
         InlineKeyboardButton(text="2", callback_data="2"), 
         InlineKeyboardButton(text="3", callback_data="3"), 
         InlineKeyboardButton(text="4", callback_data="4"), 
         InlineKeyboardButton(text="5", callback_data="5")]
    ]
    
    context.bot.send_message(context.user_data['chat_id'], text="Оцените наш сервис от 1 до 5", reply_markup=InlineKeyboardMarkup(rating))

    return LEVEL1_CHECKOUT

def checkout_rated(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    context.user_data["rating"] = query.data
    query.edit_message_reply_markup(reply_markup=None)
    context.bot.send_message(context.user_data["chat_id"], text="Спасибо за вашу оценку!", reply_markup = ReplyKeyboardRemove())
    context.bot.send_message(context.user_data["chat_id"], text="Есть ли у вас какие-либо комментарии по нашему сервису?", reply_markup = ReplyKeyboardRemove())
    return LEVEL1_CHECKOUT
    
def checkout_comments(update: Update, context: CallbackContext):
    comment = update.message
    context.bot.send_message(context.user_data["chat_id"], text="Спасибо, мы передали ваши комментарии администратору")
    
    user = update.message.from_user
    booking = context.user_data["booking"]
    user_from_booking = firebase.getUserByPhoneNumber(context.user_data["phone_number"])
    
    for adminID in admin_id_arr:
        context.bot.send_message(chat_id = adminID, text = f"""
Гость выселился из номера:
    Логин в Telegram: @{user.username}
    Имя и Фамилия: {user_from_booking['name']} {user_from_booking['lastname']}
    Номер телефона: {user_from_booking["phone_number"]}
    Дата заселения: {booking["checkin_date"].strftime("%d-%m-%Y")}
    Дата выселения: {booking["checkout_date"].strftime("%d-%m-%Y")}
    Комната: {booking["room_number"]}
    _________________________________________
    Комментарии: {comment.text}
    Оценка: {context.user_data["rating"]}/5
                             """)
        
    firebase.check_room_occupancy_if_delete(booking['user_id'], booking['id'], booking['reservation_code'])
    
    firebase.updateBookingWithId(booking['user_id'], booking['id'], {"checked_out": True})
    firebase.approveStatusFromGuestBookingID(booking['user_id'], booking['id'], 'checked_out', True)
     
    del context.user_data['booking']
    
    return my_booking_options(update, context)

#Payment

def payment(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    keyboard = [
        [InlineKeyboardButton(text="Перевод", callback_data="PEREVOD")],
        [InlineKeyboardButton(text="Наличными", callback_data="CASH")],
        [btn5]
    ]
    
    query.edit_message_text(text = "Каким способом будет расплачиваться?", reply_markup = InlineKeyboardMarkup(keyboard))
    
    return LEVEL1_PAYMENT

def payment_options(update, context):
    query = update.callback_query
    query.answer()
    
    keyboard = [
        [btn5]
    ]
    
    if query.data == "PEREVOD":
        method = "Перевод"
    else:
        method = "Наличный расчет"
        
    query.edit_message_text(text = f"Вы выбрали {method}", reply_markup = InlineKeyboardMarkup(keyboard))
    
    return LEVEL2_PAYMENT

#new booking

def new_booking(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    today = datetime.datetime.now(tz = pytz.timezone("Asia/Almaty"))
    yesterday = today - datetime.timedelta(days=1)
    
    context.bot.send_message(context.user_data["chat_id"], text="Выберите дату заезда", reply_markup = telegramcalendar.create_calendar(current_date=yesterday))

    return LEVEL1_NEW_BOOKING

    
def new_booking_select_checkout_date(update: Update, context: CallbackContext):
    selected,date = telegramcalendar.process_calendar_selection(update, context)
    if selected:
        context.bot.send_message(chat_id=update.callback_query.from_user.id,
                text=(date.strftime("%d/%m/%Y")),
                reply_markup=ReplyKeyboardRemove())
        context.user_data["new_booking_checkin_date"] = date
        
        date = date + datetime.timedelta(days=1)
        context.bot.send_message(update.callback_query.message.chat_id, text="Выберите дату выезда", reply_markup = telegramcalendar.create_calendar(year = date.year, month = date.month, current_date=date))
        return LEVEL2_NEW_BOOKING

def new_booking_select_checkout_date_again(update: Update, context: CallbackContext):
    context.bot.send_message(update.callback_query.message.chat_id, text="Выберите дату выезда", reply_markup = telegramcalendar.create_calendar())
    return LEVEL2_NEW_BOOKING

room_names_dict = {
    "shared": {"name": "В общем номере", "callback": "ROOM_SHARED", "number_of_people": 1, "shortname": "shared"},
    "double": {"name": "С большой кроватью и общей ванной комнатой", "callback": "ROOM_DOUBLE", "number_of_people": 2, "shortname": "double"},
    "twins": {"name": "С двумя отдельными кроватями и общей ванной комнатой", "callback": "ROOM_TWINS", "number_of_people": 2, "shortname": "twins"},
    "deluxe": {"name": "Улучшенный с собственной ванной комнатой", "callback": "ROOM_DELUXE", "number_of_people": 2, "shortname": "deluxe"}
}

def new_booking_select_room(update: Update, context: CallbackContext):
    
    selected,date = telegramcalendar.process_calendar_selection(update, context)
    
    if selected:
        if(context.user_data["new_booking_checkin_date"] > date):
            context.bot.send_message(update.callback_query.from_user.id, 
                                     text = "Дата выезда раньше чем дата заезда, выберите еще раз")
            time.sleep(0.5)
            return new_booking_select_checkout_date_again(update, context)
        
        context.bot.send_message(chat_id=update.callback_query.from_user.id,
                        text=(date.strftime("%d/%m/%Y")),
                        reply_markup=ReplyKeyboardRemove())
    
        context.user_data["new_booking_checkout_date"] = date
        
        keyboard = [
            [InlineKeyboardButton(text="Посмотреть фотографии всех номеров", callback_data="PHOTOS_OF_ROOMS")],
            [btn5, 
             InlineKeyboardButton(text="❌ Отменить", callback_data="CANCEL_NEW_BOOKING")],
        ]
        
        dfrom = context.user_data['new_booking_checkin_date']
        dto = context.user_data['new_booking_checkout_date']
        
        avail = wubook.get_availability_for_all(dfrom, dto)
        i = 0
        for room_name in avail:

            if min(avail[room_name]) > 0:
                delta = context.user_data['new_booking_checkout_date'] - context.user_data['new_booking_checkin_date']
                number_of_nights = delta.days
                price = wubook.price_for_room(room_names_dict[room_name]['shortname']) * number_of_nights
                print(price)
                price_in_kgs = convert_currency("USD", "KGS", float(price))
                print(price_in_kgs)
                keyboard.insert(i, 
                    [InlineKeyboardButton(text=f"{price_in_kgs} KGS | {room_names_dict[room_name]['name']}", callback_data=f"SELECT_ROOM | {room_names_dict[room_name]['callback']}")]
                                )
                i+=1
        
        context.bot.send_message(update.callback_query.from_user.id, text = "Перед вами все доступные номера на данную дату. Какой номер вы хотите?", reply_markup = InlineKeyboardMarkup(keyboard))
        
        
        return LEVEL3_NEW_BOOKING
    
def new_booking_edit_room(update: Update, context: CallbackContext):
        
    keyboard = [
        [InlineKeyboardButton(text="Посмотреть фотографии всех номеров", callback_data="PHOTOS_OF_ROOMS")],
        [btn5, 
            InlineKeyboardButton(text="❌ Отменить", callback_data="CANCEL_NEW_BOOKING")],
    ]
    
    dfrom = context.user_data['new_booking_checkin_date']
    dto = context.user_data['new_booking_checkout_date']
    
    avail = wubook.get_availability_for_all(dfrom, dto)
    
    i = 0
    for room_name in avail:
  
        if min(avail[room_name]) > 0:
            delta = context.user_data['new_booking_checkout_date'] - context.user_data['new_booking_checkin_date']
            number_of_nights = delta.days
            price = wubook.price_for_room(room_names_dict[room_name]['shortname']) * number_of_nights
            price_in_kgs = convert_currency("USD", "KGS", price)
            keyboard.insert(i, 
                [InlineKeyboardButton(text=f"{price_in_kgs} KGS | {room_names_dict[room_name]['name']}", callback_data=f"SELECT_ROOM | {room_names_dict[room_name]['callback']}")]
                            )
            i+=1
    
    context.bot.send_message(update.callback_query.from_user.id, text = "Перед вами все доступные номера на данную дату. Какой номер вы хотите?", reply_markup = InlineKeyboardMarkup(keyboard))
    
    
    return "LEVEL1_NEW_BOOKING_EDIT"

def new_booking_photos_of_rooms(update: Update, context: CallbackContext):
    
    query = update.callback_query
    query.answer()
    
    shared = [
        InputMediaPhoto(media=open('media/room_types/shared/1.jpg', 'rb'), caption="Кровать в общем номере"),
        InputMediaPhoto(media=open('media/room_types/shared/2.jpg', 'rb')),
        InputMediaPhoto(media=open('media/room_types/shared/3.jpg', 'rb')),
        InputMediaPhoto(media=open('media/room_types/shared/4.jpg', 'rb')),
    ]
    
    double = [
        InputMediaPhoto(media=open('media/room_types/double/1.jpg', 'rb'), caption="Комната с большой кроватью и общей ванной комнатой"),
        InputMediaPhoto(media=open('media/room_types/double/2.jpg', 'rb')),
        InputMediaPhoto(media=open('media/room_types/double/3.jpg', 'rb'))
    ]
    
    twins = [
        InputMediaPhoto(media=open('media/room_types/twins/1.jpg', 'rb'), caption="Комната с двумя отдельными кроватями и общей ванной комнатой"),
        InputMediaPhoto(media=open('media/room_types/twins/2.jpg', 'rb')),
        InputMediaPhoto(media=open('media/room_types/twins/3.jpg', 'rb')),
    ]
    
    deluxe = [
        InputMediaPhoto(media=open('media/room_types/deluxe/1.jpg', 'rb'), caption="Улучшенный номер с собственной ванной комнатой"),
        InputMediaPhoto(media=open('media/room_types/deluxe/2.jpg', 'rb')),
        InputMediaPhoto(media=open('media/room_types/deluxe/3.jpg', 'rb')),
        InputMediaPhoto(media=open('media/room_types/deluxe/4.jpg', 'rb')),
        InputMediaPhoto(media=open('media/room_types/deluxe/5.jpg', 'rb')),
        InputMediaPhoto(media=open('media/room_types/deluxe/6.jpg', 'rb')),
    ]
    
    context.bot.send_media_group(query.from_user.id, shared)
    context.bot.send_media_group(query.from_user.id, double)
    context.bot.send_media_group(query.from_user.id, twins)
    context.bot.send_media_group(query.from_user.id, deluxe)
    
    keyboard = [
        [btn5, 
             InlineKeyboardButton(text="❌ Отменить", callback_data="CANCEL_NEW_BOOKING")],
    ]
    
    dfrom = context.user_data['new_booking_checkin_date']
    dto = context.user_data['new_booking_checkout_date']
    
    avail = wubook.get_availability_for_all(dfrom, dto)

    
    i = 0
    for room_name in avail:

        if min(avail[room_name]) > 0:
            delta = context.user_data['new_booking_checkout_date'] - context.user_data['new_booking_checkin_date']
            number_of_nights = delta.days
            price = wubook.price_for_room(room_names_dict[room_name]['shortname']) * number_of_nights
            price_in_kgs = convert_currency("USD", "KGS", price)
            keyboard.insert(i, 
                [InlineKeyboardButton(text=f"{price_in_kgs} KGS | {room_names_dict[room_name]['name']}", callback_data=f"SELECT_ROOM | {room_names_dict[room_name]['callback']}")]
                            )
            i+=1
    
    context.bot.send_message(update.callback_query.from_user.id, text = "Перед вами все доступные номера на данную дату. Какой номер вы хотите?", reply_markup = InlineKeyboardMarkup(keyboard))

    return LEVEL4_NEW_BOOKING

def new_booking_selected_room(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    callback_data = query.data.split(" | ")
    
    if callback_data[1] == "ROOM_SHARED":
        context.user_data['new_booking_selected_room_type'] = "shared"
    elif callback_data[1] == "ROOM_DOUBLE":
        context.user_data['new_booking_selected_room_type'] = "double"
    elif callback_data[1] == "ROOM_TWINS":
        context.user_data['new_booking_selected_room_type'] = "twins"
    elif callback_data[1] == "ROOM_DELUXE":
        context.user_data['new_booking_selected_room_type'] = "deluxe"
    
    keyboard = [
        [btn5]
    ]
    
    room_type = context.user_data['new_booking_selected_room_type']
    dfrom = context.user_data['new_booking_checkin_date']
    dto = context.user_data['new_booking_checkout_date']
    avail = wubook.get_availability_for_single(room_type, dfrom, dto)
    
     
    if min(avail) == 0:
        query.edit_message_text(text="Сожалею, но на данную дату мест нет. Попробуйте выбрать другие даты")
        time.sleep(0.5)
        return new_booking(update, context)
    
    query.edit_message_text(text="Ваше имя и фамилия? Например: 'Иван Иванов'", reply_markup=None)
    
    return "LEVEL5_NEW_BOOKING"

def new_booking_incorrect_format_name(update: Update, context: CallbackContext):
    context.bot.send_message(update.message.chat_id, text = "Введите имя и фамилию в правильном формате. Например: 'Иван Иванов'")
    

def new_booking_ask_name(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    query.edit_message_text(text="Ваше имя и фамилия?", reply_markup=ReplyKeyboardRemove)
    
    return "LEVEL5_NEW_BOOKING"

def new_booking_get_name(update: Update, context: CallbackContext):
    name_and_surname = update.message.text
    
    name_and_surname = name_and_surname.split(" ")
    
    context.user_data['new_booking_name'] = name_and_surname[0]
    context.user_data['new_booking_surname'] = name_and_surname[1]
    
    context.bot.send_message(update.message.chat_id, text = "Введите ваш номер в формате +xxxxxxxxxxx:")
    
    return "LEVEL6_NEW_BOOKING"


def new_booking_incorrect_phonumber(update: Update, context: CallbackContext):
    
    context.bot.send_message(update.message.chat_id, text = f"Вы ввели некорректный номер телефона, попробуйте снова. В формате: +xxxxxxxxxxx (начинается с '+' и максимум 15 цифр)")

    return "LEVEL6_NEW_BOOKING"

def new_booking_get_phonumber(update: Update, context: CallbackContext):
    phonenumber = update.message.text
    
    context.user_data['new_booking_phonenumber'] = phonenumber
    
    context.bot.send_message(update.message.chat_id, text = f"Введите ваш адрес электронной почты. Вводите настоящий, так как он может понадобиться при входе в бота.")

    return "LEVEL7_NEW_BOOKING"

def new_booking_get_email(update: Update, context: CallbackContext):
    email = update.message.text
    
    context.user_data['new_booking_email'] = email
    
    room_type = context.user_data['new_booking_selected_room_type']
    
    number_of_people = room_names_dict[room_type]['number_of_people']
    
    context.bot.send_message(update.message.chat_id, text = f"Введите количество гостей. Имейте ввиду, что выбранный номер вмещает максимум {number_of_people} {'человека' if number_of_people == 1 else 'людей'}")

    return "LEVEL8_NEW_BOOKING"

def new_booking_ask_email_again(update: Update, context: CallbackContext):
    
    context.bot.send_message(update.message.chat_id, text = f"Вы ввели некорректный адрес электронной почты, попробуйте еще раз")

    return "LEVEL7_NEW_BOOKING"


def new_booking_ask_number_of_people_again(update: Update, context: CallbackContext):
    room_type = context.user_data['new_booking_selected_room_type']
    
    number_of_people = room_names_dict[room_type]['number_of_people']
    
    context.bot.send_message(update.message.chat_id, text = f"Введите количество гостей. Имейте ввиду, что выбранный номер вмещает максимум {number_of_people} {'человека' if number_of_people == 1 else 'людей'}")
    
    return "LEVEL8_NEW_BOOKING"
    
def new_booking_get_number_of_guests(update: Update, context: CallbackContext):
    
    room_type = context.user_data['new_booking_selected_room_type']
    
    number_of_guests = int(update.message.text)
    max_people = room_names_dict[room_type]['number_of_people']
    
    if(number_of_guests > max_people):
        context.bot.send_message(update.message.chat_id, text = "Вы выбрали больше гостей чем комната может вместить")
        return new_booking_ask_number_of_people_again(update, context)
    
    context.user_data['new_booking_number_of_guests'] = number_of_guests
    
    names_of_rooms = {
        'shared' : "Кровать в общем номере",
        'double' : "Комната с большой кроватью и общей ванной комнатой",
        'twins': "Комната с двумя отдельными кроватями и общей ванной комнатой",
        'deluxe': "Улучшенный номер с собственной ванной комнатой"
    }
    
    
    keyboard = [
        [InlineKeyboardButton(text = "Все правильно, бронируем ✅", callback_data="RIGHT_BOOKING")],
        [InlineKeyboardButton(text = "Начать заново ❌", callback_data="NEW_BOOKING_AGAIN")],
        [InlineKeyboardButton(text="В главное меню 🔙", callback_data="CANCEL_NEW_BOOKING")],
        
    ]
    
    price = wubook.price_for_room(room_type)
    
    delta = context.user_data['new_booking_checkout_date'] - context.user_data['new_booking_checkin_date']
    number_of_nights = delta.days
    
    total_price = number_of_nights*price
    
    context.bot.send_message(update.message.chat_id, text = f"""
Все ли верно?
<b>Имя</b>: {context.user_data['new_booking_name']}
<b>Фамилия</b>: {context.user_data['new_booking_surname']}
<b>Номер телефона</b>: {context.user_data['new_booking_phonenumber']}
<b>Email</b>: {context.user_data['new_booking_email']}
<b>Даты</b>: c {context.user_data['new_booking_checkin_date'].strftime("%d/%m/%Y")} по {context.user_data['new_booking_checkout_date'].strftime("%d/%m/%Y")} | {number_of_nights} {"ночь" if number_of_nights == 1 else "ночей"}
<b>Номер</b>: {names_of_rooms[room_type]}
<b>Количество гостей</b>: {context.user_data['new_booking_number_of_guests']} {"гость" if context.user_data['new_booking_number_of_guests'] == 1 else "гостей"}
                             
<b>Общая стоимость</b>: ${total_price} 
                             """, parse_mode=ParseMode.HTML, reply_markup = InlineKeyboardMarkup(keyboard))
    


    return "LEVEL8_NEW_BOOKING"

def new_booking_create_new_booking(update: Update, context: CallbackContext):
    
    names_of_rooms = {
        'shared' : "Кровать в общем номере",
        'double' : "Комната с большой кроватью и общей ванной комнатой",
        'twins': "Комната с двумя отдельными кроватями и общей ванной комнатой",
        'deluxe': "Улучшенный номер с собственной ванной комнатой"
    }
    
    query = update.callback_query
    
    query.answer("Секунду, оформляю")
    
    room_type = context.user_data['new_booking_selected_room_type']
    dfrom = context.user_data['new_booking_checkin_date']
    dto = context.user_data['new_booking_checkout_date']
    avail = wubook.get_availability_for_single(room_type, dfrom, dto)
    
    free = False
    for avail_num in avail:
        if avail_num == 0:
            free = False
            break
        elif avail_num > 0:
            free = True
        
    if free == False:
        query.edit_message_text(text="Сожалею, но мне не удалось забронировать номер.")
    else:
        booking_dict = {
            'room_type': room_type,
            'name': context.user_data['new_booking_name'],
            'surname': context.user_data['new_booking_surname'],
            'email': context.user_data['new_booking_email'],
            'phonenumber': context.user_data['new_booking_phonenumber'],
            'number_of_people': context.user_data['new_booking_number_of_guests'],
            'dfrom': context.user_data['new_booking_checkin_date'],
            'dto': context.user_data['new_booking_checkout_date']
        }
        
        keyboard = [
            [InlineKeyboardButton(text="В главное меню 🔙", callback_data="MAIN_MENU")]
        ]
        
        res = wubook.new_booking(booking_dict)
        if(res):
            query.edit_message_text(text="Номер успешно забронирован. Через несколько минут, бронирование появится в боте", reply_markup=InlineKeyboardMarkup(keyboard))
        
            user = update.callback_query.from_user
            
            for adminID in admin_id_arr:
                context.bot.send_message(chat_id = adminID, text = f"""
Новое бронирование:
    Логин в Telegram: @{user.username}
    _________________________________________
    Имя: {context.user_data['new_booking_name']} {context.user_data['new_booking_surname']}
    Номер телефона: {context.user_data['new_booking_phonenumber']}
    Email: {context.user_data['new_booking_email']}
    Гостей: {context.user_data['new_booking_number_of_guests']}
    Номер: {names_of_rooms[room_type]}
    Дата заселения: {context.user_data['new_booking_checkin_date'].strftime("%d/%m/%Y")}
    Дата выселения: {context.user_data['new_booking_checkout_date'].strftime("%d/%m/%Y")}
                             """)
                
        else:
            query.edit_message_text(text="Сожалею, но мне не удалось забронировать номер. 1")
        

        
        return "LEVEL9_NEW_BOOKING"
        

#Arbitrary callback check

def check_type(callback_data):
    return True

def handle_invalid_button(update: Update, context: CallbackContext) -> None:
    """Informs the user that the button is no longer available."""
    update.callback_query.answer()
    update.effective_message.edit_text(
        'Sorry, I could not process this button click 😕 Please send /start to get a new keyboard.'
    )
    
def check_callback_admin_search(callbackDict: dict):
    if(type(callbackDict) == dict and callbackDict['callback'] == "CHOOSE_BOOKING"):
        return True
    else:
        return False
    
def check_callback_approve_status(callback):
    # print(callback)
    if type(callback) == str and callback == "BACK":
        return False
    else: return True
    
def check_callback_approve_booking(callback):
    if type(callback) == dict and callback['callback'] == "APPROVE_BOOKING":
        return True
    else: return False
    
def check_callback_guest(callback):
    if callback == "CHECKIN_TODAY" or callback == "CHECKOUT_TODAY" or callback == "BACK":
        return False
    elif callback == "NO_CONNECTION" or callback == "APPROVE_BOOKING" or callback == "PAID" or callback == "LIVE" or callback == "NOT_PAID":
        return True

    
def check_callback_status(callback):
    print(callback)
    if "character#" in callback:
        print("Works")
        return True
    else:
        print("Does not work")
        return False
    
def check_callback_cancel_checkin_all(callback):
    if type(callback) == dict and callback['type'] == "CANCEL" and callback['booking_type'] == "all":
        return True
    else:
        return False
    
def check_callback_cancel_checkin_day_choosed(callback):
    if type(callback) == dict and callback['type'] == "CANCEL" and callback['booking_type'] == "day_choosed":
        return True
    else:
        return False
    
def check_callback_register_checkin_guest(callback):
    if type(callback) == dict and callback['callback'] == "CHECKIN":
        return True
    else:
        return False
    
def check_callback_register_no_show_guest(callback):
    if type(callback) == dict and callback['callback'] == "NO_SHOW":
        return True
    else:
        return False
    
def check_callback_register_checkout_guest(callback):
    if type(callback) == dict and callback['callback'] == "CHECKOUT":
        return True
    else:
        return False

def main() -> None:
    
    tz = pytz.timezone('Asia/Aqtau')
    
    Defaults.tzinfo = tz


    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    persistence = PicklePersistence(filename='eva_bot_with_api', store_callback_data=True)
    updater = Updater("Telegram Bot Token", persistence=persistence, arbitrary_callback_data = True) #test bot

    DB_URI = ""

    
    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher
    dispatcher.job_queue.scheduler.add_jobstore(
        PTBSQLAlchemyJobStore(
            dispatcher=dispatcher, url=DB_URI,
        ),
    )
    
    main_menu_conversation = ConversationHandler(
        entry_points= [
                CallbackQueryHandler(select_language, pattern = "^" + "LANGUAGE_SELECT"),
                CallbackQueryHandler(events, pattern = "^" + "EVENTS"),
                CallbackQueryHandler(about_hotel, pattern = "^" + "ABOUTHOTEL"),
                CallbackQueryHandler(booking, pattern = "^" + "BOOKING"),
                CallbackQueryHandler(checkin_main_menu, pattern ='^' + "CHECKIN_MAIN_MENU" ),
                CallbackQueryHandler(checkout_main_menu, pattern ='^' + "CHECKOUT_MAIN_MENU" ),
                CallbackQueryHandler(language_select_callback, pattern ='^' + "LANG" )
        ],
        states={
            LEVEL1: [
                CallbackQueryHandler(main_menu, pattern = "^" + "BACK"),
            ],
            LEVEL2: [
                CallbackQueryHandler(select_language, pattern = "^" + "LANGUAGE_SELECT"),
                CallbackQueryHandler(events, pattern = "^" + "EVENTS"),
                CallbackQueryHandler(about_hotel, pattern = "^" + "ABOUTHOTEL"),
                CallbackQueryHandler(booking, pattern = "^" + "BOOKING"),
                CallbackQueryHandler(language_select_callback, pattern ='^' + "LANG" ),
                CallbackQueryHandler(main_menu, pattern = "^" + "BACK"),
                CallbackQueryHandler(checkin_main_menu, pattern ='^' + "CHECKIN_MAIN_MENU" ),
                CallbackQueryHandler(checkout_main_menu, pattern ='^' + "CHECKOUT_MAIN_MENU" ),


            ],
            "LEVEL1_CHECKIN": [
                CallbackQueryHandler(checkin_verify_email, pattern = "^" + "VERIFY_EMAIL"),
                CallbackQueryHandler(checkin_verify_phone, pattern = "^" + "VERIFY_PHONE"), 
                CallbackQueryHandler(checkin_verify_just_phone_number, pattern = "^" + "VERIFY_JUST_NUMBER"),  
                CallbackQueryHandler(checkin_verify_just_rcode, pattern = "^" + "VERIFY_JUST_RCODE"),  
 
                CallbackQueryHandler(main_menu, pattern = "^" + "BACK"),
                
            ],
            "LEVEL2_CHECKIN": [
                MessageHandler(Filters.text, checkin_get_phone_number_and_send_email),
                MessageHandler(Filters.contact, checkin_verified_with_contact),
                
                # CallbackQueryHandler(booking, pattern = "^" + "BACK"),
            ],
            "LEVEL2_CHECKIN_JUST_PHONENUMBER": [
                MessageHandler(~Filters.regex("^\+\d{1,15}$"), checkin_verify_just_phone_number_incorrect_format),
                MessageHandler(Filters.regex("^\+\d{1,15}$"), checkin_verify_just_phone_number_get_phone),
                CallbackQueryHandler(main_menu, pattern = "^" + "BACK"),

            ],
            "LEVEL2_CHECKIN_JUST_RCODE": [
                MessageHandler(~Filters.regex("^[0-9]+$"), checkin_verify_just_rcode_incorrect_format),
                MessageHandler(Filters.regex("^[0-9]+$"), checkin_verify_just_rcode_get_rcode),
                CallbackQueryHandler(main_menu, pattern = "^" + "BACK"),

            ],
            "LEVEL3_CHECKIN": [
                MessageHandler(Filters.text, checkin_get_code_from_user),
                CallbackQueryHandler(booking, pattern = "^" + "BACK"),
                CallbackQueryHandler(checkin_get_phone_number_and_send_email, pattern = "^" + "SEND_CODE_AGAIN"),
            ],
            "LEVEL4_CHECKIN": [
                CallbackQueryHandler(checkin_selected_booking, pattern="^"+ "SELECTED_BOOKING"),
                CallbackQueryHandler(checkin_main_menu, pattern="^"+ "OTHER_PHONE")
            ],
            "LEVEL5_CHECKIN": [
                assign_room_conversation,
                guest_payment_conversation,
                # MessageHandler(Filters.photo, checkin_get_passport_photo) ,
                CallbackQueryHandler(main_menu, pattern = "^" + "BACK"),
                
            ],
            "LEVEL6_CHECKIN": [
                guest_payment_conversation,
                # MessageHandler(Filters.photo, checkin_get_passport_photo) ,
                
            ],
            "LEVEL7_CHECKIN": [
                assign_room_conversation,
                CallbackQueryHandler(main_menu, pattern = "^" + "MAIN_MENU"),
            ],
            
            

            "LEVEL1_MAIN_MENU_CHECKOUT": [
                CallbackQueryHandler(checkout_verify_email, pattern = "^" + "VERIFY_EMAIL"),
                CallbackQueryHandler(checkout_verify_phone, pattern = "^" + "VERIFY_PHONE"),  
                CallbackQueryHandler(main_menu, pattern = "^" + "BACK"),

            ],
            "LEVEL2_MAIN_MENU_CHECKOUT": [
                MessageHandler(Filters.text, checkout_get_phone_number_and_send_email),
                MessageHandler(Filters.contact, checkout_verified_with_contact),
                
                # CallbackQueryHandler(booking, pattern = "^" + "BACK"),
            ],
            "LEVEL3_MAIN_MENU_CHECKOUT": [
                MessageHandler(Filters.text, checkout_get_code_from_user),
                CallbackQueryHandler(booking, pattern = "^" + "BACK"),
            ],
            "LEVEL4_MAIN_MENU_CHECKOUT": [
                CallbackQueryHandler(checkout_selected, pattern="^"+ "SELECTED_BOOKING"),
                CallbackQueryHandler(checkout_main_menu, pattern="^"+ "OTHER_PHONE")
            ],
            "LEVEL5_MAIN_MENU_CHECKOUT": [
                CallbackQueryHandler(checkout_rated_main_menu),
                MessageHandler(Filters.text, checkout_comments_main_menu)   
                
            ],
            # "ADMIN_HELP_CONV": admin_help_conversation,
            LEVEL3_BOOKING : [
                CallbackQueryHandler(main_menu, pattern = "^" + "BACK$"),
                CallbackQueryHandler(new_booking, pattern = "^" + "BOOK"),
                CallbackQueryHandler(verify_options, pattern = "^" + "MY_BOOKING"),
                admin_help_conversation,
                guest_payment_conversation,
                assign_room_conversation,
            ],
            LEVEL34_SELECT_BOOKING: [
                CallbackQueryHandler(my_booking_selected, pattern = "^" + "SELECTED_BOOKING"),
                CallbackQueryHandler(verify_options, pattern = "^" + "OTHER_PHONE"),
            ],
            LEVEL34_BOOKING: [ 
                CallbackQueryHandler(approve_booking_status, pattern = check_callback_approve_booking),
                CallbackQueryHandler(my_booking_learn_more, pattern = "^" + "LEARN_MORE"),
                CallbackQueryHandler(booking_contact, pattern = "^" + "EDIT"),
                CallbackQueryHandler(booking_checkin, pattern = "^" + "REGISTER"),
                CallbackQueryHandler(payment, pattern = "^" + "PAYMENT"),
                CallbackQueryHandler(checkout, pattern = "^" + "CHECKOUT"),
                CallbackQueryHandler(my_booking_options, pattern = "^" + "OTHER_BOOKING"),
                CallbackQueryHandler(verify_options, pattern = "^" + "OTHER_PHONE"),
                CallbackQueryHandler(booking, pattern = "^" + "BACK"),
            ],
            "LEVEL4_BOOKING_CHECKIN": [
                MessageHandler(Filters.photo, booking_checkin_get_passport_photo),
                CallbackQueryHandler(my_booking_selected, pattern = "^" + "BACK"),
            ],
            LEVEL3_ABOUT_HOTEL: [
                CallbackQueryHandler(about_hotel_address, pattern = "^" + "ADDRESS"),
                CallbackQueryHandler(about_hotel_checkin, pattern = "^" + "CHECKIN"),
                CallbackQueryHandler(about_hotel_rooms, pattern = "^" + "ROOMS"),
                # CallbackQueryHandler(checkout_time, pattern = "^" + "CHECKOUT_TIME"),
                CallbackQueryHandler(hotel_services, pattern = "^" + "HOTEL_SERVICES"),
                # CallbackQueryHandler(wifi_password, pattern = "^" + "WIFI_PASS"),
                CallbackQueryHandler(parking, pattern = "^" + "PARKING"),
                CallbackQueryHandler(about_hotel_review, pattern = "^" + "REVIEWS"),
                CallbackQueryHandler(main_menu, pattern = "^" + "BACK"),
                
            ],
            LEVEL3_EVENTS: [
                CallbackQueryHandler(main_menu, pattern = "^" + "BACK"),
            ],
            LEVEL4_BOOKING: [
                MessageHandler(Filters.contact, verified_with_contact),
                CallbackQueryHandler(booking, pattern = "^" + "BACK"),
            ],
            LEVEL4_ABOUT_HOTEL: [
                CallbackQueryHandler(about_hotel_rooms_photos, pattern = "^" + "PHOTOS_OF_ROOMS"),
                CallbackQueryHandler(about_hotel_photos_of_services, pattern = "^" + "PHOTOS_OF_SERVICES"),
                CallbackQueryHandler(about_hotel_wifi_password, pattern = "^" + "WIFI_PASSWORD"),
                CallbackQueryHandler(about_hotel_order_laundry, pattern = "^" + "ORDER_LAUNDRY"),
                CallbackQueryHandler(about_hotel_order_cleaning, pattern = "^" + "ORDER_ROOM_CLEANING"),
                CallbackQueryHandler(about_hotel_address_callback, pattern = "^" + "AddressCallback"),
                CallbackQueryHandler(about_hotel, pattern = "^" + "BACK"),
            ],
            LEVEL5_BOOKING: [
                CallbackQueryHandler(cancel_booking, pattern = "^" + "CANCEL_BOOKING"),
                CallbackQueryHandler(edit_dates, pattern = "^" + "EDIT_DATES"),
                CallbackQueryHandler(change_room, pattern = "^" + "CHANGE_ROOM"),
                CallbackQueryHandler(my_booking_options, pattern = "^" + "BACK"),
            ],
            LEVEL5_ABOUT_HOTEL: [
                
                CallbackQueryHandler(hotel_services, pattern = "^" + "BACK"),
            ],
            "LEVEL5_ABOUT_HOTEL_ADDRESS":[
                CallbackQueryHandler(about_hotel_address, pattern = "^" + "BACK"),    
            ],
            "LEVEL5_ABOUT_HOTEL_PHOTOS": [
                CallbackQueryHandler(about_hotel_rooms, pattern = "^" + "BACK"),
                
            ],
            LEVEL6_BOOKING: [
                # MessageHandler(Filters.regex("\d{2}\/\d{2}\/\d{4}"), edit_checkin_dates),
                CallbackQueryHandler(edit_checkin_dates, pattern = "^" + "CALENDAR"),
                
                CallbackQueryHandler(select_room_type, pattern = "^" + "SELECT_ROOM"),
                CallbackQueryHandler(photos_of_rooms, pattern = "^" + "PHOTOS_OF_ROOMS"),
                
                
                CallbackQueryHandler(approve_cancel_booking, pattern = "^" + "CONFIRM_CANCEL"),
                
                CallbackQueryHandler(booking_contact, pattern = "^" + "BACK"),
                
            ],
            LEVEL7_BOOKING: [
                CallbackQueryHandler(select_room_type, pattern = "^" + "SELECT_ROOM"),
                CallbackQueryHandler(booking_contact, pattern = "^" + "BACK"),
                
            ],
            "LEVEL8_BOOKING": [
                CallbackQueryHandler(change_room_type, pattern = dict),
                CallbackQueryHandler(booking_contact, pattern = "^" + "BACK"),
                
            ],
            LEVEL7_CHECKOUT: [
                CallbackQueryHandler(edit_checkout_dates, pattern = "^" + "CALENDAR"),
                
                
            ],
            LEVEL1_VERIFY: [
                CallbackQueryHandler(verify_email, pattern = "^" + "VERIFY_EMAIL"),
                CallbackQueryHandler(verify_phone, pattern = "^" + "VERIFY_PHONE"),
                CallbackQueryHandler(verify_test, pattern = "^" + "VERIFY_TEST"),  
                CallbackQueryHandler(verify_just_phone_number, pattern = "^" + "VERIFY_JUST_NUMBER"),  
                CallbackQueryHandler(verify_just_rcode, pattern = "^" + "VERIFY_JUST_RCODE"),  

                CallbackQueryHandler(booking, pattern = "^" + "BACK"),
            ],
            LEVEL2_VERIFY: [
                MessageHandler(Filters.regex("^\+\d{1,15}$"), get_phone_number_and_send_email),
                CallbackQueryHandler(booking, pattern = "^" + "BACK"),
            ],
            "LEVEL2_VERIFY_TEST": [
                MessageHandler(Filters.regex("^\+\d{1,15}$"), verify_test_get_phone),
                CallbackQueryHandler(booking, pattern = "^" + "BACK"),

            ],
            "LEVEL2_JUST_PHONENUMBER": [
                MessageHandler(~Filters.regex("^\+\d{1,15}$"), verify_just_phone_number_incorrect_format),
                MessageHandler(Filters.regex("^\+\d{1,15}$"), verify_just_phone_number_get_phone),
                CallbackQueryHandler(booking, pattern = "^" + "BACK"),

            ],
            "LEVEL2_JUST_RCODE": [
                MessageHandler(~Filters.regex("^[0-9]+$"), verify_just_rcode_incorrect_format),
                MessageHandler(Filters.regex("^[0-9]+$"), verify_just_rcode_get_rcode),
                CallbackQueryHandler(booking, pattern = "^" + "BACK"),

            ],
            LEVEL3_VERIFY: [
                MessageHandler(Filters.text, get_code_from_user),
                CallbackQueryHandler(booking, pattern = "^" + "BACK"),
            ],
            LEVEL1_CHECKOUT: [
                CallbackQueryHandler(checkout_rated),
                MessageHandler(Filters.text, checkout_comments)
            ],
            LEVEL1_PAYMENT: [
                CallbackQueryHandler(payment_options, pattern = "^" + "PEREVOD"),
                CallbackQueryHandler(payment_options, pattern = "^" + "CASH"),
                CallbackQueryHandler(my_booking_options, pattern = "^" + "BACK"),   
            ],
            LEVEL2_PAYMENT: [
                CallbackQueryHandler(my_booking_options, pattern = "^" + "BACK"),   
            ],
            LEVEL1_NEW_BOOKING:[
                CallbackQueryHandler(new_booking_select_checkout_date, pattern = "^" + "CALENDAR"),
                # MessageHandler(Filters.regex("\d{2}:\d{2}"), new_booking_select_checkout_date),
                
            ],
            LEVEL2_NEW_BOOKING: [
                CallbackQueryHandler(new_booking_select_room, pattern = "^" + "CALENDAR"),
            ],
            LEVEL3_NEW_BOOKING: [
                CallbackQueryHandler(new_booking_selected_room, pattern = "^" + "SELECT_ROOM"),
                CallbackQueryHandler(new_booking_photos_of_rooms, pattern = "^" + "PHOTOS_OF_ROOMS"),  
                CallbackQueryHandler(new_booking, pattern = "^" + "BACK"), 
                CallbackQueryHandler(booking, pattern = "^" + "CANCEL_NEW_BOOKING"), 
                              
            ],
            LEVEL4_NEW_BOOKING: [
                CallbackQueryHandler(new_booking_selected_room, pattern = "^" + "SELECT_ROOM"),
                CallbackQueryHandler(new_booking, pattern = "^" + "BACK"),
                CallbackQueryHandler(booking, pattern = "^" + "CANCEL_NEW_BOOKING"), 
   
                
            ],
            "LEVEL5_NEW_BOOKING": [
                MessageHandler(Filters.regex("([A-Z][a-z]+|[\\u0400-\\u04FF]+)\\s([A-Z][a-z]+|[\\u0400-\\u04FF]+)"), new_booking_get_name),
                MessageHandler(~Filters.regex("([A-Z][a-z]+|[\\u0400-\\u04FF]+)\\s([A-Z][a-z]+|[\\u0400-\\u04FF]+)"), new_booking_incorrect_format_name)
            ],
            "LEVEL6_NEW_BOOKING": [
                MessageHandler(~Filters.regex("^\+\d{1,15}$"), new_booking_incorrect_phonumber),
                MessageHandler(Filters.regex("^\+\d{1,15}$"), new_booking_get_phonumber),
            ],
            "LEVEL7_NEW_BOOKING": [
                MessageHandler(Filters.regex("[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}"), new_booking_get_email),
                MessageHandler(~Filters.regex("[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}"), new_booking_ask_email_again),
                CallbackQueryHandler(main_menu, pattern = "^" + "MAIN_MENU"),   
            ],
            "LEVEL8_NEW_BOOKING": [
                MessageHandler(Filters.regex("^[0-9]*$"), new_booking_get_number_of_guests),
                CallbackQueryHandler(new_booking_create_new_booking, pattern = "^" + "RIGHT_BOOKING"),  
                CallbackQueryHandler(new_booking, pattern = "^" + "NEW_BOOKING_AGAIN"), 
                CallbackQueryHandler(booking, pattern = "^" + "CANCEL_NEW_BOOKING"), 
                 
            ],
            "LEVEL9_NEW_BOOKING": [
                # MessageHandler(Filters.regex("^[0-9]*$"), new_booking_get_number_of_guests),
                CallbackQueryHandler(main_menu, pattern = "^" + "MAIN_MENU")   
            ],
            
            "LEVEL_ADMIN_HELP": [
                admin_help_conversation
            ],
            "BACK_TO_ASSIGN_ROOM":[
                assign_room_conversation
            ]
            
            
        },
        fallbacks=[
                # CommandHandler("start", start),
                CommandHandler("admin", main_end_conversation),
                MessageHandler(Filters.regex("Меню администратора"), main_end_conversation),
                CallbackQueryHandler(admin.approveCancelBooking, pattern= "^" + "ADMIN_CANCEL_BOOKING"),
                CallbackQueryHandler(admin.approveEditDatesBooking, pattern= "^" + "ADMIN_EDIT_DATES_BOOKING"),
                CallbackQueryHandler(admin.approveEditRoomBooking, pattern= "^" + "ADMIN_EDIT_ROOM_BOOKING"),
                
                CallbackQueryHandler(select_language, pattern = "^" + "LANGUAGE_SELECT"),
                CallbackQueryHandler(events, pattern = "^" + "EVENTS"),
                CallbackQueryHandler(about_hotel, pattern = "^" + "ABOUTHOTEL"),
                CallbackQueryHandler(booking, pattern = "^" + "BOOKING"),
                CallbackQueryHandler(checkin_main_menu, pattern ='^' + "CHECKIN_MAIN_MENU" ),
                CallbackQueryHandler(checkout_main_menu, pattern ='^' + "CHECKOUT_MAIN_MENU" ),
                CallbackQueryHandler(language_select_callback, pattern ='^' + "LANG" )
                
            ],
        allow_reentry = True,
        name="main_conversation",
        persistent=True,
    )
    
    # MessageHandler(Filters.regex("Меню администратора"), admin_menu)
    # CommandHandler("admin", admin.admin_menu),
    
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CallbackQueryHandler(admin.approveCancelBooking, pattern= "^" + "ADMIN_CANCEL_BOOKING"))
    dispatcher.add_handler(CallbackQueryHandler(admin.approveEditDatesBooking, pattern= "^" + "ADMIN_EDIT_DATES_BOOKING"))
    dispatcher.add_handler(CallbackQueryHandler(admin.approveEditRoomBooking, pattern= "^" + "ADMIN_EDIT_ROOM_BOOKING"))
    
    
    dispatcher.add_handler(CallbackQueryHandler(admin.bookings_all, pattern= "^" + "REGISTER_GUESTS"))
    
    admin_menu_conversation = ConversationHandler(
        entry_points= [
            CommandHandler("admin", admin.admin_menu),
            MessageHandler(Filters.regex("Меню администратора"), admin.admin_menu),
            
        ],
        states={
            "ADMIN_LEVEL1": [
                CallbackQueryHandler(admin.select_object, pattern = "^" + "ADMIN_SELECT_OBJECT"),
                CallbackQueryHandler(admin.admin_requests, pattern = "^" + "ADMIN_REQUESTS"),
                CallbackQueryHandler(admin.room_occupation_select_date, pattern = "^" + "ADMIN_ROOM_OCCUPATION_AUTO"),
                CallbackQueryHandler(admin.room_occupation, pattern = "^" + "ADMIN_ROOM_OCCUPATION"),
                # CallbackQueryHandler(admin.room_occupation_select_date, pattern = "^" + "ADMIN_ROOM_OCCUPATION"),
                CallbackQueryHandler(admin.bookings, pattern = "^" + "ADMIN_BOOKINGS"),
                CallbackQueryHandler(admin.admin_manage, pattern = "^" + "ADMIN_MANAGE"),
                CallbackQueryHandler(admin.admin_guests, pattern = "^" + "ADMIN_GUESTS"),
                CallbackQueryHandler(admin.admin_checked_in_guests, pattern = "^" + "ADMIN_CHECKED_IN_GUESTS"),
                CallbackQueryHandler(set_evening_notification, pattern = "^" + "ADMIN_EVENING_NOTIFY"),
                CallbackQueryHandler(set_morning_notification, pattern = "^" + "ADMIN_MORNING_NOTIFY"),
                CallbackQueryHandler(notifications_menu, pattern = "^" + "ADMIN_NOTIFICATION"),
                
                CallbackQueryHandler(admin.housekeeping_menu, pattern = "^" + "ADMIN_HOUSEKEEPING"),
                CallbackQueryHandler(admin.admin_available_rooms_menu, pattern = "^" + "ADMIN_AVAILABLE_ROOMS"),
                
            ],
            "ADMIN_AVAILABLE_ROOMS_LEVEL1": [
                CallbackQueryHandler(admin.admin_available_rooms_for_today, pattern = "^" + "FOR_TODAY"),
                CallbackQueryHandler(admin.admin_available_rooms_for_period, pattern = "^" + "FOR_DATES"),
                CallbackQueryHandler(admin.admin_menu_query, pattern = "^" + "BACK"),

            ],
            "ADMIN_AVAILABLE_ROOMS_LEVEL2": [
                # CallbackQueryHandler(admin.admin_available_rooms_for_today, pattern = "^" + "FOR_TODAY"),
                CallbackQueryHandler(admin.admin_available_rooms_for_period_get_checkin_date, pattern = "^" + "CALENDAR"),
                CallbackQueryHandler(admin.admin_available_rooms_menu, pattern = "^" + "BACK"),

            ],
            "ADMIN_AVAILABLE_ROOMS_LEVEL3": [
                # CallbackQueryHandler(admin.admin_available_rooms_for_today, pattern = "^" + "FOR_TODAY"),
                CallbackQueryHandler(admin.admin_available_rooms_for_period_get_checkout_date, pattern = "^" + "CALENDAR"),
                CallbackQueryHandler(admin.admin_available_rooms_menu, pattern = "^" + "BACK"),

            ],
            "ADMIN_NOTIFICATION_LEVEL1": [
                CallbackQueryHandler(set_daily_evening_notification, pattern = "^" + "ADMIN_DAILY_EVENING_NOTIFY"),
                CallbackQueryHandler(set_daily_morning_notification, pattern = "^" + "ADMIN_DAILY_MORNING_NOTIFY"),
                CallbackQueryHandler(set_nightly_no_ota, pattern = "^" + "ADMIN_NIGHTLY_NO_OTA"),
                CallbackQueryHandler(set_daily_convert, pattern = "^" + "ADMIN_DAILY_CONVERT_PRICES"),
                CallbackQueryHandler(admin.admin_menu_query, pattern = "^" + "BACK"),

            ],
            "ADMIN_REQUESTS_LEVEL1": [
                CallbackQueryHandler(admin.admin_requests_type)
            ],
            "ADMIN_REQUESTS_LEVEL2": [
                # CallbackQueryHandler(admin.admin_approve_requests, pattern = "^" + "APPROVE_REQUEST"),
                CallbackQueryHandler(admin.admin_approve_requests, pattern = adminRequests),
                CallbackQueryHandler(admin.admin_requests, pattern = "^" + "BACK"),   
            ],
            "ADMIN_ROOM_OCCUPATION_LEVEL1": [
                CallbackQueryHandler(admin.room_occupation_automatic, pattern = "^" + "CALENDAR"),
                CallbackQueryHandler(admin.admin_menu_query, pattern = "^" + "BACK")
            ],
            "ADMIN_ROOM_OCCUPATION_LEVEL2": [
                # CallbackQueryHandler(admin.room_occupation, pattern = "^" + "CALENDAR"),
                CallbackQueryHandler(admin.admin_menu_query, pattern = "^" + "BACK")
            ],
            "ADMIN_BOOKING_LEVEL1": [
                CallbackQueryHandler(admin.bookings_choose_day, pattern = "^" + "ADMIN_CHOOSE_DAY"),
                CallbackQueryHandler(admin.bookings_all, pattern = "^" + "ADMIN_THIS_DAY"),
                CallbackQueryHandler(admin.admin_menu_query, pattern = "^" + "BACK")
                
            ],
            "ADMIN_BOOKING_LEVEL2": [
                CallbackQueryHandler(admin.bookings_day_choosed, pattern = "^" + "CALENDAR"),
                
            ],
            "ADMIN_BOOKING_LEVEL3": [
                CallbackQueryHandler(admin.bookings, pattern = "^" + "BACK_TODAY_BOOKINGS"),
                CallbackQueryHandler(admin.bookings, pattern = "^" + "BACK"),
                CallbackQueryHandler(admin.choose_no_show_or_register, pattern = check_callback_register_checkin_guest),
                CallbackQueryHandler(admin.register_guests_checkout, pattern = check_callback_register_checkout_guest)
            ],
            "ADMIN_BOOKING_CHECKOUT_LEVEL4": [
                CallbackQueryHandler(admin.guest_checkout_additional_comment, pattern = "^" + "OTHER_COMMENTS"),
                CallbackQueryHandler(admin.guest_checkout_done, pattern = "^" + "CHECKOUT_DONE"),
                CallbackQueryHandler(admin.bookings_all, pattern = "^" + "CANCEL_CHECKOUT"),
                CallbackQueryHandler(admin.edit_checkout_status, pattern = dict),   
            ],
            "ADMIN_BOOKING_CHECKOUT_LEVEL5": [
                MessageHandler(Filters.text, admin.guest_checkout_get_additional_comment),
                CallbackQueryHandler(admin.register_guests_checkout, pattern = "^" + "CANCEL_ADDITIONAL_COMMENT"),
                # CallbackQueryHandler(admin.edit_checkout_status, pattern = dict),   
            ],
            "ADMIN_BOOKING_LEVEL34":[
                CallbackQueryHandler(admin.register_guests_checkin, pattern = check_callback_register_checkin_guest),
                CallbackQueryHandler(admin.no_show_guest_checkin_choose_penalty, pattern = check_callback_register_no_show_guest),
                CallbackQueryHandler(admin.bookings_all, pattern = "^" + "RETURN_TODAY"),
                CallbackQueryHandler(admin.bookings_day_choosed, pattern = "^" + "RETURN_DAY_CHOOSED"),
                
            ],
            "ADMIN_BOOKING_NO_SHOW_LEVEL1":[
                CallbackQueryHandler(admin.no_show_guest_checkin, pattern = check_callback_register_no_show_guest),
                CallbackQueryHandler(admin.choose_no_show_or_register, pattern = "^"+"BACK"),
                
            ],
            "ADMIN_BOOKING_NO_SHOW_LEVEL2":[
                CallbackQueryHandler(admin.bookings_all, pattern = "^" + "RETURN_TODAY"),
                CallbackQueryHandler(admin.bookings_day_choosed, pattern = "^" + "RETURN_DAY_CHOOSED"),
                CallbackQueryHandler(admin.admin_menu_query, pattern = "^" + "RETURN_MAIN_MENU"),  

            ],
            "ADMIN_BOOKING_LEVEL4": [
                MessageHandler(Filters.photo, admin.register_guest_get_passport),
                CallbackQueryHandler(admin.bookings_all, pattern = check_callback_cancel_checkin_all),
                CallbackQueryHandler(admin.bookings_day_choosed, pattern = check_callback_cancel_checkin_day_choosed),
                
            ],
            "ADMIN_BOOKING_LEVEL5": [
                CallbackQueryHandler(admin.register_guest_get_payment_type, pattern = "^" + "FULL_PAYMENT"), 
                CallbackQueryHandler(admin.register_guest_get_payment_type, pattern = "^" + "PARTIAL_PAYMENT"), 
                CallbackQueryHandler(admin.register_guest_get_payment_total, pattern = "^" + "PAYMENT_NOT_NEEDED"), 
                CallbackQueryHandler(admin.register_guest_get_payment_total, pattern = "^" + "PAYMENT_NOT_PAID"), 
                CallbackQueryHandler(admin.register_guests_checkin, pattern = "^" + "BACK"), 

            ],
            "ADMIN_BOOKING_LEVEL56": [
                CallbackQueryHandler(admin.register_guest_get_payment, pattern = "^" + "PAYMENT_SBER"),
                CallbackQueryHandler(admin.register_guest_get_payment, pattern = "^" + "PAYMENT_FINKA"),
                CallbackQueryHandler(admin.register_guest_get_payment, pattern = "^" + "PAYMENT_CASH"),
                CallbackQueryHandler(admin.register_guest_get_passport, pattern = "^" + "BACK"), 
                

            ],
            "ADMIN_BOOKING_LEVEL6": [
                CallbackQueryHandler(admin.register_guest_get_payment_currency, pattern = "^" + "USD"),
                CallbackQueryHandler(admin.register_guest_get_payment_currency, pattern = "^" + "KGS"),
                CallbackQueryHandler(admin.register_guest_get_payment_currency, pattern = "^" + "RUB"), 
                CallbackQueryHandler(admin.register_guest_get_payment_type, pattern = "^" + "BACK"), 

            ],
            "ADMIN_BOOKING_LEVEL7": [
                MessageHandler(Filters.regex("^(\d+\.?\d*|\.\d+)$"), admin.register_guest_get_payment_total),
                CallbackQueryHandler(admin.register_guest_get_payment, pattern = "^" + "BACK"), 
                
            ],
            "ADMIN_BOOKING_LEVEL8": [
                CallbackQueryHandler(admin.bookings_all, pattern = "^" + "RETURN_TODAY"),
                CallbackQueryHandler(admin.bookings_day_choosed, pattern = "^" + "RETURN_DAY_CHOOSED"),
                CallbackQueryHandler(admin.admin_menu_query, pattern = "^" + "RETURN_MAIN_MENU"),  
                CallbackQueryHandler(admin.register_guest_get_passport, pattern = "^" + "BACK_PAYMENT_QUERY$"), 
                CallbackQueryHandler(admin.register_guest_get_payment_currency, pattern = "^" + "BACK_PAYMENT_TOTAL$"), 


            ],
            "ADMIN_MANAGE_LEVEL1": [
                CallbackQueryHandler(admin.bookings, pattern = "^" + "ADMIN_CASSA"),
                CallbackQueryHandler(admin.admin_manage_guests, pattern = "^" + "ADMIN_GUEST"),
                CallbackQueryHandler(admin.admin_menu_query, pattern = "^" + "BACK")
            ],
            "ADMIN_MANAGE_LEVEL2": [
                CallbackQueryHandler(admin.admin_manage_search_by_name, pattern="^"+"ADMIN_SEARCH_BY_NAME"),
                CallbackQueryHandler(admin.admin_manage_search_by_phonenumber, pattern="^"+"ADMIN_SEARCH_BY_PHONE"),
                CallbackQueryHandler(admin.admin_manage_search_by_email, pattern="^"+"ADMIN_SEARCH_BY_EMAIL"),
                CallbackQueryHandler(admin.admin_manage_get_checkin_today, pattern="^"+"ADMIN_SEARCH_TODAY"),
                CallbackQueryHandler(admin.admin_manage, pattern = "^" + "BACK")
                
            ],
            "ADMIN_MANAGE_NAME_LEVEL3": [
                MessageHandler(Filters.text, admin.admin_manage_get_search_by_name),
                CallbackQueryHandler(admin.admin_manage_guests, pattern = "^" + "BACK") 
            ],
            "ADMIN_MANAGE_LEVEL4": [
                CallbackQueryHandler(admin.admin_manage_edit_search, pattern = check_callback_admin_search),
                CallbackQueryHandler(admin.admin_manage_guests, pattern = "^" + "BACK") 
            ],
            "ADMIN_MANAGE_LEVEL5": [
                CallbackQueryHandler(admin.approve_status, pattern = check_callback_approve_status),
                CallbackQueryHandler(admin.admin_manage_guests, pattern = "^" + "BACK") 

            ],
            "ADMIN_MANAGE_NAME_LEVEL4": [
                CallbackQueryHandler(admin.admin_manage_edit_search, pattern = check_callback_admin_search),
                CallbackQueryHandler(admin.admin_manage_guests, pattern = "^" + "BACK") 
            ],
            "ADMIN_MANAGE_NAME_LEVEL5": [
                CallbackQueryHandler(admin.approve_status, pattern = check_callback_approve_status),
                CallbackQueryHandler(admin.admin_manage_guests, pattern = "^" + "BACK") 

            ],
            "ADMIN_MANAGE_PHONENUMBER_LEVEL3": [
                MessageHandler(Filters.regex("\+\d{11}"), admin.admin_manage_get_search_by_phonenumber),
                MessageHandler(~Filters.regex("\+\d{11}"), admin.admin_incorrect_phonenumber),
                CallbackQueryHandler(admin.admin_manage_guests, pattern = "^" + "BACK") 
            ],
            "ADMIN_MANAGE_PHONENUMBER_LEVEL4": [
                CallbackQueryHandler(admin.admin_manage_edit_search_by_phonenumber, pattern = "^" + "CHOOSE_BOOKING"),
                CallbackQueryHandler(admin.admin_manage_guests, pattern = "^" + "BACK") 
            ],
            "ADMIN_MANAGE_EMAIL_LEVEL3": [
                MessageHandler(Filters.regex("[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"), admin.admin_manage_get_search_by_email),
                MessageHandler(~Filters.regex("[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"), admin.admin_incorrect_email),
                CallbackQueryHandler(admin.admin_manage_guests, pattern = "^" + "BACK") 
            ],
            "ADMIN_MANAGE_EMAIL_LEVEL4": [
                CallbackQueryHandler(admin.admin_manage_edit_search_by_phonenumber, pattern = "^" + "CHOOSE_BOOKING"),
                CallbackQueryHandler(admin.admin_manage_guests, pattern = "^" + "BACK") 
            ],
            "ADMIN_MANAGE_CHECKIN_TODAY_LEVEL4": [
                CallbackQueryHandler(admin.admin_manage_edit_checkin_today, pattern = "^" + "CHOOSE_BOOKING"),
                CallbackQueryHandler(admin.admin_manage_guests, pattern = "^" + "BACK") 
            ],
            "ADMIN_GUESTS_LEVEL1": [
                CallbackQueryHandler(admin.admin_guests_status_checkin, pattern = "^" + "CHECKIN_TODAY"),
                CallbackQueryHandler(admin.admin_guests_status_checkout, pattern = "^" + "CHECKOUT_TODAY"),
                CallbackQueryHandler(admin.admin_menu_query, pattern = "^" + "BACK"),
                CallbackQueryHandler(admin.admin_guests_status_without_checkin_and_checkout, pattern = check_callback_guest),
            ],
            "ADMIN_GUESTS_LEVEL2": [
                CallbackQueryHandler(admin.status_page_callback, pattern='^character#'),
                CallbackQueryHandler(admin.admin_pages_guest, pattern='^guest#'),
                CallbackQueryHandler(admin.admin_guests, pattern = "^" + "BACK"),

            ],
            "ADMIN_GUESTS_LEVEL3": [
                # CallbackQueryHandler(admin.status_page_callback, pattern=check_callback_status),
            ],
            "ADMIN_CHECKED_IN_LEVEL1": [
                CallbackQueryHandler(admin.status_checked_in_page_callback, pattern='^character#'),
                CallbackQueryHandler(admin.admin_pages_checked_in_guest, pattern='^guest#'),
                CallbackQueryHandler(admin.admin_checked_in_guest_add_passport, pattern='^ADD_PASSPORT'),
                CallbackQueryHandler(admin.admin_checked_in_guest_add_payment, pattern='^ADD_PAYMENT'),
                CallbackQueryHandler(admin.admin_menu_query, pattern = "^" + "BACK"),
            ],
            "ADMIN_CHECKED_IN_LEVEL2": [
                CallbackQueryHandler(admin.admin_checked_in_guest_get_payment, pattern = "^" + "PAYMENT_SBER"),
                CallbackQueryHandler(admin.admin_checked_in_guest_get_payment, pattern = "^" + "PAYMENT_FINKA"),
                CallbackQueryHandler(admin.admin_checked_in_guest_get_payment, pattern = "^" + "PAYMENT_CASH"), 
                CallbackQueryHandler(admin.admin_checked_in_guest_get_payment_total, pattern = "^" + "PAYMENT_NOT_NEEDED"), 
                CallbackQueryHandler(admin.admin_checked_in_guest_get_payment_total, pattern = "^" + "PAYMENT_NOT_PAID"), 
                MessageHandler(Filters.photo, admin.admin_checked_in_guest_get_passport),
            ],
            "ADMIN_CHECKED_IN_LEVEL3": [
                CallbackQueryHandler(admin.admin_checked_in_guest_get_payment_currency, pattern = "^" + "USD"),
                CallbackQueryHandler(admin.admin_checked_in_guest_get_payment_currency, pattern = "^" + "KGS"),
                CallbackQueryHandler(admin.admin_checked_in_guest_get_payment_currency, pattern = "^" + "RUB"), 
                MessageHandler(Filters.regex("^(\d+\.?\d*|\.\d+)$"), admin.admin_checked_in_guest_get_payment_total)

            ],
            "ADMIN_HOUSEKEEPING_LEVEL1":[
                CallbackQueryHandler(admin.housekeeping_add_maid, pattern = "^" + "ADD_MAID"),
                CallbackQueryHandler(admin.admin_menu_query, pattern = "^" + "BACK"),
            ],
            "ADMIN_HOUSEKEEPING_LEVEL2":[
                MessageHandler(Filters.regex("([A-Z][a-z]+|[\\u0400-\\u04FF]+)\\s([A-Z][a-z]+|[\\u0400-\\u04FF]+)"), admin.housekeeping_get_maid_name),
                CallbackQueryHandler(admin.housekeeping_menu, pattern = "^" + "BACK"),
            ]
            
        },
        fallbacks=[
                # CommandHandler("start", start),
                # CommandHandler("admin", admin.admin_menu),
                CommandHandler("start", admin.admin_end_conversation),
                # CommandHandler("admin", admin.admin_end_conversation),
            ],
        allow_reentry = True,
        name="admin_conversation",
        persistent=True
    )
    
    
    
    # dispatcher.add_handler(starting_conversation)
    
    dispatcher.add_handler(admin_menu_conversation, group=1)
    
    dispatcher.add_handler(main_menu_conversation, group = 2)
    
    dispatcher.add_handler(admin_guest_payment_conversation)
    
    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()
