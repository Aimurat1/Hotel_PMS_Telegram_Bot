from telegram.ext import CallbackContext

def set_delete_message(context: CallbackContext, name, time, chat_id, message_id):
    jobs = context.job_queue.get_jobs_by_name(name)
        
    if len(jobs) != 0:
        text = "Already set and deleted"
        for job in jobs:
            job.schedule_removal()
        print(text)
    
    context.job_queue.run_once(delete_message, time, context={'chat_id': chat_id, 'message_id': message_id}, name = name)
    print("Set notification")

def delete_message(context: CallbackContext):
    message_dict = context.job.context
    
    context.bot.delete_message(chat_id = message_dict['chat_id'], message_id = message_dict['message_id'])
    