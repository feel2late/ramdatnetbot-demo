from typing import Optional
from aiogram.filters.callback_data import CallbackData


class RestoreShutdownDate(CallbackData, prefix="restore_shutdown"):
    user_telegram_id: Optional[int]
    date: Optional[str]
    payment_id: Optional[int]

