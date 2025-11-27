import re

def detect_device(user_agent):
    """Detect if the device is mobile or desktop"""
    mobile_patterns = [
        re.compile(r'Android', re.IGNORECASE),
        re.compile(r'iPhone', re.IGNORECASE),
        re.compile(r'iPad', re.IGNORECASE),
        re.compile(r'Windows Phone', re.IGNORECASE),
        re.compile(r'BlackBerry', re.IGNORECASE),
        re.compile(r'Mobile', re.IGNORECASE)
    ]
    
    # Check for mobile devices
    for pattern in mobile_patterns:
        if pattern.search(user_agent):
            return 'mobile'
    
    return 'desktop'

def get_client_info(request):
    """Extract client information from request"""
    user_agent = request.headers.get('User-Agent', '')
    device_type = detect_device(user_agent)
    
    return {
        'device_type': device_type,
        'user_agent': user_agent,
        'ip_address': request.remote_addr
    }