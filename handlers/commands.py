import asyncio
import datetime
import traceback
from aiogram import types
from aiogram.filters.command import Command, CommandObject
from aiogram.filters import StateFilter
import config
import db_requests
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot_init import bot
from modules.client import Client
import models
from aiogram import F, Router
from modules.states import ChatWithUser
from aiogram.fsm.context import FSMContext
from aiogram.filters.chat_member_updated import MEMBER, KICKED
from modules.callbacks_factories import RestoreShutdownDate


router = Router()


@router.message(Command('my_id'))
async def get_chat_id(message: types.Message):
    await message.answer(f'You telegram id: {message.from_user.id}')


@router.message(Command('check_who_banned_bot'))
async def test(message: types.Message):
    if message.from_user.id not in config.admins:
        return
    blocked = 0
    not_blocked = 0
    
    users = await db_requests.get_all_users()
    await message.answer(f'Проверяю, кто забанил бота...\n\nКоличество пользователей: {len(users)}\nПроверка займёт примерно {len(users) / 10} секунд.')

    for user in users:
        await asyncio.sleep(0.1)
        try:
            await bot.send_chat_action(user.user_telegram_id, 'typing')
            await db_requests.update_flag_blocked_bot(user.user_telegram_id, False)
            not_blocked += 1
        except:
            await db_requests.update_flag_blocked_bot(user.user_telegram_id, True)
            blocked += 1

    await message.answer(f'Закончил проверку.\n\nИтого:\nЗаблокировало: {blocked}\nНе заблокировало: {not_blocked}')


@router.message(Command("aavoevodin"))
async def answer_to_client(message: types.Message, command: CommandObject):
    if not db_requests.is_registered(message.from_user.id):
        await message.answer('Надо бы сначала зарегистрироваться.')
    else:
        client = Client(message.from_user.id)
        new_shutdown_date = await db_requests.add_days(client.user_telegram_id)
        
        payment_id = await db_requests.add_payment(client.user_telegram_id, client.tariff, 'voevodin')
        
        await bot.send_animation(message.from_user.id, animation='CgACAgQAAxkBAAKNR2T3VJ6efs_pNWYPNs00IFTNcxKrAAL6mwACIR5kBzwyVWBqHgUVMAQ')
        await message.answer(('Вы использовали волшебную команду, я добавил вам месяц бесплатно!\n\n'
                              f'Дата следующей оплаты: до {datetime.datetime.strftime(datetime.datetime.strptime(new_shutdown_date, "%Y-%m-%d %H:%M:%S") + datetime.timedelta(hours=int(client.timezone)), "%H:%M %d.%m.%Y")} (UTC+{client.timezone})\n\n'))
        builder = InlineKeyboardBuilder()
        builder.button(text='Откатить транзакцию', callback_data=RestoreShutdownDate(user_telegram_id=client.user_telegram_id, date=int(datetime.datetime.timestamp(datetime.datetime.strptime(client.shutdown_date, "%Y-%m-%d %H:%M:%S"))), payment_id=payment_id))
        await bot.send_message(376131047, f'Пользователь с id {message.from_user.id} ({message.from_user.username} / {message.from_user.full_name}) использовал волшебную команду "aavoevodin"', reply_markup=builder.as_markup())
        

@router.message(Command("a"))
async def answer_to_client(message: types.Message, command: CommandObject):
    admin_message: str = command.args

    try:
        recipient_telegram_id = message.reply_to_message.forward_from.id
        await bot.send_message(recipient_telegram_id, admin_message)
    except:
        await message.reply('Не получилось отправить сообщение')
        await message.reply(traceback.format_exc())
        return


@router.message(Command("user_id"))
async def get_user_id_from_forward_message(message: types.Message, command: CommandObject):
    try:
        recipient_telegram_id = message.reply_to_message.forward_from.id
        await message.answer(recipient_telegram_id)
    except:
        await message.reply('Не получилось достать id')
        await message.reply(traceback.format_exc())
        return


@router.message(Command("ban_user"))
async def answer_to_client(message: types.Message, command: CommandObject):
    admin_message: int = command.args

    if admin_message and admin_message.isnumeric():
        client: models.Access = await db_requests.get_client(admin_message)
        unban_user = await db_requests.ban_client(admin_message, client.user_name)
        if unban_user:
            await message.answer(f'Пользователь {admin_message} забанен')
        else:
            await message.answer(f'Пользователя {admin_message} уже был забанен')
        return

    try:
        user_telegram_id = message.reply_to_message.forward_from.id
        user_name = message.reply_to_message.forward_from.full_name
        ban_user = await db_requests.ban_client(user_telegram_id, user_name)
        if ban_user:
            await message.answer(f'Пользователь {user_name} / {user_telegram_id} забанен')
        else:
            await message.answer(f'Пользователь {user_name} / {user_telegram_id} уже был забанен')
    except:
        await message.reply('Не получилось забанить пользователя')
        await message.reply(traceback.format_exc())
        

@router.message(Command("unban_user"))
async def answer_to_client(message: types.Message, command: CommandObject):
    admin_message: int = command.args

    if admin_message and admin_message.isnumeric():
        unban_user = await db_requests.unban_client(admin_message)
        if unban_user:
            await message.answer(f'Пользователь {admin_message} разбанен')
        else:
            await message.answer(f'Пользователя {admin_message} нет в списке забаненных')
        return
    
    try:
        user_telegram_id = message.reply_to_message.forward_from.id
        unban_user = await db_requests.unban_client(user_telegram_id)
        if unban_user:
            await message.answer(f'Пользователь {user_telegram_id} разбанен')
        else:
            await message.answer(f'Пользователя {user_telegram_id} нет в списке забаненных')
    except:
        await message.reply('Не получилось разбанить пользователя')
        await message.reply(traceback.format_exc())


@router.message(Command("start_chat"))
async def answer_to_client(message: types.Message, command: CommandObject, state: FSMContext):
    user_telegram_id: int = command.args
    if message.from_user.id in config.admins:
        await state.set_state(ChatWithUser.active_chat)
        await state.update_data(user_telegram_id=user_telegram_id)
        await message.answer('Чат с пользователем начат. Для завершения пришли команду /stop_chat')


@router.message(Command("stop_chat"), StateFilter(ChatWithUser.active_chat))
async def stop_chat_with_user(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer('Чат с пользователем закрыт')


@router.message(StateFilter(ChatWithUser.active_chat))
async def active_chat(message: types.Message, state: FSMContext):
    message_for_user = message.text
    fsmdata = await state.get_data()
    user_telegram_id = fsmdata.get('user_telegram_id')
    try:
        await bot.send_message(user_telegram_id, message_for_user)
    except:
        await message.answer('Ошибка отправки сообщения пользователю')


@router.message()
async def anyone_message(message: types.Message):
    if message.from_user.id in config.admins:
        if message.reply_to_message:
            try:
                recipient_telegram_id = message.reply_to_message.forward_from.id
                await bot.send_message(recipient_telegram_id, message.text)
            except:
                await bot.send_message(1342357584, f'Клиент скрыл свой аккаунт при пересылке сообщений.\nНачните свой ответ ему с текста <code>/send_message</code> user_telegram_id <u>ваш текст</u>')
    else:
        registered = db_requests.is_registered(message.from_user.id)
        if registered:
            client = Client(message.from_user.id)
            if not client.chat_with_admin:
                builder = InlineKeyboardBuilder()
                builder.button(text='🆘 Помощь', callback_data='help')
                await message.answer('Ваше сообщение было отправлено администратору.\nВремя работы с 09:00 до 18:00 МСК (UTC+3).\n\nПожалуйста, ожидайте ответа.\n\n'
                                    '<b>Может быть ответ на ваш вопрос есть в разделе помощь?</b>', reply_markup=builder.as_markup())
                await db_requests.set_status_chat_with_admin(message.from_user.id, True)
                await bot.send_message(376131047, f'Пользователь с /view_user_{client.user_telegram_id} написал:')

        else:
            await message.answer('⛔️ Регистрация в сервисе только по приглашениям.\n\n'
                                        'Попросите вашего друга, который вам рекомендовал бота, прислать вам ссылку-приглашение.\n'
                                        'Он сможет её найти в меню бота.')
            await bot.send_message(376131047, 'Незарегистрированный пользователь написал.')

        await bot.forward_message(376131047, message.chat.id, message.message_id)