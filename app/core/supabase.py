from supabase import create_client, Client
from app.core.config import settings

# Public Supabase Client (Anon Key)
supabase_client: Client = (
    create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    if settings.SUPABASE_URL and settings.SUPABASE_KEY
    else None
)

# Admin Supabase Client (Service Role Key)
supabase_admin: Client = (
    create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
    if settings.SUPABASE_URL and settings.SUPABASE_SERVICE_ROLE_KEY
    else supabase_client
)
