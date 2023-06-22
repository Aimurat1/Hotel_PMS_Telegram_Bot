from telegram.ext import PicklePersistence, CallbackQueryHandler, Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler
from telegram import ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup, Update, ParseMode
from components.adminRequests import adminRequests
import firebase_with_api as firebase
import datetime
import calendar_inline.telegramcalendar_withpast as telegramcalendar
import calendar_inline.telegramcalendar as telegramcalendar_for_checkout
from utils.number_to_emoji import number_to_emoji
# from constants.admin_id import admin_id_arr, top_admin_id_arr
from constants.bot_link import bot_link
import copy
from utils.telegram_bot_pagination import InlineKeyboardPaginator
import flag  # pip install emoji-country-flag
import time
import json
import pytz
import os, logging
from utils.currency_converter import convert_currency, convert_to_usd
import wubook_functions as wubook


# adminRequests = adminRequests()

ADMIN_LEVEL1, ADMIN_REQUESTS_LEVEL1, ADMIN_REQUESTS_LEVEL2 = range(3)

back_btn = InlineKeyboardButton("🔙 Назад", callback_data="BACK")


class Admin:

    # Admin panel

    admin_menu_keyboard = [
        # [InlineKeyboardButton(text="Выбрать объект", callback_data="ADMIN_SELECT_OBJECT")],
        [InlineKeyboardButton(text="Бронирования",
                              callback_data="ADMIN_BOOKINGS")],
        [InlineKeyboardButton(text="Сейчас проживают",
                              callback_data="ADMIN_ROOM_OCCUPATION")],
        # [InlineKeyboardButton(text="Гости", callback_data="ADMIN_GUESTS")],
        # [InlineKeyboardButton(
        #     text="Управление", callback_data="ADMIN_MANAGE"),],
        # InlineKeyboardButton(text="Заявки администратору", callback_data="ADMIN_REQUESTS")],
        [InlineKeyboardButton(text="Зарегистрированные гости",
                              callback_data="ADMIN_CHECKED_IN_GUESTS"),],
        [InlineKeyboardButton(text="Доступные номера",
                              callback_data="ADMIN_AVAILABLE_ROOMS"),],
        [InlineKeyboardButton(text="Вечернее уведомление",
                              callback_data="ADMIN_EVENING_NOTIFY"),],
        [InlineKeyboardButton(text="Утреннее уведомление",
                              callback_data="ADMIN_MORNING_NOTIFY"),],

    ]

    top_admin_menu_keyboard = [
        # [InlineKeyboardButton(text="Выбрать объект", callback_data="ADMIN_SELECT_OBJECT")],
        [InlineKeyboardButton(text="Бронирования",
                              callback_data="ADMIN_BOOKINGS")],
        [InlineKeyboardButton(text="Сейчас проживают",
                              callback_data="ADMIN_ROOM_OCCUPATION")],
        # [InlineKeyboardButton(text="Заполненность номеров (auto)", callback_data="ADMIN_ROOM_OCCUPATION_AUTO")],
        [InlineKeyboardButton(text="Гости", callback_data="ADMIN_GUESTS")],
        [InlineKeyboardButton(
            text="Управление", callback_data="ADMIN_MANAGE"),],
        # InlineKeyboardButton(text="Заявки администратору", callback_data="ADMIN_REQUESTS")],
        [InlineKeyboardButton(text="Зарегистрированные гости",
                              callback_data="ADMIN_CHECKED_IN_GUESTS"),],
        [InlineKeyboardButton(text="Доступные номера",
                              callback_data="ADMIN_AVAILABLE_ROOMS"),],
        [InlineKeyboardButton(
            text="Горничные", callback_data="ADMIN_HOUSEKEEPING"),],
        [InlineKeyboardButton(text="Вечернее уведомление",
                              callback_data="ADMIN_EVENING_NOTIFY"),],
        [InlineKeyboardButton(text="Утреннее уведомление",
                              callback_data="ADMIN_MORNING_NOTIFY"),],
        [InlineKeyboardButton(text="Меню уведомлений",
                              callback_data="ADMIN_NOTIFICATION"),],
    ]
    
    def admin_end_conversation(self, update: Update, context: CallbackContext):
        return ConversationHandler.END

    def admin_menu(self, update: Update, context: CallbackContext):
        if (str(update.message.from_user.id) in top_admin_id_arr):
            admin_menu = self.top_admin_menu_keyboard

            context.bot.send_message(
                update.message.from_user.id, text="Выберите раздел", reply_markup=InlineKeyboardMarkup(admin_menu))

            return "ADMIN_LEVEL1"
        elif (str(update.message.from_user.id) in admin_id_arr):

            print(update.message.chat_id)

            admin_menu = self.admin_menu_keyboard

            context.bot.send_message(
                update.message.from_user.id, text="Выберите раздел", reply_markup=InlineKeyboardMarkup(admin_menu))

            return "ADMIN_LEVEL1"
        else:
            context.bot.send_message(
                update.message.from_user.id, text="Вы не имеете доступа к этой секции")

    def admin_menu_query(self, update: Update, context: CallbackContext):
        query = update.callback_query
        query.answer()

        if (str(query.from_user.id) in top_admin_id_arr):
            admin_menu = self.top_admin_menu_keyboard

            query.edit_message_text(
                text="Выберите раздел", reply_markup=InlineKeyboardMarkup(admin_menu))

            return "ADMIN_LEVEL1"
        elif (str(query.from_user.id) in admin_id_arr):

            # print(update.message.chat_id)
            admin_menu = self.admin_menu_keyboard

            query.edit_message_text(
                text="Выберите раздел", reply_markup=InlineKeyboardMarkup(admin_menu))

            return "ADMIN_LEVEL1"
        else:
            query.edit_message_text(text="Вы не имеете доступа к этой секции")

    def select_object(self, update: Update, context: CallbackContext):
        query = update.callback_query
        query.answer()

        keyboard = [
            [back_btn]
        ]

        query.edit_message_text(text="Выберите объект",
                                reply_markup=InlineKeyboardMarkup(keyboard))


    def admin_requests_type(self, update: Update, context: CallbackContext, **kwargs):
        try:
            query = update.callback_query
            query.answer()

            request_type = ""

            if (query.data == "CANCEL_BOOKING"):
                request_type = "cancel_booking"
            elif query.data == "EDIT_DATES":
                request_type = "edit_dates"
            elif query.data == "EDIT_ROOM":
                request_type = "edit_room"
        except:
            pass

        if "request_type" in kwargs.keys():
            request_type = kwargs['request_type']

        keyboard = [
            [],
            [back_btn]
        ]

        requests_list = firebase.getRequestsByType(request_type, False)

        # print(requests_list)

        message = f"""Список запросов, которые еще не подтверждены:
        """

        for index, request in enumerate(requests_list):
            user = firebase.getBookingById(
                request['user_id'], request['booking_id'])
            chat_id = str(user['telegram_id'])

            # --- Making request class ---#
            requestDict = {}
            if request_type == "edit_dates":
                requestDict['checkin_date'] = request['new_checkin_date']
                requestDict['checkout_date'] = request['new_checkout_date']
            if request_type == "edit_room":
                requestDict['room_number'] = request['new_room_type']

            requestClass = adminRequests(
                request['request_id'],
                request['user_id'],
                request['booking_id'],
                user['phone_number'],
                request_type,
                str(user['telegram_id']),
                request=requestDict
            )
            #!--- Making request class ---!#

            keyboard[0].append(InlineKeyboardButton(
                text=(index+1), callback_data=requestClass))

            message += f"""
Бронирование №{index+1}
    {flag.flag(user['booking']['country_code']) if user['booking']['country_code'] else ""} Имя: {user['name']}
    Фамилия: {user['lastname']}
    Телефон номера: {user['phone_number']}
    Бронирование:
        Дата заселения: {user['booking']["checkin_date"]}
        Дата выселения: {user['booking']["checkout_date"]}
        Комната: {user['booking']["room_number"]}
______________________________________________
        """
            if request_type == "edit_dates":
                message += f"""    
        Новая дата заселения: {requests_list[index]['new_checkin_date']}
        Новая дата выселения: {requests_list[index]['new_checkout_date']}
    """
            if request_type == "edit_room":
                message += f"""    
        Хочет изменить на: {requests_list[index]['new_room_type']}
    """

        query.edit_message_text(
            text=f"{message}", reply_markup=InlineKeyboardMarkup(keyboard))

        return "ADMIN_REQUESTS_LEVEL2"

    def admin_approve_requests(self, update: Update, context: CallbackContext):
        query = update.callback_query
        # query.answer()
        requestClass: adminRequests = query.data

        request_type = requestClass.request_type
        phone_number = requestClass.phone_number
        booking_id = requestClass.booking_id
        telegram_id = requestClass.telegram_id
        dict_to_update = requestClass.requestDict['request']

        dict_to_update['checkin_date_timestamp'] = int(datetime.datetime.strptime(
            dict_to_update['checkin_date'], "%Y-%m-%d").timestamp())
        dict_to_update['checkout_date_timestamp'] = int(datetime.datetime.strptime(
            dict_to_update['checkout_date'], "%Y-%m-%d").timestamp())

        # print(dict_to_update)

        if (request_type == 'cancel_booking'):
            firebase.approveBookingRequest(
                phone_number, booking_id, type="cancel_booking")

            # query.edit_message_text(text = "Заявка на отмену бронирования успешно подтверждена")
            query.answer(
                text="Заявка на изменение даты успешно подтверждена", show_alert=True)

            context.bot.send_message(int(
                telegram_id), text="Ваша заявка на изменение даты бронирования успешно подтверждена")

        elif request_type == 'edit_dates':
            # print("NEW DATES: ")
            # print(user_data["new_dates_for_edit"])
            firebase.approveBookingRequest(
                phone_number, booking_id, type="edit_dates")
            new_booking = firebase.updateBookingDetails(
                phone_number, booking_id, dict_to_update)

            # Update the user_data
            updated_booking = {'booking': new_booking}

            context.dispatcher.user_data[int(
                telegram_id)].update(updated_booking)

            context.dispatcher.update_persistence()

            # query.edit_message_text(text = "Заявка на изменение даты успешно подтверждена")
            query.answer(
                text="Заявка на изменение даты успешно подтверждена", show_alert=True)

            context.bot.send_message(int(
                telegram_id), text="Ваша заявка на изменение даты бронирования успешно подтверждена")

        elif request_type == 'edit_room':
            firebase.approveBookingRequest(
                phone_number, booking_id, type="edit_room")
            new_booking = firebase.updateBookingDetails(
                phone_number, booking_id, dict_to_update)

            # Update the user_data
            updated_booking = {'booking': new_booking}
            context.dispatcher.user_data[int(
                telegram_id)].update(updated_booking)
            context.dispatcher.update_persistence()

            # query.edit_message_text(text = "Заявка на изменение номера успешно подтверждена")
            query.answer(
                text="Заявка на изменение даты успешно подтверждена", show_alert=True)

            context.bot.send_message(int(
                telegram_id), text="Ваша заявка на изменение даты бронирования успешно подтверждена")

        return self.admin_requests_type(update, context, request_type=request_type)


# Заполненность по номерам на сегодня


    def get_not_checked_in(self, checkin_dict):
        guests = checkin_dict['checkin']

        not_checked_in = []

        for guest in guests:
            if guest['booking']['room_number'] == None or (type(guest['booking']['room_number']) == list and len(guest['booking']['room_number']) == 0):
                not_checked_in.append(guest)
        return not_checked_in

    def room_occupation(self, update: Update, context: CallbackContext):
        query = update.callback_query
        today = datetime.datetime.now(
            tz=pytz.timezone("Asia/Almaty")).strftime("%Y-%m-%d")
        firebase.dailyRoomOccupancyCheck()
        print(today)
        room_occupation = firebase.getBookingForRooms(today)
        print(room_occupation)
        query.answer("Секундочку. Ничего не нажимайте)")

        keyboard = [
            [back_btn]
        ]

        types = {
            "hostel": "Хостел",
            "standard": "Стандарт",
            "lux": "Люкс",
            "twins": "Твинс"
        }

        message = ""

        for room in room_occupation:
            room_dict: dict = room_occupation[room]
            message += f"<b>{number_to_emoji(room)} ({types[str(room_dict['type'])]}): {'занято' if room_dict['available'] == False else 'свободно'}</b>\n"
            if 'guests' in room_dict.keys():
                for guest in room_dict['guests']:
                    if guest['checkin_today']:
                        message += f"(сегодня заехал) "
                    if guest['checkout_today']:
                        message += f"(сегодня выезд) "
                    booking = firebase.getBookingById(
                        guest['guest']['user_id'], guest['guest']['booking_id'])
                    message += f"""{flag.flag(booking['booking']['country_code']) if booking['booking']['country_code'] != '--' else ''} {booking['name']} {booking['lastname']}{f' - <a href="https://wa.me/{booking["phone_number"]}">{booking["phone_number"]}</a>' if "phone_number" in booking.keys() else "" } - c {booking['booking']['checkin_date']} по {booking['booking']['checkout_date']} ({booking['booking']['number_of_nights']} ночей) - {booking['booking']['adults']} {'людей' if booking['booking']['adults'] > 2 else 'человек' if booking['booking']['adults'] == 1 else 'человека'} - {booking['booking']['room_number']} номер - {booking['booking']['channel_name']}
"""

        checkin_dict = firebase.getBookingForDay(only_checkin=True)
        not_checked_in = self.get_not_checked_in(checkin_dict)

        if len(not_checked_in) > 0:
            message += "\nТакже сегодня должны заехать следующие гости:\n"

        for checkin in not_checked_in:
            roomType = ""
            for room_type in checkin['booking']['room_type']:
                roomType += f"{room_type} "
            message += f"""🔵 {flag.flag(checkin['booking']['country_code']) if checkin['booking']['country_code'] != '--' else ''} {checkin['name']} {checkin['lastname']}{f' - <a href="https://wa.me/{checkin["phone_number"]}">{checkin["phone_number"]}</a>' if "phone_number" in checkin.keys() else "" } - {checkin['booking']['adults']} гостей - {checkin['booking']['checkin_date']} по {checkin['booking']['checkout_date']} ({checkin['booking']['number_of_nights']} ночей) - {checkin['booking']['room_number']} номер - {roomType} - {checkin['booking']['channel_name']}
"""

        query.edit_message_text(text=f"""
    Заполненность по номерам на сегодня ({today}):
{message}
                                """, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyboard), disable_web_page_preview = True)

        return "ADMIN_ROOM_OCCUPATION_LEVEL1"

    def room_occupation_select_date(self, update: Update, context: CallbackContext):
        query = update.callback_query
        query.answer()
        query.edit_message_text(
            text="Выберите дату", reply_markup=telegramcalendar.create_calendar())
        return "ADMIN_ROOM_OCCUPATION_LEVEL1"

    def room_occupation_automatic(self, update: Update, context: CallbackContext):
        selected, date = telegramcalendar.process_calendar_selection(
            update, context)
        if selected:
            query = update.callback_query
            today = date
            query.answer("Это может занять время")
            # today = datetime.datetime.now().strftime("%Y-%m-%d")
            room_occupation = firebase.getBookingForRoomTypes(today)
            # print(room_occupation)

            keyboard = [
                [back_btn]
            ]

            hotel_rooms = {
                "hostel": {
                    "5.1": [],
                    "5.2": [],
                    "5.3": [],
                    "5.4": [],
                    "5.5": [],
                    "5.6": [],
                },
                "standard": {
                    "1": [],
                    "2": [],
                    "3": []
                },
                "twins": {
                    "4": []
                },
                "lux": {
                    "6": []
                }
            }

            # for key, value in room_occupation.items():
            #     print(key, ' : ', value)

            message = ""

            for room_name in room_occupation:
                # print(room_occupation[str(i)])
                if (len(room_occupation[str(room_name)]) == 0):
                    pass
                    # message += f"{room_name} - свободен\n"
                else:
                    for guest in room_occupation[str(room_name)]:
                        if (guest['checkout_today'] == True):
                            for room in hotel_rooms[str(room_name)]:
                                if len(hotel_rooms[str(room_name)][room]) == 0:
                                    hotel_rooms[str(room_name)][room].append(
                                        {'checkout_today': True, 'guest': guest})
                                    break
                        elif guest['checkout_today'] == False:

                            for room in hotel_rooms[str(room_name)]:
                                if len(hotel_rooms[str(room_name)][room]) == 0:
                                    hotel_rooms[str(room_name)][room].append(
                                        {'checkout_today': False, 'guest': guest})
                                    break
                                elif len(hotel_rooms[str(room_name)][room]) <= 1 and hotel_rooms[str(room_name)][room][0]['checkout_today'] == True and guest['checkin_today'] == True:
                                    hotel_rooms[str(room_name)][room].append(
                                        {'checkout_today': False, 'guest': guest})
                                    break

            for room_type in hotel_rooms:
                message += f"<b>{room_type}</b>\n"
                for room in hotel_rooms[room_type]:
                    if len(hotel_rooms[room_type][room]) == 0:
                        firebase.updateRoomOccupancyTest(None, room)
                        message += f"{number_to_emoji(room)}: свободно\n"
                        # firebase.assignGuestToRoom(None, room)
                    else:
                        guestArr = hotel_rooms[room_type][room]
                        firebase.updateRoomOccupancyTest(
                            hotel_rooms[room_type][room], room)
                        for guest in guestArr:
                            if guest['checkout_today']:
                                message += f"{number_to_emoji(room)}: свободно (сегодня выезд) "
                            else:
                                if guest['guest']['checkin_today']:
                                    message += f"{number_to_emoji(room)}: занято (сегодня заезд) "
                                else:
                                    message += f"{number_to_emoji(room)}: занято "
                            booking = guest['guest']
                            message += f"{flag.flag(booking['booking']['country_code']) if booking['booking']['country_code'] != '--' else ''} | rcode: {booking['booking']['reservation_code']} | {booking['name']} {booking['lastname']} - c {booking['booking']['checkin_date']} по {booking['booking']['checkout_date']} ({booking['booking']['number_of_nights']} ночей) - {booking['booking']['adults']} {'людей' if booking['booking']['adults'] > 2 else 'человек' if booking['booking']['adults'] == 1 else 'человека'} - {booking['booking']['room_number']} номер\n"

            query.edit_message_text(text=f"""
Заполненность по номерам на сегодня ({today}):
{message}
                                """, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyboard))

            return "ADMIN_ROOM_OCCUPATION_LEVEL2"

    # Бронирования

    def bookings(self, update: Update, context: CallbackContext):
        query = update.callback_query
        query.answer()

        if query.data == "BACK_TODAY_BOOKINGS":
            context.user_data['today_checkin_message'].delete()

        keyboard = [
            [InlineKeyboardButton(
                text="На определенную дату", callback_data="ADMIN_CHOOSE_DAY")],
            [InlineKeyboardButton(
                text="На сегодня", callback_data="ADMIN_THIS_DAY")],
            [back_btn]
        ]

        query.edit_message_text(
            text="Заселения и выселения", reply_markup=InlineKeyboardMarkup(keyboard))

        return "ADMIN_BOOKING_LEVEL1"

    def bookings_choose_day(self, update: Update, context: CallbackContext):
        query = update.callback_query

        query.answer()

        context.user_data['bookings_select_date_message'] = query.edit_message_text(
            text="Выберите день", reply_markup=telegramcalendar.create_calendar())

        return "ADMIN_BOOKING_LEVEL2"

    def bookings_day_choosed(self, update: Update, context: CallbackContext):

        callback_data = update.callback_query.data
        if type(callback_data) == dict and callback_data['type'] == "CANCEL" and callback_data['room_number'] is not None:
            firebase.check_room_occupancy_if_delete(
                callback_data['booking']['user_id'], callback_data['booking']['id'], callback_data['booking']['reservation_code'])
            firebase.delete_room_number_from_booking(
                callback_data['booking']['user_id'], callback_data['booking']['id'], callback_data['room_number'])

            selected = True
            date = context.user_data['bookings_choosen_date']
        else:
            if update.callback_query.data == "RETURN_DAY_CHOOSED" or (type(callback_data) == dict and callback_data['type'] == "CANCEL" and callback_data['room_number'] is None):
                selected = True
                date = context.user_data['bookings_choosen_date']
            else:
                selected, date = telegramcalendar.process_calendar_selection(
                    update, context)

        keyboard = [
            [back_btn]
        ]

        if selected:

            context.user_data['bookings_checkin_type'] = "day_choosed"

            context.user_data['bookings_select_date_message'].edit_text(
                text="Ищу бронирования...")

            today = datetime.datetime.now(tz=pytz.timezone(
                "Asia/Almaty"))  # get the current date and time
            yesterday = today - datetime.timedelta(days=1)
            yesterday = yesterday.strftime("%Y-%m-%d")

            # yesterday = "2023-05-06"

            print(date)

            context.user_data['bookings_choosen_date'] = date

            checkin_checkout_dict = firebase.getBookingForDay(date=date)

            date_str = date.strftime("%Y-%m-%d")

            if (date_str == yesterday):

                print("yesterday")

                checkin_keyboard = [
                    # [back_btn]
                ]

                checkout_keyboard = [
                    [InlineKeyboardButton(
                        "🔙 Назад", callback_data="BACK_TODAY_BOOKINGS")]
                ]
                message = ""

                if len(checkin_checkout_dict['checkin']) > 0:
                    message += f"<b>Заезд на {date.strftime('%d.%m')}: (🟢 - прошел регистрацию 🔴 - не прошел регистрацию)\nДля регистрации гостя выберите номер гостя внизу</b>\n"
                else:
                    message += "<b>Нет заездов на сегодня</b>\n"

                i = 1
                keyboard_index = -1
                for checkin in checkin_checkout_dict['checkin']:
                    # print(checkin)
                    status = firebase.getStatusFromGuestBookingID(
                        checkin['user_id'], checkin['booking']['booking_id'])
                    if not status['checked_in']:
                        message += f"{number_to_emoji(i)} "
                        if i % 6 == 1:
                            keyboard_index += 1
                            checkin_keyboard.insert(keyboard_index, [])
                        checkin['callback'] = "CHECKIN"
                        checkin_keyboard[keyboard_index].append(
                            InlineKeyboardButton(text=i, callback_data=checkin))
                        i += 1
                    roomType = ""
                    for room_type in checkin['booking']['room_type']:
                        roomType += f"{room_type} "
                        
                    if "price_in_KGS" in checkin['booking'].keys():
                        price_message = f"{checkin['booking']['price_in_USD']} USD | {checkin['booking']['price_in_KGS']} KGS | {checkin['booking']['price_in_RUB']} RUB"
                    else:
                        price_in_USD = convert_currency(checkin['booking']['currency'], 'USD', checkin['booking']['price'])
                        price_in_KGS = convert_currency(checkin['booking']['currency'], 'KGS', checkin['booking']['price'])
                        price_in_RUB = convert_currency(checkin['booking']['currency'], 'RUB', checkin['booking']['price'])
                        
                        firebase.updateBookingWithId(checkin['user_id'], checkin['booking']['booking_id'], {
                                "price_in_KGS": price_in_KGS,
                                "price_in_USD": price_in_USD,
                                "price_in_RUB": price_in_RUB
                            })
                        price_message = f"{price_in_USD} USD | {price_in_KGS} KGS | {price_in_RUB} RUB"
                    
                        checkin['booking']['price_in_USD'] = price_in_USD
                        checkin['booking']['price_in_KGS'] = price_in_KGS
                        checkin['booking']['price_in_RUB'] = price_in_RUB
                        
                        
                    message += f"""{'🟢' if status['checked_in'] else '🔴'} {flag.flag(checkin['booking']['country_code']) if checkin['booking']['country_code'] != '--' else ''} <b>{checkin['name']} {checkin['lastname']}</b>{f' - <a href="https://wa.me/{checkin["phone_number"]}">{checkin["phone_number"]}</a>' if "phone_number" in checkin.keys() else "" } - {checkin['booking']['adults']} гостей - {checkin['booking']['checkin_date']} по {checkin['booking']['checkout_date']} ({checkin['booking']['number_of_nights']} ночей) - {checkin['booking']['room_number']} номер - {roomType} - {checkin['booking']['channel_name']} - {price_message}
"""
                    try:
                        if status['checked_in']:
                            message += f"""    {'🟥 Оплаты нет' if 'payment_total' not in checkin['booking'].keys()  else "🟩 Оплата имеется - оплата не требуется" if checkin['booking']['payment_total'] == 'NOT NEEDED' else f"🟩 Оплата имеется - {checkin['booking']['payment_total']} {checkin['booking']['payment_currency']} методом {checkin['booking']['payment_type']}"} \n"""
                            message += f"""    {'🟥 Паспорт не внесен' if 'passport_link' not in checkin['booking'].keys()  else f"🟩 Паспорт внесен"}\n"""
                    except:
                        print(checkin)

                context.user_data['today_checkin_message'] = update.callback_query.edit_message_text(
                    text=message,
                    reply_markup=InlineKeyboardMarkup(checkin_keyboard), parse_mode=ParseMode.HTML, disable_web_page_preview = True)

                if len(checkin_checkout_dict['checkout']) > 0:
                    message = f"\n<b>Выезд на {date.strftime('%d.%m')}: (🟢 - сделал выезд 🔴 - не сделал выезд)\nДля чекаута гостя выберите номер гостя внизу </b>\n"
                else:
                    message += "\n<b>Нет выездов на сегодня</b>\n"

                i = 1
                keyboard_index = -1
                for checkout in checkin_checkout_dict['checkout']:
                    if not checkout['booking']['checked_out']:
                        message += f"{number_to_emoji(i)} "
                        if i % 6 == 1:
                            keyboard_index += 1
                            checkout_keyboard.insert(keyboard_index, [])
                        checkout['callback'] = "CHECKOUT"
                        checkout_keyboard[keyboard_index].append(
                            InlineKeyboardButton(text=i, callback_data=checkout))
                        i += 1
                        
                    if "price_in_KGS" in checkin['booking'].keys():
                        price_message = f"{checkin['booking']['price_in_USD']} USD | {checkin['booking']['price_in_KGS']} KGS | {checkin['booking']['price_in_RUB']} RUB"
                    else:
                        price_in_USD = convert_currency(checkin['booking']['currency'], 'USD', checkin['booking']['price'])
                        price_in_KGS = convert_currency(checkin['booking']['currency'], 'KGS', checkin['booking']['price'])
                        price_in_RUB = convert_currency(checkin['booking']['currency'], 'RUB', checkin['booking']['price'])
                        
                        firebase.updateBookingWithId(checkin['user_id'], checkin['booking']['booking_id'], {
                                "price_in_KGS": price_in_KGS,
                                "price_in_USD": price_in_USD,
                                "price_in_RUB": price_in_RUB
                            })
                        price_message = f"{price_in_USD} USD | {price_in_KGS} KGS | {price_in_RUB} RUB"
                    
                        checkout['booking']['price_in_USD'] = price_in_USD
                        checkout['booking']['price_in_KGS'] = price_in_KGS
                        checkout['booking']['price_in_RUB'] = price_in_RUB
                    
                    message += f"""{'🟢' if checkout['booking']['checked_out'] else '🔴'} {flag.flag(checkout['booking']['country_code']) if checkout['booking']['country_code'] != '--' else ''} <b>{checkout['name']} {checkout['lastname']}</b>{f' - <a href="https://wa.me/{checkout["phone_number"]}">{checkout["phone_number"]}</a>' if "phone_number" in checkout.keys() else "" } - {checkout['booking']['adults']} гостей - {checkout['booking']['checkin_date']} по {checkout['booking']['checkout_date']} ({checkout['booking']['number_of_nights']} ночей) - {checkout['booking']['room_number']} номер - {checkout['booking']['channel_name']} - {price_message}
"""
                    if checkout['booking']['checked_out']:
                        message += f"    {'🟥 Ключ сдан' if 'key_returned' not in checkout['booking'].keys() or not checkout['booking']['key_returned'] else '🟩 Ключ сдан'} | "
                        message += f"{'🟥 Полотенце в наличии' if 'towel_is_okay' not in checkout['booking'].keys() or not checkout['booking']['towel_is_okay'] else '🟩 Полотенце в наличии'} | "
                        message += f"{'🟥 Белье в порядке' if 'linen_is_okay' not in checkout['booking'].keys() or not checkout['booking']['linen_is_okay'] else '🟩 Белье в порядке'}\n"

                        if 'checkout_additional_comments' in checkout['booking'].keys():
                            message += f"    <b>Другие замечания:</b> {checkout['booking']['checkout_additional_comments']}\n"

                context.user_data['today_checkout_message'] = context.bot.send_message(
                    chat_id=update.callback_query.message.chat_id,
                    text=message,
                    reply_markup=InlineKeyboardMarkup(checkout_keyboard), parse_mode=ParseMode.HTML, disable_web_page_preview = True)

            else:
                message = ""

                if len(checkin_checkout_dict['checkin']) > 0:
                    message += f"<b>Заезд на {date.strftime('%d.%m')}:</b>\n"
                else:
                    message += "Нет заездов на выбранную дату\n"

                for checkin in checkin_checkout_dict['checkin']:
                    roomType = ""
                    for room_type in checkin['booking']['room_type']:
                        roomType += f"{room_type} "
                    message += f"{flag.flag(checkin['booking']['country_code']) if checkin['booking']['country_code'] != '--' else ''} {checkin['name']} {checkin['lastname']} - {checkin['booking']['adults']} гостей - {checkin['booking']['checkin_date']} по {checkin['booking']['checkout_date']} ({checkin['booking']['number_of_nights']} ночей) - {checkin['booking']['room_number']} номер | {roomType}\n"

                if len(checkin_checkout_dict['checkout']) > 0:
                    message += f"\n<b>Выезд на {date.strftime('%d.%m')}:</b>\n"
                else:
                    message += "\nНет выездов на выбранную дату\n"

                for checkout in checkin_checkout_dict['checkout']:
                    roomType = ""
                    for room_type in checkout['booking']['room_type']:
                        roomType += f"{room_type} "
                    message += f"{flag.flag(checkout['booking']['country_code']) if checkout['booking']['country_code'] != '--' else ''} <b>{checkout['name']} {checkout['lastname']}</b> - {checkout['booking']['adults']} гостей - {checkout['booking']['checkin_date']} по {checkout['booking']['checkout_date']} ({checkout['booking']['number_of_nights']} ночей) - {checkout['booking']['room_number']} номер | {roomType}\n"

                update.callback_query.edit_message_text(
                    text=message,
                    reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)

            return "ADMIN_BOOKING_LEVEL3"

    def bookings_all(self, update: Update, context: CallbackContext):

        checkin_keyboard = [
            # [back_btn]
        ]

        checkout_keyboard = [
            [InlineKeyboardButton(
                "🔙 Назад", callback_data="BACK_TODAY_BOOKINGS")]
        ]

        update.callback_query.answer("Секундочку")

        context.user_data['bookings_checkin_type'] = "all"

        callback_data = update.callback_query.data

        today = datetime.datetime.now(
            tz=pytz.timezone("Asia/Almaty")).strftime("%d.%m")

        if type(callback_data) == dict and callback_data['type'] == "CANCEL" and callback_data['room_number'] is not None:
            firebase.check_room_occupancy_if_delete(
                callback_data['booking']['user_id'], callback_data['booking']['id'], callback_data['booking']['reservation_code'])
            firebase.delete_room_number_from_booking(
                callback_data['booking']['user_id'], callback_data['booking']['id'], callback_data['room_number'])

        if type(callback_data) != dict and update.callback_query.data == "RETURN_TODAY":
            checkin_checkout_dict = context.user_data['checkin_checkout_dict']
        else:
            checkin_checkout_dict = firebase.getBookingForDay()
            context.user_data['checkin_checkout_dict'] = checkin_checkout_dict

        message = ""

        if len(checkin_checkout_dict['checkin']) > 0:
            message += f"<b>Заезд на {today}: (🟢 - прошел регистрацию 🔴 - не прошел регистрацию)\nДля регистрации гостя выберите номер гостя внизу</b>\n"
        else:
            message += "<b>Нет заездов на сегодня</b>\n"

        i = 1
        keyboard_index = -1
        for checkin in checkin_checkout_dict['checkin']:
            # print(checkin)
            status = firebase.getStatusFromGuestBookingID(
                checkin['user_id'], checkin['booking']['booking_id'])
            if not status['checked_in']:
                message += f"{number_to_emoji(i)} "
                if i % 6 == 1:
                    keyboard_index += 1
                    checkin_keyboard.insert(keyboard_index, [])
                checkin['callback'] = "CHECKIN"
                checkin_keyboard[keyboard_index].append(
                    InlineKeyboardButton(text=i, callback_data=checkin))
                i += 1
            roomType = ""
            for room_type in checkin['booking']['room_type']:
                roomType += f"{room_type} "
                
            if "price_in_KGS" in checkin['booking'].keys():
                price_message = f"{checkin['booking']['price_in_USD']} USD | {checkin['booking']['price_in_KGS']} KGS | {checkin['booking']['price_in_RUB']} RUB"
            else:
                price_in_USD = convert_currency(checkin['booking']['currency'], 'USD', checkin['booking']['price'])
                price_in_KGS = convert_currency(checkin['booking']['currency'], 'KGS', checkin['booking']['price'])
                price_in_RUB = convert_currency(checkin['booking']['currency'], 'RUB', checkin['booking']['price'])
                
                firebase.updateBookingWithId(checkin['user_id'], checkin['booking']['booking_id'], {
                        "price_in_KGS": price_in_KGS,
                        "price_in_USD": price_in_USD,
                        "price_in_RUB": price_in_RUB
                    })
                price_message = f"{price_in_USD} USD | {price_in_KGS} KGS | {price_in_RUB} RUB"

                checkin['booking']['price_in_USD'] = price_in_USD
                checkin['booking']['price_in_KGS'] = price_in_KGS
                checkin['booking']['price_in_RUB'] = price_in_RUB
                       
                        
            message += f"""{'🟢' if status['checked_in'] else '🔴'} {flag.flag(checkin['booking']['country_code']) if checkin['booking']['country_code'] != '--' else ''} <b>{checkin['name']} {checkin['lastname']}</b>{f' - <a href="https://wa.me/{checkin["phone_number"]}">{checkin["phone_number"]}</a>' if "phone_number" in checkin.keys() else "" } - {checkin['booking']['adults']} гостей - {checkin['booking']['checkin_date']} по {checkin['booking']['checkout_date']} ({checkin['booking']['number_of_nights']} ночей) - {checkin['booking']['room_number']} номер - {roomType} - {checkin['booking']['channel_name']} - {price_message}
"""
            if status['checked_in']:
                message += f"""    {'🟥 Оплаты нет' if 'payment_total' not in checkin['booking'].keys() else "🟩 Оплата имеется - оплата не требуется" if checkin['booking']['payment_total'] == 'NOT NEEDED' else f"🟩 Оплата имеется - {checkin['booking']['payment_total']} {checkin['booking']['payment_currency']} методом {checkin['booking']['payment_type']}"} \n"""
                message += f"""    {'🟥 Паспорт не внесен' if 'passport_link' not in checkin['booking'].keys()  else f"🟩 Паспорт внесен"}\n"""

        context.user_data['today_checkin_message'] = update.callback_query.edit_message_text(
            text=message,
            reply_markup=InlineKeyboardMarkup(checkin_keyboard), parse_mode=ParseMode.HTML, disable_web_page_preview = True)

        if len(checkin_checkout_dict['checkout']) > 0:
            message = f"\n<b>Выезд на {today}: (🟢 - сделал выезд 🔴 - не сделал выезд)\nДля чекаута гостя выберите номер гостя внизу </b>\n"
        else:
            message += "\n<b>Нет выездов на сегодня</b>\n"

        i = 1
        keyboard_index = -1
        for checkout in checkin_checkout_dict['checkout']:
            if not checkout['booking']['checked_out']:
                message += f"{number_to_emoji(i)} "
                if i % 6 == 1:
                    keyboard_index += 1
                    checkout_keyboard.insert(keyboard_index, [])
                checkout['callback'] = "CHECKOUT"
                checkout_keyboard[keyboard_index].append(
                    InlineKeyboardButton(text=i, callback_data=checkout))
                i += 1
                        
            if "price_in_KGS" in checkin['booking'].keys():
                price_message = f"{checkin['booking']['price_in_USD']} USD | {checkin['booking']['price_in_KGS']} KGS | {checkin['booking']['price_in_RUB']} RUB"
            else:
                price_in_USD = convert_currency(checkin['booking']['currency'], 'USD', checkin['booking']['price'])
                price_in_KGS = convert_currency(checkin['booking']['currency'], 'KGS', checkin['booking']['price'])
                price_in_RUB = convert_currency(checkin['booking']['currency'], 'RUB', checkin['booking']['price'])
                
                firebase.updateBookingWithId(checkin['user_id'], checkin['booking']['booking_id'], {
                        "price_in_KGS": price_in_KGS,
                        "price_in_USD": price_in_USD,
                        "price_in_RUB": price_in_RUB
                    })
                price_message = f"{price_in_USD} USD | {price_in_KGS} KGS | {price_in_RUB} RUB"

                checkout['booking']['price_in_USD'] = price_in_USD
                checkout['booking']['price_in_KGS'] = price_in_KGS
                checkout['booking']['price_in_RUB'] = price_in_RUB


            message += f"""{'🟢' if checkout['booking']['checked_out'] else '🔴'} {flag.flag(checkout['booking']['country_code']) if checkout['booking']['country_code'] != '--' else ''} <b>{checkout['name']} {checkout['lastname']}</b>{f' - <a href="https://wa.me/{checkout["phone_number"]}">{checkout["phone_number"]}</a>' if "phone_number" in checkout.keys() else "" } - {checkout['booking']['adults']} гостей - {checkout['booking']['checkin_date']} по {checkout['booking']['checkout_date']} ({checkout['booking']['number_of_nights']} ночей) - {checkout['booking']['room_number']} номер - {checkout['booking']['channel_name']} - {price_message}
"""
            if checkout['booking']['checked_out']:
                message += f"    {'🟥 Ключ сдан' if 'key_returned' not in checkout['booking'].keys() or not checkout['booking']['key_returned'] else '🟩 Ключ сдан'} | "
                message += f"{'🟥 Полотенце в наличии' if 'towel_is_okay' not in checkout['booking'].keys() or not checkout['booking']['towel_is_okay'] else '🟩 Полотенце в наличии'} | "
                message += f"{'🟥 Белье в порядке' if 'linen_is_okay' not in checkout['booking'].keys() or not checkout['booking']['linen_is_okay'] else '🟩 Белье в порядке'}\n"

                if 'checkout_additional_comments' in checkout['booking'].keys():
                    message += f"    <b>Другие замечания:</b> {checkout['booking']['checkout_additional_comments']}\n"

        context.user_data['today_checkout_message'] = context.bot.send_message(
            chat_id=update.callback_query.message.chat_id,
            text=message,
            reply_markup=InlineKeyboardMarkup(checkout_keyboard), parse_mode=ParseMode.HTML, disable_web_page_preview = True)

        return "ADMIN_BOOKING_LEVEL3"

    # Чекаут гостя
    def generate_guest_checkout_callback(self, guest, callback):
        guest['callback'] = callback
        return copy.copy(guest)

    def generate_guest_checkout_keyboard(self, guest):
        key = "❌ Ключ сдан" if "key_returned" not in guest['booking'].keys(
        ) or guest['booking']['key_returned'] == False else "✅ Ключ сдан"
        towel = "❌ Полотенце в наличии" if "towel_is_okay" not in guest['booking'].keys(
        ) or guest['booking']['towel_is_okay'] == False else "✅ Полотенце в наличии"
        linen = "❌ Белье в порядке" if "linen_is_okay" not in guest['booking'].keys(
        ) or guest['booking']['linen_is_okay'] == False else "✅ Белье в порядке"

        keyboard = [
            [InlineKeyboardButton(text=key, callback_data=self.generate_guest_checkout_callback(
                guest, "KEY_RETURNED"))],
            [InlineKeyboardButton(text=towel, callback_data=self.generate_guest_checkout_callback(
                guest, "TOWEL_IS_OKAY"))],
            [InlineKeyboardButton(text=linen, callback_data=self.generate_guest_checkout_callback(
                guest, "LINEN_IS_OKAY"))],
            [InlineKeyboardButton(text="Другие замечания",
                                  callback_data="OTHER_COMMENTS")],
            [InlineKeyboardButton(text="🚪Оформить чекаут",
                                  callback_data="CHECKOUT_DONE")],
            [InlineKeyboardButton(
                text="🔙 Отменить", callback_data="CANCEL_CHECKOUT")]

        ]

        return keyboard

    def guest_checkout_done(self, update: Update, context: CallbackContext):

        query = update.callback_query

        user_id = context.user_data['checkout_guest_user_id']
        booking_id = context.user_data['checkout_guest_booking_id']

        firebase.updateBookingWithId(
            user_id, booking_id, {"checked_out": True})
        firebase.approveStatusFromGuestBookingID(
            user_id, booking_id, "checked_out", True)

        query.answer(
            "Чекаут сделан успешно! Перенаправляю вас на страницу сегодняшних бронирований.")

        return self.bookings_all(update, context)

    def register_guests_checkout(self, update: Update, context: CallbackContext):
        query = update.callback_query
        query.answer()

        if type(query.data) == str and query.data == "CANCEL_ADDITIONAL_COMMENT":
            checkout = context.user_data['checkout_guest']
            context.user_data['checkout_guest_message'].delete()
        else:
            checkout = query.data
            context.user_data['today_checkin_message'].delete()

        user_id, booking_id = checkout['user_id'], checkout['booking']['booking_id']

        context.user_data['checkout_guest'] = checkout
        context.user_data['checkout_guest_user_id'] = user_id
        context.user_data['checkout_guest_booking_id'] = booking_id

        keyboard = self.generate_guest_checkout_keyboard(checkout)

        context.user_data['checkout_guest_message'] = query.edit_message_text(text=f"""
{flag.flag(checkout['booking']['country_code']) if checkout['booking']['country_code'] != '--' else ''} {checkout['name']} {checkout['lastname']} - {checkout['booking']['adults']} гостей - {checkout['booking']['checkin_date']} по {checkout['booking']['checkout_date']} ({checkout['booking']['number_of_nights']} ночей) - {checkout['booking']['room_number']} номер

Проверьте комнату за гостем и отметьте все ли отлично. Если будут другие комментарии, нажмите на 'Другие замечания' и укажите
                                """, reply_markup=InlineKeyboardMarkup(keyboard))

        return "ADMIN_BOOKING_CHECKOUT_LEVEL4"

    def register_guests_checkout_send_message(self, update: Update, context: CallbackContext):

        checkout = context.user_data['checkout_guest']

        user_id, booking_id = checkout['user_id'], checkout['booking']['booking_id']

        keyboard = self.generate_guest_checkout_keyboard(checkout)

        # context.user_data['today_checkin_message'].delete()

        context.user_data['checkout_guest_message'] = context.bot.send_message(context.user_data['checkout_guest_message'].chat_id, text=f"""
{flag.flag(checkout['booking']['country_code']) if checkout['booking']['country_code'] != '--' else ''} {checkout['name']} {checkout['lastname']} - {checkout['booking']['adults']} гостей - {checkout['booking']['checkin_date']} по {checkout['booking']['checkout_date']} ({checkout['booking']['number_of_nights']} ночей) - {checkout['booking']['room_number']} номер

Проверьте комнату за гостем и отметьте все ли отлично. Если будут другие комментарии, нажмите на 'Другие замечания' и укажите
                                """, reply_markup=InlineKeyboardMarkup(keyboard))

        return "ADMIN_BOOKING_CHECKOUT_LEVEL4"

    def update_guests_checkout_message(self, update: Update, context: CallbackContext, message_to_update, checkout_dict, additional_comments=None):

        checkout = checkout_dict

        user_id, booking_id = checkout['user_id'], checkout['booking']['booking_id']

        context.user_data['checkout_guest'] = checkout
        context.user_data['checkout_guest_user_id'] = user_id
        context.user_data['checkout_guest_booking_id'] = booking_id

        keyboard = self.generate_guest_checkout_keyboard(checkout)

        message = f"{flag.flag(checkout['booking']['country_code']) if checkout['booking']['country_code'] != '--' else ''} {checkout['name']} {checkout['lastname']} - {checkout['booking']['adults']} гостей - {checkout['booking']['checkin_date']} по {checkout['booking']['checkout_date']} ({checkout['booking']['number_of_nights']} ночей) - {checkout['booking']['room_number']} номер\n\n"

        if additional_comments is not None:
            message += f"Другие замечания: {additional_comments}\n\n"

        message += f"Проверьте комнату за гостем и отметьте все ли отлично. Если будут другие комментарии, нажмите на 'Другие замечания' и укажите"
        context.user_data['checkout_guest_message'] = message_to_update.edit_text(
            text=message, reply_markup=InlineKeyboardMarkup(keyboard))

        return "ADMIN_BOOKING_CHECKOUT_LEVEL4"

    def edit_checkout_status(self, update: Update, context: CallbackContext):
        query = update.callback_query

        guest = query.data

        # print(guest['callback'])
        user_id, booking_id = guest['user_id'], guest['booking']['booking_id']

        if guest['callback'] == "KEY_RETURNED":
            key_returned = False if "key_returned" not in guest['booking'].keys(
            ) or guest['booking']['key_returned'] == False else True
            firebase.updateBookingWithId(
                user_id, booking_id, {"key_returned": not key_returned})
            guest['booking']['key_returned'] = not key_returned

        elif guest['callback'] == "TOWEL_IS_OKAY":
            towel_is_okay = False if "towel_is_okay" not in guest['booking'].keys(
            ) or guest['booking']['towel_is_okay'] == False else True
            firebase.updateBookingWithId(
                user_id, booking_id, {"towel_is_okay": not towel_is_okay})
            guest['booking']['towel_is_okay'] = not towel_is_okay

        elif guest['callback'] == "LINEN_IS_OKAY":
            linen_is_okay = False if "linen_is_okay" not in guest['booking'].keys(
            ) or guest['booking']['linen_is_okay'] == False else True
            firebase.updateBookingWithId(
                user_id, booking_id, {"linen_is_okay": not linen_is_okay})
            guest['booking']['linen_is_okay'] = not linen_is_okay

        return self.update_guests_checkout_message(update, context, query.message, guest)

    def guest_checkout_additional_comment(self, update: Update, context: CallbackContext):
        query = update.callback_query

        query.answer()

        keyboard = [
            [InlineKeyboardButton(
                text="🔙 Отмена", callback_data="CANCEL_ADDITIONAL_COMMENT")]
        ]
        context.user_data['checkout_guest_delete_messages'] = []
        mes = context.bot.send_message(query.message.chat_id, text="Отправь мне дополнительные замечания",
                                       reply_markup=InlineKeyboardMarkup(keyboard))

        context.user_data['checkout_guest_delete_messages'].append(mes)

        return "ADMIN_BOOKING_CHECKOUT_LEVEL5"

    def guest_checkout_get_additional_comment(self, update: Update, context: CallbackContext):
        comments = update.message.text

        context.user_data['checkout_guest_delete_messages'].append(
            update.message)

        print(comments)

        user_id = context.user_data['checkout_guest_user_id']
        booking_id = context.user_data['checkout_guest_booking_id']

        firebase.updateBookingWithId(
            user_id, booking_id, {"checkout_additional_comments": comments})

        mes = context.bot.send_message(update.message.chat_id, text="Принято!")

        context.user_data['checkout_guest_delete_messages'].append(mes)

        time.sleep(1.5)

        for message in context.user_data['checkout_guest_delete_messages']:
            message.delete()

        guest = context.user_data['checkout_guest']
        guest['checkout_additional_comments'] = comments

        return self.update_guests_checkout_message(update, context, context.user_data['checkout_guest_message'], guest, comments)

    # Регистрация гостя

    def choose_no_show_or_register(self, update: Update, context: CallbackContext):
        query = update.callback_query
        query.answer()

        
        if query.data == "BACK":
            checkin = context.user_data['checkin_guest_dict']
        else:
            checkin = query.data
            context.user_data['today_checkout_message'].delete()
            
            context.user_data['checkin_guest_dict'] = checkin

        no_show = copy.copy(checkin)
        no_show['callback'] = "NO_SHOW"

        if context.user_data['bookings_checkin_type'] == "day_choosed":
            keyboard = [
                [InlineKeyboardButton(
                    text="Отметить как незаезд", callback_data=no_show)],
                [InlineKeyboardButton(
                    text="Зарегистрировать гостя", callback_data=checkin)],
                [InlineKeyboardButton(
                    text="🔙 Вернуться к бронированиям", callback_data="RETURN_DAY_CHOOSED")],

            ]
        else:
            keyboard = [
                [InlineKeyboardButton(
                    text="Отметить как незаезд", callback_data=no_show)],
                [InlineKeyboardButton(
                    text="Зарегистрировать гостя", callback_data=checkin)],
                [InlineKeyboardButton(
                    text="🔙 Вернуться к сегодняшним бронированиям", callback_data="RETURN_TODAY")],

            ]

        query.edit_message_text(
            text=f"Выберите действие для гостя {checkin['name']} {checkin['lastname']}", reply_markup=InlineKeyboardMarkup(keyboard))

        return "ADMIN_BOOKING_LEVEL34"

    def no_show_guest_checkin_choose_penalty(self, update: Update, context: CallbackContext):

        query = update.callback_query
        
        callback_dict = copy.copy(query.data)
        query.answer()
        
        callback_dict['no_show_penalty'] = True
        with_penalty = copy.copy(callback_dict)
        
        callback_dict['no_show_penalty'] = False
        without_penalty = copy.copy(callback_dict)
        
        del callback_dict['no_show_penalty']
        
        keyboard = [
            [InlineKeyboardButton(text = "Со штрафем", callback_data=with_penalty)],
            [InlineKeyboardButton(text = "Без штрафа", callback_data=without_penalty)],
            [back_btn]
        ]
        
        keyboard_woodoo = [
            [InlineKeyboardButton(text = "Отметить незаезд", callback_data=callback_dict)],
            [back_btn]
        ]
        
        
        
        if callback_dict['booking']['channel_name'] == "Booking":
            query.edit_message_text(text = "Незаезд со штрафем или без?", reply_markup = InlineKeyboardMarkup(keyboard))
        elif callback_dict['booking']['channel_name'] == "WooDoo":
            query.edit_message_text(text = "Так как бронирование из WooDoo, нет возможности выбрать штраф для гостя. Но можно отметить незаезд", reply_markup = InlineKeyboardMarkup(keyboard_woodoo))
        else:
            query.edit_message_text(text = "К сожалению нельзя поставить незаезд для Airbnb.", reply_markup = InlineKeyboardMarkup([[back_btn]]))
            

        return "ADMIN_BOOKING_NO_SHOW_LEVEL1"
    
    def no_show_guest_checkin(self, update: Update, context: CallbackContext):
        query = update.callback_query
        query.answer()

        checkin = query.data

        message_to_edit = query.edit_message_text(
            text=f"Отмечаю не заезд для {checkin['name']} {checkin['lastname']}...")

        rcode = int(checkin['booking']['reservation_code'])
        
        if "no_show_penalty" in checkin.keys():
            penalty_bool = checkin['no_show_penalty']
            print(f"Penalty: {penalty_bool}")
            
        print(rcode)

        if checkin['booking']['channel_name'] == "Booking":
            res, status = wubook.make_no_show_guest(rcode, penalty_bool)
            print(res, status)

        elif checkin['booking']['channel_name'] == "WooDoo":
            res = wubook.cancel_booking(rcode)
            print(res)

        time.sleep(1)
        user_id, booking_id = checkin['user_id'], checkin['booking']['booking_id']

        if context.user_data['bookings_checkin_type'] == "day_choosed":
            keyboard = [
                [InlineKeyboardButton(
                    text="🔙 Вернуться к бронированиям", callback_data="RETURN_DAY_CHOOSED")],
                [InlineKeyboardButton(
                    text="🌐 Вернуться в главное меню", callback_data="RETURN_MAIN_MENU")],
                [back_btn],

            ]
        else:
            keyboard = [
                [InlineKeyboardButton(
                    text="🔙 Вернуться к сегодняшним бронированиям", callback_data="RETURN_TODAY")],
                [InlineKeyboardButton(
                    text="🌐 Вернуться в главное меню", callback_data="RETURN_MAIN_MENU")],
                [back_btn],

            ]

        if checkin['booking']['channel_name'] == "Airbnb":
            message_to_edit.edit_text(
                text="К сожалению нельзя поставить незаезд для Airbnb.", reply_markup=InlineKeyboardMarkup(keyboard))
        elif res == 0 or res == True:
            message_to_edit.edit_text(
                text="Гость успешно отмечен как не заезд и удален.", reply_markup=InlineKeyboardMarkup(keyboard))
            firebase.updateBookingWithId(user_id, booking_id, {'status': 5})
        else:
            message_to_edit.edit_text(
                text="Произошла какая-то ошибка.", reply_markup=InlineKeyboardMarkup(keyboard))
        
        return "ADMIN_BOOKING_NO_SHOW_LEVEL2"
        
            
    def register_guests_checkin(self, update: Update, context: CallbackContext):
        query = update.callback_query
        query.answer()
        
        if query.data != "BACK":

            checkin = query.data

            user_id, booking_id = checkin['user_id'], checkin['booking']['booking_id']

            context.user_data['register_booking'] = checkin['booking']
            context.user_data['register_user'] = checkin
            
        else:
            checkin = context.user_data['register_user']
            checkin['booking'] = context.user_data['register_booking']

        cancel_callback_dict = {
            "type": "CANCEL",
            "booking": checkin['booking'],
            "room_number": None
        }

        if context.user_data['bookings_checkin_type'] == "day_choosed":
            cancel_callback_dict['booking_type'] = "day_choosed"
        else:
            cancel_callback_dict['booking_type'] = "all"

        print(cancel_callback_dict['booking_type'])

        keyboard = [
            [InlineKeyboardButton(text="❌ Отменить чекин",
                                callback_data=cancel_callback_dict)]
        ]

        if query.data != "BACK":
            
            #Присваиваем номер как обычно
            
            # message_to_edit = context.bot.send_message(query.message.chat_id, text = f"Ищу свободну комнату для {checkin['name']} {checkin['lastname']}...")
            message_to_edit = query.edit_message_text(
                text=f"Ищу свободную комнату для {checkin['name']} {checkin['lastname']}...")

            message = ""
            error = False
            
            checkin['booking']['room_number'] = []
            
            for room_type_id in checkin['booking']['room_type_id']:
                assigned_room_number = firebase.assignGuestToRoom(checkin['booking'], room_type_id)  # actual
                # assigned_room_number = firebase.assignGuestToRoomTest(checkin['booking'], room_type_id) #test

                if (assigned_room_number is None):

                    message += "Почему то все комнаты заняты. Надо срочно исправить!\n\n"
                    error = True

                else:
                    
                    checkin['booking']['room_number'].append(assigned_room_number)

                    message += f"<b>Назначена комната {number_to_emoji(assigned_room_number)}</b>\n"
                    roomType = ""
                    for room_type in checkin['booking']['room_type']:
                        roomType += f"{room_type} "
                    message += f"{flag.flag(checkin['booking']['country_code']) if checkin['booking']['country_code'] != '--' else ''} {checkin['name']} {checkin['lastname']} - {checkin['booking']['adults']} гостей - {checkin['booking']['checkin_date']} по {checkin['booking']['checkout_date']} ({checkin['booking']['number_of_nights']} ночей) - {assigned_room_number} номер - {roomType}\n\n"
                    
                    message += f"<b>Стоимость: {checkin['booking']['price_in_USD']} USD | {checkin['booking']['price_in_KGS']} KGS | {checkin['booking']['price_in_RUB']} RUB</b>\n\n"

                    # message += f"<b>Стоимость: {'$' if checkin['booking']['currency'] == 'USD' else checkin['booking']['currency'] + ' '}{checkin['booking']['price']}</b>"
                    cancel_callback_dict['room_number'] = assigned_room_number
                    
                    context.user_data['register_booking'] = checkin['booking']
                    context.user_data['register_user'] = checkin
                    

            time.sleep(0.5)
            if not error:
                message += "<b>📷 Отправьте фото паспорта клиента</b>"
                message_to_edit.edit_text(
                    text=message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode = ParseMode.HTML)

                return "ADMIN_BOOKING_LEVEL4"
            else:
                message_to_edit.edit_text(
                    text=message, reply_markup=InlineKeyboardMarkup(keyboard))

                return "ADMIN_BOOKING_LEVEL4"
            
        else:
            assigned_room_number = " ".join(checkin['booking']['room_number'])
            
            message = f"<b>Назначена комната {number_to_emoji(assigned_room_number)}</b>\n"
            roomType = ""
            for room_type in checkin['booking']['room_type']:
                roomType += f"{room_type} "
            message += f"{flag.flag(checkin['booking']['country_code']) if checkin['booking']['country_code'] != '--' else ''} {checkin['name']} {checkin['lastname']} - {checkin['booking']['adults']} гостей - {checkin['booking']['checkin_date']} по {checkin['booking']['checkout_date']} ({checkin['booking']['number_of_nights']} ночей) - {assigned_room_number} номер - {roomType}\n\n"
            
            message += f"<b>Стоимость: {checkin['booking']['price_in_USD']} USD | {checkin['booking']['price_in_KGS']} KGS | {checkin['booking']['price_in_RUB']} RUB</b>\n\n"

            # message += f"<b>Стоимость: {'$' if checkin['booking']['currency'] == 'USD' else checkin['booking']['currency'] + ' '}{checkin['booking']['price']}</b>"
            cancel_callback_dict['room_number'] = assigned_room_number

            
        
            message += "<b>📷 Отправьте фото паспорта клиента</b>"
            query.edit_message_text(
                text=message, reply_markup = InlineKeyboardMarkup(keyboard), parse_mode = ParseMode.HTML)

            return "ADMIN_BOOKING_LEVEL4"

    def register_guest_get_passport(self, update: Update, context: CallbackContext):
        
        keyboard = [
                [InlineKeyboardButton(text="Полная оплата",
                                    callback_data="FULL_PAYMENT")],
                [InlineKeyboardButton(text="Частичная оплата",
                                    callback_data="PARTIAL_PAYMENT")],
                [InlineKeyboardButton(text="Оплата не требуется",
                                    callback_data="PAYMENT_NOT_NEEDED")],
                [InlineKeyboardButton(
                    text="Нет оплаты", callback_data="PAYMENT_NOT_PAID")],
                [back_btn]

        ]
                    
        if update.callback_query is None:
        
            photo = update.message.photo

            booking = context.user_data['register_booking']

            filename = f"passport_{booking['user_id']}_{booking['id']}.jpg"

            newFile = update.message.effective_attachment[-1].get_file()

            directory = "media/passports"
            os.makedirs(directory, exist_ok=True)

            newFile.download(custom_path=f"./media/passports/{filename}")

            public_url = firebase.upload_photo_to_cloud_storage(f"{filename}")

            print(public_url)

            firebase.put_link_passport_to_booking(
                booking['user_id'], booking['id'], f"{public_url}")


            context.bot.send_message(
                update.message.chat_id, "Выберите способ оплаты гостя", reply_markup=InlineKeyboardMarkup(keyboard))

        else:
            update.callback_query.edit_message_text("Выберите способ оплаты гостя", reply_markup=InlineKeyboardMarkup(keyboard))

            
        return "ADMIN_BOOKING_LEVEL5"

    def register_guest_get_payment_type(self, update: Update, context: CallbackContext):
        query = update.callback_query

        query.answer()
        

        if query.data != "BACK":
            
            payment_status = query.data

            booking = context.user_data['register_booking']

            user_id, booking_id = booking['user_id'], booking['id']

            firebase.updateBookingWithId(
                user_id, booking_id, {'payment_status': payment_status})
            
            context.user_data['register_booking'].update({'payment_status': payment_status})

        keyboard = [
            [InlineKeyboardButton(text="Сбер", callback_data="PAYMENT_SBER")],
            [InlineKeyboardButton(
                text="Финка", callback_data="PAYMENT_FINKA"),],
            [InlineKeyboardButton(
                text="Наличные", callback_data="PAYMENT_CASH"),],
            [back_btn]
        ]
        query.edit_message_text("Выберите способ оплаты гостя", reply_markup=InlineKeyboardMarkup(keyboard))

        return "ADMIN_BOOKING_LEVEL56"
    
    
    def register_guest_get_payment(self, update: Update, context: CallbackContext):
        query = update.callback_query

        query.answer()

        payment_dict = {'PAYMENT_SBER': "Сбер",
                        'PAYMENT_FINKA': "Финка", "PAYMENT_CASH": "Наличные"}
        
        if query.data != "BACK":

            payment_type = payment_dict[str(query.data)]

            booking = context.user_data['register_booking']

            user_id, booking_id = booking['user_id'], booking['id']

            firebase.updateBookingWithId(
                user_id, booking_id, {"payment_type": payment_type})
            
            context.user_data['register_booking'].update({"payment_type": payment_type})
        else:
            payment_type = context.user_data['register_booking']['payment_type']

        if payment_type == "Сбер":
            keyboard = [
                [InlineKeyboardButton(text="Рубли", callback_data="RUB")]
            ]
        elif payment_type == "Финка":
            keyboard = [
                [InlineKeyboardButton(text="Сомы", callback_data="KGS"),]
            ]
        elif payment_type == "Наличные":
            keyboard = [
                [
                    # InlineKeyboardButton(text="Рубли", callback_data="RUB")
                    InlineKeyboardButton(text="Сомы", callback_data="KGS"),
                    InlineKeyboardButton(text="Доллары", callback_data="USD"),
                    InlineKeyboardButton(text="Рубли", callback_data="RUB"),

                ]
            ]
            
        keyboard.append([back_btn])

        query.edit_message_text("Укажите валюту", reply_markup=InlineKeyboardMarkup(keyboard))

        return "ADMIN_BOOKING_LEVEL6"

    def register_guest_get_payment_currency(self, update: Update, context: CallbackContext):
        query = update.callback_query

        query.answer()
        
        if query.data != "BACK_PAYMENT_TOTAL":

            payment_currency = query.data

            booking = context.user_data['register_booking']

            user_id, booking_id = booking['user_id'], booking['id']

            context.user_data['register_booking_currency'] = payment_currency

            firebase.updateBookingWithId(
                user_id, booking_id, {"payment_currency": payment_currency})

        query.edit_message_text("Введите сумму", reply_markup = InlineKeyboardMarkup([[back_btn]]))

        return "ADMIN_BOOKING_LEVEL7"

    def register_guest_get_payment_total(self, update: Update, context: CallbackContext):

        try:
            query = update.callback_query
            query.answer()
            callback = query.data
            chat_id = query.message.chat_id
        except:
            callback = None

        if callback is None:

            payment_total = float(update.message.text)

            chat_id = update.message.chat_id

            booking = context.user_data['register_booking']

            user_id, booking_id = booking['user_id'], booking['id']

            firebase.updateBookingWithId(
                user_id, booking_id, {"payment_total": payment_total})

            payment_currency = context.user_data['register_booking_currency']

            try:
                payment_total_in_USD = convert_to_usd(
                    payment_currency, payment_total)

                firebase.updateBookingWithId(
                    user_id, booking_id, {"payment_total_in_USD": payment_total_in_USD})
            except:
                pass

            print(payment_total)
            
            keyboard = [
                [InlineKeyboardButton(text = "🔙 Ввести другую сумму", callback_data = "BACK_PAYMENT_TOTAL")]
            ]

        elif callback == "PAYMENT_NOT_NEEDED":
            booking = context.user_data['register_booking']

            user_id, booking_id = booking['user_id'], booking['id']
            firebase.updateBookingWithId(
                user_id, booking_id, {"payment_total": "NOT NEEDED"})
            
            keyboard = [
                [InlineKeyboardButton(text = "🔙 Выбрать другой метод оплаты", callback_data = "BACK_PAYMENT_QUERY")]
            ]

            
            
        elif callback == "PAYMENT_NOT_PAID":
            booking = context.user_data['register_booking']

            user_id, booking_id = booking['user_id'], booking['id']
            firebase.updateBookingWithId(user_id, booking_id, {
                                         "payment_total": "DELETE_FIELD", "payment_status": "NO_PAYMENT"})

            keyboard = [
                [InlineKeyboardButton(text = "🔙 Выбрать другой метод оплаты", callback_data = "BACK_PAYMENT_QUERY")]
            ]

        if context.user_data['bookings_checkin_type'] == "day_choosed":
            keyboard.extend([
                [InlineKeyboardButton(
                    text="🔙 Вернуться к бронированиям", callback_data="RETURN_DAY_CHOOSED")],
                [InlineKeyboardButton(
                    text="🌐 Вернуться в главное меню", callback_data="RETURN_MAIN_MENU")],

            ])
        else:
            keyboard.extend([
                [InlineKeyboardButton(
                    text="🔙 Вернуться к сегодняшним бронированиям", callback_data="RETURN_TODAY")],
                [InlineKeyboardButton(
                    text="🌐 Вернуться в главное меню", callback_data="RETURN_MAIN_MENU")],

            ])
        
        # print(keyboard)

        context.bot.send_message(
            chat_id, "Гость успешно зарегистрирован!", reply_markup=InlineKeyboardMarkup(keyboard))

        return "ADMIN_BOOKING_LEVEL8"


# Управление


    def admin_manage(self, update: Update, context: CallbackContext):
        query = update.callback_query
        query.answer()

        keyboard = [
            [InlineKeyboardButton(text="Касса", callback_data="ADMIN_CASSA"),
             InlineKeyboardButton(text="Гости", callback_data="ADMIN_GUEST")],
            [back_btn]
        ]

        query.edit_message_text(text="Выберите меню",
                                reply_markup=InlineKeyboardMarkup(keyboard))

        return "ADMIN_MANAGE_LEVEL1"

    def admin_manage_guests(self, update: Update, context: CallbackContext):

        query = update.callback_query
        query.answer()

        keyboard = [
            [InlineKeyboardButton(text="По ФИО", callback_data="ADMIN_SEARCH_BY_NAME"),
             InlineKeyboardButton(text="По почте", callback_data="ADMIN_SEARCH_BY_EMAIL")],
            [InlineKeyboardButton(text="По номеру телефона",
                                  callback_data="ADMIN_SEARCH_BY_PHONE")],
            [InlineKeyboardButton(text="Заезд сегодня",
                                  callback_data="ADMIN_SEARCH_TODAY")],
            [back_btn]
        ]

        query.edit_message_text(
            text="Найти бронь", reply_markup=InlineKeyboardMarkup(keyboard))

        return "ADMIN_MANAGE_LEVEL2"

    # Поиск по ФИО

    def admin_manage_search_by_name(self, update: Update, context: CallbackContext):
        query = update.callback_query

        query.answer()

        context.bot_data['previous_message'] = query.edit_message_text(
            text="Пожалуйста введите в формате (Имя Фамилия)", reply_markup=InlineKeyboardMarkup([[back_btn]]))

        return "ADMIN_MANAGE_NAME_LEVEL3"

    def admin_manage_get_search_by_name(self, update: Update, context: CallbackContext):
        fullname = update.message.text
        guests = firebase.getBookingByFullName(fullname)

        context.bot.edit_message_reply_markup(
            chat_id=update.message.from_user.id, message_id=context.bot_data['previous_message'].message_id, reply_markup=None)

        message = ""

        keyboard = [[], [back_btn]]

        if (len(guests) == 0):
            message += "Я не нашла бронирований по вашему запросу"
        else:

            if (len(guests) > 0):
                message += "Мы нашли несколько гостей по вашему запросу:\n\n"

            i = 1
            for guest in guests:
                message += f"Гость: {flag.flag(guest['booking'][0]['country_code']) if guest['booking'][0]['country_code'] != '--' else ''} {guest['name']} {guest['lastname']} - {guest['phone_number']}\n"
                for booking in guest['booking']:
                    user_booking = {'callback': 'CHOOSE_BOOKING', 'number_of_booking': i,
                                    'user_id': guest['user_id'], 'booking_id': booking['booking_id']}
                    message += f"     Бронирование {number_to_emoji(i)}: с {booking['checkin_date']} по {booking['checkout_date']} ({booking['number_of_nights']} ночей) - {booking['adults']} {'людей' if booking['adults'] > 2 else 'человек' if booking['adults'] == 1 else 'человека'} - {booking['room_number']} номер\n"
                    keyboard[0].append(InlineKeyboardButton(
                        text=f"{i}", callback_data=user_booking))
                    i += 1
                message += "\n"

        context.bot.send_message(
            update.message.from_user.id, text=message, reply_markup=InlineKeyboardMarkup(keyboard))

        return "ADMIN_MANAGE_LEVEL4"

    def generate_callback_dict(self, callbackDict: dict, callback: str):
        callbackDict['status_callback'] = callback
        return copy.copy(callbackDict)

    def generate_status_keyboard(self, statusDict: dict, callbackDict: dict):

        guest_status_keyboard = [
            [InlineKeyboardButton(text="Подтвердил ❌" if statusDict['approve_booking'] == False else "Подтвердил ✅", callback_data=self.generate_callback_dict(
                callbackDict, "APPROVED")), InlineKeyboardButton(text="Заехал ❌" if statusDict['checked_in'] == False else "Заехал ✅", callback_data=self.generate_callback_dict(callbackDict, "CHECKED_IN"))],
            [InlineKeyboardButton(text="Живет ❌" if statusDict['live'] == False else "Живет ✅", callback_data=self.generate_callback_dict(callbackDict, "LIVE")), InlineKeyboardButton(
                text="Выехал ❌" if statusDict['checked_out'] == False else "Выехал ✅", callback_data=self.generate_callback_dict(callbackDict, "CHECKED_OUT"))],
            [InlineKeyboardButton(text="Оплатил ❌" if statusDict['paid'] == False else "Оплатил ✅",
                                  callback_data=self.generate_callback_dict(callbackDict, "PAID"))],
            [back_btn]
        ]

        return guest_status_keyboard

    def admin_manage_edit_search(self, update: Update, context: CallbackContext):
        query = update.callback_query
        query.answer()

        callbackDict = query.data

        status = firebase.getStatusFromGuestBookingID(
            callbackDict['user_id'], callbackDict['booking_id'])

        message = "Выбранный гость:\n\n"

        guest = firebase.getBookingById(
            callbackDict['user_id'], callbackDict['booking_id'])
        # print(status)
        message += f"Гость: {flag.flag(guest['booking']['country_code']) if guest['booking']['country_code'] != '--' else ''} {guest['name']} {guest['lastname']} - {guest['phone_number']}\n"
        booking = guest['booking']
        message += f"       с {booking['checkin_date']} по {booking['checkout_date']} ({booking['number_of_nights']} ночей) - {booking['adults']} {'людей' if booking['adults'] > 2 else 'человек' if booking['adults'] == 1 else 'человека'} - {booking['room_number']} номер\n"

        query.edit_message_text(text=message, reply_markup=InlineKeyboardMarkup(
            self.generate_status_keyboard(status, callbackDict)))

        return "ADMIN_MANAGE_LEVEL5"

    def approve_status(self, update: Update, context: CallbackContext):
        query = update.callback_query
        statuses = {'APPROVED': 'approve_booking', 'CHECKED_IN': 'checked_in',
                    'LIVE': 'live', 'CHECKED_OUT': 'checked_out',
                    'PAID': 'paid', 'NOT_PAID': 'not_paid'}
        callback_data = query.data
        firebase.approveStatusFromGuestBookingID(
            user_id=callback_data['user_id'], booking_id=callback_data['booking_id'], status=statuses[str(callback_data['status_callback'])])
        query.answer()

        return self.admin_manage_edit_search(update, context)

        # status = firebase.getStatusFromGuestBookingID(callback_data['user_id'], callback_data['booking_id'])

        # query.edit_message_text(text = f"{query.data['number_of_booking']} {query.data['user_id']}", reply_markup=InlineKeyboardMarkup(self.generate_status_keyboard(status, callback_data)))

    # Поиск по телефону

    def admin_manage_search_by_phonenumber(self, update: Update, context: CallbackContext):
        query = update.callback_query

        query.answer()

        context.bot_data['previous_message'] = query.edit_message_text(
            text="Пожалуйста введите в формате +xxxxxxxxxxx", reply_markup=InlineKeyboardMarkup([[back_btn]]))

        return "ADMIN_MANAGE_PHONENUMBER_LEVEL3"

    def admin_incorrect_phonenumber(self, update: Update, context: CallbackContext):
        context.bot.send_message(
            update.message.chat_id, text="Неправильный формат. Введите еще раз.")

    def admin_manage_get_search_by_phonenumber(self, update: Update, context: CallbackContext):
        phonenumber = update.message.text
        guests = firebase.searchBookingByPhoneNumber(phonenumber)

        context.bot.edit_message_reply_markup(
            chat_id=update.message.from_user.id, message_id=context.bot_data['previous_message'].message_id, reply_markup=None)

        message = ""

        keyboard = [[], [back_btn]]

        if (len(guests) == 0):
            message += "Я не нашла бронирований по вашему запросу"
        else:

            if (len(guests) > 0):
                message += "Мы нашли несколько гостей по вашему запросу:\n\n"

            i = 1
            for guest in guests:
                message += f"Гость: {flag.flag(guest['booking'][0]['country_code']) if guest['booking'][0]['country_code'] != '--' else ''} {guest['name']} {guest['lastname']} - {guest['phone_number']}\n"
                for booking in guest['booking']:
                    user_booking = {'callback': 'CHOOSE_BOOKING', 'number_of_booking': i,
                                    'user_id': guest['user_id'], 'booking_id': booking['booking_id']}
                    message += f"     Бронирование {number_to_emoji(i)}: с {booking['checkin_date']} по {booking['checkout_date']} ({booking['number_of_nights']} ночей) - {booking['adults']} {'людей' if booking['adults'] > 2 else 'человек' if booking['adults'] == 1 else 'человека'} - {booking['room_number']} номер\n"
                    keyboard[0].append(InlineKeyboardButton(
                        text=f"{i}", callback_data=user_booking))
                    i += 1
                message += "\n"

        context.bot.send_message(
            update.message.from_user.id, text=message, reply_markup=InlineKeyboardMarkup(keyboard))

        return "ADMIN_MANAGE_LEVEL4"

    def admin_manage_edit_search_by_phonenumber(self, update: Update, context: CallbackContext):
        query = update.callback_query
        query.answer()

        callback = query.data.split(" | ")

        query.edit_message_text(text=callback[1])

    # Поиск по почте

    def admin_manage_search_by_email(self, update: Update, context: CallbackContext):
        query = update.callback_query

        query.answer()

        context.bot_data['previous_message'] = query.edit_message_text(
            text="Пожалуйста введите электронную почту", reply_markup=InlineKeyboardMarkup([[back_btn]]))

        return "ADMIN_MANAGE_EMAIL_LEVEL3"

    def admin_incorrect_email(self, update: Update, context: CallbackContext):
        context.bot.send_message(
            update.message.chat_id, text="Неправильный формат. Введите еще раз в формате 'user@test.ru'")

    def admin_manage_get_search_by_email(self, update: Update, context: CallbackContext):
        email = update.message.text
        guests = firebase.getBookingByEmail(email)

        context.bot.edit_message_reply_markup(
            chat_id=update.message.from_user.id, message_id=context.bot_data['previous_message'].message_id, reply_markup=None)

        message = ""

        keyboard = [[], [back_btn]]

        if (len(guests) == 0):
            message += "Я не нашла бронирований по вашему запросу"
        else:

            if (len(guests) > 0):
                message += "Мы нашли несколько гостей по вашему запросу:\n\n"

            i = 1
            for guest in guests:
                message += f"Гость: {flag.flag(guest['booking'][0]['country_code']) if guest['booking'][0]['country_code'] != '--' else ''} {guest['name']} {guest['lastname']} - {guest['phone_number']}\n"
                for booking in guest['booking']:
                    user_booking = {'callback': 'CHOOSE_BOOKING', 'number_of_booking': i,
                                    'user_id': guest['user_id'], 'booking_id': booking['booking_id']}
                    message += f"     Бронирование {number_to_emoji(i)}: с {booking['checkin_date']} по {booking['checkout_date']} ({booking['number_of_nights']} ночей) - {booking['adults']} {'людей' if booking['adults'] > 2 else 'человек' if booking['adults'] == 1 else 'человека'} - {booking['room_number']} номер\n"
                    keyboard[0].append(InlineKeyboardButton(
                        text=f"{i}", callback_data=user_booking))
                    i += 1
                message += "\n"

        context.bot.send_message(
            update.message.from_user.id, text=message, reply_markup=InlineKeyboardMarkup(keyboard))

        return "ADMIN_MANAGE_LEVEL4"

    def admin_manage_edit_search_by_email(self, update: Update, context: CallbackContext):
        query = update.callback_query
        query.answer()

        callback = query.data.split(" | ")

        query.edit_message_text(text=callback[1])

    # Заезд на сегодня

    def admin_manage_get_checkin_today(self, update: Update, context: CallbackContext):
        query = update.callback_query

        checkin_dict = firebase.getBookingForDay()['checkin']

        query.answer()

        message = ""
        keyboard = [
            [],
            [back_btn]]

        if (len(checkin_dict) == 0):
            message += "Я не нашла бронирований на сегодня"
        else:

            if (len(checkin_dict) > 0):
                message += "Мы нашли несколько гостей по вашему запросу:\n\n"

            i = 1
            for guest in checkin_dict:
                message += f"Гость: {flag.flag(guest['booking'][0]['country_code']) if guest['booking'][0]['country_code'] != '--' else ''} {guest['name']} {guest['lastname']} - {guest['phone_number']}\n"
                booking = guest['booking']
                user_booking = {'callback': 'CHOOSE_BOOKING', 'number_of_booking': i,
                                'user_id': guest['user_id'], 'booking_id': booking['booking_id']}
                message += f"     Бронирование {number_to_emoji(i)}: с {booking['checkin_date']} по {booking['checkout_date']} ({booking['number_of_nights']} ночей) - {booking['adults']} {'людей' if booking['adults'] > 2 else 'человек' if booking['adults'] == 1 else 'человека'} - {booking['room_number']} номер\n"
                keyboard[0].append(InlineKeyboardButton(
                    text=f"{i}", callback_data=user_booking))
                i += 1
                message += "\n"

        query.edit_message_text(
            text=message, reply_markup=InlineKeyboardMarkup(keyboard))

        return "ADMIN_MANAGE_LEVEL4"

    def admin_manage_edit_checkin_today(self, update: Update, context: CallbackContext):
        query = update.callback_query
        query.answer()

        callback = query.data.split(" | ")

        query.edit_message_text(text=callback[1])

    # Гости
    def admin_guests(self, update: Update, context: CallbackContext):
        query = update.callback_query
        query.answer()
        keyboard = [
            [InlineKeyboardButton(text="Нет связи", callback_data="NO_CONNECTION"), InlineKeyboardButton(
                text="Подтвердили", callback_data="APPROVE_BOOKING")],
            [InlineKeyboardButton(text="Оплатили", callback_data="PAID"), InlineKeyboardButton(
                text="Живут", callback_data="LIVE")],
            [InlineKeyboardButton(text="Сегодня заезд", callback_data="CHECKIN_TODAY"), InlineKeyboardButton(
                text="Сегодня выезд", callback_data="CHECKOUT_TODAY")],
            [InlineKeyboardButton(text="Не оплатили",
                                  callback_data="NOT_PAID")],
            [back_btn],
        ]

        query.edit_message_text(text="Выберите раздел",
                                reply_markup=InlineKeyboardMarkup(keyboard))

        return "ADMIN_GUESTS_LEVEL1"

    splitted_array = []

    page = 0

    def split_array(self, array, k, context: CallbackContext):
        context.user_data['splitted_array']: list = []
        # self.splitted_array.clear()
        for i in range(0, len(array), k):
            context.user_data['splitted_array'].append(array[i:i+k])
            # self.splitted_array.append(array[i:i+k])
        # return self.splitted_array

    def generate_page(self, page_number: int, context: CallbackContext):
        # pages = self.splitted_array
        pages = context.user_data['splitted_array']
        message = ""
        # keyboard = [[]]
        for i, guest in enumerate(pages[page_number-1]):
            new_line = '\n'
            message += f"{number_to_emoji(i+1)} {flag.flag(guest['booking']['country_code']) if guest['booking']['country_code'] != '--' else ''} {guest['name']} {guest['lastname']} - {guest['phone_number']}\n"
            message += f"     Бронирование: с {guest['booking']['checkin_date']} по {guest['booking']['checkout_date']} ({guest['booking']['number_of_nights']} ночей) - {guest['booking']['adults']} {'людей' if guest['booking']['adults'] > 2 else 'человек' if guest['booking']['adults'] == 1 else 'человека'} - {guest['booking']['room_number']} номер\n {new_line if len(pages[page_number-1]) != (i+1) else ''}"
            # keyboard[0].append(InlineKeyboardButton(text=f"{i+1}", callback_data=f"guest#{i+1}"))
        return message

    def admin_guests_status_without_checkin_and_checkout(self, update: Update, context: CallbackContext):
        query = update.callback_query

        query.answer("Пожалуйста подождите, это может занять время")

        callback = query.data

        keyboard = [
            [back_btn]
        ]

        message = ""
        guests = []

        if callback == "NO_CONNECTION":
            guests = firebase.getBookingByStatus("connection", False)
            message += "Нет связи\n"
        elif callback == "APPROVE_BOOKING":
            guests = firebase.getBookingByStatus("approve_booking", True)
            message += "Подтвердили бронирование\n"
        elif callback == "PAID":
            guests = firebase.getBookingByStatus("paid", True)
            message += "Оплатили\n"
        elif callback == "LIVE":
            guests = firebase.getBookingByStatus("live", True)
            message += "Живут\n"
        elif callback == "NOT_PAID":
            guests = firebase.getBookingByStatus("paid", False)
            message += "Не оплатили\n"

        if len(guests) == 0:
            message = "Я не нашла гостей с таким статусом"
            query.edit_message_text(
                text=message,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

            return "ADMIN_GUESTS_LEVEL2"

        guests_per_page = 5

        self.split_array(guests, guests_per_page, context)


        print(len(context.user_data['splitted_array']))

        paginator = InlineKeyboardPaginator(
            # len(self.splitted_array),
            len(context.user_data['splitted_array']),
            data_pattern='character#{page}'
        )

        context.user_data['page'] = 1
        # self.page = 1

        paginator.add_after(back_btn)

        text = self.generate_page(1, context)
        query.edit_message_text(
            text=text,
            reply_markup=paginator.markup(),
        )

        return "ADMIN_GUESTS_LEVEL2"

    def status_page_callback(self, update: Update, context: CallbackContext):
        query = update.callback_query

        query.answer()

        page = int(query.data.split('#')[1])

        paginator = InlineKeyboardPaginator(
            # len(self.splitted_array),
            len(context.user_data['splitted_array']),
            current_page=page,
            data_pattern='character#{page}'
        )

        context.user_data['page'] = page

        paginator.add_after(back_btn)

        text = self.generate_page(page, context)

        query.edit_message_text(
            text=text,
            reply_markup=paginator.markup(),
        )

        return "ADMIN_GUESTS_LEVEL2"

    def admin_pages_guest(self, update: Update, context: CallbackContext):
        query = update.callback_query

        query.answer()

        guest_number = int(query.data.split('#')[1])

        pages = context.user_data['splitted_array']

        page_number = context.user_data['page']

        guest = pages[page_number-1][guest_number-1]

        message = ""
        new_line = '\n'
        message += f"{flag.flag(guest['booking']['country_code']) if guest['booking']['country_code'] != '--' else ''} {guest['name']} {guest['lastname']} - {guest['phone_number']}\n"
        message += f"     Бронирование: с {guest['booking']['checkin_date']} по {guest['booking']['checkout_date']} ({guest['booking']['number_of_nights']} ночей) - {guest['booking']['adults']} {'людей' if guest['booking']['adults'] > 2 else 'человек' if guest['booking']['adults'] == 1 else 'человека'} - {guest['booking']['room_number']} номер\n"

        context.bot.send_message(query.message.chat_id, text=message)

    def admin_guests_status_checkin(self, update: Update, context: CallbackContext):
        keyboard = [
            [back_btn]
        ]

        checkin_checkout_dict = firebase.getBookingForDay()
        update.callback_query.answer()
        message = ""

        if len(checkin_checkout_dict['checkin']) > 0:
            message += "Заезд:\n"
        else:
            message += "Нет заездов на сегодня\n"

        for i, guest in enumerate(checkin_checkout_dict['checkin']):
            # message += f"{number_to_emoji(i+1)} {checkin['name']} {checkin['lastname']} - {checkin['phone_number']} - {checkin['booking']['number_of_people']} гостей - {checkin['booking']['checkin_date']} по {checkin['booking']['checkout_date']} - {checkin['booking']['room_number']} номер\n"
            new_line = '\n'
            message += f"🔵 {flag.flag(guest['booking']['country_code']) if guest['booking']['country_code'] != '--' else ''} {guest['name']} {guest['lastname']} - {guest['phone_number']}\n"
            message += f"     Бронирование: с {guest['booking']['checkin_date']} по {guest['booking']['checkout_date']} ({guest['booking']['number_of_nights']} ночей) - {guest['booking']['adults']} {'людей' if guest['booking']['adults'] > 2 else 'человек' if guest['booking']['adults'] == 1 else 'человека'} - {guest['booking']['room_number']} номер\n {new_line if len(checkin_checkout_dict['checkout']) != (i+1) else ''}"

        update.callback_query.edit_message_text(
            text=message,
            reply_markup=InlineKeyboardMarkup(keyboard))

        return "ADMIN_GUESTS_LEVEL2"

    def admin_guests_status_checkout(self, update: Update, context: CallbackContext):
        keyboard = [
            [back_btn]
        ]

        checkin_checkout_dict = firebase.getBookingForDay()
        update.callback_query.answer()
        message = ""

        if len(checkin_checkout_dict['checkout']) > 0:
            message += "\nВыезд:\n"
        else:
            message += "\nНет выездов на сегодня\n"

        for i, guest in enumerate(checkin_checkout_dict['checkout']):
            new_line = '\n'
            message += f"🔵 {flag.flag(guest['booking']['country_code']) if guest['booking']['country_code'] != '--' else ''} {guest['name']} {guest['lastname']} - {guest['phone_number']}\n"
            message += f"     Бронирование: с {guest['booking']['checkin_date']} по {guest['booking']['checkout_date']} ({guest['booking']['number_of_nights']} ночей) - {guest['booking']['adults']} {'людей' if guest['booking']['adults'] > 2 else 'человек' if guest['booking']['adults'] == 1 else 'человека'} - {guest['booking']['room_number']} номер\n {new_line if len(checkin_checkout_dict['checkout']) != (i+1) else ''}"

        update.callback_query.edit_message_text(
            text=message,
            reply_markup=InlineKeyboardMarkup(keyboard))

        return "ADMIN_GUESTS_LEVEL2"

    # Зарегистрированные гости

    def generate_page_checkin(self, page_number: int, context: CallbackContext):
        # pages = self.splitted_array
        pages = context.user_data['splitted_array']
        message = ""
        keyboard = [[]]
        for i, guest in enumerate(pages[page_number-1]):
            new_line = '\n'
            passport_is_exist = "passport_link" in guest['booking'].keys()
            payment_is_exist = "payment_total" in guest['booking'].keys()
            message += f"{number_to_emoji(i+1)} {'🟢' if passport_is_exist == True else '🔴'}{'🟢' if payment_is_exist == True else '🔴'} {flag.flag(guest['booking']['country_code']) if guest['booking']['country_code'] != '--' else ''} {guest['name']} {guest['lastname']} - {guest['phone_number']}\n"
            message += f"     Бронирование: с {guest['booking']['checkin_date']} по {guest['booking']['checkout_date']} ({guest['booking']['number_of_nights']} ночей) - {guest['booking']['adults']} {'людей' if guest['booking']['adults'] > 2 else 'человек' if guest['booking']['adults'] == 1 else 'человека'} - {guest['booking']['room_number']} номер\n {new_line if len(pages[page_number-1]) != (i+1) else ''}"
            keyboard[0].append(InlineKeyboardButton(
                text=f"{i+1}", callback_data=f"guest#{i+1}"))
        return (message, keyboard)

    def admin_checked_in_guests(self, update: Update, context: CallbackContext, **kwargs):

        if "update_checkin_guests_list" in kwargs.keys():
            query = context.user_data['checkin_guests_message_list']
        else:
            query = update.callback_query
            query.answer("Секунду")

            guests = firebase.getCheckedInGuests()

            if len(guests) == 0:
                query.edit_message_text(
                    "Пока нет зарегистрированных гостей", reply_markup=InlineKeyboardMarkup([[back_btn]]))
                return "ADMIN_CHECKED_IN_LEVEL1"

        message = f"""
Список зарегистрированных гостей:

Обратите внимание, индикаторы показывают наличие паспорта и оплаты. Первым идет паспорт, далее оплата

🟢 если имеется, 🔴 если нет    
    
"""
        guests_per_page = 5

        if "update_checkin_guests_list" in kwargs.keys():
            pass
        else:
            self.split_array(guests, guests_per_page, context)

        paginator = InlineKeyboardPaginator(
            len(context.user_data['splitted_array']),
            data_pattern='character#{page}'
        )

        context.user_data['page'] = 1

        paginator.add_after(back_btn)

        text, page_keyboard = self.generate_page_checkin(1, context)

        message += text

        if "update_checkin_guests_list" in kwargs.keys():
            context.user_data['checkin_guests_message_list'] = query.edit_text(
                text=message,
                reply_markup=paginator.markup(page_keyboard),

            )
        else:
            context.user_data['checkin_guests_message_list'] = query.edit_message_text(
                text=message,
                reply_markup=paginator.markup(page_keyboard),

            )

        return "ADMIN_CHECKED_IN_LEVEL1"


    def status_checked_in_page_callback(self, update: Update, context: CallbackContext, **kwargs):

        if "update_checkin_guests_list" in kwargs.keys():
            query = context.user_data['checkin_guests_message_list']
            page = context.user_data['page']
        else:
            query = update.callback_query

            query.answer()

            page = int(query.data.split('#')[1])

        paginator = InlineKeyboardPaginator(
            # len(self.splitted_array),
            len(context.user_data['splitted_array']),
            current_page=page,
            data_pattern='character#{page}'
        )

        context.user_data['page'] = page

        paginator.add_after(back_btn)

        message = f"""
Список зарегистрированных гостей:

Обратите внимание, индикаторы показывают наличие паспорта и оплаты. Первым идет паспорт, далее оплата

🟢 если имеется, 🔴 если нет    
    
"""

        text, page_keyboard = self.generate_page_checkin(page, context)

        message += text

        if "update_checkin_guests_list" in kwargs.keys():
            context.user_data['checkin_guests_message_list'] = query.edit_text(
                text=message,
                reply_markup=paginator.markup(page_keyboard),

            )
        else:
            context.user_data['checkin_guests_message_list'] = query.edit_message_text(
                text=message,
                reply_markup=paginator.markup(page_keyboard),
            )

        return "ADMIN_CHECKED_IN_LEVEL1"

    def admin_pages_checked_in_guest(self, update: Update, context: CallbackContext, **kwargs):

        query = update.callback_query

        query.answer()

        guest_number = int(query.data.split('#')[1])

        page_number = context.user_data['page']

        pages = context.user_data['splitted_array']

        guest = pages[page_number-1][guest_number-1]

        message = ""
        new_line = '\n'
        message += f"{flag.flag(guest['booking']['country_code']) if guest['booking']['country_code'] != '--' else ''} {guest['name']} {guest['lastname']} - {guest['phone_number']}\n"
        message += f"     Бронирование: с {guest['booking']['checkin_date']} по {guest['booking']['checkout_date']} ({guest['booking']['number_of_nights']} ночей) - {guest['booking']['adults']} {'людей' if guest['booking']['adults'] > 2 else 'человек' if guest['booking']['adults'] == 1 else 'человека'} - {guest['booking']['room_number']} номер\n\n"

        print("passport_link" in guest['booking'].keys())

        keyboard = [

        ]

        add_passport = [InlineKeyboardButton(
            text="🪪 Добавить паспорт", callback_data=f"ADD_PASSPORT | {page_number} {guest_number}")]
        add_payment = [InlineKeyboardButton(
            text="💵 Добавить оплату", callback_data=f"ADD_PAYMENT | {page_number} {guest_number}")]

        edit_passport = [InlineKeyboardButton(
            text="🪪 Изменить паспорт", callback_data=f"ADD_PASSPORT | {page_number} {guest_number}")]
        edit_payment = [InlineKeyboardButton(
            text="💵 Изменить оплату", callback_data=f"ADD_PAYMENT | {page_number} {guest_number}")]

        context.user_data['register_booking'] = {
            "booking": guest['booking'],
            "page_number": page_number,
            "guest_number": guest_number
        }

        if not ("passport_link" in guest['booking'].keys()):
            message += "\n🔴 Паспорта нет\n"

            keyboard.append(add_passport)

            if not ("payment_total" in guest['booking'].keys()):
                message += "🔴 Оплаты нет"
                keyboard.append(add_payment)

            guest_message = context.bot.send_message(
                chat_id=query.message.chat_id, text=message, reply_markup=InlineKeyboardMarkup(keyboard))

            print(" Паспорта нет")
        else:

            print(guest['booking']['passport_link'])

            keyboard.append(edit_passport)

            if not ("payment_total" in guest['booking'].keys()):
                message += "🔴 Оплаты нет"
                keyboard.append(add_payment)
            elif guest['booking']['payment_total'] == "NOT NEEDED":
                message += f"🟢 Внесена оплата - Оплата не требуется"
                keyboard.append(edit_payment)
            else:
                message += f"🟢 Внесена оплата - {guest['booking']['payment_total']} {guest['booking']['payment_currency']} методом {guest['booking']['payment_type']}"
                keyboard.append(edit_payment)
            guest_message = context.bot.send_photo(
                chat_id=query.message.chat_id, photo=guest['booking']['passport_link'], caption=message, reply_markup=InlineKeyboardMarkup(keyboard))

        context.user_data['checkin_guest_message'] = guest_message

    def admin_checked_in_guest_add_passport(self, update: Update, context: CallbackContext):

        query = update.callback_query

        query.answer()

        pages = context.user_data['splitted_array']

        page_number = int(query.data.split(" | ")[1].split(" ")[0])
        guest_number = int(query.data.split(" | ")[1].split(" ")[1])

        guest = pages[page_number-1][guest_number-1]

        context.user_data['register_booking'] = {
            "booking": guest['booking'],
            "page_number": page_number,
            "guest_number": guest_number
        }

        message = "Отправьте фото паспорта клиента"

        context.user_data['add_passport_messages'] = []

        mes = context.bot.send_message(query.message.chat_id, text=message)

        context.user_data['add_passport_messages'].append(mes)

        return "ADMIN_CHECKED_IN_LEVEL2"

    def admin_checked_in_guest_get_passport(self, update: Update, context: CallbackContext):
        photo = update.message.photo

        context.user_data['add_passport_messages'].append(update.message)

        booking = context.user_data['register_booking']['booking']

        page_number = context.user_data['register_booking']['page_number']
        guest_number = context.user_data['register_booking']['guest_number']

        filename = f"passport_{booking['user_id']}_{booking['id']}.jpg"

        newFile = update.message.effective_attachment[-1].get_file()

        directory = "media/passports"
        os.makedirs(directory, exist_ok=True)

        newFile.download(custom_path=f"./media/passports/{filename}")

        public_url = firebase.upload_photo_to_cloud_storage(f"{filename}")

        print(public_url)

        firebase.put_link_passport_to_booking(
            booking['user_id'], booking['id'], f"{public_url}")

        message = context.bot.send_message(
            update.message.chat_id, text="Готово!")

        context.user_data['add_passport_messages'].append(message)

        time.sleep(1.5)

        for message in context.user_data['add_passport_messages']:
            message.delete()

        context.user_data['splitted_array'][page_number -
                                            1][guest_number-1]['booking']['passport_link'] = public_url

        self.admin_checked_in_guest_update_message(update, context)

        return "ADMIN_CHECKED_IN_LEVEL1"

    def admin_checked_in_guest_update_message(self, update, context):
        page_number = context.user_data['register_booking']['page_number']
        guest_number = context.user_data['register_booking']['guest_number']

        guest = context.user_data['splitted_array'][page_number -
                                                    1][guest_number-1]

        guest_message = context.user_data['checkin_guest_message']

        guest_message.delete()

        message = ""
        new_line = '\n'
        message += f"{flag.flag(guest['booking']['country_code']) if guest['booking']['country_code'] != '--' else ''} {guest['name']} {guest['lastname']} - {guest['phone_number']}\n"
        message += f"     Бронирование: с {guest['booking']['checkin_date']} по {guest['booking']['checkout_date']} ({guest['booking']['number_of_nights']} ночей) - {guest['booking']['adults']} {'людей' if guest['booking']['adults'] > 2 else 'человек' if guest['booking']['adults'] == 1 else 'человека'} - {guest['booking']['room_number']} номер\n\n"

        print("passport_link" in guest['booking'].keys())

        keyboard = [

        ]

        add_passport = [InlineKeyboardButton(
            text="🪪 Добавить паспорт", callback_data=f"ADD_PASSPORT | {page_number} {guest_number}")]
        add_payment = [InlineKeyboardButton(
            text="💵 Добавить оплату", callback_data=f"ADD_PAYMENT | {page_number} {guest_number}")]

        edit_passport = [InlineKeyboardButton(
            text="🪪 Изменить паспорт", callback_data=f"ADD_PASSPORT | {page_number} {guest_number}")]
        edit_payment = [InlineKeyboardButton(
            text="💵 Изменить оплату", callback_data=f"ADD_PAYMENT | {page_number} {guest_number}")]

        if not ("passport_link" in guest['booking'].keys()):
            message += "\n🔴 Паспорта нет\n"

            keyboard.append(add_passport)

            if not ("payment_total" in guest['booking'].keys()):
                message += "🔴 Оплаты нет"
                keyboard.append(add_payment)

            guest_message = context.bot.send_message(
                chat_id=guest_message.chat_id, text=message, reply_markup=InlineKeyboardMarkup(keyboard))

        else:

            print(guest['booking']['passport_link'])

            keyboard.append(edit_passport)

            if not ("payment_total" in guest['booking'].keys()):
                message += "🔴 Оплаты нет"
                keyboard.append(add_payment)
            elif guest['booking']['payment_total'] == "NOT NEEDED":
                message += f"🟢 Внесена оплата - Оплата не требуется"
                keyboard.append(edit_payment)
            else:
                message += f"🟢 Внесена оплата - {guest['booking']['payment_total']} {guest['booking']['payment_currency']} методом {guest['booking']['payment_type']}"
                keyboard.append(edit_payment)

            guest_message = context.bot.send_photo(
                chat_id=guest_message.chat_id, photo=guest['booking']['passport_link'], caption=message, reply_markup=InlineKeyboardMarkup(keyboard))

        context.user_data['checkin_guest_message'] = guest_message

        if context.user_data['page'] == 1:
            return self.admin_checked_in_guests(update, context, update_checkin_guests_list=True)
        else:
            return self.status_checked_in_page_callback(update, context, update_checkin_guests_list=True)

    def admin_checked_in_guest_add_payment(self, update: Update, context: CallbackContext):
        query = update.callback_query

        query.answer()

        keyboard = [
            [
                InlineKeyboardButton(
                    text="Сбер", callback_data="PAYMENT_SBER"),
                InlineKeyboardButton(
                    text="Финка", callback_data="PAYMENT_FINKA"),
                InlineKeyboardButton(
                    text="Наличные", callback_data="PAYMENT_CASH"),
            ],
            [InlineKeyboardButton(text="Оплата не требуется",
                                  callback_data="PAYMENT_NOT_NEEDED")],
            [InlineKeyboardButton(text="Не оплачено",
                                  callback_data="PAYMENT_NOT_PAID")]
        ]
        mes = context.bot.send_message(
            query.message.chat_id, "Выберите способ оплаты гостя", reply_markup=InlineKeyboardMarkup(keyboard))
        context.user_data['add_payment_messages'] = []

        context.user_data['add_payment_messages'].append(mes)
        print("Works!")
        return "ADMIN_CHECKED_IN_LEVEL2"

    def admin_checked_in_guest_get_payment(self, update, context):
        query = update.callback_query

        query.answer()
        print("Works")

        payment_dict = {'PAYMENT_SBER': "Сбер",
                        'PAYMENT_FINKA': "Финка", "PAYMENT_CASH": "Наличные"}

        payment_type = payment_dict[str(query.data)]

        booking = context.user_data['register_booking']['booking']
        print(booking)

        user_id, booking_id = booking['user_id'], booking['id']

        firebase.updateBookingWithId(
            user_id, booking_id, {"payment_type": payment_type})

        if payment_type == "Сбер":
            keyboard = [
                [InlineKeyboardButton(text="Рубли", callback_data="RUB")]
            ]
        elif payment_type == "Финка":
            keyboard = [
                [InlineKeyboardButton(text="Сомы", callback_data="KGS"),]
            ]
        elif payment_type == "Наличные":
            keyboard = [
                [
                    # InlineKeyboardButton(text="Рубли", callback_data="RUB")
                    InlineKeyboardButton(text="Сомы", callback_data="KGS"),
                    InlineKeyboardButton(text="Доллары", callback_data="USD"),

                ]
            ]

        mes = context.bot.send_message(
            query.message.chat_id, "Укажите валюту", reply_markup=InlineKeyboardMarkup(keyboard))

        context.user_data['add_payment_messages'].append(mes)

        return "ADMIN_CHECKED_IN_LEVEL3"

    def admin_checked_in_guest_get_payment_currency(self, update: Update, context: CallbackContext):
        query = update.callback_query

        query.answer()

        payment_currency = query.data

        booking = context.user_data['register_booking']['booking']

        user_id, booking_id = booking['user_id'], booking['id']

        context.user_data['register_booking_currency'] = payment_currency

        firebase.updateBookingWithId(
            user_id, booking_id, {"payment_currency": payment_currency})

        mes = context.bot.send_message(query.message.chat_id, "Введите сумму")

        context.user_data['add_payment_messages'].append(mes)

        return "ADMIN_CHECKED_IN_LEVEL3"

    def admin_checked_in_guest_get_payment_total(self, update: Update, context: CallbackContext):

        try:
            query = update.callback_query
            query.answer()
            callback = query.data
            chat_id = query.message.chat_id

        except:
            callback = None

        if callback is None:
            context.user_data['add_payment_messages'].append(update.message)

            payment_total = float(update.message.text)

            chat_id = update.message.chat_id

            booking = context.user_data['register_booking']['booking']

            user_id, booking_id = booking['user_id'], booking['id']

            firebase.updateBookingWithId(
                user_id, booking_id, {"payment_total": payment_total})

            payment_currency = context.user_data['register_booking_currency']

            try:
                payment_total_in_USD = convert_to_usd(
                    payment_currency, payment_total)

                firebase.updateBookingWithId(
                    user_id, booking_id, {"payment_total_in_USD": payment_total_in_USD})
            except:
                pass

            print(payment_total)
        elif callback == "PAYMENT_NOT_NEEDED":
            booking = context.user_data['register_booking']['booking']

            user_id, booking_id = booking['user_id'], booking['id']
            firebase.updateBookingWithId(
                user_id, booking_id, {"payment_total": "NOT NEEDED"})
        elif callback == "PAYMENT_NOT_PAID":
            booking = context.user_data['register_booking']['booking']

            user_id, booking_id = booking['user_id'], booking['id']
            firebase.updateBookingWithId(
                user_id, booking_id, {"payment_total": "DELETE_FIELD"})

        page_number = context.user_data['register_booking']['page_number']
        guest_number = context.user_data['register_booking']['guest_number']

        context.user_data['splitted_array'][page_number-1][guest_number -
                                                           1] = firebase.getBookingById(user_id, booking_id)

        mes = context.bot.send_message(chat_id, "Оплата успешно добавлена!")
        context.user_data['add_payment_messages'].append(mes)

        time.sleep(1.5)

        for message in context.user_data['add_payment_messages']:
            message.delete()

        self.admin_checked_in_guest_update_message(update, context)

        return "ADMIN_CHECKED_IN_LEVEL1"

# горничные
    def housekeeping_menu(self, update: Update, context: CallbackContext):
        query = update.callback_query

        query.answer()

        keyboard = [
            [InlineKeyboardButton(
                text="➕ Добавить горничную", callback_data="ADD_MAID")],
            [back_btn]
        ]

        maids = firebase.get_maid()

        for maid in maids:
            keyboard.insert(0, [InlineKeyboardButton(
                text=f"🔵 {maid['name']} {maid['surname']}", callback_data=f"SELECT_MAID | {maid[id]}")])

        query.edit_message_text(text="Выберите горничную или добавьте человека на эту роль",
                                reply_markup=InlineKeyboardMarkup(keyboard))

        return "ADMIN_HOUSEKEEPING_LEVEL1"

    def housekeeping_add_maid(self, update: Update, context: CallbackContext):
        query = update.callback_query

        query.answer()

        keyboard = [
            [back_btn]
        ]

        query.edit_message_text(
            text="Введите имя и фамилию горничной", reply_markup=InlineKeyboardMarkup(keyboard))

        return "ADMIN_HOUSEKEEPING_LEVEL2"

    def housekeeping_get_maid_name(self, update: Update, context: CallbackContext):

        arr = update.message.text.split(" ")

        name, surname = arr[0], arr[1]

        firestore_id = firebase.add_maid(name, surname)

        context.bot.send_message(update.message.chat_id, text=f"""
Отправьте данную ссылку горничной. Горничная должна обязательно пройти по ссылке и нажать на старт:
{bot_link}?start={firestore_id}
""")

        return "ADMIN_HOUSEKEEPING_LEVEL3"
    
    
#Свободные номера

    def admin_available_rooms_menu(self, update: Update, context: CallbackContext):
        query = update.callback_query
        query.answer()
        
        keyboard = [
            [InlineKeyboardButton(text="На сегодня", callback_data = "FOR_TODAY")],
            [InlineKeyboardButton(text="На период", callback_data = "FOR_DATES")],
            [back_btn]
        ]
        
        query.edit_message_text(text = "Доступные номера на сегодня или на период?", reply_markup=InlineKeyboardMarkup(keyboard))
        
        return "ADMIN_AVAILABLE_ROOMS_LEVEL1"
        
    def admin_available_rooms_for_today(self, update: Update, context: CallbackContext):
        query = update.callback_query
        query.answer()
        
        keyboard = [
            [back_btn]
        ]
        
        room_names = {
            "shared": "Хостел",
            "double": "Стандарт",
            "twins": "Твин",
            "deluxe": "Люкс"
        }
        
        today = datetime.datetime.now(tz=pytz.timezone("Asia/Almaty")) - datetime.timedelta(hours = 8)

        print(today)
        today = today.date()
        today = datetime.datetime.combine(today, datetime.time.min)

        
        available_rooms = wubook.get_availability_for_all(today, today + datetime.timedelta(days=1))
        
        message = f"Доступные номера на сегодня, {today.strftime('%d-%m-%Y')}:\n"
        
        count = 0
        for room in available_rooms:
            if available_rooms[room][0] > 0:
                message += f"   {number_to_emoji(available_rooms[room][0])} {room_names[room]}\n"
                count+=1
        
        if count == 0:
            message +="     Доступных номеров нет"

        query.edit_message_text(text = message, reply_markup=InlineKeyboardMarkup(keyboard))

        return "ADMIN_AVAILABLE_ROOMS_LEVEL2"
    
    def admin_available_rooms_for_period(self, update: Update, context: CallbackContext):
        query = update.callback_query
        query.answer()
        
        keyboard = [
            [back_btn]
        ]
        
        room_names = {
            "shared": "Хостел",
            "double": "Стандарт",
            "twins": "Твин",
            "deluxe": "Люкс"
        }
        
        query.edit_message_text(text = "Выберите дату заезда:", reply_markup=telegramcalendar.create_calendar())
        
        
        return "ADMIN_AVAILABLE_ROOMS_LEVEL2"

    def admin_available_rooms_for_period_get_checkin_date(self, update: Update, context: CallbackContext):
        query = update.callback_query
        query.answer()
        
        selected, date = telegramcalendar.process_calendar_selection(
                    update, context)      
          
        if selected:
            
            context.user_data['available_rooms_checkin_date'] = date

        
            query.edit_message_text(text = "Выберите дату выезда:", reply_markup=telegramcalendar_for_checkout.create_calendar(year = date.year, month = date.month, current_date=date+datetime.timedelta(days=1)))
        
        
            return "ADMIN_AVAILABLE_ROOMS_LEVEL3"
    
    def admin_available_rooms_for_period_get_checkout_date(self, update: Update, context: CallbackContext):
        query = update.callback_query
        query.answer()
        
        selected, date = telegramcalendar.process_calendar_selection(
                    update, context)      
          
        if selected:
            
            context.user_data['available_rooms_checkout_date'] = date

            room_names = {
                "shared": "Хостел",
                "double": "Стандарт",
                "twins": "Твин",
                "deluxe": "Люкс"
            }
        
            dfrom = context.user_data['available_rooms_checkin_date']
            dto = context.user_data['available_rooms_checkout_date']
            
            available_rooms = wubook.get_availability_for_all(dfrom, dto)
            
            message = f"Доступные номера на период, с {dfrom.strftime('%d-%m-%Y')} по {dto.strftime('%d-%m-%Y')}:\n"
            
            count = 0
            for room in available_rooms:
                if min(available_rooms[room]) > 0:
                    message += f"   {number_to_emoji(min(available_rooms[room]))} {room_names[room]}\n"
                    count+=1
            
            if count == 0:
                    message +="     Доступных номеров нет"
                
            keyboard = [
                [back_btn]
            ]
        
            query.edit_message_text(text = message, reply_markup=InlineKeyboardMarkup(keyboard))
            
            
            return "ADMIN_AVAILABLE_ROOMS_LEVEL3"


def set_notification_helper(update: Update, context: CallbackContext):
    jobs = context.job_queue.get_jobs_by_name("Morning")

    print(jobs)
    if len(jobs) != 0:
        text = "Already set and deleted"
        for job in jobs:
            job.schedule_removal()
        print(text)

    time = datetime.time(hour=22, minute=32,
                         tzinfo=pytz.timezone('Asia/Aqtau'))
    context.job_queue.run_daily(admin_notification_evening, time,  days=(
        0, 1, 2, 3, 4, 5, 6), context=None, name="Morning")

    print("Set notification")


# Уведомления администратору

def set_evening_notification(update: Update, context: CallbackContext):
    query = update.callback_query

    jobs = context.job_queue.get_jobs_by_name("Evening_once")

    print(jobs)
    if len(jobs) != 0:
        text = "Already set and deleted"
        for job in jobs:
            job.schedule_removal()
        print(text)

    time = 2
    context.job_queue.run_once(
        admin_notification_evening, time, context=None, name="Evening_once")

    print("Set notification")

    query.answer("Уведомление придет через несколько секунд")


def set_morning_notification(update: Update, context: CallbackContext):
    query = update.callback_query

    jobs = context.job_queue.get_jobs_by_name("Morning_once")

    print(jobs)
    if len(jobs) != 0:
        text = "Already set and deleted"
        for job in jobs:
            job.schedule_removal()
        print(text)

    time = 2
    context.job_queue.run_once(
        admin_notification_morning, time, context=None, name="Morning_once")

    print("Set notification")

    query.answer("Уведомление придет через несколько секунд")


def set_daily_evening_notification(update: Update, context: CallbackContext):
    query = update.callback_query

    jobs = context.job_queue.get_jobs_by_name("Evening")

    print(jobs)
    if len(jobs) != 0:
        text = "Already set and deleted"
        for job in jobs:
            job.schedule_removal()
        print(text)

    # time = 2
    # context.job_queue.run_once(admin_notification_evening, time, context=None, name="Evening_once")

    time = datetime.time(
        hour=21, minute=0, tzinfo=pytz.timezone('Asia/Almaty'))
    context.job_queue.run_daily(admin_notification_evening, time,  days=(
        0, 1, 2, 3, 4, 5, 6), context=None, name="Evening")

    print("Set notification")

    query.answer("Уведомление на 9 вечера установлено")


def set_daily_morning_notification(update: Update, context: CallbackContext):
    query = update.callback_query

    jobs = context.job_queue.get_jobs_by_name("Morning")

    print(jobs)
    if len(jobs) != 0:
        text = "Already set and deleted"
        for job in jobs:
            job.schedule_removal()
        print(text)

    # time = 2
    # context.job_queue.run_once(admin_notification_morning, time, context=None, name="Morning_once")

    time = datetime.time(hour=9, minute=0, tzinfo=pytz.timezone('Asia/Almaty'))
    context.job_queue.run_daily(admin_notification_morning, time,  days=(
        0, 1, 2, 3, 4, 5, 6), context=None, name="Morning")

    print("Set notification")

    query.answer("Уведомление на 9 утра установлено")


def admin_notification_evening(context: CallbackContext):

    # not_checked_in_guests = firebase.get_not_checked_in_guests()

    message = "<b>Регулярная вечерная рассылка</b>\n\n"

    keyboard = [
        [InlineKeyboardButton(
            text="➡️ Перейти к регистрации гостей", callback_data="REGISTER_GUESTS")]
    ]

    today = datetime.datetime.now(tz=pytz.timezone("Asia/Almaty")).date()
    today = datetime.datetime.combine(today, datetime.time.min)

    # yesterday = today - datetime.timedelta(days=1)
    date = today

    # print(yesterday)

    checkin_checkout_dict = firebase.getBookingForDay(date=date)

    if len(checkin_checkout_dict['checkin']) > 0:
        message += f"<b>Заезд на {date.strftime('%d.%m')}:</b>\n"
    else:
        message += "Нет заездов на выбранную дату\n"

    checkin_arr = {
        "checked_in": [],
        "not_checked_in": []
    }

    checkout_arr = {
        "checked_out": [],
        "not_checked_out": [],
        "not_show_up": []
    }

    for checkin in checkin_checkout_dict['checkin']:
        status = firebase.getStatusFromGuestBookingID(
            checkin['user_id'], checkin['booking']['booking_id'])
        if status['checked_in']:
            checkin['booking']['status'] = status
            checkin_arr['checked_in'].append(checkin)
        else:
            checkin_arr['not_checked_in'].append(checkin)

    if len(checkin_checkout_dict['checkin']) > 0:
        message += f"Сегодня заселились {len(checkin_arr['checked_in'])} из {len(checkin_checkout_dict['checkin'])} гостей\n\n"

    for i, checkin in enumerate(checkin_arr['checked_in']):
        if i == 0:
            message += "<b>Заселились:</b>\n"

        status = checkin['booking']['status']
        roomType = ""
        for room_type in checkin['booking']['room_type']:
            roomType += f"{room_type} "
        message += f"🟢 {flag.flag(checkin['booking']['country_code']) if checkin['booking']['country_code'] != '--' else ''} <b>{checkin['name']} {checkin['lastname']}</b> - {checkin['booking']['adults']} гостей - {checkin['booking']['checkin_date']} по {checkin['booking']['checkout_date']} ({checkin['booking']['number_of_nights']} ночей) - {checkin['booking']['room_number']} номер - {roomType}\n"
        if status['checked_in']:
            message += f"""    {'🟥 Оплаты нет' if 'payment_total' not in checkin['booking'].keys()  else "🟩 Оплата имеется - оплата не требуется" if checkin['booking']['payment_total'] == 'NOT NEEDED' else f"🟩 Оплата имеется - {checkin['booking']['payment_total']} {checkin['booking']['payment_currency']} методом {checkin['booking']['payment_type']}"} \n"""
            message += f"""    {'🟥 Паспорт не внесен' if 'passport_link' not in checkin['booking'].keys()  else f"🟩 Паспорт внесен"}\n"""

        if i == len(checkin_arr['checked_in']) - 1:
            message += "\n"

    for i, checkin in enumerate(checkin_arr['not_checked_in']):
        if i == 0:
            message += "<b>Не заселились:</b>\n"

        roomType = ""
        for room_type in checkin['booking']['room_type']:
            roomType += f"{room_type} "
        message += f"🔴 {flag.flag(checkin['booking']['country_code']) if checkin['booking']['country_code'] != '--' else ''} <b>{checkin['name']} {checkin['lastname']}</b> - {checkin['booking']['adults']} гостей - {checkin['booking']['checkin_date']} по {checkin['booking']['checkout_date']} ({checkin['booking']['number_of_nights']} ночей) - {checkin['booking']['room_number']} номер - {roomType}\n"

        if i == len(checkin_arr['not_checked_in']) - 1:
            message += "\n"

    if len(checkin_checkout_dict['checkout']) > 0:
        message += f"\n<b>Выезд на {date.strftime('%d.%m')}:</b>\n"
    else:
        message += "\nНет выездов на выбранную дату\n"

    for checkout in checkin_checkout_dict['checkout']:
        status = firebase.getStatusFromGuestBookingID(
            checkout['user_id'], checkout['booking']['booking_id'])
        if checkout['booking']['checked_out']:
            checkout_arr['checked_out'].append(checkout)
        else:
            if status['checked_in']:
                checkout_arr['not_checked_out'].append(checkout)
            else:
                checkout_arr['not_show_up'].append(checkout)

    if len(checkin_checkout_dict['checkout']) > 0:
        not_show_up = f"{len(checkout_arr['not_show_up'])} {'гость' if len(checkout_arr['not_show_up']) == 1 else 'гостей'}" if len(
            checkout_arr['not_show_up']) > 0 else " "

        message += f"Сегодня выселились {len(checkout_arr['checked_out'])} из {len(checkin_checkout_dict['checkout'])} гостей| {not_show_up}\n\n"

    for i, checkout in enumerate(checkout_arr['checked_out']):
        if i == 0:
            message += "<b>Выселились:</b>\n"

        message += f"🟢 {flag.flag(checkout['booking']['country_code']) if checkout['booking']['country_code'] != '--' else ''} <b>{checkout['name']} {checkout['lastname']}</b> - {checkout['booking']['adults']} гостей - {checkout['booking']['checkin_date']} по {checkout['booking']['checkout_date']} ({checkout['booking']['number_of_nights']} ночей) - {checkout['booking']['room_number']} номер\n"
        if checkout['booking']['checked_out']:
            message += f"    {'🟥 Ключ сдан' if 'key_returned' not in checkout['booking'].keys() or not checkout['booking']['key_returned'] else '🟩 Ключ сдан'} | "
            message += f"{'🟥 Полотенце в наличии' if 'towel_is_okay' not in checkout['booking'].keys() or not checkout['booking']['towel_is_okay'] else '🟩 Полотенце в наличии'} | "
            message += f"{'🟥 Белье в порядке' if 'linen_is_okay' not in checkout['booking'].keys() or not checkout['booking']['linen_is_okay'] else '🟩 Белье в порядке'}\n"

            if 'checkout_additional_comments' in checkout['booking'].keys():
                message += f"    <b>Другие замечания:</b> {checkout['booking']['checkout_additional_comments']}\n"

        if i == len(checkout_arr['checked_out'])-1:
            message += "\n"

    for i, checkout in enumerate(checkout_arr['not_checked_out']):
        if i == 0:
            message += "<b>Не выселились:</b>\n"

        message += f"🔴 {flag.flag(checkout['booking']['country_code']) if checkout['booking']['country_code'] != '--' else ''} <b>{checkout['name']} {checkout['lastname']}</b> - {checkout['booking']['adults']} гостей - {checkout['booking']['checkin_date']} по {checkout['booking']['checkout_date']} ({checkout['booking']['number_of_nights']} ночей) - {checkout['booking']['room_number']} номер\n"

        if i == (len(checkout_arr['not_checked_out']) - 1):
            message += "\n"

    for i, checkout in enumerate(checkout_arr['not_show_up']):
        if i == 0:
            message += "<b>Не заезд:</b>\n"

        message += f"🔵 {flag.flag(checkout['booking']['country_code']) if checkout['booking']['country_code'] != '--' else ''} <b>{checkout['name']} {checkout['lastname']}</b> - {checkout['booking']['adults']} гостей - {checkout['booking']['checkin_date']} по {checkout['booking']['checkout_date']} ({checkout['booking']['number_of_nights']} ночей) - {checkout['booking']['room_number']} номер\n"

        if i == (len(checkout_arr['not_show_up']) - 1):
            message += "\n"

    for chat_id in admin_id_arr:
        context.bot.send_message(
            chat_id, text=message, parse_mode=ParseMode.HTML)


def admin_notification_morning(context: CallbackContext):

    # not_checked_in_guests = firebase.get_not_checked_in_guests()

    message = "<b>Регулярная утренняя рассылка</b>\n\n"

    keyboard = [
        [InlineKeyboardButton(
            text="➡️ Перейти к регистрации гостей", callback_data="REGISTER_GUESTS")]
    ]

    today = datetime.datetime.now(tz=pytz.timezone("Asia/Almaty")).date()
    today = datetime.datetime.combine(today, datetime.time.min)

    yesterday = today - datetime.timedelta(days=1)
    date = yesterday

    print(date)

    checkin_checkout_dict = firebase.getBookingForDay(date=date)

    if len(checkin_checkout_dict['checkin']) > 0:
        message += f"<b>Заезд на {date.strftime('%d.%m')}:</b>\n"
    else:
        message += "Нет заездов на выбранную дату\n"

    checkin_arr = {
        "checked_in": [],
        "not_checked_in": []
    }

    checkout_arr = {
        "checked_out": [],
        "not_checked_out": [],
        "not_show_up": []
    }

    for checkin in checkin_checkout_dict['checkin']:
        status = firebase.getStatusFromGuestBookingID(
            checkin['user_id'], checkin['booking']['booking_id'])
        if status['checked_in']:
            checkin['booking']['status'] = status
            checkin_arr['checked_in'].append(checkin)
        else:
            checkin_arr['not_checked_in'].append(checkin)

    if len(checkin_checkout_dict['checkin']) > 0:
        message += f"Вчера заселились {len(checkin_arr['checked_in'])} из {len(checkin_checkout_dict['checkin'])} гостей\n\n"

    for i, checkin in enumerate(checkin_arr['checked_in']):
        if i == 0:
            message += "<b>Заселились:</b>\n"

        status = checkin['booking']['status']
        roomType = ""
        for room_type in checkin['booking']['room_type']:
            roomType += f"{room_type} "
        message += f"🟢 {flag.flag(checkin['booking']['country_code']) if checkin['booking']['country_code'] != '--' else ''} <b>{checkin['name']} {checkin['lastname']}</b> - {checkin['booking']['adults']} гостей - {checkin['booking']['checkin_date']} по {checkin['booking']['checkout_date']} ({checkin['booking']['number_of_nights']} ночей) - {checkin['booking']['room_number']} номер - {roomType}\n"
        if status['checked_in']:
            message += f"""    {'🟥 Оплаты нет' if 'payment_total' not in checkin['booking'].keys()  else "🟩 Оплата имеется - оплата не требуется" if checkin['booking']['payment_total'] == 'NOT NEEDED' else f"🟩 Оплата имеется - {checkin['booking']['payment_total']} {checkin['booking']['payment_currency']} методом {checkin['booking']['payment_type']}"} \n"""
            message += f"""    {'🟥 Паспорт не внесен' if 'passport_link' not in checkin['booking'].keys()  else f"🟩 Паспорт внесен"}\n"""

        if i == len(checkin_arr['checked_in']) - 1:
            message += "\n"

    for i, checkin in enumerate(checkin_arr['not_checked_in']):
        if i == 0:
            message += "<b>Не заселились:</b>\n"

        roomType = ""
        for room_type in checkin['booking']['room_type']:
            roomType += f"{room_type} "
        message += f"🔴 {flag.flag(checkin['booking']['country_code']) if checkin['booking']['country_code'] != '--' else ''} <b>{checkin['name']} {checkin['lastname']}</b> - {checkin['booking']['adults']} гостей - {checkin['booking']['checkin_date']} по {checkin['booking']['checkout_date']} ({checkin['booking']['number_of_nights']} ночей) - {checkin['booking']['room_number']} номер - {roomType}\n"

        if i == len(checkin_arr['not_checked_in']) - 1:
            message += "\n"

    if len(checkin_checkout_dict['checkout']) > 0:
        message += f"\n<b>Выезд на {date.strftime('%d.%m')}:</b>\n"
    else:
        message += "\nНет выездов на выбранную дату\n"

    for checkout in checkin_checkout_dict['checkout']:
        status = firebase.getStatusFromGuestBookingID(
            checkout['user_id'], checkout['booking']['booking_id'])
        if checkout['booking']['checked_out']:
            checkout_arr['checked_out'].append(checkout)
        else:
            if status['checked_in']:
                checkout_arr['not_checked_out'].append(checkout)
            else:
                checkout_arr['not_show_up'].append(checkout)

    if len(checkin_checkout_dict['checkout']) > 0:
        not_show_up = f"{len(checkout_arr['not_show_up'])} {'гость' if len(checkout_arr['not_show_up']) == 1 else 'гостей'}" if len(
            checkout_arr['not_show_up']) > 0 else " "

        message += f"Вчера выселились {len(checkout_arr['checked_out'])} из {len(checkin_checkout_dict['checkout'])} гостей| {not_show_up}\n\n"

    for i, checkout in enumerate(checkout_arr['checked_out']):
        if i == 0:
            message += "<b>Выселились:</b>\n"

        message += f"🟢 {flag.flag(checkout['booking']['country_code']) if checkout['booking']['country_code'] != '--' else ''} <b>{checkout['name']} {checkout['lastname']}</b> - {checkout['booking']['adults']} гостей - {checkout['booking']['checkin_date']} по {checkout['booking']['checkout_date']} ({checkout['booking']['number_of_nights']} ночей) - {checkout['booking']['room_number']} номер\n"
        if checkout['booking']['checked_out']:
            message += f"    {'🟥 Ключ не сдан' if 'key_returned' not in checkout['booking'].keys() or not checkout['booking']['key_returned'] else '🟩 Ключ сдан'} | "
            message += f"{'🟥 Полотенце не в наличии' if 'towel_is_okay' not in checkout['booking'].keys() or not checkout['booking']['towel_is_okay'] else '🟩 Полотенце в наличии'} | "
            message += f"{'🟥 Белье не в порядке' if 'linen_is_okay' not in checkout['booking'].keys() or not checkout['booking']['linen_is_okay'] else '🟩 Белье в порядке'}\n"

            if 'checkout_additional_comments' in checkout['booking'].keys():
                message += f"    <b>Другие замечания:</b> {checkout['booking']['checkout_additional_comments']}\n"

        if i == len(checkout_arr['checked_out'])-1:
            message += "\n"

    for i, checkout in enumerate(checkout_arr['not_checked_out']):
        if i == 0:
            message += "<b>Не выселились:</b>\n"

        message += f"🔴 {flag.flag(checkout['booking']['country_code']) if checkout['booking']['country_code'] != '--' else ''} <b>{checkout['name']} {checkout['lastname']}</b> - {checkout['booking']['adults']} гостей - {checkout['booking']['checkin_date']} по {checkout['booking']['checkout_date']} ({checkout['booking']['number_of_nights']} ночей) - {checkout['booking']['room_number']} номер\n"

        if i == (len(checkout_arr['not_checked_out']) - 1):
            message += "\n"

    for i, checkout in enumerate(checkout_arr['not_show_up']):
        if i == 0:
            message += "<b>Не заезд:</b>\n"

        message += f"🔵 {flag.flag(checkout['booking']['country_code']) if checkout['booking']['country_code'] != '--' else ''} <b>{checkout['name']} {checkout['lastname']}</b> - {checkout['booking']['adults']} гостей - {checkout['booking']['checkin_date']} по {checkout['booking']['checkout_date']} ({checkout['booking']['number_of_nights']} ночей) - {checkout['booking']['room_number']} номер\n"

        if i == (len(checkout_arr['not_show_up']) - 1):
            message += "\n"

    for chat_id in admin_id_arr:
        context.bot.send_message(
            chat_id, text=message, parse_mode=ParseMode.HTML)

def set_nightly_no_ota(update: Update, context: CallbackContext):
    
    query = update.callback_query
    
    jobs = context.job_queue.get_jobs_by_name("nightly_no_ota")

    print(jobs)
    if len(jobs) != 0:
        text = "Already set and deleted"
        for job in jobs:
            job.schedule_removal()
        print(text)    
        
    query.answer("Включаю автоматическое отключение номеров")
    time = datetime.time(hour=22, minute=0, tzinfo=pytz.timezone('Asia/Almaty'))
    context.job_queue.run_daily(enable_nightly_no_ota, time, days=(
        0, 1, 2, 3, 4, 5, 6), context = None, name = "nightly_no_ota")
    
    
def enable_nightly_no_ota(context: CallbackContext):
    
    today = datetime.datetime.now(tz=pytz.timezone("Asia/Almaty")).date()
    today = datetime.datetime.combine(today, datetime.time.min)
    
    tomorrow = today + datetime.timedelta(days=1)
    date = tomorrow
    
    # date = today
    
    res = wubook.make_no_ota_for_day(date, True)
    
    if res == True: logging.info("Включение No ota успешно")
    else: logging.warning("Включение No ota с ошибками")
    
    run_after_in_hours = datetime.timedelta(hours=8)
    
    context.job_queue.run_once(disable_nightly_no_ota, run_after_in_hours, date)
    
def disable_nightly_no_ota(context: CallbackContext):

    date = context.job.context
    
    res = wubook.make_no_ota_for_day(date, False)
    
    if res == True: logging.info("Отключение No ota успешно")
    else: logging.warning("Отключение No ota с ошибками")
    
    
#Автоматическая конвертация цен
def set_daily_convert(update: Update, context: CallbackContext):
    
    query = update.callback_query
    
    jobs = context.job_queue.get_jobs_by_name("daily_price_convert")

    print(jobs)
    if len(jobs) != 0:
        text = "Already set and deleted"
        for job in jobs:
            job.schedule_removal()
        print(text)
    
    query.answer("Включаю автоматическую конвертацию цен")
    time = datetime.time(hour=0, minute=1, tzinfo=pytz.timezone('Asia/Almaty'))
    context.job_queue.run_daily(enable_auto_convert, time, days=(
        0, 1, 2, 3, 4, 5, 6), context = None, name = "daily_price_convert")

def enable_auto_convert(context: CallbackContext):
    today = datetime.datetime.now(tz=pytz.timezone("Asia/Almaty"))
    yesterday = today - datetime.timedelta(days=1)
    yesterday = yesterday.strftime("%Y-%m-%d")
    
    firebase.auto_convert_currency_for_guests()
    
    firebase.auto_convert_currency_for_guests(yesterday)
    
#Отдельное меню для отложенных функций

def notifications_menu(update: Update, context: CallbackContext):
    
    query = update.callback_query
    query.answer()
    
    keyboard = [
        [InlineKeyboardButton(text="Поставить вечернее уведомление",
                              callback_data="ADMIN_DAILY_EVENING_NOTIFY"),],
        [InlineKeyboardButton(text="Поставить утреннее уведомление",
                              callback_data="ADMIN_DAILY_MORNING_NOTIFY"),],
        [InlineKeyboardButton(text="Включить отключение номеров ночью",
                              callback_data="ADMIN_NIGHTLY_NO_OTA"),],
        [InlineKeyboardButton(text="Включить конвертацию цен гостей",
                              callback_data="ADMIN_DAILY_CONVERT_PRICES"),],
        [back_btn]
    ]
    
    query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))
    
    return "ADMIN_NOTIFICATION_LEVEL1"
