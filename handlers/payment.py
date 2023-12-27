import datetime
import random
import uuid
from aiogram import types
from aiogram.filters import Text
import db_requests
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot_init import bot
from modules.client import Client
from aiogram import F, Router
from aiogram.filters.chat_member_updated import MEMBER, KICKED
from modules.callbacks_factories import RestoreShutdownDate
from yookassa import Payment
from gifs_id import gifs_id


router = Router()


@router.message(F.photo)
async def confirmation_photo_(message: types.Message):
    builder = InlineKeyboardBuilder()
    print(message.photo[-1].file_id)
    chat_info = await bot.get_chat(message.from_user.id)
    if not chat_info.has_private_forwards:
        builder.button(text='Ссылка на пользователя', url=f'tg://user?id={message.from_user.id}')
    #await bot.send_message(376131047, f'Пользователь с id {message.from_user.id} ({message.from_user.full_name}) прислал фото', reply_markup=builder.as_markup())
    await bot.forward_message(376131047, message.chat.id, message.message_id)
    builder = InlineKeyboardBuilder()
    builder.button(text='🆘 Нет, мне нужна помощь', callback_data='help_screenshot')
    builder.button(text='✅ Да, разблокировать доступ', callback_data='confirm_payment')
    builder.adjust(1)
    await message.answer("Это скриншот с подтверждением оплаты?", reply_markup=builder.as_markup())
    

@router.callback_query(Text('confirm_payment'))
async def confirm_payment(callback: types.CallbackQuery):
    if not db_requests.is_registered(callback.from_user.id):
        await callback.answer('Я вас не узнаю. Вы зарегистрировались, прежде чем оплачивать?')
    else:
        client = Client(callback.from_user.id)
        await client.unblock()
        new_shutdown_date = await db_requests.add_days(client.user_telegram_id)
        
        payment_id = await db_requests.add_payment(client.user_telegram_id, client.tariff, 'screenshot')
        
        await callback.message.edit_text(('😌 Спасибо, документ отправлен на проверку.\n\n'
                              '✅ Доступ к сервису уже восстановлен.\n\n'
                              f'Дата следующей оплаты: до {datetime.datetime.strftime(datetime.datetime.strptime(new_shutdown_date, "%Y-%m-%d %H:%M:%S") + datetime.timedelta(hours=int(client.timezone)), "%H:%M %d.%m.%Y")} (UTC+{client.timezone})\n\n'))
        await bot.send_animation(callback.from_user.id, animation=gifs_id[random.randint(0, len(gifs_id) - 1)])
        builder = InlineKeyboardBuilder()
        builder.button(text='Откатить транзакцию', callback_data=RestoreShutdownDate(user_telegram_id=client.user_telegram_id, date=int(datetime.datetime.timestamp(datetime.datetime.strptime(client.shutdown_date, "%Y-%m-%d %H:%M:%S"))), payment_id=payment_id))
        await bot.send_message(376131047, f'Пользователь с id {callback.from_user.id} ({callback.from_user.username} / {callback.from_user.full_name}) подтвердил оплату скриншотом', reply_markup=builder.as_markup())
        
        inviter = await db_requests.get_inviter_id(client.user_telegram_id)
        if inviter:
            inviter_object = Client(inviter)
            if inviter_object.blocked:
                await inviter_object.unblock()
            if client.payment_recieved:
                await db_requests.add_days(inviter, days=3, bonus=True)
                try:
                    await bot.send_message(inviter, f'Ваш друг {client.user_name} оплатил доступ, за это вам начислено 3 бонусных дня! 😎')
                except:
                    pass
            else:
                await db_requests.add_days(inviter, bonus=True)
                try:
                    await bot.send_message(inviter, f'Ваш друг {client.user_name} впервые оплатил доступ, за это вам начислен бонусный месяц! 😎')
                except:
                    pass


@router.message(F.document)
async def confirmation_document(message: types.Message):
    builder = InlineKeyboardBuilder()
    chat_info = await bot.get_chat(message.from_user.id)
    if not chat_info.has_private_forwards:
        builder.button(text='Ссылка на пользователя', url=f'tg://user?id={message.from_user.id}')

    if not db_requests.is_registered(message.from_user.id):
        await message.answer('Очень странно, я вас не узнаю. Вы зарегистрировались, прежде чем оплачивать?')
        await bot.send_message(376131047, f'<b>НЕЗАРЕГИСТИРОВАННЫЙ</b> пользователь с id {message.from_user.id} ({message.from_user.username} / {message.from_user.first_name}) прислал фото', reply_markup=builder.as_markup())
        await bot.send_photo(chat_id=376131047, photo=message.photo[-1].file_id)
    else:
        client = Client(message.from_user.id)
        new_shutdown_date = await db_requests.add_days(client.user_telegram_id)
        await client.unblock()
        payment_id = await db_requests.add_payment(client.user_telegram_id, client.tariff, 'document')   
        
        await message.answer(('😌 Спасибо, документ отправлен на проверку.\n\n'
                              '✅ Доступ к сервису уже восстановлен.\n\n'
                              f'Дата следующей оплаты: до {datetime.datetime.strftime(datetime.datetime.strptime(new_shutdown_date, "%Y-%m-%d %H:%M:%S") + datetime.timedelta(hours=int(client.timezone)), "%H:%M %d.%m.%Y")} (UTC+{client.timezone})\n\n'))
        await bot.send_animation(message.from_user.id, animation=gifs_id[random.randint(0, len(gifs_id) - 1)])
        await bot.forward_message(376131047, message.chat.id, message.message_id)
        
        builder = InlineKeyboardBuilder()
        builder.button(text='Откатить транзакцию', callback_data=RestoreShutdownDate(user_telegram_id=client.user_telegram_id, date=int(datetime.datetime.timestamp(datetime.datetime.strptime(client.shutdown_date, "%Y-%m-%d %H:%M:%S"))), payment_id=payment_id))
        await bot.send_message(376131047, f'Пользователь с id {message.from_user.id} ({message.from_user.username} / {message.from_user.full_name}) подтвердил оплату документом', reply_markup=builder.as_markup())
        
        inviter = await db_requests.get_inviter_id(client.user_telegram_id)
        if inviter:
            inviter_object = Client(inviter)
            if inviter_object.blocked:
                await inviter_object.unblock()
            if client.payment_recieved:
                await db_requests.add_days(inviter, days=3, bonus=True)
                try:
                    await bot.send_message(inviter, f'Ваш друг {client.user_name} оплатил доступ, за это вам начислено 3 бонусных дня! 😎')
                except:
                    pass
            else:
                await db_requests.add_days(inviter, bonus=True)
                try:
                    await bot.send_message(inviter, f'Ваш друг {client.user_name} впервые оплатил доступ, за это вам начислен бонусный месяц! 😎')
                except:
                    pass
        

@router.callback_query(F.data.startswith("payment_by_card_"))
async def pay(callback: types.CallbackQuery, from_payment_by_transfer=False):
    client = await db_requests.get_client(callback.from_user.id)
    month_to_discount = {'1': 0, '3': 10, '6': 20}
    number_of_month = callback.data[16:]
    decrease_amount = (month_to_discount[number_of_month] / 100) * (client.tariff * int(number_of_month))
    amount_value = client.tariff * int(number_of_month) - decrease_amount
    
    if from_payment_by_transfer:
        message_text = ('👉🏻 Попробуйте оплату через Систему Быстрых Платежей!\n'
                        '☝🏻 Никаких переводов, никаких скриншотов, автоматическое подтверждение платежа! 🤩\n\n'
                        'Но можно и по старинке переводом и скриншотом: <code>+79964081388</code> (нажмите на номер, чтобы скопировать) (Sber, Tinkoff)')
    else:
        message_text = ('Пожалуйста, нажмите "Оплатить" для перехода на платёжный шлюз.\n\n'
                        'Подтверджение платежа происходит <b>автоматически.</b>')

    payment = Payment.create({
        "amount": {
            "value": f"{int(amount_value)}.00",
            "currency": "RUB"
        },
        "confirmation": {
            "type": "redirect",
            "return_url": "https://t.me/RAMDATNET_BOT"
        },
        "capture": True,
        "description": f"Оплата подписки на {number_of_month} месяц(а).",
        "metadata": {"user_telegram_id": client.user_telegram_id, "number_of_month": number_of_month}
        }, uuid.uuid4())
    
    builder = InlineKeyboardBuilder()
    if from_payment_by_transfer:
        builder.button(text='Оплата СБП или картой', url=payment.confirmation.confirmation_url)
    else:
        builder.button(text=f'Оплатить {int(amount_value)} р.', url=payment.confirmation.confirmation_url)
        
    builder.button(text='🔙 Назад', callback_data='payment_by_card')
    builder.adjust(1)
    message_pay = await callback.message.edit_text(message_text, reply_markup=builder.as_markup())
    return
    


@router.callback_query(Text('payment_by_transfer'))
async def payment_by_transfer(callback: types.CallbackQuery):
    await pay(callback, True)
    