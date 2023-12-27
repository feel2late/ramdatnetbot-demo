from aiogram.fsm.state import State, StatesGroup


class GetClientInfo(StatesGroup):
    user_telegram_id = State()

class ManualControl(StatesGroup):
    user_telegram_id = State()
    new_shutdown_date = State()
    new_tariff = State()

class ChatWithUser(StatesGroup):
    active_chat = State()

class SendMessageToAllUsers(StatesGroup):
    text = State()