import html
from typing import Optional, List

from telegram.ext import CommandHandler, run_async, Filters, RegexHandler
from telegram import Message, Chat, Update, Bot, User, ParseMode, InlineKeyboardMarkup, MAX_MESSAGE_LENGTH

import tg_bot.modules.helper_funcs.git_api as api
import tg_bot.modules.sql.github_sql as sql

from tg_bot import dispatcher, CallbackContext, OWNER_ID, LOGGER, SUDO_USERS, SUPPORT_USERS
from tg_bot.modules.helper_funcs.filters import CustomFilters
from tg_bot.modules.helper_funcs.chat_status import user_admin
from tg_bot.modules.disable import DisableAbleCommandHandler


def getphh(index):
    recentRelease = api.getReleaseData(
        api.getData("phhusson/treble_experimentations"), index)
    if recentRelease is None:
        return "The specified release could not be found"
    author = api.getAuthor(recentRelease)
    authorUrl = api.getAuthorUrl(recentRelease)
    name = api.getReleaseName(recentRelease)
    assets = api.getAssets(recentRelease)
    releaseName = api.getReleaseName(recentRelease)
    message = "<b>Author:</b> <a href='{}'>{}</a>\n".format(authorUrl, author)
    message += "<b>Release Name:</b> <code>" + releaseName + "</code>\n\n"
    message += "<b>Assets:</b>\n"
    for asset in assets:
        fileName = api.getReleaseFileName(asset)
        if fileName in ("manifest.xml", "patches.zip"):
            continue
        fileURL = api.getReleaseFileURL(asset)
        assetFile = "• <a href='{}'>{}</a>".format(fileURL, fileName)
        sizeB = ((api.getSize(asset)) / 1024) / 1024
        size = "{0:.2f}".format(sizeB)
        message += assetFile + "\n"
        message += "    <code>Size: " + size + " MB</code>\n"
    return message


#do not async
def getData(url, index):
    if not api.getData(url):
        return "Invalid <user>/<repo> combo"
    recentRelease = api.getReleaseData(api.getData(url), index)
    if recentRelease is None:
        return "The specified release could not be found"
    author = api.getAuthor(recentRelease)
    authorUrl = api.getAuthorUrl(recentRelease)
    name = api.getReleaseName(recentRelease)
    assets = api.getAssets(recentRelease)
    releaseName = api.getReleaseName(recentRelease)
    message = "<b>Author:</b> <a href='{}'>{}</a>\n".format(authorUrl, author)
    message += "<b>Release Name:</b> " + releaseName + "\n\n"
    for asset in assets:
        message += "<b>Asset:</b> \n"
        fileName = api.getReleaseFileName(asset)
        fileURL = api.getReleaseFileURL(asset)
        assetFile = "<a href='{}'>{}</a>".format(fileURL, fileName)
        sizeB = ((api.getSize(asset)) / 1024) / 1024
        size = "{0:.2f}".format(sizeB)
        downloadCount = api.getDownloadCount(asset)
        message += assetFile + "\n"
        message += "Size: " + size + " MB"
        message += "\nDownload Count: " + str(downloadCount) + "\n\n"
    return message


#likewise, aux function, not async
def getRepo(bot, update, reponame):
    chat_id = update.effective_chat.id
    repo = sql.get_repo(str(chat_id), reponame)
    if repo:
        return repo.value, repo.backoffset
    return None, None


def getRelease(update: Update, context: CallbackContext):
    bot = context.bot
    args = context.args
    msg = update.effective_message
    if len(args) == 0:
        msg.reply_text("Please use some arguments!")
        return
    if (len(args) != 1 and not (len(args) == 2 and args[1].isdigit())
            and not ("/" in args[0])):
        msg.reply_text("Please specify a valid combination of <user>/<repo>")
        return
    index = 0
    if len(args) == 2:
        index = int(args[1])
    url = args[0]
    text = getData(url, index)
    msg.reply_text(text,
                   parse_mode=ParseMode.HTML,
                   disable_web_page_preview=True)
    return


def hashFetch(update: Update, context: CallbackContext):
    bot = context.bot  #kanged from notes
    message = update.effective_message.text
    msg = update.effective_message
    fst_word = message.split()[0]
    no_hash = fst_word[1:]
    url, index = getRepo(bot, update, no_hash)
    if url is None and index is None:
        msg.reply_text(
            "There was a problem parsing your request. Likely this is not a saved repo shortcut",
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True)
        return
    text = getData(url, index)
    msg.reply_text(text,
                   parse_mode=ParseMode.HTML,
                   disable_web_page_preview=True)
    return


def cmdFetch(update: Update, context: CallbackContext):
    bot = context.bot
    args = context.args
    msg = update.effective_message
    if (len(args) != 1):
        msg.reply_text("Invalid repo name")
        return
    url, index = getRepo(bot, update, args[0])
    if url is None and index is None:
        msg.reply_text(
            "There was a problem parsing your request. Likely this is not a saved repo shortcut",
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True)
        return
    text = getData(url, index)
    msg.reply_text(text,
                   parse_mode=ParseMode.HTML,
                   disable_web_page_preview=True)
    return


def changelog(update: Update, context: CallbackContext):
    bot = context.bot
    args = context.args
    msg = update.effective_message
    if (len(args) != 1):
        msg.reply_text("Invalid repo name")
        return
    url, index = getRepo(bot, update, args[0])
    if not api.getData(url):
        msg.reply_text("Invalid <user>/<repo> combo")
        return
    data = api.getData(url)
    release = api.getReleaseData(data, index)
    body = api.getBody(release)
    msg.reply_text(body)
    return


@user_admin
def saveRepo(update: Update, context: CallbackContext):
    bot = context.bot
    args = context.args
    chat_id = update.effective_chat.id
    msg = update.effective_message
    if (len(args) != 2 and (len(args) != 3 and not args[2].isdigit())
            or not ("/" in args[1])):
        msg.reply_text(
            "Invalid data, use <reponame> <user>/<repo> <value (optional)>")
        return
    index = 0
    if len(args) == 3:
        index = int(args[2])
    sql.add_repo_to_db(str(chat_id), args[0], args[1], index)
    msg.reply_text("Repo shortcut saved successfully!")
    return


@user_admin
def delRepo(update: Update, context: CallbackContext):
    bot = context.bot
    args = context.args
    chat_id = update.effective_chat.id
    msg = update.effective_message
    if (len(args) != 1):
        msg.reply_text("Invalid repo name!")
        return
    sql.rm_repo(str(chat_id), args[0])
    msg.reply_text("Repo shortcut deleted successfully!")
    return


def listRepo(update: Update, context: CallbackContext):
    bot = context.bot
    chat_id = update.effective_chat.id
    chat = update.effective_chat
    chat_name = chat.title or chat.first or chat.username
    repo_list = sql.get_all_repos(str(chat_id))
    msg = "<b>GitHub repo shotcuts in {}:</b>\n"
    des = "\nYou can retrieve these repos by using <code>/fetch repo</code>, or <code>&repo</code>\n"
    for repo in repo_list:
        repo_name = (" • <code>&{}</code>\n".format(repo.name))
        if len(msg) + len(repo_name) > MAX_MESSAGE_LENGTH:
            update.effective_message.reply_text(msg, parse_mode=ParseMode.HTML)
            msg = ""
        msg += repo_name
    if msg == "<b>List of repo shotcuts in {}:</b>\n":
        update.effective_message.reply_text("No repo shortcuts in this chat!")
    elif len(msg) != 0:
        update.effective_message.reply_text(msg.format(chat_name) + des,
                                            parse_mode=ParseMode.HTML)


def getVer(update: Update, context: CallbackContext):
    bot = context.bot
    msg = update.effective_message
    ver = api.vercheck()
    msg.reply_text("GitHub API version: " + ver)
    return


__help__ = """
GitHub module. This module will help you to fetch GitHub releases.

*Available Commands:*
 - /git <user>/<repo>: will fetch the most recent release from that repo.
 - /git <user>/<repo> <number>: will fetch releases in past.
 - /fetch <reponame> or &reponame: same as /git, but you can use a saved repo shortcut
 - /listrepo: lists all repo shortcuts in chat
 - /gitver: returns the current API version
 - /changelog <reponame>: gets the changelog of a saved repo shortcut
 
*Admin only:*
 - /saverepo <name> <user>/<repo> <number (optional)>: saves a repo value as shortcut
 - /delrepo <name>: deletes a repo shortcut
"""

__mod_name__ = "GitHub"

RELEASE_HANDLER = DisableAbleCommandHandler("git",
                                            getRelease,
                                            run_async=True,
                                            admin_ok=True)
FETCH_HANDLER = DisableAbleCommandHandler("fetch",
                                          cmdFetch,
                                          run_async=True,
                                          admin_ok=True)
SAVEREPO_HANDLER = CommandHandler("saverepo", saveRepo, run_async=True)
DELREPO_HANDLER = CommandHandler("delrepo", delRepo, run_async=True)
LISTREPO_HANDLER = DisableAbleCommandHandler("listrepo",
                                             listRepo,
                                             admin_ok=True,
                                             run_async=True)
VERCHECKER_HANDLER = DisableAbleCommandHandler("gitver",
                                               getVer,
                                               admin_ok=True,
                                               run_async=True)
CHANGELOG_HANDLER = DisableAbleCommandHandler("changelog",
                                              changelog,
                                              run_async=True,
                                              admin_ok=True)

HASHFETCH_HANDLER = RegexHandler(r"^&[^\s]+", hashFetch)

dispatcher.add_handler(RELEASE_HANDLER)
dispatcher.add_handler(FETCH_HANDLER)
dispatcher.add_handler(SAVEREPO_HANDLER)
dispatcher.add_handler(DELREPO_HANDLER)
dispatcher.add_handler(LISTREPO_HANDLER)
dispatcher.add_handler(HASHFETCH_HANDLER)
dispatcher.add_handler(VERCHECKER_HANDLER)
dispatcher.add_handler(CHANGELOG_HANDLER)
