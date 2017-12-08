#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import logging
import os
from raven import Client

import requests
import database

import gspread
import telegram
import wget
from bs4 import BeautifulSoup
from oauth2client.service_account import ServiceAccountCredentials
from telegram import InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import (CallbackQueryHandler, CommandHandler, Filters,
                          InlineQueryHandler, MessageHandler, Updater)

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

class AlusaBot:
    
    def __init__(self):
        scope = ['https://spreadsheets.google.com/feeds']
        filename = wget.download(os.environ.get('FILE_SECRET'), out="client_secret.json")
        creds = ServiceAccountCredentials.from_json_keyfile_name(filename, scope)
        client = gspread.authorize(creds)
        self.sheet = client.open("Porra NFL").sheet1

    def start(self, bot, update):
        user_id = update.message.from_user.id
        register = database.insert_register(user_id)
        update.message.reply_text('¡Hola! Consulta el estado de todas las porras de Alusa. Escribe /help para más ayuda')

    def help(self, bot, update):
        html = """
        Consulta el estado de todas las porras de Alusa \n
        /nfl - Clasificación de la NFL \n
        /porra - Porra semanal del futbol \n
        """
        bot.send_message(chat_id=update.message.chat_id, text=html, parse_mode=telegram.ParseMode.HTML)

    def get_score(self, soup, team, result_1x2=False):
        client = Client('https://8af6f70453c34c469ddf1cb017e006c9:ebf39ab87837475ab8e5f15c8cc57ac6@sentry.io/255534')
        text = ""
        try:
            team_object = soup.find("span", {"title": team})
            parent_object = team_object.parent
            home = parent_object.get("class")[1:][0]
            if home == 'has-logo':
                home = parent_object.get("class")[1:][1]
            is_home = True if home == 'team1' else False
            team_search = 'team2' if is_home else 'team1'
            parent = team_object.parent.parent
            score = parent.find("td", {"class": 'score'})
            result = json.loads(score.get('data-meta'))
            if not result['home']:
                result['home'] = 0
                result['away'] = 0
            if result_1x2:
                if result['home'] == result['away']:
                    text = '%s - %s' % (team, 'X')
                elif int(result['home']) > int(result['away']):
                    text = '%s - %s' % (team, '1')
                else:
                    text = '%s - %s' % (team, '2')
                return text.decode('utf-8')
            team2 = parent.find("td", {"class": team_search})
            team2 = team2.getText()
            if is_home:
                team_home = team
                team_away = team2
            else:
                team_home = team2
                team_away = team
            text = '%s %s - %s %s \n' % (team_home,
                                        int(result['home']), int(result['away']), team_away)
        except:
            client.captureException()
        if not text:
            text = 'Ha ocurrido un error'
        if hasattr(text, 'decode'): 
            return text.decode('utf-8')
        else:
            return text

    def football(self, bot, update):
        uid = update.message.from_user
        message_dict = update.message.to_dict()
        event_name = update.message.text
        liga = requests.get('http://www.marcadores.com/futbol/espana/liga-bbva/')
        teams = ['Real Madrid', 'Barcelona']
        soup = BeautifulSoup(liga.text, "html.parser")
        html = ""
        for team in teams:
            html += self.get_score(soup, team)
        liga_second = requests.get('http://www.marcadores.com/futbol/espana/liga-adelante/')
        soup = BeautifulSoup(liga_second.text, "html.parser")
        html += self.get_score(soup, 'Córdoba', True)
        bot.send_message(chat_id=update.message.chat_id, text=html, parse_mode=telegram.ParseMode.HTML)

    def get_clasification(self):
        list_users = []
        row = 3
        col_name = 2
        col_points = 3
        while row < 21:
            name = self.sheet.cell(row, col_name).value
            points = self.sheet.cell(row, col_points).value
            if points:
                list_users.append({'user': name, 'points': int(points)})
            row += 1
        if list_users:
            list_users = sorted(list_users, key=lambda k: k['points'])
        return list_users
        
    def nfl(self, bot, update):
        uid = update.message.from_user
        message_dict = update.message.to_dict()
        event_name = update.message.text
        text = 'Elige una de estas opciones:'
        user_id = update.message.from_user.id
        register = database.insert_register(user_id)
        button_list = [[
            telegram.InlineKeyboardButton(
                text='Clasificación', callback_data='clasificacion_nfl'),
            telegram.InlineKeyboardButton(
                text='Partidos de la siguiente jornada', callback_data='partidos_nfl'),
            telegram.InlineKeyboardButton(
                text='Normas', callback_data='normas'),
        ]]
        reply_markup = telegram.InlineKeyboardMarkup(button_list)
        bot.send_message(
            chat_id=update.message.chat_id,
            text=text,
            reply_markup=reply_markup,
            parse_mode=telegram.ParseMode.HTML
        )

    def upload_photo(self, bot, update):
        user_id = update.message.chat_id
        if user_id == 4455799:
            photo = update.message.photo[-1]
            photo_id = photo.file_id
            newFile = bot.get_file(photo_id)
            newFile.download('../tmp/partidos.jpg')
            bot.send_message(chat_id=update.message.chat_id, text='Guardado', parse_mode=telegram.ParseMode.HTML)

    def callback_nfl(self, bot, update):
        query = update.callback_query
        user_id = update.callback_query.from_user.id
        message_dict = update.callback_query.message.to_dict()
        callback_text = query['data']
        text = "Ahí tienes"
        if 'partidos_nfl' in callback_text:
            text = "GO!"
            bot.send_photo(chat_id=user_id, photo=open('../tmp/partidos.jpg', 'rb'))
        elif 'normas' in callback_text:
            text = "Esto es lo que hay"
            bot.send_photo(chat_id=user_id, photo=open('images/normas.jpg', 'rb'))
        else:
            text = 'Paganini!'
            clasification = self.get_clasification()
            html = "Clasificación (NO OFICIAL): \n"
            i = 0
            for user in clasification:
                if i > 7:
                    html += "<b>%s - %s</b> \n" % (user['user'], user['points'])
                else:
                    html += "%s - %s \n" % (user['user'], user['points'])
                i += 1
            bot.send_message(chat_id=user_id,
                             text=html, parse_mode=telegram.ParseMode.HTML)
        bot.answerCallbackQuery(query.id, text=text)


    def echo(bot, update):
        message = update.message.text
        user_id = update.message.chat_id
        if user_id == 4455799:
            message_list = message.split(':')
            if message_list[0] == 'Enviar':
                text = message_list[1]
                users = database.get_registers()
                for user in users:
                    bot.send_message(
                        chat_id=user,
                        text=text,
                        parse_mode=telegram.ParseMode.HTML
                    )

    def error(self, bot, update, error):
        logger.warning('Update "%s" caused error "%s"' % (update, error))


def main():
    client = Client(
        'https://8af6f70453c34c469ddf1cb017e006c9:ebf39ab87837475ab8e5f15c8cc57ac6@sentry.io/255534')
    try:
        database.create_tables()
        TOKEN = os.environ.get('TOKEN', None)
        PORT = int(os.environ.get('PORT', '5000'))
        # Create the Updater and pass it your bot's token.
        updater = Updater(TOKEN)
        updater.start_webhook(listen="0.0.0.0", port=PORT, url_path=TOKEN)
        updater.bot.set_webhook("https://alusabot.herokuapp.com/" + TOKEN)
        # Get the dispatcher to register handlers
        dp = updater.dispatcher
        alusa = AlusaBot()
        # on different commands - answer in Telegram
        dp.add_handler(CommandHandler("start", alusa.start))
        dp.add_handler(CommandHandler("help", alusa.help))
        dp.add_handler(CommandHandler("nfl", alusa.nfl))
        dp.add_handler(CommandHandler("porra", alusa.football))
        dp.add_handler(MessageHandler(Filters.photo, alusa.upload_photo))
        dp.add_handler(MessageHandler(Filters.text, alusa.echo))


        dp.add_handler(CallbackQueryHandler(alusa.callback_nfl))

        # log all errors
        dp.add_error_handler(alusa.error)

        # Start the Bot
        updater.start_polling()

        updater.idle()
    except:
        client.captureException()

if __name__ == '__main__':
    main()
