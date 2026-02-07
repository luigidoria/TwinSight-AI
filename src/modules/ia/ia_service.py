import re
import json
import logging
from typing import Dict, Any, Optional
from openai import OpenAI
from src.utils.env import get_environment
from time import time

# --- Logging Configuration ---
logger = logging.getLogger("TwinSight-AIService")

class AIService:
    def __init__(self):
        env = get_environment()
        self.url = env.get("API_URL")
        self.api_key = env.get("API_KEY")
        self.model_for_text = env.get("MODEL_FOR_TEXT")
        self.model_for_json = env.get("MODEL_FOR_JSON")

        # Validation
        if not self.url:
            logger.warning("API_URL not set. Defaulting to OpenAI public endpoints.")
        
        if not self.api_key:
            logger.warning("API_KEY not set. Some providers may fail.")

        # Initialize Client
        try:
            self.client = OpenAI(
                base_url=self.url,
                api_key=self.api_key
            )
            logger.info(f"AI Service initialized. Targets: {self.model_for_text} and {self.model_for_json}")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            raise

    def generate_analysis(self, context: str, prompt: str) -> str:
        """
        Generates a textual analysis based on technical context (DB Data).
        Used to explain the data retrieved from the database to the user.
        """
        system_prompt = (
            "You are a Senior Industrial Engineer specializing in predictive maintenance. "
            "Use the provided 'Context' (telemetry data) to answer the user's 'Task'. "
            "Offer concise, technical insights focusing on anomalies."
        )
        
        try:
            inicio = time()
            response = self.client.chat.completions.create(
                model=self.model_for_text,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Context (Database Data): {context}\n\nTask (User Question): {prompt}"}
                ],
                max_tokens=4096,
                temperature=0.3
            )
            fim = time()
            print(f"Analysis generated in {fim - inicio:.2f} seconds. | model={self.model_for_text}")
            analysis_raw = response.choices[0].message.content.strip()
            clean_content = re.sub(r'<think>.*?</think>', '', analysis_raw, flags=re.DOTALL).strip()
            logger.debug(f"Generated Analysis: {clean_content}")
            return clean_content
        
        except Exception as e:
            logger.error(f"Error generating analysis: {e}")
            return None
        
    def convert_to_json(self, unstructured_text: str, schema_description: str) -> Dict[str, Any]:
        """
        Extracts structured query parameters from natural language user input.
        Used to convert user questions into Database Query Filters.
        """
        system_prompt = (
            "You are a Database Query Parser. Your job is to extract search parameters "
            "from the user's natural language request into a strict JSON object. "
            "Do not answer the question. Output ONLY the JSON required to query the database. "
            f"Target Schema: {schema_description}"
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model_for_json,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": unstructured_text}
                ],
                response_format={"type": "json_object"},
                temperature=0.1 
            )
            
            json_str = response.choices[0].message.content.strip()
            logger.debug(f"Raw JSON Output: {json_str}")
            return json.loads(json_str)
        
        except json.JSONDecodeError as jde:
            logger.error(f"JSON decoding failed: {jde}")
            return {"error": "Invalid JSON format returned by AI"}
        except Exception as e:
            logger.error(f"Error converting to JSON: {e}")
            return {"error": str(e)}
        

# --- Unit Test (Simulation of the Correct Flow) ---
if __name__ == "__main__":
    # Carrega as configs do .env (seja Groq, Ollama ou OpenAI)
    ai = AIService()
    
    # CENÁRIO: O engenheiro faz uma pergunta técnica em português
    user_question = "Verifique se o Motor MTR-01 teve vibração acima de 5.0 mm/s nas ultimas 2 horas."
    
    print(f"1. Pergunta do Usuário: '{user_question}'\n")

    # 2. SCHEMA: Define o que queremos extrair para filtrar no SQL
    # Isso ensina a IA quais campos existem no nosso banco de dados virtual
    db_query_schema = """
    {
        "asset_id": "string (ex: 'MTR-01', 'PUMP-02')",
        "metric_type": "string (ex: 'temperature', 'vibration', 'speed', 'load')",
        "comparison_operator": "string (ex: '>', '<', '>=', '=')",
        "threshold_value": "number (valor numérico para comparação, ex: 80.5)",
        "time_range": "string (ex: '2h', '24h', '30m', 'infinite')"
    }
    """

    print("2. Extraindo Parâmetros de Busca (JSON Mode)...")
    
    query_params = ai.convert_to_json(
        unstructured_text=user_question, 
        schema_description=db_query_schema
    )
    
    print(f"   -> Filtros para SQL: {json.dumps(query_params, indent=2)}\n")

    # 3. (Simulado) Busca no Banco de Dados usando os filtros acima
    # Imaginamos que o database_handler.py rodou um: 
    # SELECT * FROM telemetry WHERE motor_id='MTR-01' AND vibration > 5.0 AND time > NOW() - INTERVAL '2 hours'
    print("3. Buscando no Banco de Dados (Simulado)...")
    
    # Resultado fictício que o banco retornaria
    db_results = (
        "Logs encontrados:\n"
        "- 10:30 | MTR-01 | Vibração: 5.2 mm/s (ALERTA)\n"
        "- 10:35 | MTR-01 | Vibração: 5.8 mm/s (ALERTA)\n"
        "- 10:40 | MTR-01 | Vibração: 4.9 mm/s (NORMAL)\n"
        "- 10:45 | MTR-01 | Vibração: 6.1 mm/s (CRÍTICO)"
    )
    print(f"   -> Dados Retornados:\n{db_results}\n")
    
    # 4. Análise Técnica Final (Text Mode)
    # A IA recebe os dados "crus" e explica para o humano
    print("4. Gerando Análise Técnica (Text Mode)...")
    final_analysis = ai.generate_analysis(
        context=db_results, 
        prompt=user_question
    )
    print(f"   -> Resposta do Engenheiro AI:\n{final_analysis}")