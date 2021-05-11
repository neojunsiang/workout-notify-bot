from telegram import *
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
)
from airtable import Airtable
from dotenv import load_dotenv
from pathlib import Path
import os
import datetime
import json
import requests
import re
import logging
from functools import wraps

# API keys
load_dotenv()
env_path = Path('.env')
load_dotenv(dotenv_path=env_path)
TELEGRAM_API_TOKEN = os.getenv("SECRET_TELEGRAM_API_TOKEN")
bot = Bot(TELEGRAM_API_TOKEN)
CHAT_ID = os.getenv("SECRET_CHAT_ID")
LIST_OF_ADMINS = [132502315]

AIRTABLE_BASE_KEY = os.getenv("SECRET_AIRTABLE_BASE_KEY")
AIRTABLE_TABLE_NAME = os.getenv("SECRET_AIRTABLE_TABLE_NAME")
AIRTABLE_API_KEY = os.getenv("SECRET_AIRTABLE_API_KEY")

# logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)

logger = logging.getLogger()
logger.setLevel(logging.INFO)
# logger.setLevel(logging.DEBUG)

# airtable
airtable = Airtable(AIRTABLE_BASE_KEY, AIRTABLE_TABLE_NAME, AIRTABLE_API_KEY)


# /start function
def test(update, context):
    # print(bot.get_me())
    test_message = "Testing Testing 1, 2, 3..."
    bot.send_message(chat_id=update.effective_chat.id, text=test_message)


# /help function
def start(update, context):
    welcome_message = "Welcome! Here are the available commands: \n \u2022 /help \n \u2022 /view \n \u2022 /test \n \u2022 /conversion"
    bot.send_message(chat_id=update.effective_chat.id, text=welcome_message)


# airtable function to return the database_id
def wod_id(airtable, search_date):
    for page in airtable.get_iter():
        # print("page", page)
        for record in page:
            # print("record from wod_result", record)
            # print("date from wod_result", record['fields']['date'])
            result = record['fields']['date']
            if str(search_date) in result:
                # print("result1", record['id'])
                # print("result2", record['fields']['wod'])
                # wod_result = record['fields']['wod']
                # return wod_result
                wod_record_id = record['id']
                return wod_record_id


# airtable function to return the result based on database_id
def wod_result(database_id):
    if (bool(database_id)):
        record = airtable.get(database_id)
        result = record['fields']['wod']
        return result
    else:
        error_message = "No WOD. How about some rest instead?"
        return error_message


# regex check for parameters whether date are formatted as yyyy-mm-dd
def date_format_check(date):
    result = bool(
        re.search("^\d{4}\-(0?[1-9]|1[012])\-(0?[1-9]|[12][0-9]|3[01])$",
                  date))
    return result


# date converter for /view function from dd-mm-yyyy to yyyy-mm-dd
def date_converter(date):
    date_result = datetime.datetime.strptime(date,
                                             "%d-%m-%Y").strftime("%Y-%m-%d")
    return date_result


# /view function
def view(update, context):
    # extract parameters from /view function
    context_result = context.args
    print("context result", context_result)  # print the parameter in list
    print("user_message", update.message)  # obtain the chat and user info
    print("user_context", context)  # obtain the chat and user info

    if len(context_result) > 1:  # check the length of the context paramaters
        main_result = "Please key in a date!"
    elif bool(re.search(
            "[ a-zA-Z ]",
            context_result[0])):  # check whether parameter are in alphabert
        main_result = "please key in a date in this format, DD-MM-YYYY"
    else:
        search_query = context_result[0]
        print("search query from view", search_query)
        # # check the date formatting parameters
        if date_format_check(search_query):  # if date is YYYY-MM-DD
            main_result_id = wod_id(airtable, search_date=search_query)
            main_result = wod_result(main_result_id)
        else:  # if date is DD-MM-YYYY
            formatted_date = date_converter(search_query)
            main_result_id = wod_id(airtable, search_date=formatted_date)
            main_result = wod_result(main_result_id)
    # bot.send_message(chat_id=update.effective_chat.id, text=main_result)
    update.message.reply_text(main_result)


# regex check for kg
def weight_regex_check_for_kg(input):
    result = bool(re.search('^\d+(?:[.,][0|5])?\s*(kg|KG)$', input))
    return result


# regex check for lbs
def weight_regex_check_for_lbs(input):
    result = bool(re.search('^\d+(?:[.,][0|5])?\s*(lbs|LBS)$', input))
    return result


# conversion to nearest 0.5/ 0.0
def round_to_nearest_point_five(value):
    result = round(value * 2.0) / 2.0
    return result


# conversion process to relevant unit measurement
def conversion_process(input):
    KILO_TO_POUND_CONVERSION = 2.20462
    if weight_regex_check_for_kg(input):
        integer_input = float(input.lower().strip("kg"))
        # print("conversion", integer_input)
        converted_pound = round(integer_input * KILO_TO_POUND_CONVERSION, 1)
        final_converted_pound = round_to_nearest_point_five(converted_pound)
        # print("final converted pound", final_converted_pound)
        result = f"Weight will be {final_converted_pound} lbs"
        return result
    elif weight_regex_check_for_lbs(input):
        integer_input = float(input.lower().strip("lbs"))
        converted_kilogram = round(integer_input / KILO_TO_POUND_CONVERSION, 1)
        final_converted_kilogram = round_to_nearest_point_five(
            converted_kilogram)
        # print("final converted kilogram", final_converted_kilogram)
        result = f"Weight will be {final_converted_kilogram} kg"
        return result
    else:
        error_message = "Only one input and check you unit, only kg or lbs!"
        return error_message


# /conversion function
def conversion(update, context) -> int:
    print("userdata", update.message.from_user)
    context_result_for_conversion = context.args
    # print("context_result", context_result_for_conversion)
    # print("context_result_len", len(context_result_for_conversion))
    if len(context_result_for_conversion) == 0:
        result = "Please key in your weight"
    else:
        print("conversion", context_result_for_conversion)
        user = update.message.from_user
        # print("user", user)
        input_weight = (update.message.text).lstrip("/conversion ")
        # print("text1", input_weight)
        result = conversion_process(input_weight)
        # print("result", result)
        # pass
    return update.message.reply_text(result)


# Admin Access
def restricted(func):
    @wraps(func)
    def wrapped(update, context, *args, **kwargs):
        user_id = update.effective_user.id
        user_name = update.effective_user.username
        print("username", user_name)
        if user_id not in LIST_OF_ADMINS:
            print(
                "Unauthorized access denied for id: {}, username: {}.".format(
                    user_id, user_name))
            error_message = "Only the admins have access"
            update.message.reply_text(text=error_message)
            return
        return func(update, context, *args, **kwargs)

    return wrapped


# CONVERSARTION BOT ON Create, Edit & Delete, Only for ADMINS.
CHOOSING, NEW_DATE_SELECTION, NEW_WORKOUT_SELECTION, DELETE_SELECTION, EDIT_SELECTION = range(
    5)


# /create function
@restricted
def create(update, context):
    reply_keyboard = [['New'], ['Edit'], ['Delete']]
    message = "Please select your action, or send /cancel if you wish to stop"
    # bot.send_message(chat_id=update.effective_chat.id, text=test_message)
    update.message.reply_text(message,
                              reply_markup=ReplyKeyboardMarkup(
                                  reply_keyboard, one_time_keyboard=True))
    return CHOOSING


# new workout
@restricted
def new(update: Update, context: CallbackContext):
    choice = update.message.text
    print("choice", choice)
    update.message.reply_text(
        "{} workout ? Please input the date you wish to add".format(choice))
    return NEW_DATE_SELECTION


# convert keyed date into the required date for insertion in airtable
def date_conversion_for_insert(date):
    result = datetime.datetime.strptime(date, "%d-%m-%Y").strftime("%m-%d-%Y")
    return result


# airtable insertion
def airtable_insertion(input_date, input_workout):
    converted_date = str(date_conversion_for_insert(input_date))
    record = {"date": converted_date, "wod": input_workout}
    print("record", record)
    airtable.insert(record)
    return


# ask for the date to be added into db
@restricted
def insert_new_date(update: Update, context: CallbackContext):
    user_data = context.user_data
    print("user_data", user_data)
    text = update.message.text
    print("text", text)
    user_data['date'] = text
    print('after', user_data)
    update.message.reply_text("Please add the workout")
    return NEW_WORKOUT_SELECTION


# ask for the workout to be added into db
@restricted
def insert_new_workout(update: Update, context: CallbackContext):
    user_data = context.user_data
    print("new_workout", user_data)
    new_workout = update.message.text
    print("new workout", new_workout)
    user_data['wod'] = new_workout
    print("after wod user", user_data)
    try:
        airtable_insertion(user_data['date'], user_data['wod'])
        update.message.reply_text("Added to DB")
    except:
        update.message.reply_text(
            "Error with date or data, please check again")
    del user_data
    return ConversationHandler.END


@restricted
def edit(update: Update, context: CallbackContext):
    update.message.reply_text("Please input the date you wish to edit")
    # return EDIT_SELECTION


@restricted
def delete(update: Update, context: CallbackContext):
    update.message.reply_text("Please input the date you wish to delete")
    # return DELETE_SELECTION


@restricted
def cancel(update: Update, context: CallbackContext):
    user_data = context.user_data
    print("userdata", user_data)
    if 'choice' in user_data:
        del user_data['choice']
    update.message.reply_text("Goodbye")
    return ConversationHandler.END


conv_handler = ConversationHandler(
    entry_points=[CommandHandler('create', create)],
    states={
        CHOOSING: [
            MessageHandler(Filters.regex('^New$'), new),
            MessageHandler(Filters.regex('^Edit$'), edit),
            MessageHandler(Filters.regex('^Delete$'), delete)
        ],
        NEW_DATE_SELECTION:
        [MessageHandler(Filters.text & (~Filters.command), insert_new_date)],
        NEW_WORKOUT_SELECTION: [
            MessageHandler(Filters.text & (~Filters.command),
                           insert_new_workout),
        ]
    },
    fallbacks=[CommandHandler('cancel', cancel)])


# main function
def main():
    updater = Updater(TELEGRAM_API_TOKEN, use_context=True)

    dp = updater.dispatcher

    # command handler for /test
    dp.add_handler(CommandHandler("test", test))

    # command handler for /start
    dp.add_handler(CommandHandler("start", start))

    # command handler for view
    dp.add_handler(CommandHandler("view", view))

    # command handler for conversation
    dp.add_handler(CommandHandler("conversion", conversion))

    # command handler for create workout
    # dp.add_handler(CommandHandler("create", create))

    dp.add_handler(conv_handler)

    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()
"""
test - for testing purpose
start - to check for available commands
view - to view workouts, date, should be formatted as dd-mm-yyyy
conversion - unsure of the pounds-to-kg conversion? Formatted as xxx lbs / xxx kg
"""