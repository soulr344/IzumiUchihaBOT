import pyowm, time
from pyowm import timeutils, exceptions
from telegram import Message, Chat, Update, Bot, ParseMode
from telegram.ext import run_async

from tg_bot import dispatcher, updater, API_WEATHER
from tg_bot.modules.disable import DisableAbleCommandHandler

@run_async
def weather(bot, update, args):
    if len(args) == 0:
        reply = f'Write a location to check the weather.'
        del_msg = update.effective_message.reply_text("{}".format(reply),
                               parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)
        time.sleep(5)
        del_msg.delete()
        update.effective_message.delete()
        return

    location = " ".join(args)
    try:
        owm = pyowm.OWM(API_WEATHER)
        observation = owm.weather_at_place(location)
        getloc = observation.get_location()
        thelocation = getloc.get_name()
        if thelocation == None:
            thelocation = "Unknown"
        theweather = observation.get_weather()
        temperature = theweather.get_temperature(unit='celsius').get('temp')
        if temperature == None:
            temperature[0] = "Unknown"
        else:
            temperature = str(temperature).split(".")

        # Weather symbols
        status = ""
        status_now = theweather.get_weather_code()
        if status_now < 232: # Rain storm
            status += "⛈️ "
        elif status_now < 321: # Drizzle
            status += "🌧️ "
        elif status_now < 504: # Light rain
            status += "🌦️ "
        elif status_now < 531: # Cloudy rain
             status += "⛈️ "
        elif status_now < 622: # Snow
            status += "🌨️ "
        elif status_now < 781: # Atmosphere
            status += "🌪️ "
        elif status_now < 800: # Bright
            status += "🌤️ "
        elif status_now < 801: # A little cloudy
             status += "⛅️ "
        elif status_now < 804: # Cloudy
             status += "☁️ "
        status += theweather._detailed_status
        
        del_msg = update.effective_message.reply_text("Today in {} is being {}, around {}°C.\n".format(thelocation,
                status, temperature[0]))
        time.sleep(30)
        del_msg.delete()
        update.effective_message.delete()

    except pyowm.exceptions.api_response_error.NotFoundError:
        reply = f'Location not valid.'
        del_msg = update.effective_message.reply_text("{}".format(reply),
                               parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)
        time.sleep(5)
        del_msg.delete()
        update.effective_message.delete()


__help__ = """
Weather module:

 - /weather <city>: gets weather info in a particular place using openweathermap.org api
 
 \* For obvious reasons the weather command and the output will be deleted after 30 seconds
"""

__mod_name__ = "Weather"

WEATHER_HANDLER = DisableAbleCommandHandler("weather", weather, pass_args=True)

dispatcher.add_handler(WEATHER_HANDLER)