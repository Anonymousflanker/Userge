# Copyright (C) 2020 by UsergeTeam@Github, < https://github.com/UsergeTeam >.
#
# This file is part of < https://github.com/UsergeTeam/Userge > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/uaudith/Userge/blob/master/LICENSE >
#
# All rights reserved.


import os
import time
from datetime import datetime
from userge import userge, Config, Message
from userge.utils import progress

THUMB_PATH = Config.DOWN_PATH + "thumb_image.jpg"
CHANNEL = userge.getCLogger(__name__)


@userge.on_cmd('sthumb', about="""\
__Save thumbnail__

**Usage:**

    `.sthumb [reply to any photo]`""")
async def save_thumb_nail(message: Message):
    await message.edit("processing ...")
    if message.reply_to_message is not None and message.reply_to_message.photo:
        start_t = datetime.now()
        c_time = time.time()

        if os.path.exists(THUMB_PATH):
            os.remove(THUMB_PATH)

        await userge.download_media(message=message.reply_to_message,
                                    file_name=THUMB_PATH,
                                    progress=progress,
                                    progress_args=(
                                        "trying to download", userge, message, c_time))

        end_t = datetime.now()
        m_s = (end_t - start_t).seconds

        await message.edit(f"thumbnail saved in {m_s} seconds.", del_in=3, log=True)

    else:
        await message.edit("Reply to a photo to save custom thumbnail", del_in=3)


@userge.on_cmd('dthumb', about="__Delete thumbnail__")
async def clear_thumb_nail(message: Message):
    await message.edit("`processing ...`")

    if os.path.exists(THUMB_PATH):
        os.remove(THUMB_PATH)

    await message.edit("✅ Custom thumbnail deleted succesfully.", del_in=3, log=True)


@userge.on_cmd('vthumb', about="__View thumbnail__")
async def get_thumb_nail(message: Message):
    await message.edit("processing ...")
    if os.path.exists(THUMB_PATH):
        msg = await userge.send_document(chat_id=message.chat.id,
                                         document=THUMB_PATH,
                                         disable_notification=True,
                                         reply_to_message_id=message.message_id)
        await CHANNEL.fwd_msg(msg)
        await message.delete()

    else:
        await message.err("Custom Thumbnail Not Found!")
