import re
import html, time
from requests import get
from bs4 import BeautifulSoup
from telegram import Message, Update, Bot, User, Chat, ParseMode, InlineKeyboardMarkup
from telegram.ext import run_async
from tg_bot.modules.helper_funcs.misc import split_message
from telegram.utils.helpers import escape_markdown, mention_html

from tg_bot import dispatcher, updater
from tg_bot.modules.disable import DisableAbleCommandHandler

GITHUB = 'https://github.com'
DEVICES_DATA = 'https://raw.githubusercontent.com/androidtrackers/certified-android-devices/master/devices.json'

@run_async
def magisk(bot, update):
    url = 'https://raw.githubusercontent.com/topjohnwu/magisk_files/'
    releases = ""
    for type, path  in {"Stable":"master/stable", "Beta":"master/beta", "Canary":"canary/release"}.items():
        data = get(url + path + '.json').json()
        releases += f'{type}: [ZIP v{data["magisk"]["version"]}]({data["magisk"]["link"]}) | ' \
                    f'[APP v{data["app"]["version"]}]({data["app"]["link"]}) | ' \
                    f'[Uninstaller]({data["uninstaller"]["link"]})\n'
                        

    update.message.reply_text("*Latest Magisk Releases:*\n{}".format(releases),
                               parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)

@run_async
def device(bot, update, args):
    if len(args) == 0:
        reply = f'No codename provided, write a codename for fetching informations.'
        del_msg = update.effective_message.reply_text("{}".format(reply),
                               parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)
        time.sleep(5)
        del_msg.delete()
        update.effective_message.delete()
        return
    device = " ".join(args)
    found = [
        i for i in get(DEVICES_DATA).json()
        if i["device"] == device or i["model"] == device
    ]
    if found:
        reply = f'Search results for {device}:\n\n'
        for item in found:
            brand = item['brand']
            name = item['name']
            codename = item['device']
            model = item['model']
            reply += f'<b>{brand} {name}</b>\n' \
                f'Model: <code>{model}</code>\n' \
                f'Codename: <code>{codename}</code>\n\n'                
    else:
        reply = f"Couldn't find info about {device}!\n"
        del_msg = update.effective_message.reply_text("{}".format(reply),
                               parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)
        time.sleep(5)
        del_msg.delete()
        update.effective_message.delete()
        return
    update.message.reply_text("{}".format(reply),
                               parse_mode=ParseMode.HTML, disable_web_page_preview=True)

@run_async
def getfw(bot, update, args):
    if not len(args) == 2:
        reply = f'Give me something to fetch, like:\n`/getfw SM-N975F DBT`'
        del_msg = update.effective_message.reply_text("{}".format(reply),
                               parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)
        time.sleep(5)
        del_msg.delete()
        update.effective_message.delete()
        return
    temp,csc = args
    model = f'sm-'+temp if not temp.upper().startswith('SM-') else temp
    test = get(f'https://samfrew.com/model/{model.upper()}/region/{csc.upper()}/')
    if test.status_code == 404:
        reply = f"Couldn't find any firmware downloads for {temp.upper()} and {csc.upper()}, please refine your search or try again later!"
        del_msg = update.effective_message.reply_text("{}".format(reply),
                               parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)
        time.sleep(5)
        del_msg.delete()
        update.effective_message.delete()
        return
    url1 = f'• [samfrew.com](https://samfrew.com/model/{model.upper()}/region/{csc.upper()}/)'
    url2 = f'• [sammobile.com](https://www.sammobile.com/samsung/firmware/{model.upper()}/{csc.upper()}/)'
    url3 = f'• [sfirmware.com](https://sfirmware.com/samsung-{model.lower()}/#tab=firmwares)'

    reply = f'*Downloads for {model.upper()} and {csc.upper()}*\n'
    reply += f'{url1}\n'
    reply += f'{url2}\n'
    reply += f'{url3}\n'
    update.message.reply_text("{}".format(reply),
                           parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)

@run_async
def twrp(bot, update, args):
    if len(args) == 0:
        reply='No codename provided, write a codename for fetching informations.'
        del_msg = update.effective_message.reply_text("{}".format(reply),
                               parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)
        time.sleep(5)
        del_msg.delete()
        update.effective_message.delete()
        return
    device = " ".join(args)
    url = get(f'https://eu.dl.twrp.me/{device}/')
    if url.status_code == 404:
        reply = f"Couldn't find twrp downloads for {device}!\n"
        del_msg = update.effective_message.reply_text("{}".format(reply),
                               parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)
        time.sleep(5)
        del_msg.delete()
        update.effective_message.delete()
        return
    reply = f'*Latest Official TWRP for {device}*\n'            
    db = get(DEVICES_DATA).json()
    newdevice = device.strip('lte') if device.startswith('beyond') else device
    for dev in db:
        if (dev['device'] == newdevice) or (dev['model'] == newdevice):
            brand = dev['brand']
            name = dev['name']
            reply += f'*{brand} - {name}*\n'
            break
    page = BeautifulSoup(url.content, 'lxml')
    date = page.find("em").text.strip()
    reply += f'*Updated:* {date}\n'
    trs = page.find('table').find_all('tr')
    row = 2 if trs[0].find('a').text.endswith('tar') else 1
    for i in range(row):
        download = trs[i].find('a')
        dl_link = f"https://eu.dl.twrp.me{download['href']}"
        dl_file = download.text
        size = trs[i].find("span", {"class": "filesize"}).text
        reply += f'[{dl_file}]({dl_link}) - {size}\n'

    update.message.reply_text("{}".format(reply),
                               parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)

__help__ = """
*Android related commands:*

 - /magisk - gets the latest magisk release for Stable/Beta/Canary
 - /device <codename> - gets android device basic info from its codename
 - /twrp <codename> -  gets latest twrp for the android device using the codename
 - /getfw <model> <csc> - Samsung only - gets firmware download links from samfrew, sammobile and sfirmwares for the given device
 
 *Examples:*
 /device greatlte
 /twrp a5y17lte
 /getfw SM-M205FN SER
 
"""

__mod_name__ = "Android"

MAGISK_HANDLER = DisableAbleCommandHandler("magisk", magisk)
DEVICE_HANDLER = DisableAbleCommandHandler("device", device, pass_args=True)
TWRP_HANDLER = DisableAbleCommandHandler("twrp", twrp, pass_args=True)
GETFW_HANDLER = DisableAbleCommandHandler("getfw", getfw, pass_args=True)

dispatcher.add_handler(MAGISK_HANDLER)
dispatcher.add_handler(DEVICE_HANDLER)
dispatcher.add_handler(TWRP_HANDLER)
dispatcher.add_handler(GETFW_HANDLER)
