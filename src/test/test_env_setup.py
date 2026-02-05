import os
import sys
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_environment():
    """
    Simples teste para verificar se as variáveis de ambiente 
    estão sendo carregadas corretamente do arquivo .env
    """
    print("Iniciando diagnóstico de ambiente...")
    
    # Tenta carregar o .env
    loaded = load_dotenv()
    
    if not loaded:
        print("ERRO: Arquivo .env não encontrado ou vazio.")
        return
    
    secret_key = os.getenv("API_KEY")
    masked_key = f"{secret_key[:4]}...{secret_key[-4:]}" if secret_key else "None"
    model_text = os.getenv("MODEL_FOR_TEXT")
    model_json = os.getenv("MODEL_FOR_JSON")
    
    print(f".env carregado com sucesso!")
    print(f"API_KEY: {masked_key}")
    print(f"Modelo de Texto: {model_text}")
    print(f"Modelo JSON: {model_json}")
    print("-" * 30)

if __name__ == "__main__":
    test_environment()