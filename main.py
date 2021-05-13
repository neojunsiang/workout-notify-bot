from telegram import *
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
                          ConversationHandler, CallbackContext,
                          CallbackQueryHandler)
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
LIST_OF_ADMINS = [
    os.getenv("ADMIN_1"),
    os.getenv("ADMIN_2"),
]

# Airtable API keys
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
    test_message = "I am a bot and I am as strong as an 🦍"
    bot.send_message(chat_id=update.effective_chat.id, text=test_message)


# /help function
def start(update, context):
    welcome_message = "Welcome! Here are the available commands: \n \u2022 /start \n \u2022 /view \n \u2022 /test \n \u2022 /convert"
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


# regex check for parameters, whether date are formatted as yyyy-mm-dd to access airtable database
def date_format_check(date):
    result = bool(
        re.search("^\d{4}\-(0?[1-9]|1[012])\-(0?[1-9]|[12][0-9]|3[01])$",
                  date))
    return result


# regex check for parameter, whether the date is formatted in DD-MM-YYYY
def date_format_check_for_DD_MM_YYYY(date):
    result = bool(
        re.search("^(0?[1-9]|[12][0-9]|3[01])-(0?[1-9]|1[012])-\d\d\d\d$",
                  date))
    return result


# regex check for parameters, to ensure that no alphabets is entered as date
def regex_check_for_alphabert_input(input):
    result = bool(re.search("[ a-zA-Z ]", input))
    return result


# date converter for /view function from dd-mm-yyyy to yyyy-mm-dd for database access
def date_converter_for_database(date):
    date_result = datetime.datetime.strptime(date,
                                             "%d-%m-%Y").strftime("%Y-%m-%d")
    return date_result


# /view function
def view(update, context):
    # extract parameters from /view function
    context_result = context.args
    # print("context result", context_result)  # print the parameter in list
    # print("user_message", update.message)  # obtain the chat and user info
    # print("user_context", context)  # obtain the chat and user info
    if len(context_result) > 1:  # check the length of the context paramaters
        main_result = "One date only!"
    elif context_result == []:
        main_result = "Please include in a date in this format, <b><u>DD-MM-YYYY</u></b>"
    elif regex_check_for_alphabert_input(
            context_result[0]) == True or date_format_check_for_DD_MM_YYYY(
                context_result[0]) == False:
        main_result = "Please include in a date in this format, <b><u>DD-MM-YYYY</u></b>"
    else:
        search_query = context_result[0]
        print("search query from view", search_query)
        # # check the date formatting parameters
        if date_format_check(search_query):  # if date is YYYY-MM-DD
            main_result_id = wod_id(airtable, search_date=search_query)
            main_result = f"💦 <u><b>Workout of the Day:</b></u>\n\n{wod_result(main_result_id)}"
        else:  # if date is DD-MM-YYYY
            formatted_date = date_converter_for_database(search_query)
            main_result_id = wod_id(airtable, search_date=formatted_date)
            main_result = f"💦 <u><b>Workout of the Day:</b></u>\n\n{wod_result(main_result_id)}"
    update.message.reply_text(main_result, parse_mode=ParseMode.HTML)


# /convert MAIN FUNCTION
# regex check for kg (assisting func)
def weight_regex_check_for_kg(input):
    result = bool(re.search('^\d+(?:[.,][0|5])?\s*(kg|KG)$', input))
    return result


# regex check for lbs (assisting func)
def weight_regex_check_for_lbs(input):
    result = bool(re.search('^\d+(?:[.,][0|5])?\s*(lbs|LBS)$', input))
    return result


# conversion to nearest 0.5/ 0.0 (assisting func)
def round_to_nearest_point_five(value):
    result = round(value * 2.0) / 2.0
    return result


# conversion process to relevant unit measurement (assisting func)
def conversion_process(input):
    KILO_TO_POUND_CONVERSION = 2.20462
    if weight_regex_check_for_kg(input):
        integer_input = float(input.lower().strip("kg"))
        converted_pound = round(integer_input * KILO_TO_POUND_CONVERSION, 1)
        final_converted_pound = round_to_nearest_point_five(converted_pound)
        result = f"Converted weight is <b>{final_converted_pound} lbs</b>"
        return result
    elif weight_regex_check_for_lbs(input):
        integer_input = float(input.lower().strip("lbs"))
        converted_kilogram = round(integer_input / KILO_TO_POUND_CONVERSION, 1)
        final_converted_kilogram = round_to_nearest_point_five(
            converted_kilogram)
        result = f"Converted weight will be <b>{final_converted_kilogram} kg</b>"
        return result
    else:
        error_message = "Accepting only one input and please check the unit of measurement too, only <b>kg</b>/ <b>lbs</b> are allowed."
        return error_message


# /convert function (main func)
def conversion(update, context) -> int:
    # print("user_data", update.message.from_user)
    context_result_for_conversion = context.args
    # print("context_result", context_result_for_conversion)
    # print("context_result_len", len(context_result_for_conversion))
    if len(context_result_for_conversion) == 0:
        result = "Please include a desired weight for conversion, only <b>kg</b>/<b>lbs</b>!"
    else:
        print("conversion", context_result_for_conversion)
        # user = update.message.from_user
        # print("user", user)
        input_weight = (update.message.text).lstrip("/convert ")
        # print("text1", input_weight)
        result = conversion_process(input_weight)
    return update.message.reply_text(result, parse_mode=ParseMode.HTML)


# Admin Access
def restricted(func):
    @wraps(func)
    def wrapped(update, context, *args, **kwargs):
        user_id = str(update.effective_user.id)
        user_name = update.effective_user.username
        print("username", user_name)
        if user_id not in LIST_OF_ADMINS:
            print(
                "Unauthorized access denied for id: {}, username: {}.".format(
                    user_id, user_name))
            error_message = "Admin Access Only 😊"
            update.message.reply_text(text=error_message)
            return
        return func(update, context, *args, **kwargs)

    return wrapped


# CONVERSARTION BOT ON Create, Edit & Delete, Only for ADMINS.
CHOOSING, DATE_SELECTION, NEW_WORKOUT_SELECTION, DELETE_SELECTION, EDIT_SELECTION, EDIT_WORKOUT = range(
    6)


# /create function (conversation initiator)
@restricted
def create(update: Update, context: CallbackContext):
    reply_keyboard = [['New'], ['Edit'], ['Delete']]
    markup = ReplyKeyboardMarkup(reply_keyboard,
                                 one_time_keyboard=True,
                                 selective=True)
    message = "Select your action, type <b><u>/cancel</u></b> if you wish to end the conversation"
    update.message.reply_text(message,
                              reply_markup=markup,
                              parse_mode=ParseMode.HTML)
    return CHOOSING


# new workout (path: CHOOSING)
@restricted
def action(update: Update, context: CallbackContext):
    user_data = context.user_data
    choice = update.message.text
    user_data['choice'] = choice
    print("choice", choice)
    print("user_data in action", user_data)
    update.message.reply_text(
        "<b>{}</b> workout? Set the date in this format: <b><u>DD-MM-YYYY</u></b>"
        .format(choice),
        quote=True,
        parse_mode=ParseMode.HTML,
    )
    return DATE_SELECTION


# convert keyed date into the required date for insertion in airtable frontend 'date' column
def date_conversion_for_insert(date):
    result = datetime.datetime.strptime(date, "%d-%m-%Y").strftime("%m-%d-%Y")
    return result


# airtable insertion , add data into database
def airtable_insertion(input_date, input_workout):
    converted_date = str(date_conversion_for_insert(input_date))
    record = {"date": converted_date, "wod": input_workout}
    print("record", record)
    airtable.insert(record)
    return


# ask for the date to be added into db
@restricted
def date_selection(update: Update, context: CallbackContext):
    user_data = context.user_data
    if 'date' and 'wod' in user_data:  # to clear any user_data outlying data
        del user_data['date']
        del user_data['wod']
    selected_date = update.message.text
    if date_format_check_for_DD_MM_YYYY(selected_date) == False:
        update.message.reply_text(
            "<b>Invalid date</b>, please key in a date in this format: <b>DD-MM-YYYY</b>",
            parse_mode=ParseMode.HTML)
    else:
        user_data['date'] = selected_date
        if user_data['choice'] == 'New':
            update.message.reply_text(
                "Key in the workout that you wish to add 🏋️")
            return NEW_WORKOUT_SELECTION
        elif user_data['choice'] == 'Delete':
            deleting_date = user_data[
                'date']  # store deleting_date in the context
            formatted_deleting_date = date_converter_for_database(
                deleting_date
            )  # convert deleted date to match with database format
            deleted_wod_id = wod_id(
                airtable, formatted_deleting_date)  # search for id in database
            if deleted_wod_id == None:
                update.message.reply_text(
                    "No workout found in the database. Key in another date in this format: <b><u>DD-MM-YYYY</u></b>",
                    parse_mode=ParseMode.HTML)
            else:
                # store deleted_wod_id in user_data
                user_data['delete_wod_id'] = deleted_wod_id
                deleted_wod = wod_result(deleted_wod_id)  #last appended wod
                user_data['deleted_wod'] = deleted_wod
                delete_inline_keyboard = [
                    [
                        InlineKeyboardButton("Yes", callback_data='Yes'),
                        InlineKeyboardButton("No", callback_data='No'),
                    ],
                ]
                delete_inline_reply_markup = InlineKeyboardMarkup(
                    delete_inline_keyboard)
                update.message.reply_text(
                    "<b><u>Workout to be deleted for {}:</u></b>\n\n{}\n\n<i>Confirm deletion?</i> 😱"
                    .format(user_data['date'], deleted_wod),
                    reply_markup=delete_inline_reply_markup,
                    parse_mode=ParseMode.HTML)
                return DELETE_SELECTION
        elif user_data['choice'] == 'Edit':
            editing_date = user_data['date']
            formatted_editing_date = date_converter_for_database(editing_date)
            edited_wod_id = wod_id(airtable, formatted_editing_date)
            if edited_wod_id == None:
                update.message.reply_text(
                    "No WOD found in database, please key in another date in <b>DD-MM-YYYY</b>",
                    parse_mode=ParseMode.HTML)
            else:
                user_data['edited_wod_id'] = edited_wod_id
                edited_wod = wod_result(edited_wod_id)
                user_data['edited_wod'] = edited_wod
                edit_inline_keyboard = [
                    [
                        InlineKeyboardButton("Edit", callback_data='Edit'),
                        InlineKeyboardButton("Pass", callback_data='Pass'),
                    ],
                ]
                edit_inline_reply_markup = InlineKeyboardMarkup(
                    edit_inline_keyboard)
                update.message.reply_text(
                    "<b><u>Workout to be edited for <i>{}</i></u></b>:\n\n{}\n\n<i>Confirm edit?</i> 🤔"
                    .format(user_data['date'], edited_wod),
                    reply_markup=edit_inline_reply_markup,
                    parse_mode=ParseMode.HTML)
                return EDIT_SELECTION


# ask for the workout to be added into db
@restricted
def insert_new_workout(update: Update, context: CallbackContext):
    user_data = context.user_data
    new_workout = update.message.text
    user_data['wod'] = new_workout
    try:
        airtable_insertion(user_data['date'], user_data['wod'])
        update.message.reply_text(
            "🎉 <b>Workout on {} added to the database</b> 🎉".format(
                user_data['date']),
            reply_markup=ReplyKeyboardRemove(),
            parse_mode=ParseMode.HTML)
    except:
        update.message.reply_text(
            "Error with date or data, kindly check them again 😟")
    user_data.clear()
    return ConversationHandler.END


# edit workout (path : CHOOSING)
@restricted
def edit_selection_button(update: Update, context: CallbackContext):
    user_data = context.user_data
    query = update.callback_query
    # print("query in edit", query)
    if query.data.lower() == "edit":
        query.answer()
        query.edit_message_text(
            text="New workout input for <b>{}</b>:\n\n<i>{}</i>".format(
                user_data['date'], user_data['edited_wod']),
            parse_mode=ParseMode.HTML)
        return EDIT_WORKOUT
    elif query.data.lower() == "pass":
        query.answer()
        query.edit_message_text(text="No edit needed, Goodbye! 👋")
        user_data.clear()
        return ConversationHandler.END


# update airtable function
def airtable_update(edit_id, edit_data):
    fields = {'wod': str(edit_data)}
    edited_result = airtable.update(edit_id, fields)
    print("edited result in airtable_update", edited_result)
    return edited_result


# edit
@restricted
def edit_workout(update: Update, context: CallbackContext):
    user_data = context.user_data
    new_edited_workout = update.message.text
    user_data['edited_wod'] = new_edited_workout
    # print("required data: {},{}".format(user_data['edited_wod_id'],
    #                                     user_data['edited_wod']))
    if user_data['edited_wod'] != None:
        try:
            airtable_update(user_data['edited_wod_id'],
                            user_data['edited_wod'])
            update.message.reply_text(
                "<b>Edited in Database... Revised workout for {}:</b>\n\n{}\n\nEnjoy your day! 🤖"
                .format(user_data['date'], user_data['edited_wod']),
                reply_markup=ReplyKeyboardRemove(),
                parse_mode=ParseMode.HTML)
        except:
            update.message.reply_text(
                "Something wrong with the input, please check again!")
    else:
        update.message.reply_text("You need to key in something!")
    user_data.clear()
    return ConversationHandler.END


# delete workout (path : CHOOSING)
@restricted
def delete_button(update: Update, context: CallbackContext):
    user_data = context.user_data
    query = update.callback_query
    if query.data.lower() == "yes":
        try:
            airtable.delete(user_data['delete_wod_id'])
            query.answer()
            query.edit_message_text(
                text=
                "Selected workout on <b>{}</b> has been deleted from the database... 😢 Goodbye... 👋"
                .format(user_data['date']),
                parse_mode=ParseMode.HTML)
            user_data.clear()
        except:
            query.answer()
            query.edit_message_text(text="No record was found in database")
            user_data.clear()
    elif query.data.lower() == "no":
        query.answer()
        query.edit_message_text(text="Not deleting from database, Goodbye! 👋")
        user_data.clear()
    return ConversationHandler.END


# cancel conversation (path: fallback)
@restricted
def cancel(update: Update, context: CallbackContext):
    user_data = context.user_data
    update.message.reply_text("Goodbye 👋", reply_markup=ReplyKeyboardRemove())
    user_data.clear()
    return ConversationHandler.END


# conversation flow for new, edit and delete
conv_handler = ConversationHandler(
    entry_points=[CommandHandler('create', create)],
    states={
        CHOOSING: [
            MessageHandler(Filters.regex('^(New|Edit|Delete)$'), action),
        ],
        DATE_SELECTION:
        [MessageHandler(Filters.text & (~Filters.command), date_selection)],
        NEW_WORKOUT_SELECTION: [
            MessageHandler(Filters.text & (~Filters.command),
                           insert_new_workout),
        ],
        DELETE_SELECTION: [CallbackQueryHandler(delete_button)],
        EDIT_SELECTION: [CallbackQueryHandler(edit_selection_button)],
        EDIT_WORKOUT:
        [MessageHandler(Filters.text & (~Filters.command), edit_workout)]
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
    dp.add_handler(CommandHandler("convert", conversion))

    dp.add_handler(conv_handler)

    updater.start_webhook(listen="0.0.0.0",
                          port=os.getenv("PORT"),
                          url_path=TELEGRAM_API_TOKEN,
                          webhook_url="https://workout-notify.herokuapp.com/" +
                          TELEGRAM_API_TOKEN)

    # updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()
"""
test - to test if the bot is awake
start - check for all available commands
view - format date as dd-mm-yyyy to view workouts
convert - format weight as xxx lbs / xxx kg for conversion
"""