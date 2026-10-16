import os

from dotenv import load_dotenv
from supabase import create_client, Client

# Carrega as variáveis definidas no arquivo .env.
load_dotenv()

# Obtém a URL e a chave do projeto Supabase sem expô-las no código.
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

# Cria um cliente reutilizável para acessar banco e Storage do Supabase.
supabase: Client = create_client(url, key)
