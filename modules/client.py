import urllib3
urllib3.disable_warnings()
from models import db
from models import Access, Invitations, Banned, AccessKeys
import db_requests, api_requests
from bot_init import bot
import modules.control_v2ray


class Client:

    def __init__(self, user_telegram_id: str):
        client = db.query(Access).filter(Access.user_telegram_id == user_telegram_id).first()
        invited_by_client = db.query(Invitations).filter(Invitations.inviter == user_telegram_id).all()
        banned = db.query(Banned).filter(Banned.user_telegram_id == user_telegram_id).first()
        access_keys = db.query(AccessKeys).filter(AccessKeys.user_telegram_id == user_telegram_id).first()
        
        self.id = client.id
        self.user_telegram_id = client.user_telegram_id
        self.user_name = client.user_name
        self.connection_date = client.connection_date
        self.payment_recieved = client.payment_recieved
        self.shutdown_date = client.shutdown_date
        self.reminder = client.reminder
        self.invite_code = client.invite_code
        self.timezone = client.timezone
        self.rdn2 = access_keys.rdn2
        self.rdn4 = access_keys.rdn4
        self.rdn5 = access_keys.rdn5
        self.blocked = client.blocked
        self.rdn2_id = access_keys.rdn2_id
        self.rdn4_id = access_keys.rdn4_id
        self.rdn5_id = access_keys.rdn5_id
        self.ss_ned_key = access_keys.ss_ned_key
        self.ss_fin_key = access_keys.ss_fin_key
        self.ss_swe_key = access_keys.ss_swe_key
        self.vless_ned_key = access_keys.vless_ned_key
        self.vless_fin_key = access_keys.vless_fin_key
        self.vless_swe_key = access_keys.vless_swe_key
        self.tariff = client.tariff
        self.postpone_payment = client.postpone_payment
        self.chat_with_admin = client.chat_with_admin
        self.number_of_invitees = len(invited_by_client)
        self.invited_list = invited_by_client
        self.banned = True if banned else False
        self.banned_at = banned.banned_at if banned else False
        self.blocked_bot = client.blocked_bot
        self.notifications = client.notifications
        self.web_user_id = client.web_user_id

        
    async def block(self):
        """Блокирует ключи клиента, выставляет флаг блокировки, снимает флаг напоминания
        Возвращает словарь со статус-кодами от nginx для дальнейшей проверки."""
        api_requests.set_limit(self.rdn2_id, self.rdn4_id, self.rdn5_id)    
        await db_requests.update_blocked_flag(self.user_telegram_id, True)
        await db_requests.update_reminder_flag(self.user_telegram_id, False)
        await modules.control_v2ray.block_xray_user({'ss_key': self.ss_ned_key, 'vless_key': self.vless_ned_key, 'user_telegram_id': self.user_telegram_id}, 
                                              {'ss_key': self.ss_fin_key, 'vless_key': self.vless_fin_key, 'user_telegram_id': self.user_telegram_id},
                                              {'ss_key': self.ss_swe_key, 'vless_key': self.vless_swe_key, 'user_telegram_id': self.user_telegram_id})

    async def unblock(self):
        """Разблокирует ключи клиента, снимает флаг блокировки, снимает флаги обещанного платежа и напоминания. 
        Возвращает словарь со статус-кодами от nginx для дальнейшей проверки."""
        api_requests.delete_limit(self.rdn2_id, self.rdn4_id, self.rdn5_id)    
        await db_requests.update_blocked_flag(self.user_telegram_id, False)
        await db_requests.update_postpone_payment_flag(self.user_telegram_id, False)
        await db_requests.update_reminder_flag(self.user_telegram_id, False)
        await modules.control_v2ray.unblock_xray_user({'ss_key': self.ss_ned_key, 'vless_key': self.vless_ned_key, 'user_telegram_id': self.user_telegram_id}, 
                                                {'ss_key': self.ss_fin_key, 'vless_key': self.vless_fin_key, 'user_telegram_id': self.user_telegram_id},
                                                {'ss_key': self.ss_swe_key, 'vless_key': self.vless_swe_key, 'user_telegram_id': self.user_telegram_id})


    async def create_keys(self):
        client_keys = db.query(AccessKeys).filter(AccessKeys.user_telegram_id == self.user_telegram_id).first()
        responses = await modules.control_v2ray.create_new_xray_user(self.user_telegram_id, self.blocked)
        
        for response in responses:
            if list(response.keys())[0] == 'rdn-swe':
                client_keys.ss_swe_key = response.get('rdn-swe').get('ss_password')
                client_keys.vless_swe_key = response.get('rdn-swe').get('vless_id')
            elif list(response.keys())[0] == 'rdn-ned':
                client_keys.ss_ned_key = response.get('rdn-ned').get('ss_password')
                client_keys.vless_ned_key = response.get('rdn-ned').get('vless_id')
            elif list(response.keys())[0] == 'rdn-fin':
                client_keys.ss_fin_key = response.get('rdn-fin').get('ss_password')
                client_keys.vless_fin_key = response.get('rdn-fin').get('vless_id')
            db.commit()


    