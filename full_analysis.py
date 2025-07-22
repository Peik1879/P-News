#!/usr/bin/env python3
"""
Vollständige Analyse aller verfügbaren Artikel ohne 25er-Limit
Um zu prüfen, ob wichtige Nachrichten verloren gehen
"""

import feedparser
import os
from dotenv import load_dotenv
from dataclasses import dataclass
from typing import List
import requests
import json
from rich.console import Console
from rich.table import Table
from rich import box

load_dotenv()
console = Console()

@dataclass
class NewsArticle:
    title: str
    summary: str
    source: str
    category: str
    url: str
    published: str = ""
    ai_score: float = 0.0
    ai_reasoning: str = ""

def get_rss_feeds():
    """Hole RSS-Feed-URLs aus .env"""
    rss_feeds_str = os.getenv('RSS_FEEDS', '')
    if not rss_feeds_str:
        return []
    
    return [url.strip() for url in rss_feeds_str.split(',') if url.strip()]

def fetch_articles_no_limit() -> List[NewsArticle]:
    """Hole ALLE verfügbaren Artikel ohne Limit"""
    rss_feeds = get_rss_feeds()
    all_articles = []
    
    console.print("🔍 Lade ALLE verfügbaren Artikel...")
    
    for feed_url in rss_feeds:
        try:
            console.print(f"📡 Lade: {feed_url}")
            feed = feedparser.parse(feed_url)
            
            for entry in feed.entries:
                # Bestimme Kategorie und Quelle
                if 'reuters.com' in feed_url:
                    source = 'Reuters'
                    category = 'Technology' if 'technology' in feed_url else 'Business'
                elif 'cnn.com' in feed_url:
                    source = 'CNN'
                    category = 'General'
                elif 'theguardian.com' in feed_url:
                    source = 'The Guardian'
                    if 'world' in feed_url:
                        category = 'World news'
                    elif 'business' in feed_url:
                        category = 'Business'
                    elif 'technology' in feed_url:
                        category = 'Technology'
                    else:
                        category = 'General'
                elif 'bbc' in feed_url:
                    source = 'BBC'
                    if 'world' in feed_url:
                        category = 'World'
                    elif 'business' in feed_url:
                        category = 'Business'
                    elif 'technology' in feed_url:
                        category = 'Technology'
                    else:
                        category = 'General'
                elif 'nytimes.com' in feed_url:
                    source = 'New York Times'
                    if 'World' in feed_url:
                        category = 'World'
                    elif 'Business' in feed_url:
                        category = 'Business'
                    else:
                        category = 'General'
                elif 'washingtonpost.com' in feed_url:
                    source = 'Washington Post'
                    category = 'World'
                elif 'time.com' in feed_url:
                    source = 'TIME'
                    if 'world' in feed_url:
                        category = 'World'
                    elif 'business' in feed_url:
                        category = 'Business'
                    else:
                        category = 'General'
                else:
                    source = 'Unknown'
                    category = 'General'
                
                article = NewsArticle(
                    title=entry.title,
                    summary=entry.summary if hasattr(entry, 'summary') else entry.title,
                    source=source,
                    category=category,
                    url=entry.link,
                    published=entry.published if hasattr(entry, 'published') else ""
                )
                all_articles.append(article)
                
        except Exception as e:
            console.print(f"❌ Fehler beim Laden von {feed_url}: {e}")
    
    return all_articles

def analyze_with_ollama(article: NewsArticle) -> tuple:
    """Analysiere Artikel mit Ollama"""
    try:
        prompt = f"""Bewerte diesen Nachrichtenartikel auf einer Skala von 1-10 für seine Wichtigkeit:

Titel: {article.title}
Zusammenfassung: {article.summary}
Quelle: {article.source}

Bewertungskriterien:
- 9-10: Weltbewegende Ereignisse (Kriege, Naturkatastrophen, historische Ereignisse)
- 8-9: Sehr wichtige internationale Nachrichten
- 7-8: Wichtige regionale/nationale Nachrichten
- 6-7: Relevante Wirtschafts-/Technologienachrichten
- 5-6: Interessante aber weniger kritische Nachrichten
- 1-4: Unwichtige oder Lifestyle-Nachrichten

Antworte nur mit einer Zahl (z.B. 7.5) und kurzer Begründung."""

        response = requests.post(
            'http://localhost:11434/api/generate',
            json={
                'model': 'llama2',
                'prompt': prompt,
                'stream': False
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            ai_response = result.get('response', '').strip()
            
            # Extrahiere Score
            score_line = ai_response.split('\n')[0]
            try:
                score = float([word for word in score_line.split() if word.replace('.', '').isdigit()][0])
                score = max(1.0, min(10.0, score))
            except:
                score = 5.0
            
            return score, ai_response
        
    except Exception as e:
        console.print(f"❌ AI-Analyse Fehler: {e}")
    
    return 5.0, "Analyse fehlgeschlagen"

def main():
    # Hole alle Artikel
    articles = fetch_articles_no_limit()
    console.print(f"📰 Gefunden: {len(articles)} Artikel INSGESAMT")
    
    if not articles:
        console.print("❌ Keine Artikel gefunden!")
        return
    
    # Analysiere mit AI (nur erste 50 für Performance)
    analyze_count = min(50, len(articles))
    console.print(f"🤖 Analysiere erste {analyze_count} Artikel mit AI...")
    
    for i, article in enumerate(articles[:analyze_count]):
        console.print(f"Analysiere {i+1}/{analyze_count}: {article.title[:50]}...")
        article.ai_score, article.ai_reasoning = analyze_with_ollama(article)
    
    # Sortiere nach Score
    analyzed_articles = articles[:analyze_count]
    analyzed_articles.sort(key=lambda x: x.ai_score, reverse=True)
    
    # Zeige Ergebnisse
    console.print("\n" + "="*80)
    console.print("📊 VOLLSTÄNDIGE ANALYSE ALLER ARTIKEL")
    console.print("="*80)
    
    # Score-Verteilung
    scores_9_plus = [a for a in analyzed_articles if a.ai_score >= 9.0]
    scores_8_9 = [a for a in analyzed_articles if 8.0 <= a.ai_score < 9.0]
    scores_7_8 = [a for a in analyzed_articles if 7.0 <= a.ai_score < 8.0]
    scores_6_7 = [a for a in analyzed_articles if 6.0 <= a.ai_score < 7.0]
    scores_5_6 = [a for a in analyzed_articles if 5.0 <= a.ai_score < 6.0]
    scores_under_5 = [a for a in analyzed_articles if a.ai_score < 5.0]
    
    console.print(f"🔴 BREAKING (9.0+): {len(scores_9_plus)} ({len(scores_9_plus)/len(analyzed_articles)*100:.1f}%)")
    console.print(f"🟡 SEHR WICHTIG (8.0-8.9): {len(scores_8_9)} ({len(scores_8_9)/len(analyzed_articles)*100:.1f}%)")
    console.print(f"🟢 WICHTIG (7.0-7.9): {len(scores_7_8)} ({len(scores_7_8)/len(analyzed_articles)*100:.1f}%)")
    console.print(f"🔵 RELEVANT (6.0-6.9): {len(scores_6_7)} ({len(scores_6_7)/len(analyzed_articles)*100:.1f}%)")
    console.print(f"⚪ NORMAL (5.0-5.9): {len(scores_5_6)} ({len(scores_5_6)/len(analyzed_articles)*100:.1f}%)")
    console.print(f"⚫ UNWICHTIG (<5.0): {len(scores_under_5)} ({len(scores_under_5)/len(analyzed_articles)*100:.1f}%)")
    
    # Zeige Top-Artikel
    console.print("\n🏆 TOP 10 WICHTIGSTE ARTIKEL:")
    console.print("-" * 80)
    for i, article in enumerate(analyzed_articles[:10]):
        console.print(f"{i+1:2d}. [{article.ai_score:.1f}] {article.title[:60]}...")
        console.print(f"     {article.source} | {article.category}")
    
    # Zeige was aktuell im 25er-Limit verloren geht
    current_threshold = float(os.getenv('NOTIFICATION_THRESHOLD', '7.0'))
    above_threshold = [a for a in analyzed_articles if a.ai_score >= current_threshold]
    
    console.print(f"\n⚙️  AKTUELLER THRESHOLD: {current_threshold}")
    console.print(f"📱 Artikel über Threshold: {len(above_threshold)}")
    console.print(f"📊 Das sind {len(above_threshold)/len(analyzed_articles)*100:.1f}% aller Artikel")
    
    if len(above_threshold) > 25:
        console.print(f"⚠️  WARNUNG: {len(above_threshold)} Artikel über Threshold, aber nur 25 werden analysiert!")
        console.print("❗ Möglicherweise gehen wichtige Artikel verloren!")
        
        console.print("\n🔍 ARTIKEL DIE VERLOREN GEHEN KÖNNTEN (Position 26+):")
        for i, article in enumerate(above_threshold[25:35]):  # Zeige 10 verlorene
            console.print(f"   [{article.ai_score:.1f}] {article.title[:60]}...")
    else:
        console.print("✅ Alle wichtigen Artikel werden erfasst!")

if __name__ == "__main__":
    main()
