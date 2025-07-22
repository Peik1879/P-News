#!/usr/bin/env python3
"""
Demo-Version des News-Analyzers
Funktioniert ohne API-Keys mit simulierter KI-Bewertung.
"""

import feedparser
import random
import time
from datetime import datetime
from typing import List
from dataclasses import dataclass

@dataclass
class NewsArticle:
    """Vereinfachte Artikel-Klasse für Demo"""
    title: str
    description: str
    link: str
    published: str
    source: str
    ai_score: float = 0.0
    ai_reasoning: str = ""


class DemoNewsAnalyzer:
    """Demo-Version ohne externe KI-APIs"""
    
    def __init__(self):
        """Initialisierung"""
        self.rss_feeds = [
            "https://feeds.reuters.com/Reuters/PoliticsNews",
            "https://www.tagesschau.de/xml/rss2/",
            "https://feeds.bbci.co.uk/news/world/rss.xml"
        ]
    
    def fetch_articles(self) -> List[NewsArticle]:
        """Lädt Artikel aus RSS-Feeds"""
        articles = []
        
        print("📰 Lade RSS-Feeds...")
        
        for i, feed_url in enumerate(self.rss_feeds, 1):
            print(f"   {i}/{len(self.rss_feeds)}: {feed_url}")
            
            try:
                feed = feedparser.parse(feed_url)
                source_name = feed.feed.get('title', 'Unbekannte Quelle')
                
                for entry in feed.entries[:5]:  # Nur erste 5 Artikel pro Feed
                    article = NewsArticle(
                        title=entry.get('title', 'Kein Titel'),
                        description=entry.get('summary', entry.get('description', 'Keine Beschreibung'))[:200] + "...",
                        link=entry.get('link', ''),
                        published=entry.get('published', str(datetime.now())),
                        source=source_name
                    )
                    articles.append(article)
                    
            except Exception as e:
                print(f"   ❌ Fehler bei {feed_url}: {e}")
        
        print(f"✅ {len(articles)} Artikel geladen")
        return articles
    
    def simulate_ai_analysis(self, articles: List[NewsArticle]) -> List[NewsArticle]:
        """Simuliert KI-Bewertung mit intelligenten Regeln"""
        print("\n🤖 Simuliere KI-Analyse...")
        
        # Schlüsselwörter für Bewertung
        high_priority_keywords = ['krieg', 'war', 'konflikt', 'wahl', 'election', 'präsident', 'kanzler', 'terror', 'krise', 'crisis']
        medium_priority_keywords = ['politik', 'regierung', 'government', 'minister', 'parlament', 'gesetz', 'law']
        international_keywords = ['ukraine', 'russia', 'china', 'usa', 'eu', 'nato', 'un']
        
        for i, article in enumerate(articles, 1):
            print(f"   Analysiere {i}/{len(articles)}: {article.title[:40]}...")
            
            # Basis-Score
            score = 5.0
            reasoning_parts = []
            
            title_lower = article.title.lower()
            desc_lower = article.description.lower()
            
            # Erhöhe Score für wichtige Schlüsselwörter
            for keyword in high_priority_keywords:
                if keyword in title_lower or keyword in desc_lower:
                    score += 2.0
                    reasoning_parts.append(f"Enthält wichtiges Thema: {keyword}")
                    break
            
            for keyword in medium_priority_keywords:
                if keyword in title_lower or keyword in desc_lower:
                    score += 1.0
                    reasoning_parts.append("Politisch relevantes Thema")
                    break
            
            for keyword in international_keywords:
                if keyword in title_lower or keyword in desc_lower:
                    score += 1.5
                    reasoning_parts.append("Internationale Bedeutung")
                    break
            
            # Zufällige Variation für Realismus
            score += random.uniform(-0.5, 0.5)
            
            # Begrenze Score auf 1-10
            score = max(1.0, min(10.0, score))
            
            # Generiere Begründung
            if not reasoning_parts:
                reasoning_parts.append("Allgemeine Nachrichtenbewertung")
            
            if score >= 8:
                reasoning = f"Hohe Priorität: {', '.join(reasoning_parts)}"
            elif score >= 6:
                reasoning = f"Mittlere Priorität: {', '.join(reasoning_parts)}"
            else:
                reasoning = f"Niedrige Priorität: {', '.join(reasoning_parts)}"
            
            article.ai_score = round(score, 1)
            article.ai_reasoning = reasoning
            
            time.sleep(0.1)  # Simuliere Verarbeitungszeit
        
        return articles
    
    def display_results(self, articles: List[NewsArticle]):
        """Zeigt Ergebnisse an"""
        if not articles:
            print("❌ Keine Artikel gefunden")
            return
        
        # Sortiere nach Score
        sorted_articles = sorted(articles, key=lambda x: x.ai_score, reverse=True)
        
        print("\n" + "="*100)
        print("📊 NACHRICHTENANALYSE - DEMO VERSION")
        print("="*100)
        
        for i, article in enumerate(sorted_articles, 1):
            print(f"\n{i:2d}. Score: {article.ai_score}/10")
            print(f"    Titel: {article.title}")
            print(f"    Quelle: {article.source}")
            print(f"    Begründung: {article.ai_reasoning}")
            print(f"    Link: {article.link}")
            print("-" * 100)
        
        print(f"\n🎯 Top 3 wichtigste Nachrichten:")
        for i, article in enumerate(sorted_articles[:3], 1):
            print(f"{i}. {article.title} (Score: {article.ai_score})")
    
    def run_demo(self):
        """Führt die Demo aus"""
        print("🚀 DEMO: Intelligenter Nachrichten-Analyzer")
        print("   (Ohne API-Keys - Simulierte KI-Bewertung)")
        print("="*60)
        
        start_time = time.time()
        
        # 1. Artikel laden
        articles = self.fetch_articles()
        
        if not articles:
            print("❌ Keine Artikel gefunden!")
            return
        
        # 2. Simulierte KI-Analyse
        analyzed_articles = self.simulate_ai_analysis(articles)
        
        # 3. Ergebnisse anzeigen
        self.display_results(analyzed_articles)
        
        # Timing
        duration = time.time() - start_time
        print(f"\n⏱️  Demo abgeschlossen in {duration:.1f} Sekunden")
        print("\n💡 Für echte KI-Bewertung konfigurieren Sie einen OpenAI API Key")
        print("   und verwenden Sie das Hauptprogramm: python P-News.py")


def main():
    """Demo-Hauptfunktion"""
    try:
        demo = DemoNewsAnalyzer()
        demo.run_demo()
    except KeyboardInterrupt:
        print("\n❌ Demo abgebrochen")
    except Exception as e:
        print(f"❌ Fehler: {e}")


if __name__ == "__main__":
    main()
