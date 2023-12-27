import base64


async def uri_encode(uri: str) -> str:
    """Кодирование URI в base64"""
    encoded_bytes = base64.urlsafe_b64encode(uri.encode('utf-8'))
    encoded_text = encoded_bytes.decode('utf-8')
    return encoded_text