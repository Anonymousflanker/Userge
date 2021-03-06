# Copyright (C) 2020 by UsergeTeam@Github, < https://github.com/UsergeTeam >.
#
# This file is part of < https://github.com/UsergeTeam/Userge > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/uaudith/Userge/blob/master/LICENSE >
#
# All rights reserved.


import re
import os
import asyncio
from typing import List, Dict, Union, Optional, Sequence

from pyrogram import InlineKeyboardMarkup
from pyrogram.errors.exceptions import MessageAuthorRequired, MessageTooLong
from pyrogram.errors.exceptions.bad_request_400 import MessageNotModified

from userge.utils import logging, Config
from .base import BaseClient, BaseMessage

CANCEL_LIST: List[int] = []
ERROR_MSG_DELETE_TIMEOUT = 5
ERROR_STRING = "**ERROR**: `{}`"

LOG = logging.getLogger(__name__)
LOG_STR = "<<<!  [[[[[  ___{}___  ]]]]]  !>>>"


class Message(BaseMessage):
    """
    Modded Message Class For Userge
    """

    def __init__(self,
                 client: BaseClient,
                 message: BaseMessage,
                 **kwargs: Union[str, bool]) -> None:

        super().__init__(client=client,
                         **self.__msg_to_dict(message))

        self.reply_to_message: BaseMessage

        if self.reply_to_message:
            self.reply_to_message = self.__class__(self._client, self.reply_to_message)

        self.__channel = client.getCLogger(__name__)
        self.__filtered = False
        self.__process_canceled = False
        self.__filtered_input_str: str = ''
        self.__flags: Dict[str, str] = {}
        self.__kwargs = kwargs

    @property
    def input_str(self) -> str:
        """
        Returns the input string without command.
        """

        input_ = self.text

        if ' ' in input_:
            return str(input_.split(maxsplit=1)[1].strip())

        return ''

    @property
    def input_or_reply_str(self) -> str:
        """
        Returns the input string without command or replied msg text.
        """

        input_ = self.input_str

        if not input_ and self.reply_to_message:
            input_ = (self.reply_to_message.text or '').strip()

        return input_

    @property
    def filtered_input_str(self) -> str:
        """
        Returns the filtered input string without command and flags.
        """

        self.__filter()

        return self.__filtered_input_str

    @property
    def flags(self) -> Dict[str, str]:
        """
        Returns all flags in input string as `Dict`.
        """

        self.__filter()

        return self.__flags

    @property
    def process_is_canceled(self) -> bool:
        """
        Returns True if process canceled.
        """

        if self.message_id in CANCEL_LIST:
            CANCEL_LIST.remove(self.message_id)
            self.__process_canceled = True

        return self.__process_canceled

    def cancel_the_process(self) -> None:
        """
        Set True to the self.process_is_canceled.
        """

        CANCEL_LIST.append(self.message_id)

    def __msg_to_dict(self, message: BaseMessage) -> Dict[str, object]:

        kwargs_ = vars(message)
        del message

        del kwargs_['_client']

        if '_Message__channel' in kwargs_:
            del kwargs_['_Message__channel']

        if '_Message__filtered' in kwargs_:
            del kwargs_['_Message__filtered']

        if '_Message__process_canceled' in kwargs_:
            del kwargs_['_Message__process_canceled']

        if '_Message__filtered_input_str' in kwargs_:
            del kwargs_['_Message__filtered_input_str']

        if '_Message__flags' in kwargs_:
            del kwargs_['_Message__flags']

        if '_Message__kwargs' in kwargs_:
            del kwargs_['_Message__kwargs']

        return kwargs_

    def __filter(self) -> None:

        if not self.__filtered:
            prefix = str(self.__kwargs.get('prefix', '-'))
            del_pre = bool(self.__kwargs.get('del_pre', False))
            input_str = self.input_str

            for i in input_str.strip().split():
                match = re.match(f"({prefix}[a-z]+)($|[0-9]+)?$", i)

                if match:
                    items: Sequence[str] = match.groups()
                    self.__flags[items[0].lstrip(prefix) if del_pre \
                        else items[0]] = items[1] or ''

                else:
                    self.__filtered_input_str += ' ' + i

            self.__filtered_input_str = self.__filtered_input_str.strip()

            LOG.info(
                LOG_STR.format(
                    f"Filtered Input String => [ {self.__filtered_input_str}, {self.__flags} ]"))

            self.__filtered = True

    async def send_as_file(self,
                           text: str,
                           filename: str = "output.txt",
                           caption: str = '',
                           log: bool = False,
                           delete_message: bool = True) -> BaseMessage:
        """
        You can send large outputs as file

        Example:
                message.send_as_file(text="hello")

        Parameters:
            text (``str``):
                Text of the message to be sent.
            filename (``str``, *optional*):
                file_name for output file.
            caption (``str``, *optional*):
                caption for output file.
            log (``bool``, *optional*):
                If ``True``, the message will be forwarded to the log channel.
            delete_message (``bool``, *optional*):
                If ``True``, the message will be deleted after sending the file.
        Returns:
            On success, the sent Message is returned.
        """

        with open(filename, "w+", encoding="utf8") as out_file:
            out_file.write(text)

        reply_to_id = self.reply_to_message.message_id if self.reply_to_message \
            else self.message_id

        LOG.info(
            LOG_STR.format(f"Uploading {filename} To Telegram"))

        msg = await self._client.send_document(chat_id=self.chat.id,
                                               document=filename,
                                               caption=caption,
                                               disable_notification=True,
                                               reply_to_message_id=reply_to_id)

        os.remove(filename)

        if log:
            await self.__channel.fwd_msg(msg)

        if delete_message:
            await self.delete()

        return Message(self._client, msg)

    async def reply(self,
                    text: str,
                    del_in: int = -1,
                    log: bool = False,
                    quote: Optional[bool] = None,
                    parse_mode: Union[str, object] = object,
                    disable_web_page_preview: Optional[bool] = None,
                    disable_notification: Optional[bool] = None,
                    reply_to_message_id: Optional[int] = None,
                    reply_markup: InlineKeyboardMarkup = None) -> Union[BaseMessage, bool]:
        """
        Example:
                message.reply("hello")

        Parameters:
            text (``str``):
                Text of the message to be sent.
            del_in (``int``):
                Time in Seconds for delete that message.
            log (``bool``, *optional*):
                If ``True``, the message will be forwarded to the log channel.
            quote (``bool``, *optional*):
                If ``True``, the message will be sent as a reply to this message.
                If *reply_to_message_id* is passed, this parameter will be ignored.
                Defaults to ``True`` in group chats and ``False`` in private chats.
            parse_mode (``str``, *optional*):
                By default, texts are parsed using both Markdown and HTML styles.
                You can combine both syntaxes together.
                Pass "markdown" or "md" to enable Markdown-style parsing only.
                Pass "html" to enable HTML-style parsing only.
                Pass None to completely disable style parsing.
            disable_web_page_preview (``bool``, *optional*):
                Disables link previews for links in this message.
            disable_notification (``bool``, *optional*):
                Sends the message silently.
                Users will receive a notification with no sound.
            reply_to_message_id (``int``, *optional*):
                If the message is a reply, ID of the original message.
            reply_markup (:obj:`InlineKeyboardMarkup` | :obj:`ReplyKeyboardMarkup` | :obj:`ReplyKeyboardRemove` | :obj:`ForceReply`, *optional*):
                Additional interface options. An object for an inline keyboard, custom reply keyboard,
                instructions to remove reply keyboard or to force a reply from the user.
        Returns:
            On success, the sent Message or True is returned.
        Raises:
            RPCError: In case of a Telegram RPC error.
        """

        if quote is None:
            quote = self.chat.type != "private"

        if reply_to_message_id is None and quote:
            reply_to_message_id = self.message_id

        msg = await self._client.send_message(chat_id=self.chat.id,
                                              text=text,
                                              parse_mode=parse_mode,
                                              disable_web_page_preview=disable_web_page_preview,
                                              disable_notification=disable_notification,
                                              reply_to_message_id=reply_to_message_id,
                                              reply_markup=reply_markup)

        if log:
            await self.__channel.fwd_msg(msg)

        del_in = del_in or Config.MSG_DELETE_TIMEOUT

        if del_in > 0:
            await asyncio.sleep(del_in)
            return await msg.delete()

        return Message(self._client, msg)

    reply_text = reply

    async def edit(self,
                   text: str,
                   del_in: int = -1,
                   log: bool = False,
                   parse_mode: Union[str, object] = object,
                   disable_web_page_preview: Optional[bool] = None,
                   reply_markup: InlineKeyboardMarkup = None) -> Union[BaseMessage, bool]:
        """
        Example:
                message.edit_text("hello")

        Parameters:
            text (``str``):
                New text of the message.
            del_in (``int``):
                Time in Seconds for delete that message.
            log (``bool``, *optional*):
                If ``True``, the message will be forwarded to the log channel.
            parse_mode (``str``, *optional*):
                By default, texts are parsed using both Markdown and HTML styles.
                You can combine both syntaxes together.
                Pass "markdown" or "md" to enable Markdown-style parsing only.
                Pass "html" to enable HTML-style parsing only.
                Pass None to completely disable style parsing.
            disable_web_page_preview (``bool``, *optional*):
                Disables link previews for links in this message.
            reply_markup (:obj:`InlineKeyboardMarkup`, *optional*):
                An InlineKeyboardMarkup object.
        Returns:
            On success, the edited :obj:`Message` or True is returned.
        Raises:
            RPCError: In case of a Telegram RPC error.
        """

        msg = await self._client.edit_message_text(chat_id=self.chat.id,
                                                   message_id=self.message_id,
                                                   text=text,
                                                   parse_mode=parse_mode,
                                                   disable_web_page_preview=disable_web_page_preview,
                                                   reply_markup=reply_markup)

        if log:
            await self.__channel.fwd_msg(msg)

        del_in = del_in or Config.MSG_DELETE_TIMEOUT

        if del_in > 0:
            await asyncio.sleep(del_in)
            return await msg.delete()

        return Message(self._client, msg)

    edit_text = edit

    async def force_edit(self,
                         text: str,
                         del_in: int = -1,
                         log: bool = False,
                         parse_mode: Union[str, object] = object,
                         disable_web_page_preview: Optional[bool] = None,
                         reply_markup: InlineKeyboardMarkup = None,
                         **kwargs) -> Union[BaseMessage, bool]:
        """
        This will first try to message.edit. If it raise MessageAuthorRequired error,
        run message.reply.

        Example:
                message.force_edit(text='force_edit', del_in=3)

        Parameters:
            text (``str``):
                New text of the message.
            del_in (``int``):
                Time in Seconds for delete that message.
            log (``bool``, *optional*):
                If ``True``, the message will be forwarded to the log channel.
            parse_mode (``str``, *optional*):
                By default, texts are parsed using both Markdown and HTML styles.
                You can combine both syntaxes together.
                Pass "markdown" or "md" to enable Markdown-style parsing only.
                Pass "html" to enable HTML-style parsing only.
                Pass None to completely disable style parsing.
            disable_web_page_preview (``bool``, *optional*):
                Disables link previews for links in this message.
            reply_markup (:obj:`InlineKeyboardMarkup`, *optional*):
                An InlineKeyboardMarkup object.
            **kwargs (for message.reply)
        Returns:
            On success, the edited or replied :obj:`Message` or True is returned.
        """

        try:
            return await self.edit(text=text,
                                   del_in=del_in,
                                   log=log,
                                   parse_mode=parse_mode,
                                   disable_web_page_preview=disable_web_page_preview,
                                   reply_markup=reply_markup)

        except MessageAuthorRequired:
            return await self.reply(text=text,
                                    del_in=del_in,
                                    log=log,
                                    parse_mode=parse_mode,
                                    disable_web_page_preview=disable_web_page_preview,
                                    reply_markup=reply_markup,
                                    **kwargs)

    async def err(self,
                  text: str,
                  del_in: int = -1,
                  log: bool = False,
                  parse_mode: Union[str, object] = object,
                  disable_web_page_preview: Optional[bool] = None,
                  reply_markup: InlineKeyboardMarkup = None) -> Union[BaseMessage, bool]:
        """
        You can send error messages using this method

        Example:
                message.err(text='error', del_in=3)

        Parameters:
            text (``str``):
                New text of the message.
            del_in (``int``):
                Time in Seconds for delete that message.
            log (``bool``, *optional*):
                If ``True``, the message will be forwarded to the log channel.
            parse_mode (``str``, *optional*):
                By default, texts are parsed using both Markdown and HTML styles.
                You can combine both syntaxes together.
                Pass "markdown" or "md" to enable Markdown-style parsing only.
                Pass "html" to enable HTML-style parsing only.
                Pass None to completely disable style parsing.
            disable_web_page_preview (``bool``, *optional*):
                Disables link previews for links in this message.
            reply_markup (:obj:`InlineKeyboardMarkup`, *optional*):
                An InlineKeyboardMarkup object.
        Returns:
            On success, the edited :obj:`Message` or True is returned.
        """

        del_in = del_in if del_in > 0 \
            else ERROR_MSG_DELETE_TIMEOUT

        return await self.edit(text=ERROR_STRING.format(text),
                               del_in=del_in,
                               log=log,
                               parse_mode=parse_mode,
                               disable_web_page_preview=disable_web_page_preview,
                               reply_markup=reply_markup)

    async def force_err(self,
                        text: str,
                        del_in: int = -1,
                        log: bool = False,
                        parse_mode: Union[str, object] = object,
                        disable_web_page_preview: Optional[bool] = None,
                        reply_markup: InlineKeyboardMarkup = None,
                        **kwargs) -> Union[BaseMessage, bool]:
        """
        This will first try to message.edit. If it raise MessageAuthorRequired error,
        run message.reply.

        Example:
                message.force_err(text='force_err', del_in=3)

        Parameters:
            text (``str``):
                New text of the message.
            del_in (``int``):
                Time in Seconds for delete that message.
            log (``bool``, *optional*):
                If ``True``, the message will be forwarded to the log channel.
            parse_mode (``str``, *optional*):
                By default, texts are parsed using both Markdown and HTML styles.
                You can combine both syntaxes together.
                Pass "markdown" or "md" to enable Markdown-style parsing only.
                Pass "html" to enable HTML-style parsing only.
                Pass None to completely disable style parsing.
            disable_web_page_preview (``bool``, *optional*):
                Disables link previews for links in this message.
            reply_markup (:obj:`InlineKeyboardMarkup`, *optional*):
                An InlineKeyboardMarkup object.
            **kwargs (for message.reply)
        Returns:
            On success, the edited or replied :obj:`Message` or True is returned.
        """

        del_in = del_in if del_in > 0 \
            else ERROR_MSG_DELETE_TIMEOUT

        return await self.force_edit(text=ERROR_STRING.format(text),
                                     del_in=del_in,
                                     log=log,
                                     parse_mode=parse_mode,
                                     disable_web_page_preview=disable_web_page_preview,
                                     reply_markup=reply_markup,
                                     **kwargs)

    async def try_to_edit(self,
                          text: str,
                          del_in: int = -1,
                          log: bool = False,
                          parse_mode: Union[str, object] = object,
                          disable_web_page_preview: Optional[bool] = None,
                          reply_markup: InlineKeyboardMarkup = None) -> Union[BaseMessage, bool]:

        """
        This will first try to message.edit. If it raise MessageNotModified error,
        just pass it.

        Example:
                message.try_to_edit("hello")

        Parameters:
            text (``str``):
                New text of the message.
            del_in (``int``):
                Time in Seconds for delete that message.
            log (``bool``, *optional*):
                If ``True``, the message will be forwarded to the log channel.
            parse_mode (``str``, *optional*):
                By default, texts are parsed using both Markdown and HTML styles.
                You can combine both syntaxes together.
                Pass "markdown" or "md" to enable Markdown-style parsing only.
                Pass "html" to enable HTML-style parsing only.
                Pass None to completely disable style parsing.
            disable_web_page_preview (``bool``, *optional*):
                Disables link previews for links in this message.
            reply_markup (:obj:`InlineKeyboardMarkup`, *optional*):
                An InlineKeyboardMarkup object.
        Returns:
            On success, the edited :obj:`Message` or True is returned.
        Raises:
            RPCError: In case of a Telegram RPC error.
        """

        try:
            return await self.edit(text=text,
                                   del_in=del_in,
                                   log=log,
                                   parse_mode=parse_mode,
                                   disable_web_page_preview=disable_web_page_preview,
                                   reply_markup=reply_markup)

        except MessageNotModified:
            return False

    async def edit_or_send_as_file(self,
                                   text: str,
                                   del_in: int = -1,
                                   log: bool = False,
                                   parse_mode: Union[str, object] = object,
                                   disable_web_page_preview: Optional[bool] = None,
                                   reply_markup: InlineKeyboardMarkup = None,
                                   **kwargs) -> Union[BaseMessage, bool]:

        """
        This will first try to message.edit. If it raise MessageTooLong error,
        run message.send_as_file.

        Example:
                message.edit_or_send_as_file("some huge text")

        Parameters:
            text (``str``):
                New text of the message.
            del_in (``int``):
                Time in Seconds for delete that message.
            log (``bool``, *optional*):
                If ``True``, the message will be forwarded to the log channel.
            parse_mode (``str``, *optional*):
                By default, texts are parsed using both Markdown and HTML styles.
                You can combine both syntaxes together.
                Pass "markdown" or "md" to enable Markdown-style parsing only.
                Pass "html" to enable HTML-style parsing only.
                Pass None to completely disable style parsing.
            disable_web_page_preview (``bool``, *optional*):
                Disables link previews for links in this message.
            reply_markup (:obj:`InlineKeyboardMarkup`, *optional*):
                An InlineKeyboardMarkup object.
            **kwargs (for message.send_as_file)
        Returns:
            On success, the edited :obj:`Message` or True is returned.
        Raises:
            RPCError: In case of a Telegram RPC error.
        """

        try:
            return await self.edit(text=text,
                                   del_in=del_in,
                                   log=log,
                                   parse_mode=parse_mode,
                                   disable_web_page_preview=disable_web_page_preview,
                                   reply_markup=reply_markup)

        except MessageTooLong:
            return await self.send_as_file(text=text, log=log, **kwargs)

    async def reply_or_send_as_file(self,
                                    text: str,
                                    del_in: int = -1,
                                    log: bool = False,
                                    quote: Optional[bool] = None,
                                    parse_mode: Union[str, object] = object,
                                    disable_web_page_preview: Optional[bool] = None,
                                    disable_notification: Optional[bool] = None,
                                    reply_to_message_id: Optional[int] = None,
                                    reply_markup: InlineKeyboardMarkup = None,
                                    **kwargs) -> Union[BaseMessage, bool]:

        """
        This will first try to message.reply. If it raise MessageTooLong error,
        run message.send_as_file.

        Example:
                message.reply_or_send_as_file("some huge text")

        Parameters:
            text (``str``):
                Text of the message to be sent.
            del_in (``int``):
                Time in Seconds for delete that message.
            log (``bool``, *optional*):
                If ``True``, the message will be forwarded to the log channel.
            quote (``bool``, *optional*):
                If ``True``, the message will be sent as a reply to this message.
                If *reply_to_message_id* is passed, this parameter will be ignored.
                Defaults to ``True`` in group chats and ``False`` in private chats.
            parse_mode (``str``, *optional*):
                By default, texts are parsed using both Markdown and HTML styles.
                You can combine both syntaxes together.
                Pass "markdown" or "md" to enable Markdown-style parsing only.
                Pass "html" to enable HTML-style parsing only.
                Pass None to completely disable style parsing.
            disable_web_page_preview (``bool``, *optional*):
                Disables link previews for links in this message.
            disable_notification (``bool``, *optional*):
                Sends the message silently.
                Users will receive a notification with no sound.
            reply_to_message_id (``int``, *optional*):
                If the message is a reply, ID of the original message.
            reply_markup (:obj:`InlineKeyboardMarkup` | :obj:`ReplyKeyboardMarkup` | :obj:`ReplyKeyboardRemove` | :obj:`ForceReply`, *optional*):
                Additional interface options. An object for an inline keyboard, custom reply keyboard,
                instructions to remove reply keyboard or to force a reply from the user.
            **kwargs (for message.send_as_file)
        Returns:
            On success, the sent Message or True is returned.
        Raises:
            RPCError: In case of a Telegram RPC error.
        """

        try:
            return await self.reply(text=text,
                                    del_in=del_in,
                                    log=log,
                                    quote=quote,
                                    parse_mode=parse_mode,
                                    disable_web_page_preview=disable_web_page_preview,
                                    disable_notification=disable_notification,
                                    reply_to_message_id=reply_to_message_id,
                                    reply_markup=reply_markup)

        except MessageTooLong:
            return await self.send_as_file(text=text, log=log, **kwargs)

    async def force_edit_or_send_as_file(self,
                                         text: str,
                                         del_in: int = -1,
                                         log: bool = False,
                                         parse_mode: Union[str, object] = object,
                                         disable_web_page_preview: Optional[bool] = None,
                                         reply_markup: InlineKeyboardMarkup = None,
                                         **kwargs) -> Union[BaseMessage, bool]:

        """
        This will first try to message.edit_or_send_as_file. If it raise MessageAuthorRequired error,
        run message.reply_or_send_as_file.

        Example:
                message.force_edit_or_send_as_file("some huge text")

        Parameters:
            text (``str``):
                New text of the message.
            del_in (``int``):
                Time in Seconds for delete that message.
            log (``bool``, *optional*):
                If ``True``, the message will be forwarded to the log channel.
            parse_mode (``str``, *optional*):
                By default, texts are parsed using both Markdown and HTML styles.
                You can combine both syntaxes together.
                Pass "markdown" or "md" to enable Markdown-style parsing only.
                Pass "html" to enable HTML-style parsing only.
                Pass None to completely disable style parsing.
            disable_web_page_preview (``bool``, *optional*):
                Disables link previews for links in this message.
            reply_markup (:obj:`InlineKeyboardMarkup`, *optional*):
                An InlineKeyboardMarkup object.
            **kwargs (for message.reply and message.send_as_file)
        Returns:
            On success, the edited or replied :obj:`Message` or True is returned.
        """

        try:
            return await self.edit_or_send_as_file(text=text,
                                                   del_in=del_in,
                                                   log=log,
                                                   parse_mode=parse_mode,
                                                   disable_web_page_preview=disable_web_page_preview,
                                                   reply_markup=reply_markup,
                                                   **kwargs)

        except MessageAuthorRequired:
            return await self.reply_or_send_as_file(text=text,
                                                    del_in=del_in,
                                                    log=log,
                                                    parse_mode=parse_mode,
                                                    disable_web_page_preview=disable_web_page_preview,
                                                    reply_markup=reply_markup,
                                                    **kwargs)
