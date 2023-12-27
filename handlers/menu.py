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


router = Router()

@router.message(Command('menu'))
async def menu(message: types.Message, callback: types.CallbackQuery=False, answer=False):
    if message.from_user.id in config.admins:
        user = Client(message.from_user.id)
    elif callback:
        user = Client(callback.from_user.id)

    phrases = ['С чего начнём? 🙂', 'Рад вас видеть 😌', 'Выберите пункт меню 🙂', 'Я надеюсь у вас сегодня прекрасный день! 😊',
               'Вы сегодня отлично выглядите! 😍', 'Пусть сегодня вас ждёт приятный сюприз 🤗']
    if callback:
        if not db_requests.is_registered(callback.from_user.id):
            await message.answer('Кажется вы не зарегистрировались 🤨\n\n'
                                 'Попросите вашего друга, который вам рекомендовал бота, прислать вам ссылку-приглашение.\n'
                                 'Он сможет её найти в своём профиле в меню бота.')
            return
    elif not db_requests.is_registered(message.from_user.id):
        await message.answer('Кажется вы не зарегистрировались 🤨\n\n'
                                 'Попросите вашего друга, который вам рекомендовал бота, прислать вам ссылку-приглашение.\n'
                                 'Он сможет её найти в своём профиле в меню бота.', reply_markup='')
        return

    builder = InlineKeyboardBuilder()
    builder.button(text='👤 Профиль', callback_data='profile')
    builder.button(text='📲 Скачать приложение', callback_data='get_app')
    builder.button(text='🔑 Подключиться', callback_data='connect')
    #builder.button(text='🔑 Получить ключ', callback_data='keys_and_configs')
    #builder.button(text='⚙️ Как настроить?', callback_data='setup')
    builder.button(text='🤝 Ссылка-приглашение', callback_data='invite_link')
    builder.button(text='🆘 У меня проблема!', callback_data='help')
    
    if message.from_user.id in config.admins:
        builder.button(text='🥷🏼 Admin menu', callback_data='admin_menu')
    elif callback:
        if callback.from_user.id in config.admins:
            builder.button(text='🥷🏼 Admin menu', callback_data='admin_menu')

    builder.adjust(1)
    message_text = 'Выберите пункт меню.'
    if not callback:
        #await message.answer(phrases[random.randint(0, len(phrases) - 1)], reply_markup=builder.as_markup())
        await message.answer(message_text, reply_markup=builder.as_markup())
    else:
        if answer:
            await message.answer(message_text, reply_markup=builder.as_markup())
        else:
            await message.edit_text(message_text, reply_markup=builder.as_markup())


@router.callback_query(Text('menu'))
async def menu_callback(callback: types.CallbackQuery):
    await menu(callback.message, callback=callback)


@router.message(Command('setup'))
@router.callback_query(Text('setup'))
async def setup(callback: types.CallbackQuery):
    if not hasattr(callback, 'message') and not db_requests.is_registered(callback.from_user.id):
        await callback.answer('Кажется вы не зарегистрировались 🤨\n\n'
                                 'Попросите вашего друга, который вам рекомендовал бота, прислать вам ссылку-приглашение.\n'
                                 'Он сможет её найти в своём профиле в меню бота.', reply_markup='')
        return
    message_text = ('Выберите приложение для получения инструкции.\n\n'
                    '<b>Outline</b> - Для подключения по протоколу Shadowsocks\n\n'
                    '<b>FoXray/v2rayNG</b> - Для подключения по протоколу vless/XTLS-Reality')
    builder = InlineKeyboardBuilder()
    builder.button(text='Outline', url='https://telegra.ph/Nastrojka-Outline-10-28')
    builder.button(text='FoXray (iOS)', url='https://telegra.ph/Nastrojka-FoXray-10-28')
    builder.button(text='v2rayNG (Android)', url='https://telegra.ph/Nastrojka-v2rayNG-10-28')
    builder.button(text='🔙 Назад', callback_data='menu')
    builder.adjust(1)
    
    if hasattr(callback, 'message'):
        await callback.message.edit_text(message_text, reply_markup=builder.as_markup())
    else:
        await callback.answer(message_text, reply_markup=builder.as_markup())


@router.message(Command('get_app'))
@router.callback_query(Text('get_app'))
async def get_app(callback: types.CallbackQuery):
    if not hasattr(callback, 'message') and not db_requests.is_registered(callback.from_user.id):
        await callback.answer('Кажется вы не зарегистрировались 🤨\n\n'
                                 'Попросите вашего друга, который вам рекомендовал бота, прислать вам ссылку-приглашение.\n'
                                 'Он сможет её найти в своём профиле в меню бота.', reply_markup='')
        return
    message_text = ('Я рекомендую для iOS использовать Streisand, а для Android - v2rayNG.\n\n'
                    'Также скоро будут доступны ссылки на альтернативные клиенты.')
    builder = InlineKeyboardBuilder()
    builder.button(text='📲 Установить рекомендуемое приложение', url='https://ramdat.net/app_redirect')
    #builder.button(text='Установить Streisand', url='https://apps.apple.com/ru/app/streisand/id6450534064')
    #builder.button(text='Установить v2rayNG', url='https://play.google.com/store/apps/details?id=com.v2ray.ang&hl=ru')
    builder.button(text='🔙 Назад', callback_data='menu')
    builder.adjust(1)
    
    if hasattr(callback, 'message'):
        await callback.message.edit_text(message_text, reply_markup=builder.as_markup())
    else:
        await callback.answer(message_text, reply_markup=builder.as_markup())


@router.callback_query(Text('get_outline_app'))
async def get_outline_app(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.button(text='🍏 Outline для IOS', url='https://apps.apple.com/ru/app/outline-app/id1356177741')
    builder.button(text='🤖 Outline для Android', url='https://play.google.com/store/apps/details?id=org.outline.android.client&hl=ru&gl=US')
    builder.button(text='💻 Outline для Windows', url='https://raw.githubusercontent.com/Jigsaw-Code/outline-releases/master/client/stable/Outline-Client.exe')
    builder.button(text='🔙 Назад', callback_data='get_app')
    builder.adjust(1)
    await callback.message.edit_text('Выберите свою операционную систему:', reply_markup=builder.as_markup())


@router.callback_query(Text('get_xray_app'))
async def get_outline_app(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.button(text='🍏 FoXray для IOS', url='https://apps.apple.com/us/app/foxray/id6448898396')
    builder.button(text='🤖 v2rayNG для Android', url='https://play.google.com/store/apps/details?id=com.v2ray.ang&hl=ru&gl=US')
    builder.button(text='🔙 Назад', callback_data='get_app')
    builder.adjust(1)
    await callback.message.edit_text('Выберите свою операционную систему:', reply_markup=builder.as_markup())