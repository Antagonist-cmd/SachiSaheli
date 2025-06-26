import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Explicitly load .env located one folder above this file
dotenv_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(dotenv_path)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise Exception("SUPABASE_URL or SUPABASE_KEY not set in .env")

# Create a global Supabase client (anon/public access)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_supabase_with_token(access_token: str) -> Client:
    """Create Supabase client authenticated with user's access token."""
    authed_client = create_client(SUPABASE_URL, SUPABASE_KEY)
    authed_client.auth.set_session(access_token)
    return authed_client
