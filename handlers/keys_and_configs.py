from aiogram import types
from aiogram.filters.command import Command
from aiogram.filters import  Text
import config
import db_requests
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot_init import bot
from modules.client import Client
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.filters.chat_member_updated import MEMBER, KICKED

router = Router()


@router.message(Command('get_key'))
@router.callback_query(Text('keys_and_configs'))
async def keys_and_configs(callback: types.CallbackQuery):
    if not hasattr(callback, 'message') and not db_requests.is_registered(callback.from_user.id):
        await callback.answer('Кажется вы не зарегистрировались 🤨\n\n'
                                 'Попросите вашего друга, который вам рекомендовал бота, прислать вам ссылку-приглашение.\n'
                                 'Он сможет её найти в своём профиле в меню бота.', reply_markup='')
        return
    builder = InlineKeyboardBuilder()
    builder.button(text='Outline', callback_data='outline')
    builder.button(text='FoXray/v2rayNG', callback_data='xray')
    #builder.button(text='❓Какой выбрать?', callback_data='which_to_choose')
    builder.button(text='🔙 Назад', callback_data='menu')
    builder.adjust(1)
    message_text = ('Вы можете подключиться по двум протоколам (приложениям):\n\n'
                    '<b>Outline</b> - Протокол Shadowsocks - проверенный временем, быстрый, но легко определяется властями и есть риск блокировки.\n\n'
                    '<b>FoXray/v2rayNG</b> - Протокол XTLS-Reality - самая передовая и недетектируемая технология обхода блокировок. Власти не умеют определять и блокировать.')
    if hasattr(callback, 'message'):
        await callback.message.edit_text(message_text, reply_markup=builder.as_markup())
    else:
        await callback.answer(message_text, reply_markup=builder.as_markup())



@router.callback_query(Text('xray'))
async def xray(callback: types.CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.button(text='🇫🇮 Финляндия', callback_data='get_xray_key_fin')
    builder.button(text='🇳🇱 Нидерланды', callback_data='get_xray_key_ned')
    #builder.button(text='🇷🇺 Россия', callback_data='get_xray_key_rus')
    builder.button(text='🔙 Назад', callback_data='keys_and_configs')
    builder.adjust(1)

    message_text = 'Выберите страну для подключения по протоколу XTLS-Reality.\n\n'
    await callback.message.edit_text(message_text, reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith('get_xray_key_'))
async def get_outline_key(callback: types.CallbackQuery):
    country = callback.data[13:]
    builder = InlineKeyboardBuilder()
    builder.button(text='📲 Скачать FoXray или v2rayNG', callback_data='get_xray_app')
    builder.button(text='🔙 Назад', callback_data='xray')
    builder.adjust(1)
    client = Client(callback.from_user.id)
    
    if country == 'fin':
        if not client.v2ray4_key:
            create_status = await client.create_v2ray_key(server='rdn-fin')
            if create_status not in [200, 409]:
                message_text = 'Ошибка создания ключа доступа. Информация уже отправлена разработчику, попробуйте позже.'
                await bot.send_message(config.admins[0], 'Ошибка при создании xray ключа на сервере Финляндия.')
            else:
                message_text = (f'Скопируйте ключ <i>(копируется при нажатии на него)</i> и вставьте его в приложение FoXray (iOS) или v2rayNG (Android).\n\n'
                                f'<code>vless://{client.v2ray4_key}@rdn-fin.ramdatnet.space:443?flow=xtls-rprx-vision&type=tcp&security=reality&fp=chrome&sni=www.samsung.com&pbk=clSf7bklBmz6IictrfRrQ8jbfXsvhnp40mjbMkklXyI&sid=80f4edbab1b18af3#RAMDATNET! 🇫🇮 Finland</code>')
        else:
            message_text = (f'Скопируйте ключ <i>(копируется при нажатии на него)</i> и вставьте его в приложение FoXray (iOS) или v2rayNG (Android).\n\n'
                            f'<code>vless://{client.v2ray4_key}@rdn-fin.ramdatnet.space:443?flow=xtls-rprx-vision&type=tcp&security=reality&fp=chrome&sni=www.samsung.com&pbk=clSf7bklBmz6IictrfRrQ8jbfXsvhnp40mjbMkklXyI&sid=80f4edbab1b18af3#RAMDATNET! 🇫🇮 Finland</code>')
    elif country == 'ned':
        if not client.v2ray1_key:
            create_status = await client.create_v2ray_key(server='rdn-ned')
            if create_status not in [200, 409]:
                message_text = 'Ошибка создания ключа доступа. Информация уже отправлена разработчику, попробуйте позже.'
                await bot.send_message(config.admins[0], 'Ошибка при создании xray ключа на сервере Нидерланды.')
            else:
                message_text = (f'Скопируйте ключ <i>(копируется при нажатии на него)</i> и вставьте его в приложение Outline.\n\n'
                            f'<code>vless://{client.v2ray1_key}@rdn-ned.ramdatnet.space:443?flow=xtls-rprx-vision&type=tcp&security=reality&fp=chrome&sni=www.samsung.com&pbk=8WlCXDUo5g787g8nJCt_FcAeaFDY0FWB4AnVO_4FhCI&sid=b3af36d97da93973#RAMDATNET! 🇳🇱 Nederland</code>')
        else:
            message_text = (f'Скопируйте ключ <i>(копируется при нажатии на него)</i> и вставьте его в приложение Outline.\n\n'
                            f'<code>vless://{client.v2ray1_key}@rdn-ned.ramdatnet.space:443?flow=xtls-rprx-vision&type=tcp&security=reality&fp=chrome&sni=www.samsung.com&pbk=8WlCXDUo5g787g8nJCt_FcAeaFDY0FWB4AnVO_4FhCI&sid=b3af36d97da93973#RAMDATNET! 🇳🇱 Nederland</code>')
    elif country == 'rus':
        message_text = (f'Локация "🇷🇺 Россия" доступна только по протоколу Shadowsocks.\n\n')
        builder = InlineKeyboardBuilder()
        builder.button(text='Перейти к настройке Shadowsocks', callback_data='get_outline_key_rus')
        builder.button(text='🔙 Назад', callback_data='xray')
        builder.adjust(1)

    await callback.message.edit_text(message_text, reply_markup=builder.as_markup())


@router.callback_query(Text('xray_instruction'))
async def xray(callback: types.CallbackQuery, state: FSMContext):
    fsmdata = await state.get_data()
    bot_message = fsmdata.get('bot_message')
    await bot_message.edit_reply_markup(answer_markup='')
    builder = InlineKeyboardBuilder()
    builder.button(text='🍏 IOS', callback_data='xray_instruction_iphone')
    builder.button(text='🤖 Android', callback_data='xray_instruction_android')
    builder.button(text='🔙 Назад в XTLS-Reality', callback_data='xray')
    builder.adjust(1)
    bot_message = await callback.message.answer('Выберите свою операционную систему.', reply_markup=builder.as_markup())
    await state.update_data(bot_message=bot_message)


@router.callback_query(Text('xray_instruction_iphone'))
async def xray_instruction(callback: types.CallbackQuery, state: FSMContext):
    fsmdata = await state.get_data()
    bot_message = fsmdata.get('bot_message')
    await bot_message.delete()
    message_text = ('Сейчас сверху два сообщения:\n\n'
                    '1) Ссылка, которую нужно скопировать (vless://).\n\n'
                    '2) Скриншоты с описанием куда эту ссылку вставить и как подключиться.\n\n')
    builder = InlineKeyboardBuilder()
    builder.button(text='Скачать FoXray для IOS', url='https://apps.apple.com/us/app/foxray/id6448898396')
    builder.button(text='🔙 Назад в XTLS-Reality', callback_data='xray')
    builder.adjust(1)
    photos = [
        types.InputMediaPhoto(media='AgACAgIAAxkBAAJ_NWTTsd7oSKAkPE3nkpThltnm6ua6AAIu0jEbYqiZSh15E9J-WF-0AQADAgADeQADMAQ', caption='Шаг 1'),
        types.InputMediaPhoto(media='AgACAgIAAxkBAAJ_OGTTsgcxtJCUbKh7-RWVurqntIHcAAIx0jEbYqiZSltdcXTOc-faAQADAgADeQADMAQ', caption='Шаг 2')
    ]
    await bot.send_media_group(chat_id=callback.from_user.id, media=photos)
    await callback.message.answer(message_text, reply_markup=builder.as_markup())
    

@router.callback_query(Text('xray_instruction_android'))
async def xray_instruction(callback: types.CallbackQuery, state: FSMContext):
    fsmdata = await state.get_data()
    bot_message = fsmdata.get('bot_message')
    await bot_message.delete()
    
    message_text = ('Сейчас сверху два сообщения:\n\n'
                    '1) Ссылка, которую нужно скопировать (vless://).\n\n'
                    '2) Скриншоты с описанием куда эту ссылку вставить и как подключиться.\n\n')
    builder = InlineKeyboardBuilder()
    builder.button(text='Скачать v2rayNG для Android', url='https://play.google.com/store/apps/details?id=com.v2ray.ang&hl=ru&gl=US')
    builder.button(text='🔙 Назад в XTLS-Reality', callback_data='xray')
    builder.adjust(1)
    photos = [
        types.InputMediaPhoto(media='AgACAgIAAxkBAAJ_O2TTsg8Ze7qnT1qgL1IUW3jvpZKAAAIy0jEbYqiZShopBqHkKupUAQADAgADeQADMAQ', caption='Шаг 1'),
        types.InputMediaPhoto(media='AgACAgIAAxkBAAJ_PmTTshMobyOFMZVVow3qwTyHMpTMAAIz0jEbYqiZSnmYhqqbmWH1AQADAgADeQADMAQ', caption='Шаг 2'),
        types.InputMediaPhoto(media='AgACAgIAAxkBAAJ_QWTTshYtjaMWF64bfgjcK46MwRVlAAI00jEbYqiZSqm_R089PGkRAQADAgADeQADMAQ', caption='Шаг 3')
    ]
    await bot.send_media_group(chat_id=callback.from_user.id, media=photos)
    await callback.message.answer(message_text, reply_markup=builder.as_markup())


@router.callback_query(Text('which_to_choose'))
async def which_to_choose(callback: types.CallbackQuery):
    message_text = ''
    builder = InlineKeyboardBuilder()
    builder.button(text='🔙 Назад в ключи и конфиги', callback_data='keys_and_configs')
    await callback.message.edit_text(message_text, reply_markup=builder.as_markup())


@router.callback_query(Text('outline'))
async def outline(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    #builder.button(text='🔑 Получить ключ', callback_data='get_outline_key')
    #builder.button(text='📲 Скачать приложение', callback_data='get_outline_app')
    builder.button(text='🇫🇮 Финляндия', callback_data='get_outline_key_fin')
    builder.button(text='🇳🇱 Нидерланды', callback_data='get_outline_key_ned')
    builder.button(text='🇷🇺 Россия', callback_data='get_outline_key_rus')
    builder.button(text='🔙 Назад', callback_data='keys_and_configs')
    builder.adjust(1)
    message_text = 'Выберите страну для подключения по протоколу Shadowsocks.\n\n'
    await callback.message.edit_text(message_text, reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith('get_outline_key_'))
async def get_outline_key(callback: types.CallbackQuery):
    country = callback.data[16:]
    builder = InlineKeyboardBuilder()
    builder.button(text='📲 Скачать Outline', callback_data='get_outline_app')
    builder.button(text='🔙 Назад', callback_data='outline')
    builder.adjust(1)
    client = Client(callback.from_user.id)
    
    if country == 'fin':
        if not client.rdn4:
            create_status = client.create_outline_rdn4_key()
            if not create_status:
                message_text = 'Ошибка создания ключа доступа. Информация уже отправлена разработчику, попробуйте позже.'
                await bot.send_message(config.admins[0], 'Ошибка при создании Shadowsocks ключа на сервере Финляндия.')
            else:
                message_text = (f'Скопируйте ключ <i>(копируется при нажатии на него)</i> и вставьте его в приложение Outline.\n\n'
                                f'<code>{client.rdn4}#🇫🇮 Finland</code>')
        else:
            message_text = (f'Скопируйте ключ <i>(копируется при нажатии на него)</i> и вставьте его в приложение Outline.\n\n'
                            f'<code>{client.rdn4}#🇫🇮 Finland</code>')
    elif country == 'ned':
        if not client.rdn2:
            create_status = client.create_outline_rdn2_key()
            if not create_status:
                message_text = 'Ошибка создания ключа доступа. Информация уже отправлена разработчику, попробуйте позже.'
                await bot.send_message(config.admins[0], 'Ошибка при создании Shadowsocks ключа на сервере Нидерланды.')
            else:
                message_text = (f'Скопируйте ключ <i>(копируется при нажатии на него)</i> и вставьте его в приложение Outline.\n\n'
                            f'<code>{client.rdn2}#🇳🇱 Nederland</code>')
        else:
            message_text = (f'Скопируйте ключ <i>(копируется при нажатии на него)</i> и вставьте его в приложение Outline.\n\n'
                            f'<code>{client.rdn2}#🇳🇱 Nederland</code>')
    elif country == 'rus':
        if not client.rdn5:
            create_status = client.create_outline_rdn5_key()
            if not create_status:
                message_text = 'Ошибка создания ключа доступа. Информация уже отправлена разработчику, попробуйте позже.'
                await bot.send_message(config.admins[0], 'Ошибка при создании Shadowsocks ключа на сервере Россия.')
            else:
                message_text = (f'Скопируйте ключ <i>(копируется при нажатии на него)</i> и вставьте его в приложение Outline.\n\n'
                            '⚠️ Используйте этот ключ только для того, чтобы получить доступ к российским сервисам (банкам, госуслугам) если вы находитесь за границей.\n\n'
                            f'<code>{client.rdn5}#🇷🇺 Russia</code>')
        else:
            message_text = (f'Скопируйте ключ <i>(копируется при нажатии на него)</i> и вставьте его в приложение Outline.\n\n'
                            '⚠️ Используйте этот ключ только для того, чтобы получить доступ к российским сервисам (банкам, госуслугам) если вы находитесь за границей.\n\n'
                            f'<code>{client.rdn5}#🇷🇺 Russia</code>')

    await callback.message.edit_text(message_text, reply_markup=builder.as_markup())


