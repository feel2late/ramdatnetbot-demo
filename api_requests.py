import requests
import urllib3
urllib3.disable_warnings()


def set_limit(rdn2_id: str = None, rdn4_id: str = None, rdn5_id: str = None):
    if rdn2_id:
        requests.put(f'https://***/access-keys/{rdn2_id}/data-limit', json={"limit": {"bytes": 1000000}}, verify=False)
    if rdn4_id:
        requests.put(f'https://***/access-keys/{rdn4_id}/data-limit', json={"limit": {"bytes": 1000000}}, verify=False)
    if rdn5_id:
        requests.put(f'https://***/access-keys/{rdn5_id}/data-limit', json={"limit": {"bytes": 1000000}}, verify=False)


def delete_limit(rdn2_id: str = None, rdn4_id: str = None, rdn5_id: str = None):
    if rdn2_id:
        requests.delete(f'https://***/access-keys/{rdn2_id}/data-limit', verify=False)
    if rdn4_id:
        requests.delete(f'https://***/access-keys/{rdn4_id}/data-limit', verify=False)
    if rdn5_id:
        requests.delete(f'https://***/access-keys/{rdn5_id}/data-limit', verify=False)


def delete_access_key(rdn2_id: str = None, rdn4_id: str = None, rdn5_id: str = None):
    if rdn2_id:
        request = requests.delete(f'https://***/access-keys/{rdn2_id}', verify=False)
        print(request)
    if rdn4_id:
        request = requests.delete(f'https://***/access-keys/{rdn4_id}', verify=False)
        print(request)
    if rdn5_id:
        request = requests.delete(f'https://***/access-keys/{rdn5_id}', verify=False)
        print(request)

def get_data_transferred():
    response_rdn2 = requests.get('https://***/metrics/transfer', verify=False).json()
    response_rdn4 = requests.get('https://***/metrics/transfer', verify=False).json()

    return {'rdn2': response_rdn2, 'rdn4': response_rdn4}

