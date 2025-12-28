import os
import logging
from openai import AsyncOpenAI
from dotenv import load_dotenv
from typing import Dict, Any, List, Optional

load_dotenv()
logger = logging.getLogger(__name__)

class AIAnalyzer:
    def __init__(self):
        # Folosim Emergent LLM Key
        self.api_key = os.environ.get('OPENAI_API_KEY')
        if not self.api_key:
            logger.warning("OPENAI_API_KEY not found in environment - using fallback")
        
        self.client = AsyncOpenAI(api_key=self.api_key) if self.api_key else None

    async def analyze(
        self, 
        symbol: str, 
        indicators: Dict[str, Any], 
        risk_data: Dict[str, Any], 
        signal: str, 
        context: Dict[str, Any], 
        alerts: List[Dict[str, Any]], 
        fundamentals: Optional[Dict[str, Any]] = None
    ) -> str:
        if not self.client:
            logger.warning("OpenAI client not initialized - using fallback")
            return self._generate_fallback_analysis(symbol, indicators, signal, risk_data, fundamentals)
        
        try:
            analysis_context = self._build_context(symbol, indicators, risk_data, signal, context, alerts, fundamentals)
            
            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system", 
                        "content": """Ești un expert senior în analiză tehnică și fundamentală pentru trading.
Analizează datele și oferă o interpretare STRUCTURATĂ, PRECISĂ și ACȚIONABILĂ în limba română.

Format OBLIGATORIU (exact 4 secțiuni):

1. 📊 **Aspect Tehnic**: 
   - Analiza indicatorilor tehnici (RSI, MACD, Trend, Suport/Rezistență)
   - Identifică setup-ul curent (trending, ranging, overbought, oversold)

2. 💰 **Fundamentale**: 
   - Sănătate financiară (Revenue, FCF, Debt, Valuation)
   - Evaluează soliditatea companiei pe termen lung

3. ⚠️ **Riscuri**: 
   - Identifică riscurile majore (Overbought, Volum scăzut, Earnings, etc.)
   - Evaluează probabilitatea de eșec

4. 🎯 **Plan de Acțiune**:
   - Dacă BUY: Preț intrare, SL, TP precis
   - Dacă WAIT/NEUTRAL: 
     * **Buy the Dip**: "Așteptați retragere la suport $X (R/R devine Y:1). Setați Limit Order."
     * **Breakout Alert**: "Monitorizați rezistență $X. Cumpărați DOAR dacă volum > 1.2x."
     * **Earnings Warning**: "Raport în X zile - Stay in Cash până după publicare."
   - Dacă SELL: "Take Profit acum - protejați capitalul."

Fii SPECIFIC, DIRECT și UTIL. Include NUMERE CONCRETE (prețuri, procente, niveluri). 
Evită generalitățile - oferă un plan de acțiune clar pe care traderul îl poate executa imediat."""
                    },
                    {
                        "role": "user", 
                        "content": f"Analizează {symbol}:\n\n{analysis_context}"
                    }
                ],
                max_tokens=700,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"AI analysis error for {symbol}: {str(e)}")
            return self._generate_fallback_analysis(symbol, indicators, signal, risk_data, fundamentals)

    def _build_context(
        self, 
        symbol: str, 
        indicators: Dict[str, Any], 
        risk_data: Dict[str, Any], 
        signal: str, 
        context: Dict[str, Any], 
        alerts: List[Dict[str, Any]], 
        fundamentals: Optional[Dict[str, Any]]
    ) -> str:
        """Build comprehensive context for AI analysis"""
        lines = []
        
        # 1. Basic Info
        lines.append(f"═══ ANALIZĂ COMPLETĂ: {symbol} ═══\n")
        lines.append(f"🎯 SEMNAL GENERAT: {signal}")
        lines.append(f"📊 PREȚ CURENT: ${indicators['price']['current']:.2f}\n")
        
        # 2. Technical Indicators
        lines.append("═══ INDICATORI TEHNICI ═══")
        lines.append(f"• RSI(14): {indicators['rsi']['value']:.1f} - {indicators['rsi']['signal']}")
        lines.append(f"• Stoch RSI: K={indicators['stoch_rsi']['k']:.1f}%, D={indicators['stoch_rsi']['d']:.1f}%")
        lines.append(f"• ADX: {indicators['adx']['value']:.1f} ({indicators['adx']['regime']})")
        lines.append(f"• MACD: {indicators['macd']['cross']} cross")
        lines.append(f"• Trend: {indicators['trend']['direction']} ({indicators['trend']['strength']})")
        lines.append(f"• EMA 20: ${indicators['price']['ema_20']:.2f}")
        lines.append(f"• EMA 50: ${indicators['price']['ema_50']:.2f}")
        if indicators['price'].get('ema_200'):
            lines.append(f"• EMA 200: ${indicators['price']['ema_200']:.2f}")
        lines.append(f"• Volum: {indicators['volume']['ratio']:.2f}x media ({indicators['volume']['trend']})\n")
        
        # 3. Risk Management
        lines.append("═══ RISK MANAGEMENT ═══")
        lines.append(f"• Entry: ${risk_data['entry_price']:.2f}")
        lines.append(f"• Stop Loss: ${risk_data['stop_loss']:.2f} (-{risk_data['stop_loss_percent']:.1f}%)")
        lines.append(f"• Take Profit: ${risk_data['take_profit']:.2f}")
        lines.append(f"• Risk/Reward: {risk_data['risk_reward_ratio']:.2f}")
        lines.append(f"• Suport Major: ${risk_data['support']:.2f}")
        lines.append(f"• Rezistență Major: ${risk_data['resistance']:.2f}")
        lines.append(f"• Risc: {risk_data['risk_assessment']}\n")
        
        # 4. Fundamentals (if available)
        if fundamentals:
            lines.append("═══ FUNDAMENTALE ═══")
            
            # Market Cap
            if fundamentals.get('market_cap'):
                mc = fundamentals['market_cap']
                if mc > 1e12:
                    lines.append(f"• Market Cap: ${mc/1e12:.2f}T")
                elif mc > 1e9:
                    lines.append(f"• Market Cap: ${mc/1e9:.2f}B")
                else:
                    lines.append(f"• Market Cap: ${mc/1e6:.2f}M")
            
            # Valuation
            if fundamentals.get('pe_ratio'):
                lines.append(f"• P/E Ratio: {fundamentals['pe_ratio']:.2f}")
            if fundamentals.get('price_to_book'):
                lines.append(f"• P/B Ratio: {fundamentals['price_to_book']:.2f}")
            
            # Profitability
            if fundamentals.get('profit_margin'):
                lines.append(f"• Profit Margin: {fundamentals['profit_margin']*100:.1f}%")
            if fundamentals.get('return_on_equity'):
                lines.append(f"• ROE: {fundamentals['return_on_equity']*100:.1f}%")
            
            # Growth
            if fundamentals.get('revenue'):
                rev = fundamentals['revenue']
                if rev > 1e9:
                    lines.append(f"• Revenue (TTM): ${rev/1e9:.2f}B")
                else:
                    lines.append(f"• Revenue (TTM): ${rev/1e6:.2f}M")
            
            if fundamentals.get('revenue_growth'):
                lines.append(f"• Revenue Growth: {fundamentals['revenue_growth']*100:.1f}%")
            
            # Financial Health
            if fundamentals.get('free_cash_flow'):
                fcf = fundamentals['free_cash_flow']
                if fcf > 1e9:
                    lines.append(f"• Free Cash Flow: ${fcf/1e9:.2f}B")
                elif fcf < 0:
                    lines.append(f"• Free Cash Flow: NEGATIV (${fcf/1e6:.1f}M) ⚠️")
                else:
                    lines.append(f"• Free Cash Flow: ${fcf/1e6:.2f}M")
            
            if fundamentals.get('debt_to_equity'):
                dte = fundamentals['debt_to_equity']
                if dte > 200:
                    lines.append(f"• Debt/Equity: {dte:.0f}% ⚠️ RIDICAT")
                else:
                    lines.append(f"• Debt/Equity: {dte:.1f}%")
            
            lines.append("")
        
        # 5. Market Context
        lines.append("═══ CONTEXT PIAȚĂ ═══")
        if context.get('vix'):
            lines.append(f"• VIX: {context['vix']['value']} ({context['vix']['level']})")
        if context.get('sp500'):
            lines.append(f"• S&P 500: {context['sp500']['trend']} ({context['sp500']['change_percent']:+.2f}%)\n")
        
        # 6. Alerts
        if alerts:
            lines.append("═══ ALERTE CRITICE ═══")
            for alert in alerts[:5]:  # Max 5 alerts
                lines.append(f"• {alert['type']}: {alert['message'][:100]}")
            lines.append("")
        
        return "\n".join(lines)

    def _generate_fallback_analysis(
        self, 
        symbol: str, 
        indicators: Dict[str, Any], 
        signal: str, 
        risk_data: Dict[str, Any], 
        fundamentals: Optional[Dict[str, Any]]
    ) -> str:
        """Generate fallback analysis when OpenAI is unavailable"""
        
        rsi = indicators['rsi']['value']
        stoch_rsi = indicators['stoch_rsi']['k']
        trend = indicators['trend']['direction']
        volume_ratio = indicators['volume']['ratio']
        rr_ratio = risk_data['risk_reward_ratio']
        
        analysis_parts = []
        
        # Technical Assessment
        if trend == 'BULLISH' and rsi < 70:
            analysis_parts.append("• 📊 Tehnic: Trend bullish activ cu RSI în zona normală. Setup favorabil.")
        elif trend == 'BULLISH' and rsi > 70:
            analysis_parts.append("• 📊 Tehnic: Trend bullish DAR RSI supracumpărat. Risc de corecție pe termen scurt.")
        elif trend == 'BEARISH':
            analysis_parts.append("• 📊 Tehnic: Trend bearish activ. Evitați intrări lungi până la revenire.")
        
        # Fundamentals
        if fundamentals:
            fcf = fundamentals.get('free_cash_flow', 0)
            dte = fundamentals.get('debt_to_equity', 0)
            
            if fcf > 0 and dte < 100:
                analysis_parts.append("• 💰 Fundamentale: Sănătate financiară solidă (FCF pozitiv, datorii moderate).")
            elif fcf < 0:
                analysis_parts.append("• 💰 Fundamentale: ⚠️ Free Cash Flow NEGATIV - compania arde bani. Risc ridicat.")
            elif dte > 200:
                analysis_parts.append("• 💰 Fundamentale: ⚠️ Debt/Equity > 200% - companie supraleviată. Prudență.")
        else:
            analysis_parts.append("• 💰 Fundamentale: Date fundamentale indisponibile.")
        
        # Risks
        risks = []
        if stoch_rsi > 85:
            risks.append("Stoch RSI extrem (>85%)")
        if volume_ratio < 0.8:
            risks.append("Volum scăzut (<0.8x)")
        if rr_ratio < 1.5:
            risks.append(f"R/R nefavorabil ({rr_ratio:.2f})")
        
        if risks:
            analysis_parts.append(f"• ⚠️ Riscuri: {', '.join(risks)}. Prudență recomandată.")
        else:
            analysis_parts.append("• ⚠️ Riscuri: Nu sunt detectate riscuri majore imediate.")
        
        # Recommendation with ACTION PLANS
        current_price = indicators['price']['current']
        support = risk_data.get('support', indicators['price'].get('ema_20', current_price * 0.95))
        resistance = risk_data.get('resistance', current_price * 1.05)
        ema_20 = indicators['price'].get('ema_20', current_price)
        ema_50 = indicators['price'].get('ema_50', current_price)
        adx = indicators.get('adx', {}).get('value', 20)
        
        if signal == 'BUY':
            analysis_parts.append(f"• 🎯 Recomandare: BUY cu R/R {rr_ratio:.2f}. SL strict la ${risk_data['stop_loss']:.2f}.")
        
        elif signal == 'SELL':
            analysis_parts.append("• 🎯 Recomandare: SELL - Take profit sau exit. Zone de overbought/risc ridicat.")
        
        elif signal == 'HOLD':
            analysis_parts.append("• 🎯 Recomandare: HOLD poziția actuală. Monitorizați nivelurile cheie.")
        
        elif signal in ['WAIT', 'NEUTRAL']:
            # Generate ACTION PLAN based on conditions
            action_plan_parts = ["• 🎯 Recomandare: WAIT - Setup nefavorabil."]
            
            # 1. Buy the Dip Plan
            if rr_ratio < 1.5 and support > 0:
                # Calculate ideal entry at support
                ideal_entry = support
                ideal_tp = resistance
                ideal_sl = ideal_entry * 0.97  # 3% below entry
                ideal_rr = (ideal_tp - ideal_entry) / (ideal_entry - ideal_sl)
                
                action_plan_parts.append(
                    f"💡 **Plan Alternativ (Buy the Dip)**: Așteptați o retragere (pullback) la nivelul de suport "
                    f"${support:.2f} (sau EMA 20 la ${ema_20:.2f}). "
                    f"Acolo, raportul Risc/Recompensă devine favorabil ({ideal_rr:.2f}:1). "
                    f"Setați un ordin limită (Limit Order) în această zonă."
                )
            
            # 2. Breakout Plan
            if adx < 20 and current_price > resistance * 0.95:
                action_plan_parts.append(
                    f"🚀 **Alertă Breakout**: Monitorizați prețul la depășirea rezistenței de ${resistance:.2f}. "
                    f"Cumpărați NUMAI dacă volumul (Volume Ratio) trece de 1.2x. "
                    f"Fără confirmare de volum, evitați intrarea (risc de breakout fals)."
                )
            
            # 3. Ranging Market Strategy
            if adx < 20:
                action_plan_parts.append(
                    f"📊 **Piață Laterală (ADX {adx:.1f}< 20)**: Evitați intrări noi până la confirmarea trendului. "
                    f"Așteptați ADX > 25 pentru mișcare direcțională clară."
                )
            
            # 4. Volume Warning
            if volume_ratio < 0.8:
                action_plan_parts.append(
                    f"⚠️ **Volum Scăzut ({volume_ratio:.2f}x)**: Lipsă de interes din partea cumpărătorilor. "
                    f"Mișcările pe volum mic sunt nesustenabile. Așteptați creșterea volumului la > 1.0x."
                )
            
            analysis_parts.append("\n".join(action_plan_parts))
        
        return "\n".join(analysis_parts)
