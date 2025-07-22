#!/usr/bin/env python3
"""
GUI-Test Script für Aktienanalyse
Testet direkt die GUI-Methoden
"""

import sys
import os
import importlib.util
import traceback

# Lade das GUI-Modul
try:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    spec = importlib.util.spec_from_file_location("gui_module", "news_gui_automated.py")
    gui_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gui_module)
    
    # Test-Artikel erstellen
    test_article = gui_module.NewsArticle(
        title="Fed Announces Interest Rate Cut of 0.75%",
        description="The Federal Reserve announced a significant interest rate cut of 0.75 percentage points to stimulate economic growth amid recession concerns.",
        source="Financial Times",
        link="https://example.com/fed-rate-cut",
        published="2025-01-20T14:30:00Z",
        ai_score=8.5,
        ai_reasoning="Hochrelevante Wirtschaftsnachricht mit globalen Auswirkungen"
    )
    
    print("🧪 Teste GUI-Aktienanalyse-Methoden...")
    print(f"📰 Test-Artikel: {test_article.title}")
    print(f"📊 News Score: {test_article.ai_score}")
    print()
    
    # Erstelle GUI-Instanz (nur für Methoden-Tests)
    gui = gui_module.NewsAnalyzerGUI()
    
    print("✅ GUI-Klasse erfolgreich geladen")
    print(f"🤖 AI Model Type: {getattr(gui.analyzer, 'ai_model_type', 'NICHT GESETZT')}")
    print()
    
    # Teste Prompt-Erstellung
    if hasattr(gui, '_create_stock_analysis_prompt'):
        prompt = gui._create_stock_analysis_prompt(test_article)
        print("✅ Stock Analysis Prompt erstellt:")
        print("=" * 50)
        print(prompt[:300] + "..." if len(prompt) > 300 else prompt)
        print("=" * 50)
    else:
        print("❌ _create_stock_analysis_prompt Methode nicht gefunden!")
    
    print()
    
    # Teste Ollama-Analyse direkt
    if hasattr(gui, 'analyze_with_ollama_live'):
        print("🤖 Teste analyze_with_ollama_live Methode...")
        try:
            result = gui.analyze_with_ollama_live([test_article])
            if result and len(result) > 0:
                analyzed_article = result[0]
                print("✅ Analyse erfolgreich!")
                print(f"📊 Stock Impact Score: {analyzed_article.stock_impact_score}")
                print(f"📈 Stock Direction: {analyzed_article.stock_direction}")
                print(f"🏢 Affected Stocks: {analyzed_article.affected_stocks}")
                print(f"💭 Stock Reasoning: {analyzed_article.stock_reasoning[:200]}...")
            else:
                print("❌ Keine Analyseergebnisse erhalten!")
        except Exception as e:
            print(f"❌ Fehler bei analyze_with_ollama_live: {e}")
            traceback.print_exc()
    else:
        print("❌ analyze_with_ollama_live Methode nicht gefunden!")

except Exception as e:
    print(f"❌ Fehler beim Laden der GUI: {e}")
    traceback.print_exc()
