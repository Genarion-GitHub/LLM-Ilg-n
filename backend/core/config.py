import os
from dotenv import load_dotenv

# .env dosyasının yolunu bul (bu dosyanın bir üst dizininde)
# Örn: backend/core/ -> backend/
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'api', '.env')

if os.path.exists(env_path):
    load_dotenv(dotenv_path=env_path)
else:
    print(f"Uyarı: .env dosyası şu yolda bulunamadı: {env_path}")
    load_dotenv() 

# .env'den DATA_PATH değişkenini oku ve dışarıya aktar
DATA_PATH = os.environ.get("DATA_PATH")

if not DATA_PATH:
    print("KRİTİK HATA: .env dosyasında DATA_PATH değişkeni ayarlanmamış!")