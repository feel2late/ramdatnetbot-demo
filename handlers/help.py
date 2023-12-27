from aiogram import types
from aiogram.filters.command import Command, CommandObject
from aiogram.filters import Text
import db_requests
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot_init import bot
from aiogram import F, Router
from aiogram.filters.chat_member_updated import MEMBER, KICKED


router = Router()


@router.message(Command('help'))
@router.callback_query(Text('help'))
async def help(callback: types.CallbackQuery):
    if not hasattr(callback, 'message') and not db_requests.is_registered(callback.from_user.id):
        await callback.answer('Кажется вы не зарегистрировались 🤨\n\n'
                                 'Попросите вашего друга, который вам рекомендовал бота, прислать вам ссылку-приглашение.\n'
                                 'Он сможет её найти в своём профиле в меню бота.', reply_markup='')
        return
    message_text = ''
    builder = InlineKeyboardBuilder()
    builder.button(text='⚙️ Статус серверов', callback_data='health_status')
    builder.button(text='🔙 Назад в меню', callback_data='menu')
    builder.adjust(1)
    if hasattr(callback, 'message'):
        await callback.message.edit_text(message_text, reply_markup=builder.as_markup())
    else:
        await callback.answer(message_text, reply_markup=builder.as_markup())


@router.callback_query(Text('help_screenshot'))
async def help(callback: types.CallbackQuery):
    message_text = ('✅ Ваш скриншот отправлен администратору.\n\nПожалуйста, ожидайте, ответа.')
    await bot.send_message(376131047, f'Пользователь с id {callback.from_user.id} ({callback.from_user.username} / {callback.from_user.full_name}) нуждается в помощи по скриншоту.')
    builder = InlineKeyboardBuilder()
    builder.button(text='🔙 Назад в меню', callback_data='menu')
    builder.adjust(1)
    await callback.message.edit_text(message_text, reply_markup=builder.as_markup())

