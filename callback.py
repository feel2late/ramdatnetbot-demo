from fastapi import FastAPI, Request
from bot_init import bot
import db_requests
import config
import datetime
import traceback
from modules.client import Client
from gifs_id import gifs_id
import random


app = FastAPI()


async def send_message_to_admins(message_text: str):
    for admin in config.admins:
        try:
            await bot.send_message(admin, message_text)
        except:
            print(traceback.format_exc())


@app.post("/callback")
async def payment_webhook(request: Request):
    webhook_data = await request.json()
    
    if webhook_data['event'] == 'payment.succeeded':
        client = Client(webhook_data["object"]['metadata']['user_telegram_id'])
    
        new_shutdown_date = await db_requests.add_days(user_telegram_id=client.user_telegram_id, days=31 * int(webhook_data["object"]["metadata"]["number_of_month"]))
        await db_requests.add_payment(client.user_telegram_id, int(float(webhook_data["object"]["amount"]["value"])), 'yookassa')
        try:
            await client.unblock()
        except:
            await bot.send_message(376131047, f'Ошибка при вызове метода client.unblock() для пользователя {client.user_telegram_id}:\n\n{traceback.format_exc()}')
        try:
            await bot.send_animation(client.user_telegram_id, animation=gifs_id[random.randint(0, len(gifs_id) - 1)])
            await bot.send_message(client.user_telegram_id, ('😌 Спасибо, оплата получена.\n\n'
                                                            f'Дата следующей оплаты: до {datetime.datetime.strftime(datetime.datetime.strptime(new_shutdown_date, "%Y-%m-%d %H:%M:%S") + datetime.timedelta(hours=int(client.timezone)), "%H:%M %d.%m.%Y")} (UTC+{client.timezone})\n\n'))
        except:
            await bot.send_message(376131047, f'Ошибка при отправке сообщения об успешной оплате для пользователя {client.user_telegram_id}:\n\n{traceback.format_exc()}')
        inviter_id = await db_requests.get_inviter_id(client.user_telegram_id)
        if inviter_id:
            inviter_object = Client(inviter_id)
            if inviter_object.blocked:
                await inviter_object.unblock()
            if client.payment_recieved:
                await db_requests.add_days(inviter_id, days=3, bonus=True)
                if inviter_object.notifications:
                    try:
                        await bot.send_message(inviter_id, f'Ваш друг {client.user_name} оплатил доступ, за это вам начислено 3 бонусных дня! 😎')
                    except:
                        pass
            else:
                await db_requests.add_days(inviter_id, bonus=True)
                if inviter_object.notifications:
                    try:
                        await bot.send_message(inviter_id, f'Ваш друг {client.user_name} впервые оплатил доступ, за это вам начислен бонусный месяц! 😎')
                    except:
                        pass
        await bot.send_message(376131047, f'Пользователь с id {client.user_telegram_id} ({client.user_name}) оплатил {int(float(webhook_data["object"]["amount"]["value"]))} руб. через YOOKASSA ({webhook_data["object"]["payment_method"]["type"]})')    
        return

    return {"message": "Webhook received successfully"}
