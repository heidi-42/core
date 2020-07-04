import keyring


EMAIL = 'http://localhost:33333'

ACCESS = 'http://localhost:33334'

POSTGRES_PASSWD = keyring.get_password('postgres', 'heidi')
POSTGRES = f'postgresql://heidi:{POSTGRES_PASSWD}@localhost'

REDIS_PASSWD = keyring.get_password('redis', 'heidi')
REDIS = f'redis://:{REDIS_PASSWD}@localhost'

DELIVERY = 'http://localhost:33335'

