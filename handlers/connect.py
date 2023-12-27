from aiogram import types
from aiogram.filters.command import Command
from aiogram.filters import Text
import db_requests
from aiogram.utils.keyboard import InlineKeyboardBuilder
from modules.client import Client
from aiogram import F, Router
from aiogram.filters.chat_member_updated import MEMBER, KICKED


router = Router()


@router.message(Command('connect'))
@router.callback_query(Text('connect'))
async def connect(callback: types.CallbackQuery):
    if not hasattr(callback, 'message') and not db_requests.is_registered(callback.from_user.id):
        await callback.answer('Кажется вы не зарегистрировались 🤨\n\n'
                                 'Попросите вашего друга, который вам рекомендовал бота, прислать вам ссылку-приглашение.\n'
                                 'Он сможет её найти в своём профиле в меню бота.', reply_markup='')
        return
    client = Client(callback.from_user.id)
    builder = InlineKeyboardBuilder()
    builder.button(text='📲 Установить приложение', url='https://ramdat.net/app_redirect')
    #builder.button(text='Установить Streisand', url='https://apps.apple.com/ru/app/streisand/id6450534064')
    #builder.button(text='Установить v2rayNG', url='https://play.google.com/store/apps/details?id=com.v2ray.ang&hl=ru')
    builder.button(text='🚀 Загрузить список серверов', url=f'https://ramdat.net/sub_redirect/{client.user_telegram_id}')
    builder.button(text='🔙 Назад', callback_data='menu')
    builder.adjust(1)
    '''message_text = ('Перед подключением убедитесь что вы установили нужное приложение:\n'
                    '<b>FoXray</b> для iOS\n'
                    '<b>v2rayNG</b> для Android')'''
    message_text = ('➊ Скачиваете приложение\n\n'
                    '➋ Загружаете список серверов\n\n'
                    '➌ В приложении подключаетесь к любому серверу')
    if hasattr(callback, 'message'):
        await callback.message.edit_text(message_text, reply_markup=builder.as_markup())
    else:
        await callback.answer(message_text, reply_markup=builder.as_markup())

