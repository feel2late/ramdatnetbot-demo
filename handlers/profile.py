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
from middlewares.outer import CheckForUserBan, CheckForUserBanCallback


router = Router()


@router.message(Command('profile'))
@router.callback_query(Text('profile'))
async def profile(callback: types.CallbackQuery):
    if not hasattr(callback, 'message') and not db_requests.is_registered(callback.from_user.id):
        await callback.answer('Кажется вы не зарегистрировались 🤨\n\n'
                                 'Попросите вашего друга, который вам рекомендовал бота, прислать вам ссылку-приглашение.\n'
                                 'Он сможет её найти в своём профиле в меню бота.', reply_markup='')
        return
    client: models.Access = await db_requests.get_client(callback.from_user.id)
    message_text = (f'🔐 Доступ: {"разрешён ✅" if not client.blocked else "запрещён ❌"}\n\n'
                    f'📅 Доступ до: {datetime.datetime.strftime(datetime.datetime.strptime(client.shutdown_date, "%Y-%m-%d %H:%M:%S") + datetime.timedelta(hours=int(client.timezone)), "%H:%M %d.%m.%Y")} (UTC+{client.timezone})\n\n'
                    f'💰 Стоимость: {client.tariff} р.\n\n'
                    f'{"❗️ Использован доверительный платёж" if client.postpone_payment else ""}')
    
    builder = InlineKeyboardBuilder()
    builder.button(text='💳 Оплатить', callback_data='payment_by_card')
    builder.button(text='⏳ Доверительный платёж', callback_data='postpone_payment')
    builder.button(text='🌎 Часовой пояс', callback_data='timezone')
    if client.notifications:
        builder.button(text='🟢 Уведомления включены', callback_data=f'change_notification_status_{client.id}')
    else:
        builder.button(text='🔘 Уведомления выключены', callback_data=f'change_notification_status_{client.id}')
    builder.button(text='🔙 Назад', callback_data='menu')
    builder.adjust(1)

    if hasattr(callback, 'message'):
        await callback.message.edit_text(message_text, reply_markup=builder.as_markup())
    else:
        await callback.answer(message_text, reply_markup=builder.as_markup())


@router.callback_query(Text('payment_by_card'))
async def payment_by_card(callback: types.CallbackQuery):
    client = Client(callback.from_user.id)
    month_to_discount = {'1': 0, '3': 10, '6': 20}
    decrease_amount_3_month = (month_to_discount['3'] / 100) * (client.tariff * int('3'))
    decrease_amount_6_month = (month_to_discount['6'] / 100) * (client.tariff * int('6'))
    amount_value_3_month = client.tariff * 3 - decrease_amount_3_month
    amount_value_6_month = client.tariff * 6 - decrease_amount_6_month
    message_text = ('Выберите период оплаты.\n\n'
                    'Больше период - больше скидка.\n\n'
                    f'<b>3 месяца</b> - {amount_value_3_month} р. (-10%)\n'
                    f'<b>6 месяцев</b> - {amount_value_6_month} р. (-20%)')
    builder = InlineKeyboardBuilder()
    builder.button(text='🙂 1 месяц', callback_data='payment_by_card_1')
    builder.button(text='😀 3 месяца', callback_data='payment_by_card_3')
    builder.button(text='🤩 6 месяцев', callback_data='payment_by_card_6')
    builder.button(text='🔙 Назад', callback_data='profile')
    builder.adjust(1)
    await callback.message.edit_text(message_text, reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith('change_notification_status_from_not_'))
async def change_notification_status(callback: types.CallbackQuery):
    client_id = callback.data[36:]
    notification_status = await db_requests.change_notification_status(client_id)
    if not notification_status:
        await callback.answer('Выключены все уведомления, кроме уведомлений оплаты.', show_alert=True)
    client = Client(callback.from_user.id)
    builder = InlineKeyboardBuilder()
    if client.notifications:
        builder.button(text='🟢 Уведомления включены', callback_data=f'change_notification_status_from_not_{client.id}')
    else:
        builder.button(text='🔘 Уведомления выключены', callback_data=f'change_notification_status_from_not_{client.id}')
    await callback.message.edit_reply_markup(reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith('change_notification_status_'))
async def change_notification_status(callback: types.CallbackQuery):
    client_id = callback.data[27:]
    notification_status = await db_requests.change_notification_status(client_id)
    if not notification_status:
        await callback.answer('Выключены все уведомления, кроме уведомлений оплаты.', show_alert=True)
    client = Client(callback.from_user.id)
    message_text = (f'🔐 Доступ: {"разрешён ✅" if not client.blocked else "запрещён ❌"}\n\n'
                    f'📅 Доступ до: {datetime.datetime.strftime(datetime.datetime.strptime(client.shutdown_date, "%Y-%m-%d %H:%M:%S") + datetime.timedelta(hours=int(client.timezone)), "%H:%M %d.%m.%Y")} (UTC+{client.timezone})\n\n'
                    f'💰 Стоимость: {client.tariff} р.\n\n'
                    f'{"❗️ Использован доверительный платёж" if client.postpone_payment else ""}')
    
    builder = InlineKeyboardBuilder()
    builder.button(text='💳 Оплатить', callback_data='payment_by_card')
    builder.button(text='⏳ Доверительный платёж', callback_data='postpone_payment')
    builder.button(text='🌎 Часовой пояс', callback_data='timezone')
    if client.notifications:
        builder.button(text='🟢 Уведомления включены', callback_data=f'change_notification_status_{client.id}')
    else:
        builder.button(text='🔘 Уведомления выключены', callback_data=f'change_notification_status_{client.id}')
    builder.button(text='🔙 Назад', callback_data='menu')
    builder.adjust(1)
    await callback.message.edit_text(message_text, reply_markup=builder.as_markup())


@router.callback_query(Text('postpone_payment'))
async def postpone_payment(callback: types.CallbackQuery):
    client = Client(callback.from_user.id)
    if client.postpone_payment:
        await callback.answer('😕 Вы уже активировали услугу "Доверительный платёж".', show_alert=True)
        return
    
    builder = InlineKeyboardBuilder()
    builder.button(text='✅ Активировать', callback_data='activate_postponed_pay')
    builder.button(text='🔙 Назад в профиль', callback_data='profile')
    builder.adjust(1)
    message_text = ('Услуга "Доверительный платёж" бесплатно добавит 3 дня пользования сервисом.\n\n'
                    'При последующей оплате эти дни будут учтены.')
    
    await callback.message.edit_text(message_text, reply_markup=builder.as_markup())


@router.callback_query(Text('activate_postponed_pay'))
async def activate_postponed_pay(callback: types.CallbackQuery):
    client = Client(callback.from_user.id)
    builder = InlineKeyboardBuilder()
    builder.button(text='🔙 Назад в профиль', callback_data='profile')

    await client.unblock()
    postpone_payment_date = await db_requests.add_postpone_payment_days(client.user_telegram_id)

    message_text = (f'✅ Услуга "Доверительный платёж" успешно активирована.\n\n'
                    f'Вам необходимо оплатить доступ до {datetime.datetime.strftime(datetime.datetime.strptime(postpone_payment_date, "%Y-%m-%d %H:%M:%S") + datetime.timedelta(hours=int(client.timezone)), "%H:%M:%S %d.%m.%Y")} (UTC+{client.timezone})')

    await callback.message.edit_text(message_text, reply_markup=builder.as_markup())
    await bot.send_message(config.admins[0], f'Пользователь {client.user_name} <code>({client.user_telegram_id})</code> воспользовался доверительным платежом.')


@router.message(Command('invite_link'))
@router.callback_query(Text('invite_link'))
async def invite_link(callback: types.CallbackQuery):
    if not hasattr(callback, 'message') and not db_requests.is_registered(callback.from_user.id):
        await callback.answer('Кажется вы не зарегистрировались 🤨\n\n'
                                 'Попросите вашего друга, который вам рекомендовал бота, прислать вам ссылку-приглашение.\n'
                                 'Он сможет её найти в своём профиле в меню бота.', reply_markup='')
        return
    client = Client(callback.from_user.id)
    invite_url = f'https://t.me/RAMDATNET_BOT?start={client.invite_code}'
    message_text = ('Ваша индивидуальная ссылка-приглашение для ваших друзей:\n'
                    f'{invite_url}\n\n'
                    '⚠️ Регистрация в сервисе доступна только по приглашению действующего участника.\n\n'
                    '✅ Ваш друг, зарегистрировашись по вашей ссылке, получит месяц бесплатного доступа к сервису.\n'
                    '✅ Вы - месяц бесплатно, когда он впервые оплатит доступ и по 3 дня бесплатно <b>каждый раз</b>, когда он будет оплачивать подписку.\n\n'
                    f'{"Вы пока никого не пригласили 😔" if client.number_of_invitees == 0 else f"🥳 Вы пригласили {client.number_of_invitees} друзей!" }')

    builder = InlineKeyboardBuilder()
    builder.button(text='⤴️ Отправить другу', url=f'https://t.me/share/url?url={invite_url}')
    #builder.button(text='🔙 Назад в профиль', callback_data='profile')
    builder.button(text='🔙 Назад в меню', callback_data='menu')
    builder.adjust(1)

    if hasattr(callback, 'message'):
        await callback.message.edit_text(message_text, reply_markup=builder.as_markup())
    else:
        await callback.answer(message_text, reply_markup=builder.as_markup())


@router.callback_query(Text('timezone'))
async def timezone(callback: types.CallbackQuery):
    client = Client(callback.from_user.id)

    message_text = (f'⚠️ Для вас установлен часовой пояс UTC+{client.timezone}\n\n'
                    'Установка часового пояса позволит получать уведомления вовремя, а в ночное время получать их без звука.\n\n'
                    'Вы можете установить новый.')
    
    builder = InlineKeyboardBuilder()
    builder.button(text='UTC+2', callback_data=f'set_timezone_2')
    builder.button(text='UTC+3', callback_data=f'set_timezone_3')
    builder.button(text='UTC+4', callback_data=f'set_timezone_4')
    builder.button(text='UTC+5', callback_data=f'set_timezone_5')
    builder.button(text='UTC+6', callback_data=f'set_timezone_6')
    builder.button(text='UTC+7', callback_data=f'set_timezone_7')
    builder.button(text='UTC+8', callback_data=f'set_timezone_8')
    builder.button(text='UTC+9', callback_data=f'set_timezone_9')
    builder.button(text='UTC+10', callback_data=f'set_timezone_10')
    builder.button(text='UTC+11', callback_data=f'set_timezone_11')
    builder.button(text='UTC+12', callback_data=f'set_timezone_12')
    builder.button(text='🔙 Назад в профиль', callback_data='profile')
    builder.adjust(3, 3, 3, 2, 1)
    await callback.message.edit_text(message_text, reply_markup=builder.as_markup())


@router.callback_query(Text(contains='set_timezone_'))
async def set_timezone(callback: types.CallbackQuery):
    timezone = int(callback.data[13:])
    await db_requests.set_timezone(callback.from_user.id, timezone)

    builder = InlineKeyboardBuilder()
    builder.button(text='🔙 Назад в профиль', callback_data='profile')
    await callback.message.edit_text(f'✅ Для вас установлен часовой пояс UTC+{timezone}\n\nТеперь все уведомления будут приходить учитывая ваше локальное время.', reply_markup=builder.as_markup())
