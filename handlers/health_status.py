from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import F, Router
from aiogram.filters.chat_member_updated import MEMBER, KICKED
import modules.check_servers_status as check_servers_status


router = Router()  


@router.callback_query(F.data =='health_status')
async def health_status(callback: types.CallbackQuery, admin_menu=False):
    xray_ned_status = check_servers_status.get_xray_ned_status()
    xray_fin_status = check_servers_status.get_xray_fin_status()
    xray_swe_status = check_servers_status.get_xray_swe_status()
    rdn2_status = check_servers_status.get_rdn2_status()
    rdn4_status = check_servers_status.get_rdn2_status()
    rdn5_status = check_servers_status.get_rdn2_status()
    
    
    message_text = ('Доступность серверов.\n\n'
                    '🇳🇱 <b>Нидерланды:</b>\n'
                    f'Outline: {f"✅" if rdn2_status else "❌"}\n'
                    f'Xray: {"✅" if xray_ned_status.get("status") == "active" else "❌"}\n\n'
                    '🇫🇮 <b>Финляндия:</b>\n'
                    f'Outline: {f"✅" if rdn4_status else "❌"}\n'
                    f'Xray: {"✅" if xray_fin_status.get("status") == "active" else "❌"}\n\n'
                    '🇸🇪 <b>Швеция:</b>\n'
                    f'Xray: {"✅" if xray_ned_status.get("status") == "active" else "❌"}\n\n'
                    '🇷🇺 <b>Россия:</b>\n'
                    f'Outline: {f"✅" if rdn5_status else "❌"}\n\n')
    
    builder = InlineKeyboardBuilder()
    if admin_menu:
        builder.button(text='🔙 Назад в админ меню', callback_data='admin_menu')
    else:
        builder.button(text='🔙 Назад', callback_data='help')
    await callback.message.edit_text(message_text, reply_markup=builder.as_markup())