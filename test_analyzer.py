#!/usr/bin/env python3
"""
Test-Skript für den News-Analyzer
Führt grundlegende Tests der Hauptfunktionen durch.
"""

import os
import sys
from unittest.mock import Mock, patch

# Füge das aktuelle Verzeichnis zum Python-Pfad hinzu
sys.path.insert(0, os.path.dirname(__file__))

try:
    # Importiere aus dem Hauptprogramm (P-News.py wird als P_News importiert)
    import importlib.util
    import sys
    
    # Lade das Hauptmodul dynamisch
    spec = importlib.util.spec_from_file_location("news_module", "P-News.py")
    news_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(news_module)
    
    NewsAnalyzer = news_module.NewsAnalyzer
    NewsArticle = news_module.NewsArticle
    
    import feedparser
    import requests
except ImportError as e:
    print(f"❌ Import-Fehler: {e}")
    print("Bitte stellen Sie sicher, dass alle Abhängigkeiten installiert sind:")
    print("pip install -r requirements.txt")
    sys.exit(1)


def test_rss_parsing():
    """Test RSS-Feed Parsing"""
    print("🧪 Teste RSS-Feed Parsing...")
    
    try:
        # Teste einen öffentlichen RSS-Feed
        feed_url = "https://feeds.reuters.com/Reuters/PoliticsNews"
        feed = feedparser.parse(feed_url)
        
        if len(feed.entries) > 0:
            print(f"✅ RSS-Feed erfolgreich geladen: {len(feed.entries)} Artikel gefunden")
            
            # Teste ersten Artikel
            entry = feed.entries[0]
            print(f"   Beispiel-Titel: {entry.get('title', 'Kein Titel')[:50]}...")
            return True
        else:
            print("⚠️  RSS-Feed leer oder nicht erreichbar")
            return False
            
    except Exception as e:
        print(f"❌ RSS-Test fehlgeschlagen: {e}")
        return False


def test_article_creation():
    """Test NewsArticle Datenklasse"""
    print("🧪 Teste NewsArticle-Erstellung...")
    
    try:
        article = NewsArticle(
            title="Test-Artikel",
            description="Das ist ein Test-Artikel für die Überprüfung.",
            link="https://example.com/article",
            published="2024-01-01",
            source="Test-Quelle"
        )
        
        assert article.title == "Test-Artikel"
        assert article.ai_score is None
        assert article.ai_reasoning is None
        
        print("✅ NewsArticle erfolgreich erstellt")
        return True
        
    except Exception as e:
        print(f"❌ NewsArticle-Test fehlgeschlagen: {e}")
        return False


def test_analyzer_initialization():
    """Test NewsAnalyzer Initialisierung"""
    print("🧪 Teste NewsAnalyzer-Initialisierung...")
    
    try:
        analyzer = NewsAnalyzer()
        
        assert hasattr(analyzer, 'rss_feeds')
        assert hasattr(analyzer, 'max_articles')
        assert hasattr(analyzer, 'ai_model_type')
        
        print("✅ NewsAnalyzer erfolgreich initialisiert")
        print(f"   Konfigurierte Feeds: {len(analyzer.rss_feeds)}")
        print(f"   AI-Model-Typ: {analyzer.ai_model_type}")
        print(f"   Max. Artikel: {analyzer.max_articles}")
        return True
        
    except Exception as e:
        print(f"❌ NewsAnalyzer-Test fehlgeschlagen: {e}")
        return False


def test_prompt_creation():
    """Test KI-Prompt Erstellung"""
    print("🧪 Teste KI-Prompt Erstellung...")
    
    try:
        analyzer = NewsAnalyzer()
        
        test_article = NewsArticle(
            title="Test-Nachricht",
            description="Eine wichtige Test-Nachricht für die Analyse.",
            link="https://example.com",
            published="2024-01-01",
            source="Test-Quelle"
        )
        
        prompt = analyzer._create_analysis_prompt(test_article)
        
        assert "Test-Nachricht" in prompt
        assert "Score:" in prompt
        assert "Begründung:" in prompt
        
        print("✅ KI-Prompt erfolgreich erstellt")
        return True
        
    except Exception as e:
        print(f"❌ Prompt-Test fehlgeschlagen: {e}")
        return False


def test_response_parsing():
    """Test KI-Antwort Parsing"""
    print("🧪 Teste KI-Antwort Parsing...")
    
    try:
        analyzer = NewsAnalyzer()
        
        # Simuliere KI-Antwort
        test_response = """
Score: 8.5
Begründung: Dies ist eine wichtige politische Nachricht mit internationaler Reichweite.
"""
        
        score, reasoning = analyzer._parse_ai_response(test_response)
        
        assert abs(score - 8.5) < 0.1  # Floating-point Vergleich mit Toleranz
        assert "wichtige politische" in reasoning
        
        print("✅ KI-Antwort erfolgreich geparst")
        print(f"   Score: {score}")
        print(f"   Begründung: {reasoning[:50]}...")
        return True
        
    except Exception as e:
        print(f"❌ Response-Parsing-Test fehlgeschlagen: {e}")
        return False


def test_article_sorting():
    """Test Artikel-Sortierung"""
    print("🧪 Teste Artikel-Sortierung...")
    
    try:
        analyzer = NewsAnalyzer()
        
        # Erstelle Test-Artikel mit verschiedenen Scores
        articles = [
            NewsArticle("Artikel 1", "Beschreibung", "link", "date", "source", ai_score=5.0),
            NewsArticle("Artikel 2", "Beschreibung", "link", "date", "source", ai_score=9.0),
            NewsArticle("Artikel 3", "Beschreibung", "link", "date", "source", ai_score=2.0),
            NewsArticle("Artikel 4", "Beschreibung", "link", "date", "source", ai_score=7.5),
        ]
        
        sorted_articles = analyzer.sort_articles_by_importance(articles)
        
        # Überprüfe Sortierung (absteigend)
        scores = [article.ai_score for article in sorted_articles]
        assert scores == [9.0, 7.5, 5.0, 2.0]
        
        print("✅ Artikel-Sortierung erfolgreich")
        print(f"   Sortierte Scores: {scores}")
        return True
        
    except Exception as e:
        print(f"❌ Sortierungs-Test fehlgeschlagen: {e}")
        return False


def run_all_tests():
    """Führt alle Tests aus"""
    print("🚀 Starte News-Analyzer Tests...\n")
    
    tests = [
        test_article_creation,
        test_analyzer_initialization,
        test_prompt_creation,
        test_response_parsing,
        test_article_sorting,
        test_rss_parsing,  # Netzwerk-Test am Ende
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            print()  # Leerzeile zwischen Tests
        except Exception as e:
            print(f"❌ Unerwarteter Fehler in {test.__name__}: {e}\n")
    
    print("="*60)
    print(f"📊 Test-Ergebnis: {passed}/{total} Tests bestanden")
    
    if passed == total:
        print("🎉 Alle Tests erfolgreich!")
        return True
    else:
        print("⚠️  Einige Tests sind fehlgeschlagen")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    
    if not success:
        print("\n💡 Tipps zur Fehlerbehebung:")
        print("   - Überprüfen Sie die .env Konfiguration")
        print("   - Stellen Sie sicher, dass alle Pakete installiert sind")
        print("   - Überprüfen Sie die Internetverbindung für RSS-Tests")
        
        sys.exit(1)
    else:
        print("\n✅ Alle Tests bestanden - der News-Analyzer ist bereit!")
        print("\n🚀 Starten Sie das Hauptprogramm mit: python P-News.py")
