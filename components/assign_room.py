from telegram import ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup, Update, ForceReply, KeyboardButton, ReplyKeyboardMarkup,InputMediaPhoto, ParseMode, ChatAction
from telegram.ext import Defaults, InvalidCallbackData, PicklePersistence, CallbackQueryHandler, Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler
import time
import firebase_with_api as firebase

from constants.admin_id import admin_id_arr

from utils.currency_converter import convert_currency, convert_to_usd

import components.admin_help as admin_help
from utils.delete_message import set_delete_message
import copy, datetime, os, pytz

import ver2_api

LEVEL1, LEVEL2, LEVEL3, LEVEL3_ABOUT_HOTEL, LEVEL3_EVENTS, LEVEL4_ABOUT_HOTEL, LEVEL5_ABOUT_HOTEL, LEVEL3_BOOKING, LEVEL34_BOOKING, LEVEL4_BOOKING, LEVEL5_BOOKING, LEVEL6_BOOKING, LEVEL1_VERIFY, LEVEL2_VERIFY, LEVEL3_VERIFY,LEVEL7_CHECKIN, LEVEL7_CHECKOUT, LEVEL7_BOOKING, LEVEL1_CHECKOUT, LEVEL1_PAYMENT, LEVEL2_PAYMENT, LEVEL1_NEW_BOOKING, LEVEL2_NEW_BOOKING, LEVEL3_NEW_BOOKING, LEVEL4_NEW_BOOKING, LEVEL34_SELECT_BOOKING= range(26)


passcodes_for_rooms = {
    "1": "xxxx",
    "2": "xxxx",
    "3": "xxxx",
    "4": "xxxx",
    "5.1": "xxxx",
    "5.2": "xxxx",
    "5.3": "xxxx",
    "5.4": "xxxx",
    "5.5": "xxxx",
    "5.6": "xxxx",
    "6": "xxxx"
}

assign_room_final_keyboard = [
    [InlineKeyboardButton(text = "🧭 Экскурсия по гостинице", callback_data="EXCURSION")],
    [InlineKeyboardButton(text = "🔜 Далее", callback_data="NEXT")],
]

def assign_room_starting_func(update: Update, context: CallbackContext):
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
  
        
    message_text = "Подбираю специально для вас комнату 😉 Напоминаю, что регистрация возможна только в день заезда."
    
    text_message = context.bot.send_message(chat_id, text = message_text)
    # context.user_data['guest_payment_messages'].append(mes)
    context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
    
    time.sleep(4)
    
    
    booking = context.user_data['booking']
    
    print(booking["checkin_date"].date())
    
    # if(booking["checkin_date"].date() != datetime.datetime.now(tz=pytz.timezone("Asia/Almaty")).date()):
    if(booking["checkin_date"].date() != booking["checkin_date"].date()):
        text_message.edit_text(f"""
Ваша дата заезда {booking["checkin_date"].strftime("%d/%m/%Y")}, а сегодня {datetime.datetime.today().strftime("%d/%m/%Y")}. Я смогу вас зарегистрировать в день заезда...
                               """)
        
        message_to_delete = []
        
        message_to_delete.append(context.bot.send_sticker(chat_id, sticker = "CAACAgIAAxkBAAEJKDdkdkTzNXjhISPiK62ZpLl7ZVPFqAACUysAAsojOUkhSBZ08KHEQC8E"))
        
        time.sleep(3)
        message_to_delete.append(context.bot.send_message(chat_id, text = "Я напомню вам о регистрации в день заезда в гостиницу!"))
        
        message_to_delete.append(context.bot.send_sticker(chat_id, sticker = "CAACAgIAAxkBAAEJN8Jkfe1_87MRYdrGXA_7jPjcAAE3SJMAAoYoAAKsYzlJuHfgOZWvgLsvBA"))
        
        # time.sleep(6)
        
        # for mes in message_to_delete:
        #     mes.delete()
    else:
        text_message.edit_text(f"""
Еще чуть-чуть – и готово! Чтобы дать вам номер комнаты и ключ, мне нужно фото вашего паспорта или водительских прав. 

Фотография документа нужна для того, чтобы уже в гостинице убедиться, что приехали именно вы. 

Отправьте фотографию своего паспорта или прав, но, только проследите, чтобы фотография была без бликов. Нам нужна страничка с вашим лицом. Для отправки фото используйте значок скрепки 📎

Спасибо за понимание! 😊
                               """)
        
        mes = context.bot.send_sticker(chat_id, "CAACAgIAAxkBAAEJOIJkfiCkcBYxqDnfuMCsKUpdT3mNzgACUisAAihfOUnq-G42Ry4tIS8E")
    
        set_delete_message(context, "delete_sticker", 20, mes.chat_id, mes.message_id)
        
        return "LEVEL1_ASSIGN_ROOM"
    
def assign_room_get_passport(update: Update, context: CallbackContext):
    
    chat_id = update.message.chat_id
    
    booking = context.user_data['booking']
    
    filename = f"passport_{booking['user_id']}_{booking['id']}.jpg"
    
    newFile = update.message.effective_attachment[-1].get_file()
    
    directory = "media/passports"
    
    os.makedirs(directory, exist_ok=True)
    
    newFile.download(custom_path = f"./media/passports/{filename}")

    public_url = firebase.upload_photo_to_cloud_storage(f"{filename}")
    
    firebase.put_link_passport_to_booking(booking['user_id'], booking['id'], f"{public_url}")

    #Присвоение комнаты
    
    # assigned_room_number = firebase.assignGuestToRoomTest(booking, booking['room_type_id'][0])
        
    assigned_room_number = "4"
    
    # context.user_data["booking"]['checkin_date'] = datetime.datetime.strptime(booking['checkin_date'], "%Y-%m-%d")
    # context.user_data["booking"]['checkout_date'] = datetime.datetime.strptime(booking['checkout_date'], "%Y-%m-%d")

    user_id, booking_id = context.user_data['booking']['user_id'], context.user_data['booking']['id']
    booking = firebase.getBookingById(user_id, booking_id)['booking']
    booking['checkin_date'] = datetime.datetime.strptime(booking['checkin_date'], "%d-%m-%Y")
    booking['checkout_date'] = datetime.datetime.strptime(booking['checkout_date'], "%d-%m-%Y")

    context.user_data["booking"] = booking
    
    
    if(assigned_room_number is None):
        message = "Почему то все комнаты заняты, сообщите администратору"
        context.bot.send_message(update.message.chat_id, text = message)
        
        # return "LEVEL4_BOOKING_CHECKIN"
    else:
        
        firebase.approveStatusFromGuestBookingID(user_id, booking_id, "checked_in", True)
        
        # starting_hour, starting_minute = 14, 0
        starting_hour, starting_minute = 0, 20
        
        if datetime.time(starting_hour, starting_minute) < datetime.datetime.now(tz=pytz.timezone("Asia/Almaty")).time():
            # Можно отправлять инструкцию
            
            context.bot.send_message(chat_id, text = f"""
Спасибо, я получила фото. Вы отлично справляетесь! 😊 Ваша комната {assigned_room_number}. Высылаю инструкцию для входа в комнату...
                        """)
            
            context.bot.send_sticker(chat_id, "CAACAgIAAxkBAAEJOIZkfigwcS4EsJCc_wO5953_H3wE0AACVCYAAnVOOUn9roMfpcFDhS8E")
            
            time.sleep(2)
            
            context.bot.send_message(chat_id, text = f"""
Ваша комната {assigned_room_number} 🚪 Ключ от двери лежит в мини-сейфе рядом с дверью. Наберите на сейфе цифры {passcodes_for_rooms[assigned_room_number]}, возьмите ключ и откройте дверь комнаты
                                     """)
            
            job_dict = {
                'chat_id': chat_id,
                'user_id': user_id,
                'booking_id': booking_id,
                'time': 5,
                'type': "after_five_minutes",
                'need_help': "FIRST"
            }
            
            assign_room_notification(context, job_dict, assign_room_message_after_five_minutes)
            
            return "LEVEL2_ASSIGN_ROOM"

            
        else:
            context.bot.send_message(chat_id, text = f"""
Спасибо, я получила фото. Вы отлично справляетесь! 😊 Итак, ваша комната {assigned_room_number}, она будет готова в 14:00. Я сообщу, когда комната будет в вашем распоряжении. А пока располагайтесь, не стесняйтесь!  В общей зоне есть мягкий комфортный диван. Может быть чай/кофе? Рядом вы увидите чайник и коферварку. Можете насладиться ароматным напитком и перекусить 😉 
                                     """)
            
            context.bot.send_sticker(chat_id, "CAACAgIAAxkBAAEJOIZkfigwcS4EsJCc_wO5953_H3wE0AACVCYAAnVOOUn9roMfpcFDhS8E")
            
                 
        # print(datetime.time(0, 20) < datetime.datetime.now(tz=pytz.timezone("Asia/Almaty")).time())
        
def assign_room_need_help_or_not(update: Update, context: CallbackContext):
    
    query = update.callback_query
    query.answer()
    
    print(query.data)
    
    callback = query.data.split(" | ")
    
    if callback[0] == "NEED_HELP":
        #Need help
        
        # context.user_data['assign_room_help_needed'] = callback[1]
        
        if callback[1] == "FIRST":
        
            query.edit_message_text("Давайте попробуем еще раз")
            chat_id = query.message.chat_id
            
            time.sleep(1)
            
            print(context.user_data['booking']['room_number'])
            
            context.bot.send_message(chat_id, text = f"""
    Ключ от двери лежит в мини-сейфе рядом с дверью. Наберите на сейфе цифры {passcodes_for_rooms[context.user_data['booking']['room_number'][0]]}, возьмите ключ и откройте дверь комнаты
                                    """)
            
            mes = context.bot.send_sticker(chat_id, "CAACAgIAAxkBAAEJOZtkfuEZ2RVyP2YpzAHiimr5ns-3sQACVCYAAnVOOUn9roMfpcFDhS8E")
            
            set_delete_message(context, "delete_sticker_1", 20, mes.chat_id, mes.message_id)
            
            user_id, booking_id = context.user_data['booking']['user_id'], context.user_data['booking']['id']
            
            
            job_dict = {
                    'chat_id': chat_id,
                    'user_id': user_id,
                    'booking_id': booking_id,
                    'time': 5,
                    'type': "after_five_minutes",
                    'need_help': "SECOND"
                    
            }
            
            assign_room_notification(context, job_dict, assign_room_message_after_five_minutes)
            return "LEVEL2_ASSIGN_ROOM"

        else:
            
            keyboard = [
                [InlineKeyboardButton(text = "Позвать администратора", callback_data="ADMIN_HELP")]
            ]
            query.edit_message_text("Мне очень жаль, хотите позвать администратора на помощь?", reply_markup=InlineKeyboardMarkup(keyboard))
            
            context.user_data['admin_help_finishing'] = {
                "button_text": "🔜 Далее",
                "return_state": "BACK_TO_ASSIGN_ROOM"
            }
            
            return "ADMIN_HELP"

    elif callback[0] == "NOT_NEED_HELP":
        #Help not needed
        query.edit_message_text(text = "Отлично, я довольна! 🥳 Располагайтесь поудобнее", reply_markup=InlineKeyboardMarkup(assign_room_final_keyboard))
        
        return "LEVEL3_ASSIGN_ROOM"
    
    
        
def assign_room_notification(context: CallbackContext, job_dict: dict, callback_function):
    
    chat_id = job_dict['chat_id']
    user_id = job_dict['user_id']
    booking_id = job_dict['booking_id']
    time = job_dict['time']
    type = job_dict['type']
    
    name = f"{type}_{user_id}_{booking_id}"
    
    jobs = context.job_queue.get_jobs_by_name(name)
        
    # print(jobs)
    if len(jobs) != 0:
        text = f"Already set and deleted - {name}"
        for job in jobs:
            job.schedule_removal()
        print(text)
    
    context.job_queue.run_once(callback_function, time, job_dict, name)
    print(f"Set notification - {name}")
    
    
    
    
def assign_room_message_after_five_minutes(context: CallbackContext):
    job_dict = context.job.context
    
    print(job_dict['need_help'])
    
    keyboard = [
        [InlineKeyboardButton(text = "У меня все получилось! 👍", callback_data="NOT_NEED_HELP")],
        [InlineKeyboardButton(text = "У меня не получается! 😥", callback_data=f"NEED_HELP | {job_dict['need_help']}")],
    ]
    
    context.bot.send_message(job_dict['chat_id'], text = """
Хочу убедиться, что вы вошли в комнату. Все получилось? 😊
                             """, reply_markup = InlineKeyboardMarkup(keyboard))
    
    return "LEVEL2_ASSIGN_ROOM"
    
        
def assign_room_admin_help_returned(update: Update, context: CallbackContext):
    
    query = update.callback_query
    query.answer()  
    
    query.edit_message_text(text = "Отлично, я довольна! Располагайтесь поудобнее. Провести вам мини-экскурсию по гостинице?", reply_markup=InlineKeyboardMarkup(assign_room_final_keyboard))
    
    return "LEVEL3_ASSIGN_ROOM"

def assign_room_admin_final(update: Update, context: CallbackContext):
    
    query = update.callback_query
    
    assign_room_final_dict = context.user_data['assign_room_final']
    
    if query.data == "EXCURSION":
        print("excursion")
    else:
        eval(assign_room_final_dict['next_func'])
        return assign_room_final_dict['next_state']

assign_room_conversation = ConversationHandler(
    entry_points= [
        CallbackQueryHandler(assign_room_starting_func, pattern="^"+ "ASSIGN_ROOM"),
        CallbackQueryHandler(assign_room_admin_help_returned, pattern="^"+ "BACK_TO_ASSIGN_ROOM"),
    ],
    states={
        "LEVEL1_ASSIGN_ROOM": [
            MessageHandler(Filters.photo, assign_room_get_passport),
            
            # CallbackQueryHandler(guest_payment_get_payment_status, pattern=check_guest_payment_callback),
        ],
        "LEVEL2_ASSIGN_ROOM": [
            CallbackQueryHandler(assign_room_need_help_or_not, pattern="^"+ "NOT_NEED_HELP"),
            CallbackQueryHandler(assign_room_need_help_or_not, pattern="^"+ "NEED_HELP"),
            # admin_help.admin_help_conversation,
        ],
        "LEVEL3_ASSIGN_ROOM": [
            CallbackQueryHandler(assign_room_admin_final, pattern="^"+ "EXCURSION"),
            CallbackQueryHandler(assign_room_admin_final, pattern="^"+ "NEXT"),
            # admin_help.admin_help_conversation,
        ],
        # "LEVEL2_GUEST_PAYMENT": [
        #     CallbackQueryHandler(next, pattern="^"+ "CONTINUE$"),
        #     CallbackQueryHandler(guest_payment_no_cash_payment_select_payment_type, pattern=dict),
        # ],
        # "LEVEL3_GUEST_PAYMENT": [
        #     MessageHandler(Filters.photo, guest_payment_no_cash_payment_get_screenshot),
            
        # ],
        
        
    },
    fallbacks=[
            # CommandHandler("start", start)
        # CallbackQueryHandler(guest_payment_cash_payment, pattern='^' + "BACK_ADMIN_HELP"),
            
    ],
    map_to_parent={
        # "NEXT": LEVEL3_BOOKING
        "ADMIN_HELP": "LEVEL_ADMIN_HELP",
        "NEXT_BOOKING": LEVEL3_BOOKING,
        "NEXT_CHECKIN": "LEVEL5_CHECKIN",
        "NEXT_CHECKIN_FINAL": "LEVEL7_CHECKIN"
    },
    allow_reentry = True,
    persistent=True,
    name = "assign_room_conversation"
)