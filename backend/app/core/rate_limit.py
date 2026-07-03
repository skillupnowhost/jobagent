from slowapi import Limiter
from slowapi.util import get_remote_address

# In-memory storage is only correct because the app runs with a single
# gunicorn worker on the free-tier host. If worker count is ever raised
# above 1, this must switch to a Redis-backed storage_uri.
limiter = Limiter(key_func=get_remote_address)
