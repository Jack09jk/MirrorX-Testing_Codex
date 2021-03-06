from telegram import Bot, Update, ParseMode
from telegram.ext import CommandHandler
from bot import Interval, DOWNLOAD_DIR, DOWNLOAD_STATUS_UPDATE_INTERVAL, dispatcher, LOGGER, SOURCE_LOG, FSUB_ENABLED, FSUB_CHANNEL_ID, FSUB_CHANNEL_LINK, OWNER_ID, SUDO_USERS
from bot.helper.ext_utils.bot_utils import setInterval
from bot.helper.telegram_helper.message_utils import update_all_messages, sendMessage, sendStatusMessage
from .mirror import MirrorListener
from bot.helper.mirror_utils.download_utils.youtube_dl_download_helper import YoutubeDLHelper
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.filters import CustomFilters
import threading


def _watch(bot: Bot, update, isTar=False):
    mssg = update.message.text
    user_id = update.effective_user.id
    message_args = mssg.split(' ')
    name_args = mssg.split('|')

    user_is_normal = True
    if (user_id == OWNER_ID) or (user_id in SUDO_USERS):
        user_is_normal = False

    if user_is_normal:
        print("Normal User trying to access")
        if FSUB_ENABLED is True:
            member_sub_status = bot.get_chat_member(
                chat_id=FSUB_CHANNEL_ID,
                user_id=user_id
            )
            if member_sub_status.status not in ["creator", "administrator", "member", "restricted"]:
                update.effective_message.reply_markdown(
                    f"Why don't you join {FSUB_CHANNEL_LINK} and try using me again?"
                )
                return

    try:
        link = message_args[1]
    except IndexError:
        msg = f"/{BotCommands.WatchCommand} [yt_dl supported link] [quality] |[CustomName] to mirror with youtube_dl.\n\n"
        msg += "<b>Note :- Quality and custom name are optional</b>\n\nExample of quality :- audio, 144, 240, 360, 480, 720, 1080, 2160."
        msg += "\n\nIf you want to use custom filename, plz enter it after |"
        msg += f"\n\nExample :-\n<code>/{BotCommands.WatchCommand} https://youtu.be/ocX2FN1nguA 720 |My video bro</code>\n\n"
        msg += "This file will be downloaded in 720p quality and it's name will be <b>My video bro</b>"
        sendMessage(msg, bot, update)
        return
    try:
        if "|" in mssg:
            mssg = mssg.split("|")
            qual = mssg[0].split(" ")[2]
            if qual == "":
                raise IndexError
        else:
            qual = message_args[2]
        if qual != "audio":
            qual = f'bestvideo[height<={qual}]+bestaudio/best[height<={qual}]'
    except IndexError:
        qual = "bestvideo+bestaudio/best"

    uname = f'<a href="tg://user?id={update.effective_user.id}">{update.effective_user.first_name}</a>'
    links_log = f'<b>User:</b> {uname} <b>User ID:</b> <code>{update.effective_user.id}</code>\n<b>Sent:</b> <code>{link}</code>'
    bot.send_message(SOURCE_LOG, links_log, parse_mode=ParseMode.HTML)

    try:
        name = name_args[1]
    except IndexError:
        name = ""
    reply_to = update.message.reply_to_message
    if reply_to is not None:
        tag = reply_to.from_user.username
    else:
        tag = None
    pswd = ""
    listener = MirrorListener(bot, update, pswd, isTar, tag)
    ydl = YoutubeDLHelper(listener)
    threading.Thread(target=ydl.add_download,args=(link, f'{DOWNLOAD_DIR}{listener.uid}', qual, name)).start()
    sendStatusMessage(update, bot)
    if len(Interval) == 0:
        Interval.append(setInterval(DOWNLOAD_STATUS_UPDATE_INTERVAL, update_all_messages))


def watchTar(update, context):
    _watch(context.bot, update, True)


def watch(update, context):
    _watch(context.bot, update)


mirror_handler = CommandHandler(BotCommands.WatchCommand, watch,
                                filters=CustomFilters.authorized_chat | CustomFilters.authorized_user, run_async=True)
tar_mirror_handler = CommandHandler(BotCommands.TarWatchCommand, watchTar,
                                    filters=CustomFilters.authorized_chat | CustomFilters.authorized_user, run_async=True)
dispatcher.add_handler(mirror_handler)
dispatcher.add_handler(tar_mirror_handler)
