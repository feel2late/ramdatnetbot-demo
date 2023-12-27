import datetime
import traceback
import secrets
import string
from models import Access, Invitations, Banned, Payments, AccessKeys
from models import db
from sqlalchemy import and_, func, or_



async def register(user_telegram_id: int, user_name: str):
    """Добавляем пользователя в БД"""
    client = db.query(Access).filter(Access.user_telegram_id == user_telegram_id).first()
    
    if not client:
        letters_and_digits = string.ascii_letters + string.digits
        crypt_rand_string = ''.join(secrets.choice(letters_and_digits) for i in range(16))
        current_time = datetime.datetime.utcnow().replace(microsecond=0)
        shutdown_date = current_time + datetime.timedelta(days=31)
        client = Access(user_telegram_id=user_telegram_id, user_name=user_name,
                        connection_date=current_time, shutdown_date=shutdown_date,
                        tariff=250, invite_code=crypt_rand_string)
        client_keys = AccessKeys(user_telegram_id=user_telegram_id)
        try:
            db.add_all([client, client_keys])
            db.commit()
            return True
        except:
            print(traceback.format_exc())
            return False
    else:
        return False


def is_registered(user_id):
    """Проверяем, зарегистрирован ли пользователь"""
    client = db.query(Access).filter(Access.user_telegram_id == user_id).first()
    if client:
        return True
    else:
        return False


async def get_first_free_id():
    """Получаем первый свободный id (без пользователя)"""
    free_id = db.query(Access).filter(Access.user_telegram_id == None).order_by(Access.id).first()
    return free_id.id


async def get_free_keys():
    keys = db.query(Access).filter(Access.user_telegram_id == None).all()
    return len(keys)

async def generate_invite_codes():
    clients = db.query(Access).all()
    letters_and_digits = string.ascii_letters + string.digits
    
    try:
        for client in clients:
            if not client.invite_code:
                crypt_rand_string = ''.join(secrets.choice(letters_and_digits) for i in range(16))
                client.invite_code = crypt_rand_string
            else:
                continue
    except:
        print(traceback.format_exc())
        return False
    
    try:
        db.commit()
        return True
    except:
        print(traceback.format_exc())
        return False


async def get_clients():
    clients = db.query(Access).filter(Access.user_telegram_id != None).all()
    return clients


async def get_client(user_telegram_id):
    client = db.query(Access).filter(Access.user_telegram_id == user_telegram_id).first()
    return client


async def add_invitation(inviter, invited):
    object = Invitations(inviter=inviter, invited=invited)
    db.add(object)
    db.commit()


async def set_timezone(user_telegram_id: str, new_timezone: int):
    client = db.query(Access).filter(Access.user_telegram_id == user_telegram_id).first()
    
    if client:
        client.timezone=new_timezone
        db.commit()


async def get_clients_for_ban() -> list:
    clients = db.query(Access).filter(Access.user_telegram_id != None).all()
    clients_for_ban = []
    
    for client in clients:
        current_time = datetime.datetime.utcnow()
        client_shutdown_date = datetime.datetime.strptime(client.shutdown_date, "%Y-%m-%d %H:%M:%S")

        if (client.blocked == False or client.blocked == None) and client_shutdown_date < current_time:
            clients_for_ban.append(client)
        
    return clients_for_ban


async def get_clients_for_remind() -> list:
    clients = db.query(Access).filter(Access.user_telegram_id != None).all()
    clients_for_remind = []
    
    for client in clients:
        if client.blocked == False or client.blocked == None:
            current_time = datetime.datetime.utcnow()
            client_shutdown_date = datetime.datetime.strptime(client.shutdown_date, "%Y-%m-%d %H:%M:%S")
            difference = client_shutdown_date - current_time
            less_than_24_hours = difference.days == 0 and difference.seconds < 86400

            if less_than_24_hours and not client.reminder:
                clients_for_remind.append(client)
                client.reminder = True
                db.commit()

    return clients_for_remind


async def update_reminder_flag(user_telegram_id: str, flag: bool):
    client = db.query(Access).filter(Access.user_telegram_id == user_telegram_id).first()

    if flag == True:
        client.reminder = True
    elif flag == False:
        client.reminder = False
    
    db.commit()


async def update_blocked_flag(user_telegram_id: str, flag: bool):
    client = db.query(Access).filter(Access.user_telegram_id == user_telegram_id).first()

    if flag == True:
        client.blocked = True
    elif flag == False:
        client.blocked = False
    
    db.commit()


async def add_days(user_telegram_id: str, days: int = 31, bonus: bool = False) -> datetime:
    '''Возвращает следующую дату оплаты'''

    client = db.query(Access).filter(Access.user_telegram_id == user_telegram_id).first()

    if client:
        current_date = datetime.datetime.utcnow().replace(microsecond=0)
        client_shutdown_date = datetime.datetime.strptime(client.shutdown_date, "%Y-%m-%d %H:%M:%S")
        
        if current_date > client_shutdown_date:
            if client.postpone_payment:
                client.shutdown_date = current_date + datetime.timedelta(days=days-3)
                client.postpone_payment = False
            else:
                client.shutdown_date = current_date + datetime.timedelta(days=days)
                
        else:
            if client.postpone_payment:
                client.shutdown_date = datetime.datetime.strptime(client.shutdown_date, "%Y-%m-%d %H:%M:%S") + datetime.timedelta(days=days-3)
                client.postpone_payment = False
            else:
                client.shutdown_date = datetime.datetime.strptime(client.shutdown_date, "%Y-%m-%d %H:%M:%S") + datetime.timedelta(days=days)
        
        if not bonus:
            client.payment_recieved = current_date
        
        db.commit()
        return client.shutdown_date
    
    
async def update_postpone_payment_flag(user_telegram_id, flag):
    client = db.query(Access).filter(Access.user_telegram_id == user_telegram_id).first()

    if client:
        if flag == True:
            client.postpone_payment = True
            db.commit()
        elif flag == False:
            client.postpone_payment = False
            db.commit()


async def add_postpone_payment_days(user_telegram_id):
    client = db.query(Access).filter(Access.user_telegram_id == user_telegram_id).first()

    if client:
        current_client_date = datetime.datetime.utcnow().replace(microsecond=0) + datetime.timedelta(hours=int(client.timezone))
        client_shutdown_date = datetime.datetime.strptime(client.shutdown_date, "%Y-%m-%d %H:%M:%S")
        
        if current_client_date > client_shutdown_date:
            client.shutdown_date = current_client_date + datetime.timedelta(days=3)     
        else:
            client.shutdown_date = datetime.datetime.strptime(client.shutdown_date, "%Y-%m-%d %H:%M:%S") + datetime.timedelta(days=3)
        db.commit()

        await update_postpone_payment_flag(client.user_telegram_id, True)
        return client.shutdown_date


async def set_status_chat_with_admin(user_telegram_id: str, status: bool) -> None:
    client = db.query(Access).filter(Access.user_telegram_id == user_telegram_id).first()

    if client:
        if status == True:
            client.chat_with_admin = True
        elif status == False:
            client.chat_with_admin = False
        db.commit()


async def get_clients_with_active_chat():
    clients = db.query(Access).filter(Access.chat_with_admin == True).all()
    return clients


async def ban_client(user_telegram_id, user_name):
    client = db.query(Banned).filter(Banned.user_telegram_id == user_telegram_id).first()
    if not client:
        now = datetime.datetime.utcnow().replace(microsecond=0)
        client = Banned(user_telegram_id=user_telegram_id, user_name=user_name, banned_at=now)
        db.add(client)
        try:
            db.commit()
            return True
        except:
            print(traceback.format_exc())
            return False
    else:
        return False
        
    
async def unban_client(user_telegram_id):
    client = db.query(Banned).filter(Banned.user_telegram_id == user_telegram_id).first()
    if client:
        db.delete(client)
        try:
            db.commit()
            return True
        except:
            print(traceback.format_exc())
            return False
    else:
        return False


async def get_banned_users() -> list:
    clients = db.query(Banned).all()
    banned_clients = []

    for client in clients:
        banned_clients.append(client.user_telegram_id)
    
    return banned_clients


async def get_active_users():
    clients = db.query(Access).filter(and_(Access.user_telegram_id != None, or_(Access.blocked == False, Access.blocked == None))).order_by(Access.shutdown_date).all()
    
    return clients


async def get_all_users() -> list:
    clients = db.query(Access).filter(Access.user_telegram_id != None).order_by(Access.id).all()
    
    return clients


async def set_new_shutdown_date(user_telegram_id: str, new_shutdown_date: datetime):
    client = db.query(Access).filter(Access.user_telegram_id == user_telegram_id).first()
    
    if client:
        client.shutdown_date = new_shutdown_date
        
        try:
            db.commit()
            return True
        except:
            print(traceback.format_exc())
            return False


async def set_new_tariff(user_telegram_id: str, new_tariff: int):
    client = db.query(Access).filter(Access.user_telegram_id == user_telegram_id).first()
    
    if client:
        client.tariff = new_tariff
        try:
            db.commit()
            return True
        except:
            print(traceback.format_exc())
            return False
        
        
async def update_flag_blocked_bot(user_telegram_id: str, flag: bool):
    client = db.query(Access).filter(Access.user_telegram_id == user_telegram_id).first()
    
    if client:
        try:
            if flag == True:
                client.blocked_bot = True
            elif flag == False:
                client.blocked_bot = False
            db.commit()
        except:
            print(traceback.format_exc())


async def restore_shutdown_date(user_telegram_id: str, shutdown_date: datetime) -> datetime:
    client = db.query(Access).filter(Access.user_telegram_id == user_telegram_id).first()

    if client:
        client.shutdown_date = shutdown_date
        db.commit()


async def add_payment(user_telegram_id: int, amount: int, type: str) -> int:
    payment = Payments(user_telegram_id=user_telegram_id, amount=amount, type=type, datetime=datetime.datetime.utcnow().replace(microsecond=0), month=datetime.datetime.utcnow().month, year=datetime.datetime.utcnow().year)
    db.add(payment)
    db.commit()
    return payment.id


async def delete_payment(payment_id) -> None:
    payment = db.query(Payments).filter(Payments.id == payment_id).first()
    db.delete(payment)
    db.commit()


async def get_payments():
    payments = db.query(Payments).all()
    return payments


async def get_inviter_id(invited_user_telegram_id) -> int:
    invited = db.query(Invitations).filter(Invitations.invited == invited_user_telegram_id).first()

    if invited:
        return invited.inviter
    else:
        return False
    
async def get_inviters() -> int:
    invitations = db.query(Invitations).all()
    inviters = {}
    for invitation in invitations:
        if inviters.get(invitation.inviter):
            inviters[invitation.inviter] += 1
        else:
            inviters[invitation.inviter] = 1
    sorted_inviters = dict(sorted(inviters.items(), key=lambda item: item[1], reverse=True))
    return sorted_inviters


async def recieved_update_message(user_telegram_id, flag):
    client = db.query(Access).filter(Access.user_telegram_id == user_telegram_id).first()
    
    if client:
        if flag == True:
            client.recieved_update_message = True
        elif flag == False:
            client.recieved_update_message = False
        db.commit()

async def get_user_payments(user_telegram_id):
    user_payments = db.query(Payments).filter(Payments.user_telegram_id == user_telegram_id).all()
    return user_payments

async def get_last_payments() -> Payments:
    payments = db.query(Payments).order_by(Payments.id).all()
    return payments[-50:]

async def change_notification_status(client_id: int) -> bool:
    """ Возвращает новое состояние True или False"""
    client = db.query(Access).filter(Access.id == client_id).first()
    if client.notifications:
        client.notifications = False    
    else:
        client.notifications = True
    db.commit()
    return client.notifications


async def get_payments_for_day(date: datetime) -> list[Payments]:
    payments = db.query(Payments).filter(func.DATE(Payments.datetime) == date).all()
    return payments

async def get_payments_for_period(start_date: datetime, end_date: datetime) -> list[Payments]:
    payments = db.query(Payments).filter(Payments.datetime.between(start_date, end_date)).all()
    return payments

async def get_payments_for_month(month: int, year: int) -> list[Payments]:
    payments = db.query(Payments).filter(Payments.month == month, Payments.year == year).all()
    return payments

async def get_ss_port(port: int) -> AccessKeys:
    port = db.query(AccessKeys).filter(or_(AccessKeys.ss_fin_port == port, AccessKeys.ss_ned_port == port, AccessKeys.ss_swe_port == port)).all()
    return port
