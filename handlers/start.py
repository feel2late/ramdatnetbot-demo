from aiogram import types
from aiogram.filters.command import Command, CommandObject
import db_requests
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot_init import bot
from modules.client import Client
from aiogram import F, Router
from aiogram.filters.chat_member_updated import ChatMemberUpdatedFilter, MEMBER, KICKED
from handlers.menu import menu
import modules.control_v2ray

router = Router()  


@router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=KICKED))
async def user_blocked_bot(event: types.ChatMemberUpdated):
    client = None
    builder = InlineKeyboardBuilder()
    builder.button(text='Ссылка на пользователя', url=f'tg://user?id={event.from_user.id}')

    try:
        client = Client(event.from_user.id)
        await db_requests.update_flag_blocked_bot(client.user_telegram_id, True)
        try:
            await bot.send_message(376131047, f'Действующий пользователь {client.user_telegram_id} / {client.user_name} заблокировал бота.', reply_markup=builder.as_markup())
        except:
            await bot.send_message(376131047, f'Действующий пользователь {client.user_telegram_id} / {client.user_name} заблокировал бота.')
    except:
        try:
            await bot.send_message(376131047, f'Новый пользователь {event.from_user.id} / {event.from_user.full_name} заблокировал бота незарегистрировавшись.', reply_markup=builder.as_markup())
        except:
            await bot.send_message(376131047, f'Новый пользователь {event.from_user.id} / {event.from_user.full_name} заблокировал бота незарегистрировавшись.')
    

@router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=MEMBER))
async def user_unblocked_bot(event: types.ChatMemberUpdated):
    client = None
    builder = InlineKeyboardBuilder()
    builder.button(text='Ссылка на пользователя', url=f'tg://user?id={event.from_user.id}')

    try:
        client = Client(event.from_user.id)
        if not client.recieved_update_message:
            await db_requests.recieved_update_message(client.user_telegram_id, True)
        await db_requests.update_flag_blocked_bot(client.user_telegram_id, False)
        try:
            await bot.send_message(376131047, f'Действующий пользователь {client.user_telegram_id} / {client.user_name} перезапустил (разблокировал) бота.', reply_markup=builder.as_markup())
        except:
            await bot.send_message(376131047, f'Действующий пользователь {client.user_telegram_id} / {client.user_name} перезапустил (разблокировал) бота.')
    except:
        try:
            await bot.send_message(376131047, f'Новый пользователь {event.from_user.id} / {event.from_user.full_name} запустил бота.', reply_markup=builder.as_markup())
        except:
            await bot.send_message(376131047, f'Новый пользователь {event.from_user.id} / {event.from_user.full_name} запустил бота.')
    

@router.message(Command("start"))
async def cmd_start(message: types.Message, command: CommandObject):
    invite_code: str = command.args
    
    if not db_requests.is_registered(message.from_user.id):
        if invite_code:
            clients = await db_requests.get_clients()
            
            for client in clients:         
                if invite_code == client.invite_code:
                    registration = await db_requests.register(message.from_user.id, message.from_user.full_name)
                    client_ = Client(client.user_telegram_id)
                    if registration:
                        await db_requests.add_invitation(client.user_telegram_id, message.from_user.id)
                        builder = InlineKeyboardBuilder()

                        #user_id = message.from_user.id
                        chat_info = await bot.get_chat(message.from_user.id)
                        if not chat_info.has_private_forwards:
                            builder.button(text='Ссылка на пользователя', url=f'tg://user?id={message.from_user.id}')
                        
                        await bot.send_message(376131047, ('Пользователь зарегистрировался!\n'
                                                            f'User id: {message.from_user.id}\n'
                                                            f'Имя: {message.from_user.full_name}\n'
                                                            f'Пригласил: <code>{client_.user_telegram_id}</code> {client_.user_name} (инвайтов: {client_.number_of_invitees})'), reply_markup=builder.as_markup())
                        await bot.send_animation(message.from_user.id, animation='CgACAgQAAxkBAAKMhmT2Add20Rh9NJdPI6XbKn7-oArOAAKnAQAC7qsEU9cluTMam_gHMAQ')
                        await message.answer('Рад вас приветствовать под знаменем свободного интернета! 🫡\n\n'
                                             '✅ Для вас - месяц бесплатного доступа.\n'
                                             '✅ Для вашего друга - месяц бесплатно, когда вы первый раз оплатите доступ.\n\n')
                        await menu(message)
                        return
                        
                    else:
                        await message.answer('Что-то пошло не так...\n\nИнформация об ошибке уже отправлена разработчику.\nПожалуйста, попробуйте позже.')
                        await bot.send_message(376131047, '🆘 Ошибка при регистрации пользователя!\n'
                                                        f'User id: {message.from_user.id}\n'
                                                        f'Имя: {message.from_user.full_name}')
                        return
                
            await message.answer('🧐 Я не смог найти ваш инвайт-код в базе данных.\n\nПроверьте, полностью ли вы скопировали ссылку, которую вам дал ваш друг.')
            return
        else:
            await message.answer('⛔️ Регистрация в сервисе только по приглашениям.\n\n'
                                 'Попросите вашего друга, который вам рекомендовал бота, прислать вам ссылку-приглашение.\n'
                                 'Он сможет её найти в своём профиле в меню бота.')
            return
    else:
        await menu(message)
        return
    
