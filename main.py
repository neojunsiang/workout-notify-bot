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

# API keys
load_dotenv()
env_path = Path('.env')
load_dotenv(dotenv_path=env_path)
TELEGRAM_API_TOKEN = os.getenv("SECRET_TELEGRAM_API_TOKEN")
bot = Bot(TELEGRAM_API_TOKEN)
CHAT_ID = os.getenv("SECRET_CHAT_ID")

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
    welcome_message = "Welcome! Here are the available commands: \n \u2022 /help \n \u2022 /view \n \u2022 /test"
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

    # dp.add_handler(conv_handler)

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