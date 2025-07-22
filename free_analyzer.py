#!/usr/bin/env python3
"""
KOSTENLOSE Version des intelligenten Nachrichten-Analyzers
Kombiniert regelbasierte Bewertung mit lokaler KI für maximale Effizienz
"""

import feedparser
import random
import time
import re
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass

# Für bessere lokale KI (optional)
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

@dataclass
class NewsArticle:
    """Artikel-Klasse mit KI-Score"""
    title: str
    description: str
    link: str
    published: str
    source: str
    ai_score: float = 0.0
    ai_reasoning: str = ""
    priority_keywords: List[str] = None


class FreeNewsAnalyzer:
    """Kostenlose Version mit intelligenter regelbasierter + lokaler KI"""
    
    def __init__(self):
        """Initialisierung"""
        self.rss_feeds = [
            "https://feeds.reuters.com/Reuters/PoliticsNews",
            "https://www.tagesschau.de/xml/rss2/",
            "https://feeds.bbci.co.uk/news/world/rss.xml"
        ]
        
        # Erweiterte Schlüsselwort-Datenbank für bessere Bewertung
        self.keyword_scores = {
            # Sehr hohe Priorität (8-10 Punkte)
            'krieg': 9, 'war': 9, 'terror': 9, 'nuklear': 10, 'nuclear': 10,
            'präsident': 8, 'president': 8, 'kanzler': 8, 'chancellor': 8,
            'wahlen': 8, 'election': 8, 'referendum': 8, 'coup': 10,
            'krise': 8, 'crisis': 8, 'kollaps': 9, 'collapse': 9,
            
            # Hohe Priorität (6-7 Punkte)
            'politik': 6, 'politik': 6, 'government': 6, 'regierung': 6,
            'minister': 6, 'parlament': 6, 'congress': 6, 'senate': 6,
            'gesetz': 6, 'law': 6, 'urteil': 7, 'verdict': 7,
            'sanktionen': 7, 'sanctions': 7, 'handel': 6, 'trade': 6,
            
            # Internationale Relevanz (Bonus +2 Punkte)
            'ukraine': 2, 'russia': 2, 'china': 2, 'usa': 2, 'america': 2,
            'eu': 2, 'europa': 2, 'nato': 2, 'un': 2, 'israel': 2,
            'deutschland': 1, 'germany': 1, 'frankreich': 1, 'france': 1,
            
            # Wirtschaft (4-6 Punkte)
            'wirtschaft': 5, 'economy': 5, 'inflation': 6, 'rezession': 7,
            'recession': 7, 'börse': 5, 'market': 5, 'bank': 5,
            
            # Gesellschaft (3-5 Punkte)
            'proteste': 5, 'protests': 5, 'demonstration': 4, 'streik': 4,
            'strike': 4, 'reform': 5, 'skandal': 6, 'scandal': 6
        }
        
        # Geografische Gewichtung
        self.geo_weights = {
            'global': 2.0, 'international': 1.8, 'national': 1.5,
            'regional': 1.2, 'local': 1.0
        }
        
        self.use_ollama = self._check_ollama_availability()
    
    def _check_ollama_availability(self) -> bool:
        """Prüft ob Ollama verfügbar ist"""
        if not REQUESTS_AVAILABLE:
            return False
        
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def fetch_articles(self) -> List[NewsArticle]:
        """Lädt Artikel aus RSS-Feeds"""
        articles = []
        
        print("🆓 KOSTENLOSE Nachrichten-Analyse startet...")
        print("📰 Lade RSS-Feeds...")
        
        for i, feed_url in enumerate(self.rss_feeds, 1):
            print(f"   {i}/{len(self.rss_feeds)}: {feed_url}")
            
            try:
                feed = feedparser.parse(feed_url)
                source_name = feed.feed.get('title', 'Unbekannte Quelle')
                
                for entry in feed.entries[:8]:  # Begrenzt für Performance
                    article = NewsArticle(
                        title=entry.get('title', 'Kein Titel'),
                        description=entry.get('summary', entry.get('description', 'Keine Beschreibung'))[:300],
                        link=entry.get('link', ''),
                        published=entry.get('published', str(datetime.now())),
                        source=source_name,
                        priority_keywords=[]
                    )
                    articles.append(article)
                    
            except Exception as e:
                print(f"   ❌ Fehler bei {feed_url}: {e}")
        
        print(f"✅ {len(articles)} Artikel geladen")
        return articles
    
    def smart_rule_based_analysis(self, articles: List[NewsArticle]) -> List[NewsArticle]:
        """Erweiterte regelbasierte Analyse"""
        print("\n🧠 Intelligente regelbasierte Analyse...")
        
        for i, article in enumerate(articles, 1):
            print(f"   Analysiere {i}/{len(articles)}: {article.title[:40]}...")
            
            # Basis-Score
            score = 5.0
            found_keywords = []
            reasoning_parts = []
            
            # Text für Analyse vorbereiten
            text = (article.title + " " + article.description).lower()
            text = re.sub(r'[^\w\s]', ' ', text)  # Entferne Interpunktion
            
            # Schlüsselwort-Analyse
            for keyword, weight in self.keyword_scores.items():
                if keyword in text:
                    score += weight
                    found_keywords.append(keyword)
                    if weight >= 8:
                        reasoning_parts.append(f"Kritisches Thema: {keyword}")
                    elif weight >= 6:
                        reasoning_parts.append(f"Wichtiges Thema: {keyword}")
            
            # Geografische Relevanz
            geo_score = self._analyze_geographic_relevance(text)
            score *= geo_score
            
            if geo_score > 1.5:
                reasoning_parts.append("Internationale Bedeutung")
            elif geo_score > 1.2:
                reasoning_parts.append("Nationale Relevanz")
            
            # Aktualitäts-Bonus
            urgency_bonus = self._analyze_urgency(text)
            score += urgency_bonus
            
            if urgency_bonus > 1:
                reasoning_parts.append("Hohe Aktualität")
            
            # Begrenze Score auf 1-10
            score = max(1.0, min(10.0, score))
            
            # Erstelle Begründung
            if not reasoning_parts:
                reasoning_parts.append("Standard-Nachrichtenbewertung")
            
            if score >= 8:
                category = "Sehr hohe Priorität"
            elif score >= 6:
                category = "Hohe Priorität"
            elif score >= 4:
                category = "Mittlere Priorität"
            else:
                category = "Niedrige Priorität"
            
            article.ai_score = round(score, 1)
            article.ai_reasoning = f"{category}: {', '.join(reasoning_parts)}"
            article.priority_keywords = found_keywords
        
        return articles
    
    def _analyze_geographic_relevance(self, text: str) -> float:
        """Analysiert geografische Relevanz"""
        international_indicators = ['international', 'global', 'world', 'worldwide', 'eu', 'nato', 'un']
        national_indicators = ['deutschland', 'germany', 'bundestag', 'bundesrat', 'berlin']
        
        for indicator in international_indicators:
            if indicator in text:
                return 1.8
        
        for indicator in national_indicators:
            if indicator in text:
                return 1.4
        
        return 1.0
    
    def _analyze_urgency(self, text: str) -> float:
        """Analysiert Dringlichkeit/Aktualität"""
        urgent_indicators = ['breaking', 'eilmeldung', 'urgent', 'sofort', 'jetzt', 'today', 'heute']
        developing_indicators = ['developing', 'ongoing', 'continues', 'weiter', 'aktuell']
        
        urgency_score = 0
        
        for indicator in urgent_indicators:
            if indicator in text:
                urgency_score += 2
                break
        
        for indicator in developing_indicators:
            if indicator in text:
                urgency_score += 1
                break
        
        return urgency_score
    
    def enhance_with_ollama(self, articles: List[NewsArticle]) -> List[NewsArticle]:
        """Verbessert Bewertungen mit lokalem Ollama (falls verfügbar)"""
        if not self.use_ollama:
            print("💡 Ollama nicht verfügbar - verwende nur regelbasierte Analyse")
            return articles
        
        print("🤖 Verfeinere mit lokaler KI (Ollama)...")
        
        # Nur Top-Artikel mit Ollama analysieren (Performance)
        top_articles = sorted(articles, key=lambda x: x.ai_score, reverse=True)[:5]
        
        for article in top_articles:
            try:
                # Einfacher Prompt für bessere Performance
                prompt = f"""Rate this news article importance 1-10:
Title: {article.title}
Current score: {article.ai_score}
Give only: Score X, Reason: [brief reason]"""
                
                response = requests.post(
                    "http://localhost:11434/api/generate",
                    json={
                        "model": "llama2",
                        "prompt": prompt,
                        "stream": False,
                        "options": {"temperature": 0.3, "num_predict": 50}
                    },
                    timeout=15
                )
                
                if response.status_code == 200:
                    result = response.json()['response']
                    enhanced_score, enhanced_reason = self._parse_ollama_response(result)
                    
                    if enhanced_score > 0:
                        # Mische regelbasierte und KI-Bewertung
                        final_score = (article.ai_score * 0.7) + (enhanced_score * 0.3)
                        article.ai_score = round(final_score, 1)
                        article.ai_reasoning = f"{article.ai_reasoning} | KI: {enhanced_reason}"
                
            except Exception as e:
                print(f"   ⚠️ Ollama-Fehler für {article.title[:30]}...: {e}")
        
        return articles
    
    def _parse_ollama_response(self, response: str) -> tuple:
        """Extrahiert Score und Reason aus Ollama-Antwort"""
        try:
            score_match = re.search(r'score[:\s]*(\d+(?:\.\d+)?)', response, re.IGNORECASE)
            reason_match = re.search(r'reason[:\s]*(.+)', response, re.IGNORECASE)
            
            score = float(score_match.group(1)) if score_match else 0
            reason = reason_match.group(1).strip() if reason_match else "KI-Bewertung"
            
            return score, reason[:100]  # Begrenze Länge
        except:
            return 0, "KI-Analyse-Fehler"
    
    def display_results(self, articles: List[NewsArticle]):
        """Zeigt Ergebnisse an"""
        if not articles:
            print("❌ Keine Artikel gefunden")
            return
        
        # Sortiere nach Score
        sorted_articles = sorted(articles, key=lambda x: x.ai_score, reverse=True)
        
        print("\n" + "="*120)
        print("🆓 KOSTENLOSE INTELLIGENTE NACHRICHTENANALYSE")
        print("="*120)
        
        for i, article in enumerate(sorted_articles, 1):
            print(f"\n{i:2d}. Score: {article.ai_score}/10")
            print(f"    📰 Titel: {article.title}")
            print(f"    🏢 Quelle: {article.source}")
            print(f"    🧠 Analyse: {article.ai_reasoning}")
            if article.priority_keywords:
                print(f"    🔑 Schlüsselwörter: {', '.join(article.priority_keywords)}")
            print(f"    🔗 Link: {article.link}")
            print("-" * 120)
        
        print(f"\n🏆 TOP 5 WICHTIGSTE NACHRICHTEN:")
        for i, article in enumerate(sorted_articles[:5], 1):
            print(f"{i}. {article.title} (Score: {article.ai_score})")
        
        # Statistiken
        avg_score = sum(a.ai_score for a in articles) / len(articles)
        high_priority = len([a for a in articles if a.ai_score >= 7])
        
        print(f"\n📊 STATISTIKEN:")
        print(f"   Durchschnittsscore: {avg_score:.1f}")
        print(f"   Hochpriorisierte Artikel (Score ≥7): {high_priority}")
        print(f"   Ollama-KI verwendet: {'Ja' if self.use_ollama else 'Nein'}")
    
    def run_free_analysis(self):
        """Führt die kostenlose Analyse durch"""
        start_time = time.time()
        
        print("💰 KOMPLETT KOSTENLOSES NEWS-ANALYSIS SYSTEM 💰")
        print("🚀 Startet intelligente Nachrichtenbewertung...")
        
        # 1. Artikel laden
        articles = self.fetch_articles()
        
        if not articles:
            print("❌ Keine Artikel gefunden!")
            return
        
        # 2. Regelbasierte Analyse
        articles = self.smart_rule_based_analysis(articles)
        
        # 3. Optional: Ollama-Verbesserung
        if self.use_ollama:
            articles = self.enhance_with_ollama(articles)
        
        # 4. Ergebnisse anzeigen
        self.display_results(articles)
        
        # Timing
        duration = time.time() - start_time
        print(f"\n⏱️  Kostenlose Analyse abgeschlossen in {duration:.1f} Sekunden")
        print("\n💡 TIPPS FÜR NOCH BESSERE ERGEBNISSE:")
        if not self.use_ollama:
            print("   • Installiere Ollama für KI-verstärkte Bewertung: https://ollama.ai")
            print("   • Führe aus: ollama pull llama2")
        print("   • Passe RSS-Feeds in der Konfiguration an")
        print("   • Erweitere Schlüsselwort-Datenbank für deine Interessensgebiete")


def main():
    """Hauptfunktion für kostenlose Analyse"""
    try:
        analyzer = FreeNewsAnalyzer()
        analyzer.run_free_analysis()
    except KeyboardInterrupt:
        print("\n❌ Analyse abgebrochen durch Benutzer")
    except Exception as e:
        print(f"❌ Unerwarteter Fehler: {e}")


if __name__ == "__main__":
    main()
