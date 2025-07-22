#!/usr/bin/env python3
"""
Debug-Script für Aktienmarkt-Analyse
Testet ob die Stock-Analyse funktioniert
"""

import requests
from dataclasses import dataclass
from typing import List

@dataclass
class NewsArticle:
    title: str = ""
    description: str = ""
    source: str = ""
    link: str = ""
    published: str = ""
    category: str = ""
    ai_score: float = 0.0
    ai_reasoning: str = ""
    stock_impact_score: float = 0.0
    stock_direction: str = "NEUTRAL"
    affected_stocks: List[str] = None
    stock_reasoning: str = ""
    
    def __post_init__(self):
        if self.affected_stocks is None:
            self.affected_stocks = []

def create_stock_analysis_prompt(article):
    """Erstellt einen Prompt für die Aktienmarkt-Analyse"""
    return f"""
Analysiere die möglichen Auswirkungen des folgenden Nachrichtenartikels auf den Aktienmarkt.

Artikel:
Titel: {article.title}
Beschreibung: {article.description}
Quelle: {article.source}

Bewerte die Marktauswirkungen:
1. StockScore: 1-10 (1=keine Auswirkung, 10=massive Marktbewegung)
2. Direction: UP/DOWN/NEUTRAL (erwartete Marktrichtung)
3. Stocks: Betroffene Aktien/Sektoren (kommagetrennt, oder "None" wenn keine)
4. StockReasoning: Kurze Begründung

Antworte in folgendem Format:
StockScore: [1-10]
Direction: [UP/DOWN/NEUTRAL]
Stocks: [Aktien/Sektoren oder None]
StockReasoning: [Begründung]
"""

def test_stock_analysis():
    """Testet die Aktienmarkt-Analyse mit einem Beispiel-Artikel"""
    
    # Test-Artikel
    test_article = NewsArticle(
        title="Fed Announces Interest Rate Cut of 0.75%",
        description="The Federal Reserve announced a significant interest rate cut of 0.75 percentage points to stimulate economic growth amid recession concerns.",
        source="Financial Times"
    )
    
    print("🧪 Teste Aktienmarkt-Analyse...")
    print(f"📰 Test-Artikel: {test_article.title}")
    print()
    
    # Erstelle Prompt
    prompt = create_stock_analysis_prompt(test_article)
    print("📝 Aktien-Prompt:")
    print("=" * 50)
    print(prompt)
    print("=" * 50)
    print()
    
    # Teste Ollama-API
    print("🤖 Sende an Ollama...")
    try:
        response = requests.post(
            'http://localhost:11434/api/generate',
            json={
                'model': 'llama2',
                'prompt': prompt,
                'stream': False
            },
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            analysis_text = result.get('response', '')
            
            print("✅ Ollama-Antwort erhalten:")
            print("-" * 30)
            print(analysis_text)
            print("-" * 30)
            print()
            
            # Parse das Ergebnis
            print("🔍 Parse Aktien-Analyse...")
            try:
                import re
                
                # Stock Score
                stock_score_match = re.search(r'StockScore:\s*(\d+(?:\.\d+)?)', analysis_text)
                if stock_score_match:
                    stock_score = float(stock_score_match.group(1))
                    print(f"📊 StockScore: {stock_score}")
                else:
                    stock_score = 1.0
                    print("❌ StockScore nicht gefunden, verwende 1.0")
                
                # Direction
                direction_match = re.search(r'Direction:\s*(\w+)', analysis_text)
                if direction_match:
                    direction = direction_match.group(1).upper()
                    print(f"📈 Direction: {direction}")
                else:
                    direction = "NEUTRAL"
                    print("❌ Direction nicht gefunden, verwende NEUTRAL")
                
                # Stocks
                stocks_match = re.search(r'Stocks:\s*(.+)', analysis_text)
                if stocks_match:
                    stocks_str = stocks_match.group(1).strip()
                    if stocks_str and stocks_str != "None" and stocks_str != "-":
                        stocks = [s.strip() for s in stocks_str.split(',') if s.strip()]
                        print(f"🏢 Stocks: {stocks}")
                    else:
                        stocks = []
                        print("📊 Stocks: Keine spezifischen Aktien")
                else:
                    stocks = []
                    print("❌ Stocks nicht gefunden")
                
                # Stock Reasoning
                stock_reasoning_match = re.search(r'StockReasoning:\s*(.+)', analysis_text, re.DOTALL)
                if stock_reasoning_match:
                    stock_reasoning = stock_reasoning_match.group(1).strip()
                    print(f"💭 Reasoning: {stock_reasoning}")
                else:
                    stock_reasoning = "Keine Aktienanalyse verfügbar"
                    print("❌ Stock Reasoning nicht gefunden")
                
                # Aktualisiere Test-Artikel
                test_article.stock_impact_score = min(10.0, max(1.0, stock_score))
                test_article.stock_direction = direction if direction in ['UP', 'DOWN', 'NEUTRAL'] else 'NEUTRAL'
                test_article.affected_stocks = stocks
                test_article.stock_reasoning = stock_reasoning
                
                print()
                print("✅ FINALE AKTIEN-ANALYSE:")
                print(f"   📊 Impact Score: {test_article.stock_impact_score}/10")
                print(f"   📈 Direction: {test_article.stock_direction}")
                print(f"   🏢 Affected Stocks: {test_article.affected_stocks}")
                print(f"   💭 Reasoning: {test_article.stock_reasoning}")
                
            except Exception as parse_error:
                print(f"❌ Parse-Fehler: {parse_error}")
                
        else:
            print(f"❌ Ollama-Fehler: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Verbindungsfehler: {e}")

if __name__ == "__main__":
    test_stock_analysis()
