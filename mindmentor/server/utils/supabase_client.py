import os
from dotenv import load_dotenv
from supabase import create_client, Client
import logging

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

# supabase_client.py


# Set up logging for better debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Explicitly load .env located one folder above this file
dotenv_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(dotenv_path)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise Exception("❌ SUPABASE_URL or SUPABASE_KEY not set in .env file")

try:
    # Create a global Supabase client (service role access for backend operations)
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    logger.info("✅ Supabase client initialized successfully")
except Exception as e:
    logger.error(f"❌ Failed to initialize Supabase client: {e}")
    raise

def get_supabase_with_token(access_token: str) -> Client:
    """
    Create Supabase client authenticated with user's access token.
    
    Args:
        access_token (str): User's JWT access token
        
    Returns:
        Client: Authenticated Supabase client
    """
    try:
        authed_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        authed_client.auth.set_session(access_token)
        return authed_client
    except Exception as e:
        logger.error(f"❌ Failed to create authenticated client: {e}")
        raise

def test_connection() -> bool:
    """
    Test if Supabase connection is working.
    
    Returns:
        bool: True if connection successful, False otherwise
    """
    try:
        # Simple test query
        response = supabase.table('profiles').select('id').limit(1).execute()
        logger.info("✅ Supabase connection test successful")
        return True
    except Exception as e:
        logger.error(f"❌ Supabase connection test failed: {e}")
        return False

# Test connection on import (optional - comment out if it slows startup)
if __name__ == "__main__":
    test_connection()
