import asyncio
import datetime
import logging
import random
import time
import traceback
import uuid
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command, CommandObject
from aiogram.filters import StateFilter, Text
from glQiwiApi import QiwiP2PClient
import config
import aioschedule
import db_requests
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot_init import bot
from modules.client import Client
import models
import api_requests
from aiogram.enums.content_type import ContentType
from aiogram import F, Router
from modules.states import ManualControl, ChatWithUser, SendMessageToAllUsers
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters.chat_member_updated import \
    ChatMemberUpdatedFilter, MEMBER, KICKED
from modules.callbacks_factories import RestoreShutdownDate
import modules.check_servers_status as check_servers_status
import modules.control_v2ray as control_v2ray
from yookassa import Payment
from modules.uri_encode import uri_encode
from gifs_id import gifs_id
from cryptography.fernet import Fernet
import base64


router = Router()

def encrypt_data(data, key):
    cipher_suite = Fernet(key)
    encrypted_data = cipher_suite.encrypt(data.encode())
    return base64.urlsafe_b64encode(encrypted_data).decode()

@router.callback_query(Text('generate_register_link_in_web_panel'))
async def generate_register_link_in_web_panel(callback: types.CallbackQuery):
    user = Client(callback.from_user.id)
    base_link = 'https://ramdat.net/register/?registration_hash='
    message_text = 'Для вас сгенерирована индивидуальная ссылка для регистрации.\n\n⚠️ Пожалуйста, никому не передавайте эту ссылку, иначе доступ к вашему аккаунту будет утерян.'
    hash = encrypt_data(str(user.user_telegram_id)+':'+config.SECRET_REGISTRATION_PHRASE, config.SECRET_REGISTRATION_KEY)
    builder = InlineKeyboardBuilder()
    builder.button(text='Зарегистрироваться на сайте', url=base_link+hash)
    builder.button(text='🔙 Назад', callback_data='menu')
    builder.adjust(1)
    await callback.message.edit_text(message_text, reply_markup=builder.as_markup())