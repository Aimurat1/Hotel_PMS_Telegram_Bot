from telegram import ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup, Update, ForceReply, KeyboardButton, ReplyKeyboardMarkup,InputMediaPhoto, ParseMode, ChatAction
from telegram.ext import Defaults, InvalidCallbackData, PicklePersistence, CallbackQueryHandler, Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler
import time
import firebase_with_api as firebase

from constants.admin_id import admin_id_arr

from utils.currency_converter import convert_currency, convert_to_usd

from utils.delete_message import set_delete_message
import copy

import ver2_api

LEVEL1, LEVEL2, LEVEL3, LEVEL3_ABOUT_HOTEL, LEVEL3_EVENTS, LEVEL4_ABOUT_HOTEL, LEVEL5_ABOUT_HOTEL, LEVEL3_BOOKING, LEVEL34_BOOKING, LEVEL4_BOOKING, LEVEL5_BOOKING, LEVEL6_BOOKING, LEVEL1_VERIFY, LEVEL2_VERIFY, LEVEL3_VERIFY,LEVEL7_CHECKIN, LEVEL7_CHECKOUT, LEVEL7_BOOKING, LEVEL1_CHECKOUT, LEVEL1_PAYMENT, LEVEL2_PAYMENT, LEVEL1_NEW_BOOKING, LEVEL2_NEW_BOOKING, LEVEL3_NEW_BOOKING, LEVEL4_NEW_BOOKING, LEVEL34_SELECT_BOOKING= range(26)


def guest_payment_final(update, context):
    
    guest_payment_final_dict = context.user_data['guest_payment_final']
    
    eval(guest_payment_final_dict['next_func'])
    
    print(guest_payment_final_dict['next_state'])
    
    return guest_payment_final_dict['next_state']

def guest_payment_starting_func(update: Update, context: CallbackContext):
    try:
        query = update.callback_query
        # print(query)
        message_type = "query"
    except:
        message_type = "send"
    
    if message_type == "query":
        chat_id = update.callback_query.message.chat_id
        telegram_id = update.callback_query.from_user.id
        telegram_username = update.callback_query.from_user.username
        
        query.message.delete()
        
        
    elif message_type == "send":
        chat_id = update.message.chat_id  
        telegram_id = update.message.from_user.id
        telegram_username = update.message.from_user.username
  
        
    message_text = "Давайте проверим, все ли услуги оплачены, это займет меньше минуты."
    
    
    context.user_data['guest_payment_messages'] = []
    text_message = context.bot.send_message(chat_id, text = message_text)
    # context.user_data['guest_payment_messages'].append(mes)
    
    sticker_message = context.bot.send_sticker(chat_id, sticker = "CAACAgIAAxkBAAEJJzRkddbTrIVo_qAzzddwW_YDJ41N6wAC_igAAtayOUnlq6M2ad-OMS8E")
    # context.user_data['guest_payment_messages'].append(mes)
    
    # time.sleep(2)
    
    context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
    
    booking = context.user_data['booking']
    
    user = firebase.getBookingById(booking['user_id'], booking['id'])
    user_id, booking_id = user['booking']['user_id'], user['booking']['id']
    
    booking = user['booking']
    
    total_price = booking['price']
    payment_amount = 0 if "payment_total" not in booking.keys() else booking['payment_total_in_USD']

    payment_needed = round(float(total_price) - float(payment_amount), 2)
    
    context.user_data['booking']['payment_needed'] = payment_needed
    
    firebase.updateBookingWithId(user_id, booking_id, {'payment_needed': float(payment_needed)})
    
    firebase.setTelegramDetailsToUserByID(booking['user_id'], telegram_username, telegram_id)
    
    guest_payment_final_dict = context.user_data['guest_payment_final']
    
    keyboard = [
        [InlineKeyboardButton(text = "🔙 Назад", callback_data=f"{guest_payment_final_dict['next_state']}")]
    ]
    
    status = firebase.getStatusFromGuestBookingID(user_id, booking_id)
    
    if "payment_status" in status.keys() and status['payment_status'] == "WAITING_APPROVE":
        
        context.user_data['guest_payment_wait_approve'] = True
        text_message.edit_text(text = "Нужно дождаться подтверждения администратора перед тем как сделать новую оплату", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        if(booking['channel_name'] == "Airbnb" or payment_needed == 0 or ("payment_total" in booking.keys() and booking['payment_total'] == "NOT NEEDED")):
            text_message.edit_text(text = "Я проверила ваше бронирование, все услуги оплачены. Вы молодец!", reply_markup=InlineKeyboardMarkup(keyboard))
            sticker_message.delete()
            sticker_message = context.bot.send_sticker(chat_id, sticker = "CAACAgIAAxkBAAEJKARkdj_xErN8BfJJkYYSZEbPRy-WLQACVCYAAnVOOUn9roMfpcFDhS8E")
            
            
            set_delete_message(context, "delete_sticker", 20, sticker_message.chat_id, sticker_message.message_id)
        else:
            
            user = firebase.getBookingById(booking['user_id'], booking['id'])
            
            callback_dict = {
                'type': "GET_GUEST_NO_CASH_PAYMENT",
                'user': user
            }
            
            keyboard = [
                [InlineKeyboardButton(text = "Наличный расчет", callback_data="CASH")],
                # [InlineKeyboardButton(text = "Безналичный расчет", callback_data="NOT_CASH")],
                [InlineKeyboardButton(text = "Перевод с РФ карты по СБП на Сбербанк", callback_data=guest_payment_generate_callback({"payment_type": "Сбер"}, callback_dict))],
                [InlineKeyboardButton(text = "Перевод с КР карты на Финкабанк", callback_data=guest_payment_generate_callback({"payment_type": "Финка"}, callback_dict))],

                [InlineKeyboardButton(text = "Оплатить позже", callback_data = "NO_PAYMENT")]
            ]
            
            room_type = ""
            
            context.user_data['guest_payment_sticker_message'] = sticker_message
            
            for i, room in enumerate(booking['room_type']):
                room_type += room
                if i != len(booking['room_type']) - 1:
                    room_type += " "
            
            
            text_message.edit_text(text = f"""
Вы забронировали номер {room_type}. 
<b>Полная стоимость:</b> {booking['price']} {booking['currency']} | {convert_currency(booking['currency'], "KGS", booking['price'])} KGS | {convert_currency(booking['currency'], "RUB", booking['price'])} RUB.
{f"<b>Вы внесли:</b> {convert_currency(booking['payment_currency'], 'USD', booking['payment_total']) } USD | {convert_currency(booking['payment_currency'], 'KGS', booking['payment_total'])} KGS | {convert_currency(booking['payment_currency'], 'RUB', booking['payment_total'])} RUB." if "payment_total" in booking.keys() else ""} 
<b>К оплате: </b> {payment_needed} {booking['currency']} | {convert_currency(booking['currency'], "KGS", payment_needed)} KGS | {convert_currency(booking['currency'], "RUB", payment_needed)} RUB. Как будете платить?  
                               """, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
        
    return "LEVEL1_GUEST_PAYMENT"

def check_guest_payment_callback(callback) -> bool:
    if type(callback) == dict and ("type" in callback.keys()) and callback['type'] == "GET_GUEST_PAYMENT":
        return True
    else:
        return False
    
def guest_payment_generate_callback(update_dict, callback_dict):
    callback_dict = copy.copy(callback_dict)
    callback_dict.update(update_dict)
    # callback_dict['payment_type'] = payment_type
    return callback_dict
    
def guest_payment_cash_payment(update: Update, context: CallbackContext):

    query = update.callback_query
    
    query.edit_message_text(text = f"""
Хорошо 👌🏻. Я сообщу администратору, он заберет вашу оплату. Администратор подойдет в зону ресепшн в течение получаса!
                            """)
    
    context.user_data['guest_payment_sticker_message'].delete()
    
    context.bot.send_sticker(chat_id = query.message.chat_id, sticker = "CAACAgIAAxkBAAEJKDdkdkTzNXjhISPiK62ZpLl7ZVPFqAACUysAAsojOUkhSBZ08KHEQC8E")

    
    booking = context.user_data['booking']
    user = firebase.getBookingById(booking['user_id'], booking['id'])
    user_id, booking_id = user['booking']['user_id'], user['booking']['id']
    
    firebase.updateBookingWithId(user_id, booking_id, {"payment_type": "Наличные"})
    
    room_type = ""
    
    callback_dict = {
        'type': "GET_GUEST_PAYMENT",
        'user': user
    }
    
    
    keyboard = [
        [InlineKeyboardButton(text = "Внести частичную оплату", callback_data=guest_payment_generate_callback({"payment_type": "PARTIAL_PAYMENT"}, callback_dict))],
        [InlineKeyboardButton(text = "Внести полную оплату", callback_data=guest_payment_generate_callback({"payment_type": "FULL_PAYMENT"}, callback_dict))],
        # [InlineKeyboardButton(text = "Без оплаты", callback_data=guest_payment_generate_callback({"payment_type": "NO_PAYMENT"}, callback_dict))],
    ]
        
    firebase.approveStatusFromGuestBookingID(user_id, booking_id, "payment_status", "WAITING_APPROVE")
        
    for room in user['booking']['room_type']:
        room_type += room
        room_type += " "
        
    for admin in admin_id_arr:
        
        # context.dispatcher.user_data[int(admin)].update({"guest_payment_booking": {}})
        # context.dispatcher.update_persistence()
        message_text = f"""
❗❗❗<b>ВНИМАНИЕ</b>❗❗❗
Гость <b>{user['name']} {user['lastname']}</b> хочет произвести оплату.
С {user['booking']['checkin_date']} по {user['booking']['checkout_date']} - {room_type}
<b>Полная сумма:</b> {user['booking']['price']} {user['booking']['currency']} | {convert_currency(user['booking']['currency'], "KGS", user['booking']['price'])} KGS | {convert_currency(user['booking']['currency'], "RUB", user['booking']['price'])} RUB"""
        
        if "payment_total" in context.user_data['booking'].keys():
            message_text += f"""
            
<b>Уже внесено: </b> {convert_currency(user['booking']['payment_currency'], "USD", user['booking']['payment_total'])} USD | {convert_currency(user['booking']['payment_currency'], "KGS", user['booking']['payment_total'])} KGS | {convert_currency(user['booking']['payment_currency'], "RUB", user['booking']['payment_total'])} RUB
<b>Необходимо оплатить:</b> {user['booking']['payment_needed']} USD | {convert_currency(user['booking']['currency'], "KGS", user['booking']['payment_needed'])} KGS | {convert_currency(user['booking']['currency'], "RUB", user['booking']['payment_needed'])} RUB

Выбирайте полную оплату, если гость вносит всю сумму долга.
"""
        
        mes = context.bot.send_message(chat_id = admin, text = message_text, parse_mode = ParseMode.HTML, reply_markup = InlineKeyboardMarkup(keyboard))

        print("Message id: " + str(mes.chat_id))
        # context.dispatcher.user_data[int(admin)].update({'guest_payment_message': mes})
        # context.dispatcher.update_persistence()
        
        if "guest_payment_booking" not in context.dispatcher.user_data[int(admin)].keys():
            context.dispatcher.user_data[int(admin)].update({"guest_payment_booking": {}})

        guest_payment_booking = context.dispatcher.user_data[int(admin)]['guest_payment_booking']
        # user['booking']['payment_status'] = payment_status
        user_dict = user
        user_dict['payment_message'] = copy.copy(mes)
        guest_payment_booking[str(booking_id)] = copy.copy(user_dict)
        
        context.dispatcher.user_data[int(admin)].update({'guest_payment_booking': guest_payment_booking})
        context.dispatcher.update_persistence()


        # context.user_data['guest_payment_booking'][booking_id]
        
    return "LEVEL2_GUEST_PAYMENT"

def guest_payment_no_payment(update: Update, context: CallbackContext):

    query = update.callback_query
    
    query.edit_message_text(text = f"""
Хорошо 👌🏻. Только не забудь вовремя все оплатить
                            """)
    
    context.user_data['guest_payment_sticker_message'].delete()
    

    
    booking = context.user_data['booking']
    user = firebase.getBookingById(booking['user_id'], booking['id'])
    user_id, booking_id = user['booking']['user_id'], user['booking']['id']
    
    
    if "payment_total" not in user['booking'].keys():
        firebase.updateBookingWithId(user_id, booking_id, {"payment_total": "DELETE_FIELD", "payment_status": "NO_PAYMENT"})
    
    
    room_type = ""
        
    firebase.approveStatusFromGuestBookingID(user_id, booking_id, "payment_status", "APPROVED")
        
    for room in user['booking']['room_type']:
        room_type += room
        room_type += " "
        
    for admin in admin_id_arr:
        
        # context.dispatcher.user_data[int(admin)].update({"guest_payment_booking": {}})
        # context.dispatcher.update_persistence()
        
#         message_text = f"""
# 🔴<b> Гость {user['name']} {user['lastname']} пока не внес оплату </b>🔴
# С {user['booking']['checkin_date']} по {user['booking']['checkout_date']} - {room_type}
# <b>Сумма для оплаты:</b> {user['booking']['price']} {user['booking']['currency']} | {convert_currency(user['booking']['currency'], "KGS", user['booking']['price'])} KGS | {convert_currency(user['booking']['currency'], "RUB", user['booking']['price'])} RUB
#         """

        message_text = f"""
❗❗❗<b>ВНИМАНИЕ</b>❗❗❗
🔴<b> Гость {user['name']} {user['lastname']} пока не внес оплату </b>🔴
С {user['booking']['checkin_date']} по {user['booking']['checkout_date']} - {room_type}
<b>Полная сумма:</b> {user['booking']['price']} {user['booking']['currency']} | {convert_currency(user['booking']['currency'], "KGS", user['booking']['price'])} KGS | {convert_currency(user['booking']['currency'], "RUB", user['booking']['price'])} RUB"""
        
        if "payment_total" in context.user_data['booking'].keys():
            message_text += f"""
<b>Уже внесено: </b> {convert_currency(user['booking']['payment_currency'], "USD", user['booking']['payment_total'])} USD | {convert_currency(user['booking']['payment_currency'], "KGS", user['booking']['payment_total'])} KGS | {convert_currency(user['booking']['payment_currency'], "RUB", user['booking']['payment_total'])} RUB
<b>Необходимо оплатить:</b> {user['booking']['payment_needed']} USD | {convert_currency(user['booking']['currency'], "KGS", user['booking']['payment_needed'])} KGS | {convert_currency(user['booking']['currency'], "RUB", user['booking']['payment_needed'])} RUB
"""
        
        mes = context.bot.send_message(chat_id = admin, text = message_text, parse_mode = ParseMode.HTML)

        # context.user_data['guest_payment_booking'][booking_id]
        
    return "LEVEL2_GUEST_PAYMENT"

def guest_payment_no_cash_payment(update: Update, context: CallbackContext):

    query = update.callback_query
    
    payment_dict = {'PAYMENT_SBER': "Сбер", 'PAYMENT_FINKA': "Финка", "PAYMENT_CASH": "Наличные"}
        
    booking = context.user_data['booking']
    user = firebase.getBookingById(booking['user_id'], booking['id'])
    user_id, booking_id = user['booking']['user_id'], user['booking']['id']

    callback_dict = {
        'type': "GET_GUEST_NO_CASH_PAYMENT",
        'user': user
    }
    
    keyboard = [
        [InlineKeyboardButton(text = "Сбер", callback_data=guest_payment_generate_callback({"payment_type": "Сбер"}, callback_dict))],
        [InlineKeyboardButton(text = "Финка", callback_data=guest_payment_generate_callback({"payment_type": "Финка"}, callback_dict))],
    ]
        
    query.edit_message_text(text = f"""
У нас доступна оплата переводом, через что будете переводить?
""", reply_markup=InlineKeyboardMarkup(keyboard))
    
    context.user_data['guest_payment_sticker_message'].delete()
        # context.user_data['guest_payment_booking'][booking_id]
        
    return "LEVEL2_GUEST_PAYMENT"

def guest_payment_no_cash_payment_select_payment_type(update: Update, context: CallbackContext):
    query = update.callback_query
    
    chat_id = query.message.chat_id
    user = query.data['user']
    user_id, booking_id = user['booking']['user_id'], user['booking']['id']

    payment_type = query.data['payment_type']
    
    print(payment_type)
    
    firebase.updateBookingWithId(user_id, booking_id, {"payment_type": payment_type})
    
    query.edit_message_reply_markup(reply_markup=None)
    
    context.bot.send_message(chat_id, text = """
Сделайте скриншот чека после оплаты и отправьте сюда. Для отправки нажмите скрепку, что в углу экрана 📎
                            """)
    
    return "LEVEL3_GUEST_PAYMENT"

def guest_payment_no_cash_payment_get_screenshot(update: Update, context: CallbackContext):
    photos = update.message.photo
    chat_id = update.message.chat_id
    
    context.bot.send_message(chat_id, text = "Я получила твой скриншот и отправила его администратору. Когда администратор подтвердит платеж, тебе придет ответ!")
    
    print(photos)
    
    booking = context.user_data['booking']
    user = firebase.getBookingById(booking['user_id'], booking['id'])
    user_id, booking_id = user['booking']['user_id'], user['booking']['id']

    callback_dict = {
        'type': "GET_GUEST_PAYMENT",
        'user': user
    }
    
    keyboard = [
        [InlineKeyboardButton(text = "Внести частичную оплату", callback_data=guest_payment_generate_callback({"payment_type": "PARTIAL_PAYMENT"}, callback_dict))],
        [InlineKeyboardButton(text = "Внести полную оплату", callback_data=guest_payment_generate_callback({"payment_type": "FULL_PAYMENT"}, callback_dict))],
        # [InlineKeyboardButton(text = "Без оплаты", callback_data=guest_payment_generate_callback({"payment_type": "NO_PAYMENT"}, callback_dict))],
    ]


    room_type = ""
    
    for room in user['booking']['room_type']:
        room_type += room
        room_type += " "
    
    for admin in admin_id_arr:
        
        message_text = f"""
❗❗❗<b>ВНИМАНИЕ</b>❗❗❗
Гость <b>{user['name']} {user['lastname']}</b> хочет произвести оплату.
С {user['booking']['checkin_date']} по {user['booking']['checkout_date']} - {room_type}
<b>Полная сумма:</b> {user['booking']['price']} {user['booking']['currency']} | {convert_currency(user['booking']['currency'], "KGS", user['booking']['price'])} KGS | {convert_currency(user['booking']['currency'], "RUB", user['booking']['price'])} RUB"""
        
        if "payment_total" in context.user_data['booking'].keys():
            message_text += f"""
<b>Уже внесено: </b> {convert_currency(user['booking']['payment_currency'], "USD", user['booking']['payment_total'])} USD | {convert_currency(user['booking']['payment_currency'], "KGS", user['booking']['payment_total'])} KGS | {convert_currency(user['booking']['payment_currency'], "RUB", user['booking']['payment_total'])} RUB
<b>Необходимо оплатить:</b> {user['booking']['payment_needed']} USD | {convert_currency(user['booking']['currency'], "KGS", user['booking']['payment_needed'])} KGS | {convert_currency(user['booking']['currency'], "RUB", user['booking']['payment_needed'])} RUB
"""
        
        mes = context.bot.send_photo(chat_id = admin, photo = photos[0], caption = message_text, parse_mode = ParseMode.HTML, reply_markup = InlineKeyboardMarkup(keyboard))
        
        # context.dispatcher.user_data[int(admin)].update({'guest_payment_message': mes})
        # context.dispatcher.update_persistence()
        
        if "guest_payment_booking" not in context.dispatcher.user_data[int(admin)].keys():
            context.user_data["guest_payment_booking"] = {}

        guest_payment_booking = context.dispatcher.user_data[int(admin)]['guest_payment_booking']
        # user['booking']['payment_status'] = payment_status
        user_dict = user
        user_dict['payment_message'] = copy.copy(mes)
        guest_payment_booking[str(booking_id)] = copy.copy(user_dict)
        
        context.dispatcher.user_data[int(admin)].update({'guest_payment_booking': guest_payment_booking})
        context.dispatcher.update_persistence()
        
    return "LEVEL2_GUEST_PAYMENT"
    

def guest_payment_get_payment_status(update: Update, context: CallbackContext):

    query = update.callback_query
    query.answer()
    
    if len(query.message.photo) == 0:
        is_it_photo = False
    else:
        is_it_photo = True
        
    print(is_it_photo)
    
    payment_status = query.data['payment_type']
    
    user = query.data['user']
    user_id, booking_id = user['booking']['user_id'], user['booking']['id']

    
    # if "guest_payment_booking" not in context.user_data.keys():
    #     context.user_data["guest_payment_booking"] = {}

    # guest_payment_booking = context.user_data['guest_payment_booking']
    # user['booking']['payment_status'] = payment_status
    # guest_payment_booking[str(booking_id)] = user
    
    # context.user_data["guest_payment_booking"] = guest_payment_booking
    
    # firebase.updateBookingWithId(user_id, booking_id, {"payment_status": payment_status})
    
    context.user_data['guest_payment_booking'][booking_id]['booking']['payment_status'] = payment_status
    booking = context.user_data['guest_payment_booking'][booking_id]['booking']
    
    print("User ID: " + user_id + " Booking id: " + booking_id)
    print(user['name'])
    print(payment_status)
    
    room_type = ""
    
    for room in user['booking']['room_type']:
        room_type += room
        room_type += " "
    
    if is_it_photo:
        payment_type = user['booking']['payment_type']
        
        if payment_type == "Сбер":
            keyboard = [
                [InlineKeyboardButton(text = "Рубли", callback_data=f"G_PAY_CURR | RUB | {booking_id}")],
            ]
        elif payment_type == "Финка":
            keyboard = [
                [InlineKeyboardButton(text = "Сомы", callback_data=f"G_PAY_CURR | KGS | {booking_id}")],
            ]    
        
    else:
        keyboard = [
            [InlineKeyboardButton(text = "Доллары", callback_data=f"G_PAY_CURR | USD | {booking_id}")],
            [InlineKeyboardButton(text = "Сомы", callback_data=f"G_PAY_CURR | KGS | {booking_id}")],
            [InlineKeyboardButton(text = "Рубли", callback_data=f"G_PAY_CURR | RUB | {booking_id}")],
        ]
    
    # print(context.dispatcher.user_data[int(query.message.chat_id)]['guest_payment_booking'])
    
    if payment_status == "NO_PAYMENT":
        firebase.updateBookingWithId(user_id, booking_id, {"payment_total": "DELETE_FIELD", "payment_status": payment_status})
        
        # payment_message = context.user_data['guest_payment_message']
        payment_messages = []
        
        for admin_id in admin_id_arr:
            payment_messages.append(context.dispatcher.user_data[int(admin_id)]['guest_payment_booking'][booking_id]['payment_message'])
            
        room_type = ""
        
        for room in user['booking']['room_type']:
            room_type += room
            room_type += " "
            
        message_text = f"""
🔴<b> Гость {user['name']} {user['lastname']} пока не внес оплату </b>🔴
С {user['booking']['checkin_date']} по {user['booking']['checkout_date']} - {room_type}
<b>Сумма для оплаты:</b> {user['booking']['price']} {user['booking']['currency']} | {convert_currency(user['booking']['currency'], "KGS", user['booking']['price'])} KGS | {convert_currency(user['booking']['currency'], "RUB", user['booking']['price'])} RUB
        """
        
        for payment_message in payment_messages:
            if is_it_photo:
                payment_message.edit_caption(message_text, parse_mode = ParseMode.HTML)
            else:
                payment_message.edit_text(message_text, parse_mode = ParseMode.HTML)
        
    elif payment_status == "FULL_PAYMENT":
        

        firebase.updateBookingWithId(user_id, booking_id, {"payment_status": payment_status})

        message_text = f"""
Гость <b>{user['name']} {user['lastname']}</b> хочет произвести оплату.
С {user['booking']['checkin_date']} по {user['booking']['checkout_date']} - {room_type}
<b>Полная сумма:</b> {user['booking']['price']} {user['booking']['currency']} | {convert_currency(user['booking']['currency'], "KGS", user['booking']['price'])} KGS | {convert_currency(user['booking']['currency'], "RUB", user['booking']['price'])} RUB"""
        
        if "payment_total" in user['booking'].keys():
            message_text += f"""
<b>Уже внесено: </b> {convert_currency(user['booking']['payment_currency'], "USD", user['booking']['payment_total'])} USD | {convert_currency(user['booking']['payment_currency'], "KGS", user['booking']['payment_total'])} KGS | {convert_currency(user['booking']['payment_currency'], "RUB", user['booking']['payment_total'])} RUB
<b>Необходимо оплатить:</b> {user['booking']['payment_needed']} USD | {convert_currency(user['booking']['currency'], "KGS", user['booking']['payment_needed'])} KGS | {convert_currency(user['booking']['currency'], "RUB", user['booking']['payment_needed'])} RUB
"""
        
        message_text += f"""
Выберите валюту оплаты:"""
    
        if is_it_photo:
            query.edit_message_caption(caption = message_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
        else:
            query.edit_message_text(text = message_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
        
    elif payment_status == "PARTIAL_PAYMENT":
        
        firebase.updateBookingWithId(user_id, booking_id, {"payment_status": payment_status})

        message_text = f"""
Гость <b>{user['name']} {user['lastname']}</b> хочет произвести оплату.
С {user['booking']['checkin_date']} по {user['booking']['checkout_date']} - {room_type}
<b>Полная сумма:</b> {user['booking']['price']} {user['booking']['currency']} | {convert_currency(user['booking']['currency'], "KGS", user['booking']['price'])} KGS | {convert_currency(user['booking']['currency'], "RUB", user['booking']['price'])} RUB"""
        
        if "payment_total" in user['booking'].keys():
            message_text += f"""
<b>Уже внесено: </b> {convert_currency(user['booking']['payment_currency'], "USD", user['booking']['payment_total'])} USD | {convert_currency(user['booking']['payment_currency'], "KGS", user['booking']['payment_total'])} KGS | {convert_currency(user['booking']['payment_currency'], "RUB", user['booking']['payment_total'])} RUB
<b>Необходимо оплатить:</b> {user['booking']['payment_needed']} USD | {convert_currency(user['booking']['currency'], "KGS", user['booking']['payment_needed'])} KGS | {convert_currency(user['booking']['currency'], "RUB", user['booking']['payment_needed'])} RUB
"""
        
        message_text += f"""
Выберите валюту оплаты:"""
        
        if is_it_photo:
            query.edit_message_caption(caption = message_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
        else:
            query.edit_message_text(text = message_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)

    
    return "ADMIN_LEVEL3_GUEST_PAYMENT"

def guest_payment_get_payment_currency(update: Update, context: CallbackContext):

    query = update.callback_query
    
    query.answer()
    
    if len(query.message.photo) == 0:
        is_it_photo = False
    else:
        is_it_photo = True
    
    payment_currency = query.data.split(" | ")[1]
    booking_id = query.data.split(" | ")[2]
    
    user = context.user_data['guest_payment_booking'][booking_id]
    user_id, booking_id = user['booking']['user_id'], user['booking']['id']
    
    old_payment_currency = user['booking']['payment_currency']

    context.user_data['guest_payment_booking_id'] = booking_id

    payment_status = user['booking']['payment_status']
    
    context.user_data['guest_payment_booking'][booking_id]['booking']['payment_currency'] = payment_currency
    context.user_data['guest_payment_booking'][booking_id]['booking']['old_payment_currency'] = old_payment_currency
    
    firebase.updateBookingWithId(user_id, booking_id, {"payment_currency": payment_currency, 'old_payment_currency': old_payment_currency})


    print("User ID: " + user_id + " Booking id: " + booking_id)
    print(user['name'])
    print(payment_currency)
    print(payment_status)
    
    room_type = ""
    
    for room in user['booking']['room_type']:
        room_type += room
        room_type += " "
    
    if payment_status == "PARTIAL_PAYMENT":
        
        
        message_text = f"""
Гость <b>{user['name']} {user['lastname']}</b> хочет произвести оплату.
С {user['booking']['checkin_date']} по {user['booking']['checkout_date']} - {room_type}
<b>Полная сумма:</b> {user['booking']['price']} {user['booking']['currency']} | {convert_currency(user['booking']['currency'], "KGS", user['booking']['price'])} KGS | {convert_currency(user['booking']['currency'], "RUB", user['booking']['price'])} RUB"""
        
        if "payment_total" in user['booking'].keys():
            message_text += f"""
<b>Уже внесено: </b> {convert_currency(user['booking']['old_payment_currency'], "USD", user['booking']['payment_total'])} USD | {convert_currency(user['booking']['old_payment_currency'], "KGS", user['booking']['payment_total'])} KGS | {convert_currency(user['booking']['old_payment_currency'], "RUB", user['booking']['payment_total'])} RUB"""

        
                
        message_text += f"""
<b>Необходимо оплатить:</b> {user['booking']['payment_needed']} USD | {convert_currency(user['booking']['currency'], "KGS", user['booking']['payment_needed'])} KGS | {convert_currency(user['booking']['currency'], "RUB", user['booking']['payment_needed'])} RUB
        
Введите сумму оплаты, в {payment_currency} (если в десятичных, то пишите через точку, пример: 32.12):"""
        
#         message_text = f"""
# Гость <b>{user['name']} {user['lastname']}</b> хочет произвести оплату.
# С {user['booking']['checkin_date']} по {user['booking']['checkout_date']} - {room_type}
# <b>Сумма для оплаты:</b> {user['booking']['price']} {user['booking']['currency']} | {convert_currency(user['booking']['currency'], "KGS", user['booking']['price'])} KGS | {convert_currency(user['booking']['currency'], "RUB", user['booking']['price'])} RUB
                              
# Введите сумму оплаты, в {payment_currency} (если в десятичных, то пишите через точку, пример: 32.12):"""
        
        if is_it_photo:
            query.edit_message_caption(message_text, parse_mode=ParseMode.HTML)
        else:
            query.edit_message_text(message_text, parse_mode=ParseMode.HTML)
   
    elif payment_status == "FULL_PAYMENT":
        firebase.approveStatusFromGuestBookingID(user_id, booking_id, "payment_status", "APPROVED")
        
        payment_total = convert_currency(user['booking']['currency'], payment_currency, user['booking']['price'])
        firebase.updateBookingWithId(user_id, booking_id, {"payment_total": payment_total, "payment_total_in_USD": user['booking']['price']})
        # payment_message = context.user_data['guest_payment_message']
        payment_messages = []
        
        for admin_id in admin_id_arr:
            payment_messages.append(context.dispatcher.user_data[int(admin_id)]['guest_payment_booking'][booking_id]['payment_message'])
        
            
        room_type = ""
        
        for room in user['booking']['room_type']:
            room_type += room
            room_type += " "
        
        message_text = f"""
🟢<b> Оплата успешно принята для гостя {user['name']} {user['lastname']} </b>🟢
С {user['booking']['checkin_date']} по {user['booking']['checkout_date']} - {room_type}
<b>Сумма для оплаты:</b> {user['booking']['price']} {user['booking']['currency']} | {convert_currency(user['booking']['currency'], "KGS", user['booking']['price'])} KGS | {convert_currency(user['booking']['currency'], "RUB", user['booking']['price'])} RUB
<b>Внесено гостем в общем:</b> {convert_currency(user['booking']['currency'], "USD", user['booking']['price'])} USD | {convert_currency(user['booking']['currency'], "KGS",  user['booking']['price'])} KGS | {convert_currency(user['booking']['currency'], "RUB",  user['booking']['price'])} RUB - {"Частичная оплата" if payment_status == "PARTIAL_PAYMENT" else "Полная оплата" if payment_status == "FULL_PAYMENT" else "Без оплаты"}
        
<b>Сумма внесена полностью</b>        
        """
        for payment_message in payment_messages:
            if is_it_photo:
                payment_message.edit_caption(message_text, parse_mode = ParseMode.HTML)
            else:
                payment_message.edit_text(message_text, parse_mode = ParseMode.HTML)
                
        keyboard = [
         [InlineKeyboardButton(text = "🔜 Далее", callback_data="CONTINUE")]
        ]
        
        context.bot.send_message(chat_id = user['telegram_id'], text = f"""
Ура, администратор подтвердил оплату. Оплата прошла успешно! Благодарю, что выбрали проживание в нашем отеле. Надеюсь, вам очень понравится!
                             """, reply_markup = InlineKeyboardMarkup(keyboard))
    
        sticker_message = context.bot.send_sticker(chat_id = user['telegram_id'], sticker = "CAACAgIAAxkBAAEJNZ9kfNSitwlAo6ULrcTkUKI1yonBjAACVCYAAnVOOUn9roMfpcFDhS8E")
        
        set_delete_message(context, "delete_sticker", 20, sticker_message.chat_id, sticker_message.message_id)
        
    return "ADMIN_LEVEL4_GUEST_PAYMENT"
    
def guest_payment_get_payment_total(update: Update, context: CallbackContext):
    
    payment_total = float(update.message.text)
    
    context.user_data['guest_payment_messages'] = []
    
    context.user_data['guest_payment_messages'].append(update.message)
    
    booking_id = context.user_data['guest_payment_booking_id']
    
    user = context.user_data['guest_payment_booking'][booking_id]
    user_id, booking_id = user['booking']['user_id'], user['booking']['id']
    
    payment_currency = user['booking']['payment_currency']
    
    if "payment_total" in user['booking'].keys():
        previous_payment_total = user['booking']['payment_total']
        previous_payment_currency = user['booking']['old_payment_currency']
    else:
        previous_payment_total = 0
        previous_payment_currency = payment_currency
        
    total_payment_total = convert_currency(previous_payment_currency, payment_currency, previous_payment_total) + payment_total
    

    firebase.updateBookingWithId(user_id, booking_id, {"payment_total": total_payment_total})
    
    
    payment_total_in_USD = convert_to_usd(payment_currency, total_payment_total)
    
    firebase.updateBookingWithId(user_id, booking_id, {"payment_total_in_USD": payment_total_in_USD})
    firebase.approveStatusFromGuestBookingID(user_id, booking_id, "payment_status", "APPROVED")

    mes = context.bot.send_message(chat_id = update.message.chat_id, text = "✅ Оплата успешно принята")

    context.user_data['guest_payment_messages'].append(mes)
    
    time.sleep(2)
    
    for message in context.user_data['guest_payment_messages']:
        message.delete()
        
    # payment_message = context.user_data['guest_payment_message']
    payment_messages = []
    
    for admin_id in admin_id_arr:
        # print(admin_id)
        mes = context.dispatcher.user_data[int(admin_id)]['guest_payment_booking'][booking_id]['payment_message']
        print("Loop: " + str(mes.chat_id))
        payment_messages.append(mes)
    
    
    
    payment_status = user['booking']['payment_status']
        
    room_type = ""
    
    for room in user['booking']['room_type']:
        room_type += room
        room_type += " "
        
    total_price = user['booking']['price']
    
    print(f"Total price: {total_price}")
    print(f"Guest total payment: {total_payment_total}")
    payment_amount = 0 if "payment_total" not in user['booking'].keys() else user['booking']['payment_total_in_USD']

    payment_needed = round(convert_currency(user['booking']['currency'] ,"USD", float(total_price)) - convert_currency(user['booking']['payment_currency'], "USD", float(total_payment_total)), 2)
    

        
    message_text = f"""
🟢<b> Оплата успешно принята для гостя {user['name']} {user['lastname']} </b>🟢
С {user['booking']['checkin_date']} по {user['booking']['checkout_date']} - {room_type}
<b>Общая стоимость:</b> {user['booking']['price']} {user['booking']['currency']} | {convert_currency(user['booking']['currency'], "KGS", user['booking']['price'])} KGS | {convert_currency(user['booking']['currency'], "RUB", user['booking']['price'])} RUB
<b>Внесено гостем в общем:</b> {convert_currency(payment_currency, "USD", total_payment_total)} USD | {convert_currency(payment_currency, "KGS", total_payment_total)} KGS | {convert_currency(payment_currency, "RUB", total_payment_total)} RUB - {"Частичная оплата" if payment_status == "PARTIAL_PAYMENT" else "Полная оплата" if payment_status == "FULL_PAYMENT" else "Без оплаты"}
   
<b>Необходимо внести:</b> {convert_currency("USD", "USD", payment_needed)} USD | {convert_currency("USD", "KGS", payment_needed)} KGS | {convert_currency("USD", "RUB", payment_needed)} RUB 
    """
    
    for payment_message in payment_messages:
        print(payment_message.chat_id)
        try:
            payment_message.edit_text(message_text, parse_mode = ParseMode.HTML)
        except:
            payment_message.edit_caption(message_text, parse_mode = ParseMode.HTML)
    
    
    keyboard = [
        [InlineKeyboardButton(text = "🔜 Далее", callback_data="CONTINUE")]
    ]
    context.bot.send_message(chat_id = user['telegram_id'], text = f"""
Ура, администратор подтвердил оплату. Оплата прошла успешно! Благодарю, что выбрали проживание в нашем отеле. Надеюсь, вам очень понравится!
                             """, reply_markup = InlineKeyboardMarkup(keyboard))
    
    sticker_message = context.bot.send_sticker(chat_id = user['telegram_id'], sticker = "CAACAgIAAxkBAAEJNZ9kfNSitwlAo6ULrcTkUKI1yonBjAACVCYAAnVOOUn9roMfpcFDhS8E")
    
    set_delete_message(context, "delete_sticker", 20, sticker_message.chat_id, sticker_message.message_id)

guest_payment_conversation = ConversationHandler(
    entry_points= [CallbackQueryHandler(guest_payment_starting_func, pattern="^"+ "GUEST_PAYMENT"),],
    states={
        "LEVEL1_GUEST_PAYMENT": [
            CallbackQueryHandler(guest_payment_cash_payment, pattern="^"+ "CASH$"),
            # CallbackQueryHandler(guest_payment_no_cash_payment, pattern="^"+ "NOT_CASH$"),
            CallbackQueryHandler(guest_payment_no_payment, pattern="^"+ "NO_PAYMENT$"),
            CallbackQueryHandler(guest_payment_no_cash_payment_select_payment_type, pattern=dict),
            
            CallbackQueryHandler(guest_payment_final, pattern="^"+"NEXT"),
            
            
            # CallbackQueryHandler(guest_payment_get_payment_status, pattern=check_guest_payment_callback),
        ],
        "LEVEL2_GUEST_PAYMENT": [
            CallbackQueryHandler(guest_payment_final, pattern="^"+ "CONTINUE$"),
            CallbackQueryHandler(guest_payment_no_cash_payment_select_payment_type, pattern=dict),
        ],
        "LEVEL3_GUEST_PAYMENT": [
            MessageHandler(Filters.photo, guest_payment_no_cash_payment_get_screenshot),
            
        ],
        
        
    },
    fallbacks=[
            # CommandHandler("start", start)
        CallbackQueryHandler(guest_payment_cash_payment, pattern='^' + "BACK_ADMIN_HELP"),
            
    ],
    map_to_parent={
        "NEXT": LEVEL3_BOOKING,
        "NEXT_CHECKIN": "LEVEL7_CHECKIN"
    },
    allow_reentry = True,
    persistent=True,
    name = "guest_payment_conversation"
)

admin_guest_payment_conversation = ConversationHandler(
        entry_points= [CallbackQueryHandler(guest_payment_get_payment_status, pattern=check_guest_payment_callback),],
        states={
            "ADMIN_LEVEL3_GUEST_PAYMENT": [
                CallbackQueryHandler(guest_payment_get_payment_currency, pattern="^"+ "G_PAY_CURR"),
            ],
            "ADMIN_LEVEL4_GUEST_PAYMENT": [
                MessageHandler(Filters.regex("^(\d+\.?\d*|\.\d+)$"), guest_payment_get_payment_total)

            ]
            
            
        },
        fallbacks=[
                # CommandHandler("start", start)
            CallbackQueryHandler(guest_payment_cash_payment, pattern='^' + "BACK_ADMIN_HELP"),
                
        ],
        allow_reentry = True,
        persistent=True,
        name = "admin_guest_payment_conversation"
)
