from telegram import ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup, Update, ForceReply, KeyboardButton, ReplyKeyboardMarkup,InputMediaPhoto, ParseMode
from telegram.ext import Defaults, InvalidCallbackData, PicklePersistence, CallbackQueryHandler, Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler
import time

from ver2_api import booking

def admin_help_entry(update, context):
    return "ADMIN_HELP_CONV"

def admin_help_send_admin_number(update: Update, context: CallbackContext, *args, **kwargs):
    
    try:
        query = update.callback_query
        # print(query)
        message_type = "query"
    except:
        message_type = "send"
    
    if message_type == "query":
        chat_id = update.callback_query.message.chat_id
        query.message.delete()
        
    elif message_type == "send":
        chat_id = update.message.chat_id
    
    message_text = "Вот номер администратора 😉"
    
    context.user_data['admin_help_messages'] = []
    mes = context.bot.send_message(chat_id, text = message_text)
    context.user_data['admin_help_messages'].append(mes)
    
    time.sleep(2)
    
    keyboard = [
        [InlineKeyboardButton(text = "Да", callback_data="PROBLEM_SOLVED")],
        [InlineKeyboardButton(text = "Нет", callback_data="PROBLEM_NOT_SOLVED")],
    ]
    
    message_text = "Подскажите, ваша проблема была решена?"
    
    mes = context.bot.send_sticker(chat_id, sticker = "CAACAgIAAxkBAAEJJzRkddbTrIVo_qAzzddwW_YDJ41N6wAC_igAAtayOUnlq6M2ad-OMS8E")
    context.user_data['admin_help_messages'].append(mes)
    
    mes = context.bot.send_message(chat_id, text = message_text,reply_markup = InlineKeyboardMarkup(keyboard))
    context.user_data['admin_help_messages'].append(mes)
    
    return "LEVEL1_ADMIN_HELP"

def admin_help_problem_solved(update: Update, context: CallbackContext):
    
    query = update.callback_query
    
    admin_help_dict = context.user_data['admin_help_finishing'] 
    
    keyboard = [
        [InlineKeyboardButton(text = f"{admin_help_dict['button_text']}", callback_data=f"{admin_help_dict['return_state']}")]
        # [InlineKeyboardButton(text = "🔙 Назад", callback_data="BACK_ADMIN_HELP")]
    ]
    
    context.bot.send_message(query.message.chat_id, "Супер, рада за вас!", reply_markup = InlineKeyboardMarkup(keyboard))
    mes = context.bot.send_sticker(query.message.chat_id, sticker = "CAACAgIAAxkBAAEJJ71kdiHEWt2EW9iPQLpIZjQq-X6NAANTKQACUd04SdD5RGFqIKJ5LwQ")
    
    time.sleep(2)
    context.user_data['admin_help_messages'].append(mes)
    for message in context.user_data['admin_help_messages']:
        message.delete()
    
    context.user_data['admin_help_messages'] = []    

    return admin_help_dict['return_state']
    
    


def admin_help_problem_not_solved(update: Update, context: CallbackContext):
    
    query = update.callback_query
    
    admin_help_dict = context.user_data['admin_help_finishing'] 
        
    # mes = context.bot.send_sticker(query.message.chat_id, sticker = "CAACAgIAAxkBAAEJJ71kdiHEWt2EW9iPQLpIZjQq-X6NAANTKQACUd04SdD5RGFqIKJ5LwQ")
    # context.user_data['admin_help_messages'].append(mes)
    keyboard = [
        [InlineKeyboardButton(text = f"{admin_help_dict['button_text']}", callback_data=f"{admin_help_dict['return_state']}")]
        # [InlineKeyboardButton(text = "🔙 Назад", callback_data="BACK_ADMIN_HELP")]
    ]
        
    context.bot.send_message(query.message.chat_id, "Даю вам номер директора 😊", reply_markup = InlineKeyboardMarkup(keyboard))
    
    for message in context.user_data['admin_help_messages']:
        message.delete()
        
    context.user_data['admin_help_messages'] = []
    
    return admin_help_dict['return_state']
 
def admin_help_end(update: Update, context: CallbackContext):
    
    for message in context.user_data['admin_help_messages']:
        message.delete()
        
    return booking(update, context)
    
    
admin_help_conversation = ConversationHandler(
    entry_points= [CallbackQueryHandler(admin_help_send_admin_number, pattern="^"+ "ADMIN_HELP"),],
    states={
        "LEVEL1_ADMIN_HELP": [
            CallbackQueryHandler(admin_help_problem_solved, pattern="^"+ "PROBLEM_SOLVED"),
            CallbackQueryHandler(admin_help_problem_not_solved, pattern="^"+ "PROBLEM_NOT_SOLVED"),
        ],
        
        
    },
    fallbacks=[
            # CommandHandler("start", start)
        CallbackQueryHandler(admin_help_end, pattern='^' + "BACK_ADMIN_HELP"),
            
    ],
    map_to_parent={
        "BACK_TO_ASSIGN_ROOM": "BACK_TO_ASSIGN_ROOM"
    },
    allow_reentry = True,
)
