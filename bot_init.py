import logging
from aiogram import Bot
import config
from aiogram.enums.parse_mode import ParseMode
from yookassa import Configuration


logging.basicConfig(level=logging.INFO)

bot = Bot(token=config.API_TOKEN, parse_mode=ParseMode.HTML)
Configuration.account_id = config.YOOKASSA_SHOP_ID
Configuration.secret_key = config.YOOKASSA_SECRET_KEY

