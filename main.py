import asyncio
import datetime
from aiogram import Dispatcher
import config
import aioschedule
import db_requests
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot_init import bot
from modules.client import Client
import models
from aiogram import F, Router
from middlewares.outer import CheckForUserBan, CheckForUserBanCallback, BotInService, BotInServiceCallback
import handlers.start, handlers.admin_menu, handlers.keys_and_configs, handlers.menu, handlers.help
import handlers.payment, handlers.profile, handlers.cancel_from, handlers.commands, handlers.health_status, handlers.web
import handlers.connect


router = Router()


async def ban():
    clients_for_ban = await db_requests.get_clients_for_ban()
    builder = InlineKeyboardBuilder()
    builder.button(text='💳 Оплатить', callback_data='payment_by_card')
    builder.button(text='⏳ Доверительный платёж', callback_data='postpone_payment')
    builder.adjust(1)
    admin_message_text = f'Заблокировал {len(clients_for_ban)} клиентов:\n'
    for client_ in clients_for_ban:
        client = Client(client_.user_telegram_id)
        admin_message_text += f'/view_user_{client.user_telegram_id} / {client.user_name}\n'
        await client.block()
        message_text = ('Мне очень жаль, но я вынужден ограничить доступ из-за отсутствия оплаты 😞\n\n'
                    f'Вы можете восстановить доступ, оплатив {client.tariff} рублей или взяв Доверительный платёж.')
        try:
            await bot.send_message(client.user_telegram_id, message_text, reply_markup=builder.as_markup())
        except:
            pass
    
    if len(clients_for_ban) > 0:
        await bot.send_message(376131047, admin_message_text)


async def remind():
    clients_for_remind = await db_requests.get_clients_for_remind()
    builder = InlineKeyboardBuilder()
    builder.button(text='💳 Оплатить картой', callback_data='payment_by_card')
    builder.button(text='⏳ Доверительный платёж', callback_data='postpone_payment')
    builder.adjust(1)
    current_time = datetime.datetime.utcnow()

    for client in clients_for_remind:
        client: models.Access
        message_text = (f'Пожалуйста, не забудьте оплатить доступ <b>до {datetime.datetime.strftime(datetime.datetime.strptime(client.shutdown_date, "%Y-%m-%d %H:%M:%S") + datetime.timedelta(hours=int(client.timezone)), "%H:%M %d.%m.%Y")} (UTC+{client.timezone})</b> чтобы продолжить пользоваться сервисом.\n\n'
                    f'Также вы можете продлить доступ на 3 дня взяв Доверительный платёж.')
        
        current_client_time = current_time + datetime.timedelta(hours=int(client.timezone))
        
        if 8 < current_client_time.hour < 22:
            try:
                await bot.send_message(client.user_telegram_id, message_text, reply_markup=builder.as_markup())
            except:
                pass
        else:
            try:
                await bot.send_message(client.user_telegram_id, message_text, disable_notification=True, reply_markup=builder.as_markup())
            except:
                pass


async def reset_chat_with_admin_status():
    clients = await db_requests.get_clients_with_active_chat()
    for client in clients:
        await db_requests.set_status_chat_with_admin(client.user_telegram_id, False)


async def reminder():
    if not config.DEBUG:
        aioschedule.every(1).minutes.do(ban)
        aioschedule.every(1).minutes.do(remind)
        aioschedule.every().day.at("00:00").do(reset_chat_with_admin_status)
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)


async def on_startup():
    asyncio.create_task(reminder())


async def main():
    router = Dispatcher()
    router.include_routers(handlers.start.router, handlers.admin_menu.router, handlers.cancel_from.router, handlers.connect.router,
                           handlers.health_status.router, handlers.help.router, handlers.keys_and_configs.router, handlers.menu.router, 
                           handlers.payment.router, handlers.profile.router, handlers.commands.router, handlers.chart.router, handlers.web.router) 
    router.message.outer_middleware(CheckForUserBan())
    #router.message.outer_middleware(BotInService())
    router.callback_query.outer_middleware(CheckForUserBanCallback())
    #router.callback_query.outer_middleware(BotInServiceCallback())
    await on_startup()
    await router.start_polling(bot, skip_updates=True)


if __name__ == "__main__":
    asyncio.run(main())
    