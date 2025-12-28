export const FUNDAMENTALS_HELP = {
  MARKET_CAP: {
    name: "Market Capitalization",
    description: "Valoarea totală de piață a companiei (preț acțiune × nr. acțiuni)",
    interpretation: {
      mega_cap: "Peste $200B = Mega Cap (Apple, Microsoft) - Stabilitate mare",
      large_cap: "$10B-$200B = Large Cap - Companii mature, risc moderat",
      mid_cap: "$2B-$10B = Mid Cap - Creștere potențială, risc mediu",
      small_cap: "Sub $2B = Small Cap - Risc ridicat, volatilitate mare"
    },
    action: "Companiile mari (Mega/Large Cap) sunt mai stabile dar cresc mai lent. Small caps pot aduce randamente mari dar cu risc semnificativ."
  },
  PE_RATIO: {
    name: "Price-to-Earnings Ratio (P/E)",
    description: "Raportul între prețul acțiunii și profitul pe acțiune",
    interpretation: {
      low: "P/E < 15 = Subevaluat sau industrie matur\u0103",
      normal: "P/E 15-25 = Evaluare normală pentru majoritatea companiilor",
      high: "P/E 25-50 = Evaluare ridicată - așteptări mari de creștere",
      very_high: "P/E > 50 = Supraeval. EXTREM - risc de corecție mare"
    },
    action: "P/E ridicat (>50) combinat cu risc tehnic mare = PRUDENȚĂ! Prețul reflectă așteptări optimiste care pot să nu se materializeze."
  },
  REVENUE: {
    name: "Revenue (TTM - Trailing Twelve Months)",
    description: "Venituri totale generate în ultimele 12 luni",
    interpretation: {
      growth: "Creștere YoY > 20% = Companie în expansiune rapidă",
      stable: "Creștere YoY 5-20% = Creștere sănătoasă",
      declining: "Scădere YoY = RED FLAG - investigați cauza"
    },
    action: "Revenue în creștere constantă = semn de sănătate. Scăderi consecutive = avertisment."
  },
  FREE_CASH_FLOW: {
    name: "Free Cash Flow (FCF)",
    description: "Bani cash generați după investiții capitale (disponibili pentru dividende, buybacks)",
    interpretation: {
      positive_high: "FCF pozitiv > $10B = Companie foarte profitabilă",
      positive: "FCF pozitiv = Bun - compania generează cash",
      negative: "FCF negativ = Compania arde cash - risc pentru investitori"
    },
    action: "FCF pozitiv consistent = indicator excelent de sănătate financiară. FCF negativ = risc mare de probleme viitoare."
  },
  DEBT: {
    name: "Total Debt & Debt-to-Equity",
    description: "Datorii totale ale companiei față de capitalul propriu",
    interpretation: {
      low: "D/E < 0.5 = Datorie mică - bilanț sănătos",
      moderate: "D/E 0.5-1.5 = Datorie moderată - acceptabil",
      high: "D/E 1.5-3 = Datorie ridicată - risc în recesiune",
      very_high: "D/E > 3 = Datorie CRITICĂ - risc de faliment"
    },
    action: "Companii cu datorie mare (D/E > 2) sunt vulnerabile în crize. Preferă companii cu D/E < 1 pentru siguranță."
  },
  PROFIT_MARGIN: {
    name: "Profit Margin",
    description: "Procentul din venituri care devine profit net",
    interpretation: {
      excellent: "> 25% = Marjă excelentă (tech companies)",
      good: "10-25% = Marjă bună",
      average: "5-10% = Marjă medie (retail, auto)",
      poor: "< 5% = Marjă slabă - presiune pe costuri"
    },
    action: "Marje mari (>20%) = avantaj competitiv puternic (ex: Apple). Marje mici = business dificil, sensibil la costuri."
  }
};

export function getFundamentalsHelp(key) {
  return FUNDAMENTALS_HELP[key] || null;
}
