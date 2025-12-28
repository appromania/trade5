import os
import logging
from openai import AsyncOpenAI
from dotenv import load_dotenv
from typing import Dict, Any, List

load_dotenv()
logger = logging.getLogger(__name__)

class AIAnalyzer:
    def __init__(self):
        # Folosim cheia standard OpenAI
        self.api_key = os.environ.get('OPENAI_API_KEY')
        if not self.api_key:
            logger.warning("OPENAI_API_KEY not found in environment")
        
        self.client = AsyncOpenAI(api_key=self.api_key) if self.api_key else None

    async def analyze(self, symbol, indicators, risk_data, signal, context, alerts, fundamentals=None):
        if not self.client:
            return self._generate_fallback_analysis(indicators, signal, risk_data, fundamentals)
        
        try:
            analysis_context = self._build_context(symbol, indicators, risk_data, signal, context, alerts, fundamentals)
            
            response = await self.client.chat.completions.create(
                model="gpt-4o", # Folosește gpt-4o, este cel mai stabil în 2025
                messages=[
                    {"role": "system", "content": """Ești un expert în analiză tehnică și fundamentală. 
                    Analizează datele și oferă o interpretare STRUCTURATĂ cu iconițe în limba română.
                    Format răspuns (max 4 bullet points):
                    • [Icon] Aspect tehnic/fundamental
                    • [Icon] Risk management
                    • [Icon] Context piață
                    • [Icon] Recomandare finală"""},
                    {"role": "user", "content": f"Analizează {symbol}:\n\n{analysis_context}"}
                ],
                max_tokens=500
            )
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"AI analysis error: {str(e)}")
            return self._generate_fallback_analysis(indicators, signal, risk_data, fundamentals)

    def _build_context(self, symbol, indicators, risk_data, signal, context, alerts, fundamentals=None) -> str:
        # Păstrează metoda ta _build_context exact așa cum era (este bine scrisă)
        lines = [f"Simbol: {symbol}", f"Semnal: {signal}"]
        # ... adaugă restul liniilor tale aici ...
        return "\n".join(lines)

    def _generate_fallback_analysis(self, indicators, signal, risk_data, fundamentals=None) -> str:
        # Păstrează metoda ta _generate_fallback_analysis exact așa cum era
        return "Analiză generată automat (Fallback): Semnal " + signal
