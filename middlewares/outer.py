from datetime import datetime
from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
import db_requests
import asyncio


class CheckForUserBan(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        banned_users = await db_requests.get_banned_users()
        user_id = data.get('event_from_user').id

        if user_id in banned_users:
            return
        else:
            return await handler(event, data)        


class CheckForUserBanCallback(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[CallbackQuery, Dict[str, Any]], Awaitable[Any]],
        event: CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        banned_users = await db_requests.get_banned_users()
        user_id = data.get('event_from_user').id

        if user_id in banned_users:
            return
        else:
            return await handler(event, data)       


class ResponseDelayMessage(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        await asyncio.sleep(1)
        return await handler(event, data)


class ResponseDelayCallback(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[CallbackQuery, Dict[str, Any]], Awaitable[Any]],
        event: CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        await asyncio.sleep(1)
        return await handler(event, data)
        


class BotInService(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        user_id = data.get('event_from_user').id

        if user_id in [376131047, 6006358760]:
            return await handler(event, data) 
        else:
            await event.answer("👷‍♂️ Добавляю новую фичу, фиксики помогают. Закончу до 11:00 МСК.")      


class BotInServiceCallback(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[CallbackQuery, Dict[str, Any]], Awaitable[Any]],
        event: CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        user_id = data.get('event_from_user').id

        if user_id in [376131047, 6006358760]:
            return await handler(event, data) 
        else:
            await event.answer("👷‍♂️ Добавляю новую фичу, фиксики помогают. Закончу до 11:00 МСК.", show_alert=True)       