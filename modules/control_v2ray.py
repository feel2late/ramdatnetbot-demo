import random
import subprocess
import traceback
import requests
import json
from db_requests import get_ss_port
from domains import API_SERVER_DOMAINS
import asyncio
import aiohttp
from bot_init import bot
import config


def restart_server():
    try:
        subprocess.run(['systemctl', 'restart', 'xray.service'], check=True)
        print('Xray server successfully restart.')
        return True
    except subprocess.CalledProcessError:
        return False


async def get_free_ss_port() -> int:
    while True:
        random_port = random.randint(10000, 30000)
        existing_keys = await get_ss_port(random_port)
        if not existing_keys:
            return random_port
    

async def create_new_xray_user(user_telegram_id: int, is_blocked: bool) -> list[object]:
    """Возвращае список ответов серверов"""
    shadowsocks_port = await get_free_ss_port()
    headers = {"Authorization": "***", "Content-Type": "application/json"}
    user_info = {'user_telegram_id': user_telegram_id, 'is_blocked': is_blocked, 'shadowsocks_port': shadowsocks_port}
    responses = []
    for domain in API_SERVER_DOMAINS:
        url = f'https://{domain}:8443/create_user'
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=user_info, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    responses.append(await response.json())
        except asyncio.exceptions.TimeoutError:
            try:
                await bot.send_message(user_telegram_id, f'Ошибка создания ключей на сервере {domain}: сервер недоступен.')
            except:
                pass
            await bot.send_message(config.admins[0], f'Ошибка создания ключей на сервере {domain}: сервер недоступен (таймаут после 5 секунд).')
        except Exception as e:
            print(traceback.format_exc())
    return responses


async def unblock_xray_user(*keys):
    """Ключи передавать СТРОГО в порядке соответствия серверам, перечисленным в файле domains.py!"""
    headers = {"Authorization": "***", "Content-Type": "application/json"}
    for server_id, key in enumerate(keys):
        url = f'https://{API_SERVER_DOMAINS[server_id]}:8443/unblock_user'
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json={"ss_key": key.get('ss_key'), 'vless_key': key.get('vless_key'), 'user_telegram_id': key.get('user_telegram_id')}, 
                                        timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status != 200:
                        await bot.send_message(config.admins[0], f'Ошибка разблокировки ключей на сервере {API_SERVER_DOMAINS[server_id]}:\n{await response.text()}')
        except asyncio.exceptions.TimeoutError:
            await bot.send_message(config.admins[0], f'Ошибка разблокировки ключей на сервере {API_SERVER_DOMAINS[server_id]}: сервер недоступен (таймаут после 5 секунд).')
        except:
            await bot.send_message(config.admins[0], f'Ошибка разблокировки ключей на сервере {API_SERVER_DOMAINS[server_id]}:\n{traceback.format_exc()}')



async def block_xray_user(*keys):
    """Ключи передавать СТРОГО в порядке соответствия серверам, перечисленным в файле domains.py!"""
    headers = {"Authorization": "***", "Content-Type": "application/json"}
    for server_id, key in enumerate(keys):
        url = f'https://{API_SERVER_DOMAINS[server_id]}:8443/block_user'
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json={"ss_key": key.get('ss_key'), 'vless_key': key.get('vless_key'), 'user_telegram_id': key.get('user_telegram_id')}, 
                                        timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status != 200:
                        await bot.send_message(config.admins[0], f'Ошибка разблокировки ключей на сервере {API_SERVER_DOMAINS[server_id]} для пользователя {key.get("user_telegram_id")}:\n{await response.text()}')
                    
        
        except asyncio.exceptions.TimeoutError:
            await bot.send_message(config.admins[0], f'Ошибка блокировки ключей на сервере {API_SERVER_DOMAINS[server_id]} для пользователя {key.get("user_telegram_id")}: сервер недоступен (таймаут после 5 секунд).')
        except:
            await bot.send_message(config.admins[0], f'Ошибка блокировки ключей на сервере {API_SERVER_DOMAINS[server_id]} для пользователя {key.get("user_telegram_id")}:\n{traceback.format_exc()}')