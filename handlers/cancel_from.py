from aiogram import types
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from handlers.admin_menu import admin_menu

router = Router()  


@router.callback_query(F.data.startswith('cancel_from_'), StateFilter('*'))
async def cancel_state(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await admin_menu(callback, state)