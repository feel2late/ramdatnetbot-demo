from aiogram import types
from aiogram.filters.command import Command
import db_requests
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot_init import bot
from modules.client import Client
from aiogram import F, Router
from handlers.menu import menu
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
import datetime
from modules.states import ManualControl, SendMessageToAllUsers
import traceback
import api_requests
import config
import asyncio
from modules.callbacks_factories import RestoreShutdownDate


router = Router()  


@router.callback_query(F.data == 'admin_menu')
async def admin_menu(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    builder = InlineKeyboardBuilder()
    builder.button(text='Поиск пользователя', callback_data='manual_control')
    builder.button(text='Активные пользователи', callback_data='active_users')
    builder.button(text='Приглашающие', callback_data='inviters')
    builder.button(text='Оплаты', callback_data='payments')
    builder.button(text='Анализ', callback_data='analysis')
    #builder.button(text='Команды', callback_data='admin_commands')
    builder.button(text='Состояние сервиса', callback_data='health_status')
    builder.button(text='Рассылка', callback_data='admin_send_message_to_all_users')
    builder.button(text='🔙 Назад в меню', callback_data='menu')
    builder.adjust(1)

    active_users = await db_requests.get_active_users()
    payments_sum = 0
    payments_num = 0
    payments = await db_requests.get_payments()
    for payment in payments:
        if int(payment.month) == datetime.datetime.utcnow().month:
            payments_sum += payment.amount
            payments_num += 1

    message_text = (f'🥷 Админ меню\n\n'
                    f'💰 Доход в этом месяце: {payments_sum} р. ({payments_num} платежей)\n\n'
                    f'👥 Активных пользователей: {len(active_users)}\n\n')

    await callback.message.edit_text(message_text, reply_markup=builder.as_markup())


@router.callback_query(F.data == 'analysis')
async def analysis(callback: types.CallbackQuery, state: FSMContext):
    now = datetime.datetime.utcnow()

    # Получаем все платежи за текущий и прошлый месяцы
    current_month_payments = await db_requests.get_payments_for_period(now.replace(day=1, hour=0, minute=0, second=0), now)
    last_month_payments = await db_requests.get_payments_for_period(now.replace(month=now.month - 1, day=1, hour=0, minute=0, second=0), now.replace(month=now.month - 1))
    
    # Считаем сумму платежей за месяцы
    current_month_total_amount = sum(payment.amount for payment in current_month_payments)
    last_month_total_amount = sum(payment.amount for payment in last_month_payments)
    

    message_text = (f'Анализ сумм и количества оплат: текущая неделя/эта неделя прошлого месяца, текущий месяц/прошлый месяц.\n\n'
                    f'<b>Этот месяц:</b> {len(current_month_payments)} на сумму {current_month_total_amount}\n'
                    f'<b>Прошлый месяц:</b> {len(last_month_payments)} на сумму {last_month_total_amount}\n'
                    f'<b>Разница сумм:</b> {int(((current_month_total_amount - last_month_total_amount) / last_month_total_amount) * 100)}% или {current_month_total_amount - last_month_total_amount} руб.\n'
                    f'<b>Разница кол-во:</b> {int(((len(current_month_payments) - len(last_month_payments)) / len(last_month_payments)) * 100)}% или {len(current_month_payments) - len(last_month_payments)} платежей.')
    
    
    builder = InlineKeyboardBuilder()
    builder.button(text='🔙 Назад в админ меню', callback_data='admin_menu')
    await callback.message.edit_text(message_text, reply_markup=builder.as_markup())
   

@router.callback_query(F.data == 'payments')
async def payments(callback: types.CallbackQuery, state: FSMContext):
    all_payments = await db_requests.get_last_payments()
    message_text = 'Последние 50 платежей:\n\n'
    for i, payment in enumerate(all_payments):
        user = Client(payment.user_telegram_id)
        message_text += (f'{i + 1}) {datetime.datetime.strftime(payment.datetime, "%H:%M %d.%m.%Y")}: '
                         f'{payment.type}: '
                         f'{payment.amount}: '
                         f'{user.user_name}\n')
    builder = InlineKeyboardBuilder()
    builder.button(text='🔙 Назад', callback_data='admin_menu')
    await callback.message.edit_text(message_text, reply_markup=builder.as_markup())

@router.callback_query(F.data == 'manual_control', StateFilter('*'))
async def manual_control(callback: types.CallbackQuery, state: FSMContext):
    fsmdata = await state.get_data()
    await callback.message.edit_reply_markup(answer_markup='')
    if fsmdata.get('user_telegram_id'):
        await state.set_state()
        await user_info(callback.message, state)
        return

    builder = InlineKeyboardBuilder()
    builder.button(text='Отмена', callback_data='cancel_from_')
    await state.set_state(ManualControl.user_telegram_id)
    await callback.message.edit_text('Пришли user_telegram_id', reply_markup=builder.as_markup())


@router.message(F.text.startswith('/view_user_'))
@router.message(StateFilter(ManualControl.user_telegram_id))
async def user_info(message: types.Message, state: FSMContext):
    fsmdata = await state.get_data()
    
    if message.text.startswith('/view_user_'):
        if not message.from_user.id in config.admins:
            return
        user_telegram_id = message.text[11:]
        await state.update_data(user_telegram_id=user_telegram_id)
    else:
        if fsmdata.get('user_telegram_id'):
            user_telegram_id = fsmdata['user_telegram_id']
        else:
            if message.text.isnumeric():
                user_telegram_id = message.text
                await state.update_data(user_telegram_id=user_telegram_id)
            else:
                await message.answer('user_telegram_id должен состоять только из цифр. Попробуй ещё раз')
                return
    
    client = Client(user_telegram_id)
    user_payments = await db_requests.get_user_payments(client.user_telegram_id)
    builder = InlineKeyboardBuilder()
    builder.button(text='Изменить дату блокировки', callback_data='change_shutdown_date')
    builder.button(text='Изменить тариф', callback_data='change_client_tariff')
    if client.banned:
        builder.button(text='Разбанить в боте', callback_data='unban_user_in_bot')
    else:
        builder.button(text='Забанить в боте', callback_data='ban_user_in_bot')
    builder.button(text='Принудительно заблокировать ключи', callback_data='client_block')    
    builder.button(text='Принудительно разблокировать ключи', callback_data='client_unblock')
    builder.button(text=f'Платежи ({len(user_payments)})', callback_data='client_payments')
    builder.button(text='🔙 Назад в админ меню', callback_data='admin_menu')
    builder.adjust(1)
    
    message_text = (f'<b>ВСЕ ДАТЫ УКАЗАНЫ В UTC+0</b>\n\n'
                    f'<b>Telegram id:</b> {client.user_telegram_id}\n'
                    f'<b>Имя:</b> {client.user_name}\n'
                    f'<b>Локальное время:</b> {datetime.datetime.utcnow().replace(microsecond=0) + datetime.timedelta(hours=int(client.timezone))} (UTC+{client.timezone})\n'
                    f'<b>Дата блокировки:</b> {datetime.datetime.strptime(client.shutdown_date, "%Y-%m-%d %H:%M:%S")}\n'
                    f'<b>Последний платеж получен:</b> { f"{client.payment_recieved}" if client.payment_recieved else "не поступало"}\n'
                    f'<b>Платежей:</b> {len(user_payments)}\n'
                    f'<b>Дата подключения:</b> {client.connection_date}\n'
                    f'<b>Ключи заблокированы:</b> {"Да" if client.blocked else "Нет"}\n'
                    f'<b>Напоминание:</b> {"Да" if client.reminder else "Нет"}\n'
                    f'<b>Часовой пояс:</b> UTC+{client.timezone}\n'
                    f'<b>Тариф:</b> {client.tariff} р.\n'
                    f'<b>Обещанный платёж:</b> {"Активен" if client.postpone_payment else "Нет"}\n'
                    f'<b>Активный чат с админом:</b> {"Да" if client.chat_with_admin else "Нет"}\n'
                    f'<b>Количество приглашённых:</b> {client.number_of_invitees}\n'
                    f'<b>Забанен:</b> {"Да" if client.banned else "Нет"}\n'
                    f'<b>Дата бана:</b> {"Нет" if not client.banned_at else client.banned_at} {"(UTC+0)" if client.banned_at else ""}\n'
                    f'<b>Бот заблокирован:</b> {"Да" if client.blocked_bot else "Нет"}'
                    )
    await state.set_state()
    admin_msg = await message.answer(message_text, reply_markup=builder.as_markup())
    await state.update_data(admin_msg=admin_msg)
    

@router.callback_query(F.data == 'client_payments')
async def client_payments(callback: types.CallbackQuery, state: FSMContext):
    fsmdata = await state.get_data()
    client = Client(fsmdata.get('user_telegram_id'))
    user_payments = await db_requests.get_user_payments(client.user_telegram_id)
    message_text = 'История платежей:\n\n'
    
    for payment in user_payments:
        message_text += f'{datetime.datetime.strftime(payment.datetime, "%H:%M %d.%m.%Y")} - {payment.amount} ({payment.type})\n'
    
    builder = InlineKeyboardBuilder()
    builder.button(text='🔙 Назад к клиенту', callback_data='manual_control')
    await callback.message.edit_text(message_text, reply_markup=builder.as_markup())


@router.callback_query(F.data == 'inviters')
async def inviters(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.button(text='🔙 Назад в админ меню', callback_data='admin_menu')
    inviters = await db_requests.get_inviters()
    message_text = 'Список инвайтеров в порядке убывания количества приглашённых:\n\n'
    for i, inviter in enumerate(inviters):
        inviter_as_client = Client(inviter)
        message_text += f'{i+1}) {inviter_as_client.user_telegram_id} {inviter_as_client.user_name} - {inviters.get(inviter)}\n'
    await callback.message.edit_text(message_text, reply_markup=builder.as_markup())


@router.callback_query(F.data == 'change_client_tariff')
async def change_client_tariff(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(answer_markup='')
    builder = InlineKeyboardBuilder()
    builder.button(text='🔙 Назад к клиенту', callback_data='manual_control')
    await state.set_state(ManualControl.new_tariff)

    await callback.message.edit_text('Пришлите значение для нового тарифа', reply_markup=builder.as_markup())


@router.message(StateFilter(ManualControl.new_tariff))
async def set_new_tariff(message: types.Message, state: FSMContext):
    fsmdata = await state.get_data()
    client = Client(fsmdata.get('user_telegram_id'))
    builder = InlineKeyboardBuilder()
    builder.button(text='🔙 Назад к клиенту', callback_data='manual_control')
    
    new_tariff = int(message.text)

    await db_requests.set_new_tariff(client.user_telegram_id, new_tariff)

    await message.answer(f'Для пользователя {client.user_name} / {client.user_telegram_id} установлен новый тариф: {new_tariff} р.', reply_markup=builder.as_markup())


@router.callback_query(F.data == 'client_block')
async def client_block(callback: types.CallbackQuery, state: FSMContext):
    fsmdata = await state.get_data()
    client = Client(fsmdata.get('user_telegram_id'))
    await client.block()
    builder = InlineKeyboardBuilder()
    builder.button(text='🔙 Назад к клиенту', callback_data='manual_control')
    
    await callback.message.edit_text(f'Для пользователя {client.user_name} / {client.user_telegram_id} принудительно заблокированы ключи и установлен флаг блокировки.\n\n'
                                     'ВНИМАНИЕ! Дата блокировки осталась прежней.', reply_markup=builder.as_markup())  


@router.callback_query(F.data == 'client_unblock')
async def client_block(callback: types.CallbackQuery, state: FSMContext):
    fsmdata = await state.get_data()
    client = Client(fsmdata.get('user_telegram_id'))
    await client.unblock()
    builder = InlineKeyboardBuilder()
    builder.button(text='🔙 Назад к клиенту', callback_data='manual_control')

    await callback.message.edit_text(f'Для пользователя {client.user_name} / {client.user_telegram_id} принудительно разблокированы ключи и снят флаг блокировки.\n\n'
                                     'ВНИМАНИЕ! Дата блокировки осталась прежней.', reply_markup=builder.as_markup())  
    

@router.message(Command('get_free_keys'))
async def add_key(message: types.Message):
    await message.reply(f"Количество свободных ключей: {await db_requests.get_free_keys()}")


@router.callback_query(F.data == 'ban_user_in_bot')
async def ban_user_in_bot(callback: types.CallbackQuery, state: FSMContext):
    fsmdata = await state.get_data()
    client = Client(fsmdata.get('user_telegram_id'))
    builder = InlineKeyboardBuilder()
    builder.button(text='🔙 Назад к клиенту', callback_data='manual_control')  

    try:
        user_telegram_id = client.user_telegram_id
        user_name = client.user_name
        ban_user = await db_requests.ban_client(user_telegram_id, user_name)
        if ban_user:
            await callback.message.edit_text(f'Пользователь {user_name} / {user_telegram_id} забанен', reply_markup=builder.as_markup())
        else:
            await callback.message.edit_text(f'Пользователь {user_name} / {user_telegram_id} уже был забанен', reply_markup=builder.as_markup())
    except:
        await callback.message.edit_text('Не получилось забанить пользователя', reply_markup=builder.as_markup())
        await callback.message.reply(traceback.format_exc())


@router.callback_query(F.data == 'unban_user_in_bot')
async def unban_user_in_bot(callback: types.CallbackQuery, state: FSMContext):
    fsmdata = await state.get_data()
    client = Client(fsmdata.get('user_telegram_id'))
    builder = InlineKeyboardBuilder()
    builder.button(text='🔙 Назад к клиенту', callback_data='manual_control')  
    
    try:
        user_telegram_id = client.user_telegram_id
        user_name = client.user_name
        ban_user = await db_requests.unban_client(user_telegram_id)
        if ban_user:
            await callback.message.edit_text(f'Пользователь {user_name} / {user_telegram_id} разбанен', reply_markup=builder.as_markup())
        else:
            await callback.message.edit_text(f'Пользователь {user_name} / {user_telegram_id} уже был разбанен', reply_markup=builder.as_markup())
    except:
        await callback.message.edit_text('Не получилось разбанить пользователя', reply_markup=builder.as_markup())
        await callback.message.reply(traceback.format_exc())


@router.callback_query(F.data == 'change_shutdown_date')
async def change_shutdown_date(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(answer_markup='')
    await state.set_state(ManualControl.new_shutdown_date)
    builder = InlineKeyboardBuilder()
    builder.button(text='Отмена', callback_data='manual_control')
    await callback.message.answer('Пришли новую дату блокировки в формате hh:mm DD.MM.YYYY (UTC+0)\n\n'
                                  'Если дата будет МЕНЬШЕ текущей даты пользователь будет заблокирован\n'
                                  'Если дата будет БОЛЬШЕ текущей даты пользователь будет разблокирован\n', reply_markup=builder.as_markup())
    

@router.message(StateFilter(ManualControl.new_shutdown_date))
async def set_new_shutdown_date(message: types.Message, state: FSMContext):
    fsmdata = await state.get_data()
    client = Client(fsmdata['user_telegram_id'])
    #old_shutdown_date = datetime.datetime.strptime(client.shutdown_date, "%Y-%m-%d %H:%M:%S")
    #current_client_time = datetime.datetime.utcnow() + datetime.timedelta(hours=int(client.timezone))
    current_time = datetime.datetime.utcnow()
    date = message.text
    try:
        datetime.datetime.strptime(date, '%H:%M %d.%m.%Y')
        new_shutdown_date = datetime.datetime.strptime(date, "%H:%M %d.%m.%Y")
    except ValueError:
        print(traceback.format_exc())
        builder = InlineKeyboardBuilder()
        builder.button(text='Отмена', callback_data='cancel_from_')         
        await message.answer('Неправильный формат даты', reply_markup=builder.as_markup())
        return
    
    await db_requests.set_new_shutdown_date(client.user_telegram_id, new_shutdown_date)

    if new_shutdown_date < current_time:
        await client.block()
    else:
        await client.unblock()
    
    builder = InlineKeyboardBuilder()
    builder.button(text='🔙 Назад к клиенту', callback_data='manual_control')  
    await message.answer(f'Для клиента {client.user_telegram_id} / {client.user_name}\nУстановлена дата блокировки: {new_shutdown_date}', reply_markup=builder.as_markup())
    await state.set_state()
    

@router.callback_query(F.data == 'active_users')
async def active_users(callback: types.CallbackQuery):
    active_users = await db_requests.get_active_users()
    message_text = 'Данные по трафику в GB\n\n'   
    data_transfered = api_requests.get_data_transferred()
    rdn2_data_transfered = data_transfered.get('rdn2').get('bytesTransferredByUserId')
    rdn4_data_transfered = data_transfered.get('rdn4').get('bytesTransferredByUserId')
    builder = InlineKeyboardBuilder()
    builder.button(text='🔙 Назад в админ меню', callback_data='admin_menu')
    users_without_payments = 'Пользователи с безлимитным доступом:\n\n'

    for id, user in enumerate(active_users):
        client = Client(user.user_telegram_id)
        rdn2_transfered = int(rdn2_data_transfered.get(str(client.rdn2_id)) / 1073741824) if rdn2_data_transfered.get(str(client.rdn2_id)) else 0
        rdn4_transfered = int(rdn4_data_transfered.get(str(client.rdn4_id)) / 1073741824) if rdn4_data_transfered.get(str(client.rdn4_id)) else 0
        if client.user_telegram_id in config.USERS_WITHOUT_PAYMENT:
            users_without_payments += (f'{"⛔️ " if client.blocked_bot else ""}{client.user_telegram_id} | {client.user_name} | {"❗️ " + str(rdn2_transfered) if rdn2_transfered > 150 else rdn2_transfered} ' 
                                        f'@ {"❗️ " + str(rdn4_transfered) if rdn4_transfered > 150 else rdn4_transfered} | ' 
                                        f'{datetime.datetime.strftime(datetime.datetime.strptime(client.shutdown_date, "%Y-%m-%d %H:%M:%S"), "%d.%m.%Y")}\n\n')
            continue
        try:
            message_text += (f'{"⛔️ " + str(id + 1) if client.blocked_bot else id + 1}) {client.user_telegram_id} | {client.user_name} | {"❗️ " + str(rdn2_transfered) if rdn2_transfered > 150 else rdn2_transfered} ' 
                            f'@ {"❗️ " + str(rdn4_transfered) if rdn4_transfered > 150 else rdn4_transfered} | ' 
                            f'{datetime.datetime.strftime(datetime.datetime.strptime(user.shutdown_date, "%Y-%m-%d %H:%M:%S"), "%d.%m.%Y")}\n\n')
        except:
            print(traceback.format_exc())
            print('Не найден: ' + str(user.user_name) + str(user.rdn2_id))
            continue

    MESS_MAX_LENGTH = 4096
    for x in range(0, len(message_text), MESS_MAX_LENGTH):
        mess = message_text[x: x + MESS_MAX_LENGTH]
        await callback.message.answer(mess)
    await callback.message.answer(users_without_payments)

@router.callback_query(F.data == 'all_users')
async def all_users(callback: types.CallbackQuery):
    active_users = await db_requests.get_all_users()
    message_text = ''

    builder = InlineKeyboardBuilder()
    builder.button(text='🔙 Назад в админ меню', callback_data='admin_menu')

    for id, user in enumerate(active_users):
        message_text += f'{id + 1}) {user.user_telegram_id}| {user.user_name} | {(datetime.datetime.strftime(datetime.datetime.strptime(user.connection_date, "%Y-%m-%d %H:%M:%S"), "%d.%m.%Y")) if user.connection_date else "нет данных"} | {datetime.datetime.strftime(datetime.datetime.strptime(user.shutdown_date, "%Y-%m-%d %H:%M:%S"), "%d.%m.%Y")}\n'

    MESS_MAX_LENGTH = 4096
    for x in range(0, len(message_text), MESS_MAX_LENGTH):
                mess = message_text[x: x + MESS_MAX_LENGTH]
                await callback.message.answer(mess)

    #await callback.message.edit_text(message_text[:4000], reply_markup=builder.as_markup())


@router.callback_query(F.data == "admin_send_message_to_all_users")
async def admin_send_message_to_all_users(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(SendMessageToAllUsers.text)
    message_text = 'Пришлите текст, который вы хотите разослать пользователям.'
    builder = InlineKeyboardBuilder()
    builder.button(text='❌ Отмена', callback_data='cancel_from_')
    await callback.message.edit_text(message_text, reply_markup=builder.as_markup())


@router.message(StateFilter(SendMessageToAllUsers.text))
async def text_message_recieved(message: types.Message, state: FSMContext):
    await state.update_data(message_text=message.text)
    builder = InlineKeyboardBuilder()
    builder.button(text='✅ Отправить', callback_data='confirm_send_message_to_users')
    builder.button(text='❌ Отмена', callback_data='cancel_from_')
    builder.adjust(1)
    await message.answer('Проверь текст.\n\nЕсли всё верно, нажми "✅ Отправить"\nЕсли передумал, нажми "❌ Отмена"\nЕсли хочешь что-то исправить, просто пришли мне новый вариант')
    await message.answer(message.text, reply_markup=builder.as_markup())


@router.callback_query(F.data == 'confirm_send_message_to_users', StateFilter(SendMessageToAllUsers.text))
async def confirm_send_message_to_users(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state()
    await callback.message.delete()
    await callback.message.answer('Начинаю рассылку сообщения')
    fsmdata = await state.get_data()
    message_text = fsmdata.get('message_text')
    message_text += '\n\nЧтобы выключить уведомления и больше не получать важные новости и обновления, нажмите кнопку ниже.'
    clients = await db_requests.get_clients()
    total_sent = 0
    for client in clients:
        if not client.blocked_bot and client.notifications:
            try:
                builder = InlineKeyboardBuilder()
                if client.notifications:
                    builder.button(text='🟢 Уведомления включены', callback_data=f'change_notification_status_from_not_{client.id}')
                else:
                    builder.button(text='🔘 Уведомления выключены', callback_data=f'change_notification_status_from_not_{client.id}')
                await bot.send_message(client.user_telegram_id, message_text, reply_markup=builder.as_markup())
                total_sent += 1
            except:
                print(f'Не получилось отправить сообщение пользователю с id {client.user_telegram_id}, хотя он не блокировал бота ')
                await callback.message.answer(f'Не получилось отправить сообщение пользователю с id {client.user_telegram_id}, хотя он не блокировал бота')
            await asyncio.sleep(0.1)
    await callback.message.answer(f'Закончил. {total_sent} пользователей получили сообщение.')


@router.callback_query(RestoreShutdownDate.filter())
async def restore_shutdown_date(callback: types.CallbackQuery, callback_data: RestoreShutdownDate):
    await callback.message.edit_reply_markup(answer_markup='')
    user_telegram_id = callback_data.user_telegram_id
    shutdown_date = datetime.datetime.fromtimestamp(int(callback_data.date))
    payment_id = callback_data.payment_id
    client = Client(user_telegram_id)
    await db_requests.delete_payment(payment_id)
    await db_requests.restore_shutdown_date(user_telegram_id, shutdown_date)
    await callback.message.answer(f'Для клиента восстановлена дата: {shutdown_date} (UTC+{client.timezone}).\nИнформация о платеже удалена.\n\nЕсли нужно заблокировать ключи, сделай это явно.')


'''@router.message(Command('test'))
async def test(message: types.Message):
    api_requests.delete_access_key(rdn5_id=3)'''


