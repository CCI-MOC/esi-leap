def register_all():
    __import__("esi_leap.objects.console_auth_token")
    __import__("esi_leap.objects.event")
    __import__("esi_leap.objects.lease")
    __import__("esi_leap.objects.offer")
