import requests
import urllib3
urllib3.disable_warnings()
import json
import subprocess



def get_rdn2_status():
    headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36'
    }
    try:
        request = requests.get(f'https://***/server', headers=headers, verify=False)
        return request.text
    except:
        return False
    

def get_rdn4_status():
    headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36'
    }
    try:
        request = requests.get(f'https://***/server', headers=headers, verify=False)
        return request.text
    except:
        return False
    

def get_rdn5_status():
    headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36'
    }
    try:
        request = requests.get(f'https://***/server', headers=headers, verify=False)
        return request.text
    except:
        return False


def get_xray_ned_status():
    try:
        request = requests.get(f'https://api.rdn-ned.ramdat.net:8443/get_status')
        return request.json()
    except:
        return {'status': 'shutdown'}
    

def get_xray_fin_status():
    try:
        request = requests.get(f'https://api.rdn-fin.ramdat.net:8443/get_status', verify=False)
        return request.json()
    except:
        return {'status': 'shutdown'}
    
def get_xray_swe_status():
    try:
        request = requests.get(f'https://api.rdn-swe.ramdat.net:8443/get_status', verify=False)
        return request.json()
    except:
        return {'status': 'shutdown'}
    

