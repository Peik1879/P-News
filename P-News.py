 #!/usr/bin/env python3
"""
Intelligenter Nachrichten-Analyzer
Lädt RSS-Feeds, bewertet Artikel durch KI und sortiert nach Wichtigkeit.

Author: News-AI-Bot
Version: 1.0
"""

import feedparser
import requests
import json
import os
import time
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from dotenv import load_dotenv

# Für schöne Ausgabe
try:
    from rich.console import Console
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("Rich nicht installiert - einfache Textausgabe wird verwendet")

# OpenAI Import
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("OpenAI nicht installiert - nur lokale Modelle verfügbar")


@dataclass
class NewsArticle:
    """Datenklasse für einen Nachrichtenartikel"""
    title: str
    description: str
    link: str
    published: str
    source: str
    ai_score: Optional[float] = None
    ai_reasoning: Optional[str] = None
    
    # Neue Aktienmarkt-Analyse Felder
    stock_impact_score: Optional[float] = None  # 1-10 Bewertung der Marktauswirkung
    stock_direction: Optional[str] = None       # "UP", "DOWN", "NEUTRAL"
    affected_stocks: Optional[List[str]] = None  # Liste der betroffenen Aktien/Sektoren
    stock_reasoning: Optional[str] = None       # Begründung der Aktienanalyse
    
    def __post_init__(self):
        if self.affected_stocks is None:
            self.affected_stocks = []


class NewsAnalyzer:
    """Hauptklasse für die Nachrichtenanalyse"""
    
    def __init__(self):
        """Initialisiert den NewsAnalyzer"""
        load_dotenv()
        self.console = Console() if RICH_AVAILABLE else None
        self.openai_client = None
        self.ai_model_type = os.getenv('AI_MODEL_TYPE', 'openai').lower()
        
        # OpenAI Setup
        if self.ai_model_type == 'openai' and OPENAI_AVAILABLE:
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key and api_key != 'your_openai_api_key_here':
                self.openai_client = OpenAI(api_key=api_key)
            else:
                self._print("⚠️  OpenAI API Key nicht gefunden! Bitte .env Datei konfigurieren.")
        
        # RSS Feed URLs
        feed_urls_str = os.getenv('RSS_FEEDS', 'https://feeds.reuters.com/Reuters/PoliticsNews')
        self.rss_feeds = [url.strip() for url in feed_urls_str.split(',')]
        
        # Weitere Konfiguration
        self.max_articles = int(os.getenv('MAX_ARTICLES', '75'))  # Erhöht von 20 auf 75
        self.openai_model = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')
    
    def _print(self, message: str, style: str = None):
        """Hilfsfunktion für Ausgabe mit/ohne Rich"""
        if self.console and style:
            self.console.print(message, style=style)
        else:
            print(message)
    
    def fetch_rss_articles(self) -> List[NewsArticle]:
        """Lädt Artikel aus allen konfigurierten RSS-Feeds"""
        articles = []
        
        if RICH_AVAILABLE:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
            ) as progress:
                task = progress.add_task("Lade RSS-Feeds...", total=len(self.rss_feeds))
                
                for feed_url in self.rss_feeds:
                    progress.update(task, description=f"Lade: {feed_url}")
                    articles.extend(self._fetch_single_feed(feed_url))
                    progress.advance(task)
        else:
            for i, feed_url in enumerate(self.rss_feeds, 1):
                print(f"Lade Feed {i}/{len(self.rss_feeds)}: {feed_url}")
                articles.extend(self._fetch_single_feed(feed_url))
        
        # Limitierung auf max_articles
        if len(articles) > self.max_articles:
            articles = articles[:self.max_articles]
            self._print(f"Limitiert auf {self.max_articles} Artikel", "yellow")
        
        return articles
    
    def _fetch_single_feed(self, feed_url: str) -> List[NewsArticle]:
        """Lädt Artikel aus einem einzelnen RSS-Feed"""
        articles = []
        
        try:
            feed = feedparser.parse(feed_url)
            source_name = feed.feed.get('title', 'Unbekannte Quelle')
            
            for entry in feed.entries:
                article = NewsArticle(
                    title=entry.get('title', 'Kein Titel'),
                    description=entry.get('summary', entry.get('description', 'Keine Beschreibung')),
                    link=entry.get('link', ''),
                    published=entry.get('published', str(datetime.now())),
                    source=source_name
                )
                articles.append(article)
                
        except Exception as e:
            self._print(f"❌ Fehler beim Laden von {feed_url}: {e}", "red")
        
        return articles
    
    def analyze_articles_with_ai(self, articles: List[NewsArticle]) -> List[NewsArticle]:
        """Bewertet alle Artikel mit KI - zweistufiger Prozess"""
        if not articles:
            return articles
        
        # Phase 1: Schnelle Titel-Bewertung aller Artikel
        print(f"📊 Phase 1: Schnelle Titel-Analyse von {len(articles)} Artikeln...")
        title_scored_articles = self._quick_title_analysis(articles)
        
        # Sortiere nach Score und nimm die Top 10 für Vollanalyse
        title_scored_articles.sort(key=lambda x: x.score, reverse=True)
        top_articles = title_scored_articles[:10]
        remaining_articles = title_scored_articles[10:]
        
        print(f"🎯 Phase 2: Vollanalyse der Top {len(top_articles)} Artikel...")
        
        # Phase 2: Vollständige Analyse nur der Top 10
        if self.ai_model_type == 'openai':
            analyzed_top = self._analyze_with_openai(top_articles)
        elif self.ai_model_type == 'ollama':
            analyzed_top = self._analyze_with_ollama(top_articles)
        else:
            self._print("❌ Unbekannter AI-Model-Typ konfiguriert", "red")
            # Fallback: Setze Standard-Scores für Demo
            for article in top_articles:
                article.ai_score = article.score  # Verwende Titel-Score
                article.ai_reasoning = "Keine KI-Analyse verfügbar"
            analyzed_top = top_articles
        
        # Phase 3: Für restliche Artikel nur Score übernehmen (keine vollständige Analyse)
        for article in remaining_articles:
            article.ai_score = article.score  # Titel-Score als ai_score verwenden
            article.ai_reasoning = "Nur Titel-Analyse (nicht in Top 10)"
        
        # Kombiniere alle Artikel und sortiere nach ai_score
        all_articles = analyzed_top + remaining_articles
        all_articles.sort(key=lambda x: x.ai_score, reverse=True)
        
        return all_articles
    
    def _quick_title_analysis(self, articles: List[NewsArticle]) -> List[NewsArticle]:
        """Schnelle Bewertung basierend nur auf Titel - für Vorauswahl"""
        # Sehr wichtige Keywords (9.0+)
        critical_keywords = {
            'killing': 9.5, 'killed': 9.5, 'murder': 9.5, 'massacre': 9.5, 'dead': 9.0,
            'attack': 9.0, 'bombing': 9.5, 'explosion': 9.0, 'terror': 9.5,
            'war': 9.0, 'invasion': 9.5, 'military': 8.5, 'soldiers': 8.0,
            'crisis': 9.0, 'emergency': 9.0, 'disaster': 9.0, 'catastrophe': 9.5,
            'breaking': 9.5, 'urgent': 9.0, 'live': 8.5, 'developing': 8.0,
            'hundreds': 9.0, 'dozens': 8.5, 'thousands': 9.5, 'mass': 9.0,
            'vehicle drives': 9.0, 'crowd': 8.5, 'injured': 8.0, 'wounded': 8.0
        }
        
        # Wichtige Keywords (7.0-8.9)
        high_priority_keywords = {
            'ukraine': 8.0, 'russia': 8.0, 'putin': 8.0, 'russian': 8.0,
            'china': 7.5, 'chinese': 7.5, 'taiwan': 8.0, 'beijing': 7.5,
            'israel': 8.0, 'gaza': 8.5, 'palestine': 8.0, 'hamas': 8.0,
            'iran': 7.5, 'syria': 8.0, 'syrian': 8.0, 'middle east': 8.0,
            'trump': 7.5, 'biden': 7.0, 'president': 7.0, 'administration': 7.0,
            'government': 7.0, 'parliament': 7.0, 'minister': 7.0,
            'election': 7.5, 'vote': 7.0, 'democracy': 7.5,
            'spy': 8.0, 'spies': 8.0, 'intelligence': 7.5, 'cyber': 7.5,
            'sudan': 8.5, 'sudanese': 8.5, 'rsf': 8.5, 'paramilitary': 8.5,
            'malaria': 8.0, 'epidemic': 8.5, 'disease': 7.5, 'health': 7.0,
            'children': 8.0, 'vaccination': 7.5, 'medical': 7.0,
            'zimbabwe': 7.5, 'africa': 7.0, 'african': 7.0,
            'brazil': 7.5, 'brazilian': 7.5, 'environment': 7.5,
            'climate': 7.0, 'devastation': 8.0, 'destruction': 8.0
        }
        
        # Mittlere Priorität (5.0-6.9)
        medium_priority_keywords = {
            'economy': 6.5, 'economic': 6.5, 'market': 6.0, 'business': 6.0,
            'trade': 6.0, 'tariff': 6.5, 'oil': 6.5, 'gas': 6.5,
            'technology': 5.5, 'tech': 5.5, 'ai': 6.0, 'artificial': 6.0,
            'court': 6.5, 'legal': 6.0, 'law': 6.0, 'police': 7.0,
            'weather': 6.0, 'storm': 7.0, 'flood': 7.5, 'drought': 7.0,
            'company': 5.5, 'corporation': 5.5, 'industry': 5.5
        }
        
        for article in articles:
            title_lower = article.title.lower()
            max_score = 4.0  # Basis-Score
            
            # Prüfe auf kritische Keywords
            for keyword, score in critical_keywords.items():
                if keyword in title_lower:
                    max_score = max(max_score, score)
            
            # Prüfe auf wichtige Keywords
            for keyword, score in high_priority_keywords.items():
                if keyword in title_lower:
                    max_score = max(max_score, score)
            
            # Prüfe auf mittlere Keywords
            for keyword, score in medium_priority_keywords.items():
                if keyword in title_lower:
                    max_score = max(max_score, score)
            
            # Bonus für Premium-Quellen
            if 'Reuters' in article.source or 'BBC' in article.source:
                max_score += 0.5
            elif 'Guardian' in article.source or 'CNN' in article.source:
                max_score += 0.3
            
            # Penalty für lokale/spezifische Themen
            local_indicators = ['local', 'county', 'village', 'town', 'city council', 'festival', 'sport', 'beach']
            if any(indicator in title_lower for indicator in local_indicators):
                max_score -= 1.5
            
            # Penalty für weniger wichtige Themen
            low_priority = ['holiday', 'vacation', 'celebrity', 'entertainment', 'fashion', 'lifestyle']
            if any(indicator in title_lower for indicator in low_priority):
                max_score -= 2.0
            
            article.score = max(min(max_score, 10.0), 1.0)  # Zwischen 1.0 und 10.0
            article.ai_reasoning = "Schnelle Titel-Analyse"
        
        return articles

    def _analyze_with_openai(self, articles: List[NewsArticle]) -> List[NewsArticle]:
        """Analysiert Artikel mit OpenAI GPT"""
        if not self.openai_client:
            self._print("❌ OpenAI Client nicht verfügbar - verwende Fallback-Bewertung", "red")
            # Fallback: Setze Standard-Scores
            for article in articles:
                article.ai_score = 5.0
                article.ai_reasoning = "OpenAI nicht verfügbar - Standard-Score"
            return articles
        
        self._print("🤖 Analysiere Artikel mit OpenAI GPT...", "blue")
        
        for i, article in enumerate(articles, 1):
            try:
                if RICH_AVAILABLE:
                    self.console.print(f"Analysiere Artikel {i}/{len(articles)}: {article.title[:50]}...", style="cyan")
                else:
                    print(f"Analysiere {i}/{len(articles)}: {article.title[:50]}...")
                
                prompt = self._create_analysis_prompt(article)
                
                response = self.openai_client.chat.completions.create(
                    model=self.openai_model,
                    messages=[
                        {"role": "system", "content": "Du bist ein Experte für politische Nachrichtenanalyse."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=200,
                    temperature=0.3
                )
                
                result = response.choices[0].message.content.strip()
                score, reasoning = self._parse_ai_response(result)
                
                article.ai_score = score
                article.ai_reasoning = reasoning
                
                # Kleine Pause um Rate Limits zu vermeiden
                time.sleep(0.5)
                
            except Exception as e:
                self._print(f"❌ Fehler bei Artikel-Analyse: {e}", "red")
                article.ai_score = 5.0  # Fallback-Score
                article.ai_reasoning = "Fehler bei der Analyse"
        
        return articles
    
    def _analyze_with_ollama(self, articles: List[NewsArticle]) -> List[NewsArticle]:
        """Analysiert Artikel mit lokalem Ollama-Modell (News + Aktien)"""
        base_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
        model = os.getenv('OLLAMA_MODEL', 'llama2')
        
        self._print(f"🤖 Analysiere Artikel mit Ollama ({model})...", "blue")
        
        for i, article in enumerate(articles, 1):
            try:
                if RICH_AVAILABLE:
                    self.console.print(f"Analysiere Artikel {i}/{len(articles)}: {article.title[:50]}...", style="cyan")
                else:
                    print(f"Analysiere {i}/{len(articles)}: {article.title[:50]}...")
                
                # 1. News-Relevanz-Analyse
                news_prompt = self._create_analysis_prompt(article)
                
                response = requests.post(
                    f"{base_url}/api/generate",
                    json={
                        "model": model,
                        "prompt": news_prompt,
                        "stream": False
                    },
                    timeout=60
                )
                
                if response.status_code == 200:
                    result = response.json()['response']
                    score, reasoning = self._parse_ai_response(result)
                    article.ai_score = score
                    article.ai_reasoning = reasoning
                else:
                    article.ai_score = 5.0
                    article.ai_reasoning = f"API-Fehler: {response.status_code}"
                
                # 2. Aktienmarkt-Analyse
                stock_prompt = self._create_stock_analysis_prompt(article)
                
                stock_response = requests.post(
                    f"{base_url}/api/generate",
                    json={
                        "model": model,
                        "prompt": stock_prompt,
                        "stream": False
                    },
                    timeout=60
                )
                
                if stock_response.status_code == 200:
                    stock_result = stock_response.json()['response']
                    stock_score, direction, stocks, stock_reasoning = self._parse_stock_analysis_response(stock_result)
                    article.stock_impact_score = stock_score
                    article.stock_direction = direction
                    article.affected_stocks = stocks
                    article.stock_reasoning = stock_reasoning
                else:
                    article.stock_impact_score = 1.0
                    article.stock_direction = "NEUTRAL"
                    article.affected_stocks = []
                    article.stock_reasoning = f"Aktien-API-Fehler: {stock_response.status_code}"
                
                # Status-Update
                if RICH_AVAILABLE:
                    stock_emoji = "📈" if direction == "UP" else "📉" if direction == "DOWN" else "➡️"
                    self.console.print(f"  ✅ News: {score:.1f}/10 | 📊 Aktien: {stock_score:.1f}/10 {stock_emoji}", style="green")
                
            except Exception as e:
                self._print(f"❌ Fehler bei Ollama-Analyse: {e}", "red")
                article.ai_score = 5.0
                article.ai_reasoning = "Fehler bei der lokalen Analyse"
                article.stock_impact_score = 1.0
                article.stock_direction = "NEUTRAL"
                article.affected_stocks = []
                article.stock_reasoning = "Fehler bei der Aktienanalyse"
        
        return articles
        
        return articles
    
    def _create_analysis_prompt(self, article: NewsArticle) -> str:
        """Erstellt den Prompt für die KI-Analyse"""
        return f"""
Bewerte diesen Nachrichtenartikel auf einer Skala von 1-10 nach politischer Relevanz und gesellschaftlicher Wichtigkeit:

Titel: {article.title}
Beschreibung: {article.description}
Quelle: {article.source}

Bewertungskriterien:
- 1-3: Lokale/unwichtige Nachrichten
- 4-6: Regionale/moderate Wichtigkeit  
- 7-8: National/international wichtig
- 9-10: Historisch bedeutsam/gesellschaftsprägend

Antworte in folgendem Format:
Score: [Zahl von 1-10]
Begründung: [Kurze Erklärung in 1-2 Sätzen]
"""
    
    def _create_stock_analysis_prompt(self, article: NewsArticle) -> str:
        """Erstellt den Prompt für die Aktienmarkt-Analyse"""
        return f"""
Analysiere diese Nachricht auf ihre Auswirkungen auf den Aktienmarkt:

Titel: {article.title}
Beschreibung: {article.description}
Quelle: {article.source}

Bewerte:
1. Marktauswirkung (1-10): Wie stark wird der Aktienmarkt reagieren?
2. Richtung: Wird der Markt steigen (UP), fallen (DOWN) oder neutral bleiben (NEUTRAL)?
3. Betroffene Aktien/Sektoren: Welche spezifischen Unternehmen oder Branchen sind betroffen?

Bewertungskriterien für Marktauswirkung:
- 1-2: Keine Marktauswirkung
- 3-4: Minimale Sektorauswirkung
- 5-6: Moderate Sektorauswirkung
- 7-8: Bedeutende Marktauswirkung
- 9-10: Massive Marktbewegung erwartet

Antworte in folgendem Format:
StockScore: [Zahl von 1-10]
Direction: [UP/DOWN/NEUTRAL]
Stocks: [Kommagetrennte Liste: z.B. "AAPL, TSLA, Technologie-Sektor"]
StockReasoning: [Kurze Erklärung der Marktauswirkung]
"""
    
    def _parse_ai_response(self, response: str) -> Tuple[float, str]:
        """Extrahiert Score und Begründung aus der KI-Antwort"""
        try:
            lines = response.strip().split('\n')
            score = 5.0
            reasoning = "Keine Begründung verfügbar"
            
            for line in lines:
                if line.startswith('Score:'):
                    score_str = line.replace('Score:', '').strip()
                    # Extrahiere Zahl aus dem String
                    import re
                    numbers = re.findall(r'\d+\.?\d*', score_str)
                    if numbers:
                        score = float(numbers[0])
                        score = max(1.0, min(10.0, score))  # Clamp zwischen 1-10
                
                elif line.startswith('Begründung:'):
                    reasoning = line.replace('Begründung:', '').strip()
            
            return score, reasoning
            
        except Exception:
            return 5.0, "Fehler beim Parsen der KI-Antwort"
    
    def _parse_stock_analysis_response(self, response: str) -> Tuple[float, str, List[str], str]:
        """Extrahiert Aktienmarkt-Analyse aus der KI-Antwort"""
        try:
            lines = response.strip().split('\n')
            stock_score = 1.0
            direction = "NEUTRAL"
            stocks = []
            stock_reasoning = "Keine Aktienanalyse verfügbar"
            
            for line in lines:
                if line.startswith('StockScore:'):
                    score_str = line.replace('StockScore:', '').strip()
                    import re
                    numbers = re.findall(r'\d+\.?\d*', score_str)
                    if numbers:
                        stock_score = float(numbers[0])
                        stock_score = max(1.0, min(10.0, stock_score))
                
                elif line.startswith('Direction:'):
                    direction = line.replace('Direction:', '').strip().upper()
                    if direction not in ['UP', 'DOWN', 'NEUTRAL']:
                        direction = "NEUTRAL"
                
                elif line.startswith('Stocks:'):
                    stocks_str = line.replace('Stocks:', '').strip()
                    if stocks_str and stocks_str != "None" and stocks_str != "-":
                        stocks = [s.strip() for s in stocks_str.split(',') if s.strip()]
                
                elif line.startswith('StockReasoning:'):
                    stock_reasoning = line.replace('StockReasoning:', '').strip()
            
            return stock_score, direction, stocks, stock_reasoning
            
        except Exception:
            return 1.0, "NEUTRAL", [], "Fehler beim Parsen der Aktienanalyse"
    
    def sort_articles_by_importance(self, articles: List[NewsArticle]) -> List[NewsArticle]:
        """Sortiert Artikel nach KI-Score (höchste zuerst)"""
        return sorted(articles, key=lambda x: x.ai_score or 0, reverse=True)
    
    def display_results(self, articles: List[NewsArticle]):
        """Zeigt die Ergebnisse in einer schönen Tabelle an"""
        if not articles:
            self._print("❌ Keine Artikel gefunden", "red")
            return
        
        if RICH_AVAILABLE:
            self._display_rich_table(articles)
        else:
            self._display_simple_table(articles)
    
    def _display_rich_table(self, articles: List[NewsArticle]):
        """Zeigt Ergebnisse mit Rich-Tabelle inkl. Aktienmarkt-Analyse"""
        table = Table(title="🗞️  Wichtigste Nachrichten (KI-bewertet + Aktienmarkt-Analyse)")
        
        table.add_column("Rang", style="cyan", width=4)
        table.add_column("News", style="magenta", width=6)
        table.add_column("📊 Aktien", style="yellow", width=8)
        table.add_column("Titel", style="white", width=45)
        table.add_column("Quelle", style="blue", width=15)
        table.add_column("🏢 Betroffene Aktien", style="green", width=25)
        
        for i, article in enumerate(articles, 1):
            news_score = f"{article.ai_score:.1f}/10" if article.ai_score is not None else "N/A"
            
            # Aktienmarkt-Info
            stock_score = article.stock_impact_score or 0
            direction = article.stock_direction or "NEUTRAL"
            stock_emoji = "📈" if direction == "UP" else "📉" if direction == "DOWN" else "➡️"
            stock_display = f"{stock_score:.1f} {stock_emoji}"
            
            # Betroffene Aktien (max 3)
            affected = article.affected_stocks or []
            stocks_display = ", ".join(affected[:3])
            if len(affected) > 3:
                stocks_display += f" +{len(affected)-3}"
            if not stocks_display:
                stocks_display = "-"
            
            table.add_row(
                str(i),
                news_score,
                stock_display,
                article.title[:42] + "..." if len(article.title) > 45 else article.title,
                article.source[:12] + "..." if len(article.source) > 15 else article.source,
                stocks_display[:22] + "..." if len(stocks_display) > 25 else stocks_display
            )
        
        self.console.print(table)
        
        # Top 3 Details mit Aktienanalyse
        self.console.print("\n📊 Top 3 Artikel im Detail:", style="bold yellow")
        for i, article in enumerate(articles[:3], 1):
            news_score = f"{article.ai_score:.1f}/10" if article.ai_score is not None else "N/A"
            stock_score = article.stock_impact_score or 0
            direction = article.stock_direction or "NEUTRAL"
            
            self.console.print(f"\n{i}. {article.title}", style="bold white")
            self.console.print(f"   📰 News-Score: {news_score}", style="magenta")
            self.console.print(f"   💭 News-Begründung: {article.ai_reasoning or 'Keine verfügbar'}", style="green")
            
            # Aktienmarkt-Details
            stock_emoji = "📈" if direction == "UP" else "📉" if direction == "DOWN" else "➡️"
            self.console.print(f"   📊 Aktien-Impact: {stock_score:.1f}/10 {stock_emoji} ({direction})", style="yellow")
            
            if article.affected_stocks:
                stocks_str = ", ".join(article.affected_stocks)
                self.console.print(f"   🏢 Betroffene Aktien: {stocks_str}", style="cyan")
            
            if article.stock_reasoning:
                self.console.print(f"   💡 Aktien-Analyse: {article.stock_reasoning}", style="bright_blue")
            
            self.console.print(f"   🔗 Link: {article.link}", style="blue")
    
    def _display_simple_table(self, articles: List[NewsArticle]):
        """Zeigt Ergebnisse als einfache Textausgabe"""
        print("\n" + "="*80)
        print("📰 WICHTIGSTE NACHRICHTEN (KI-BEWERTET)")
        print("="*80)
        
        for i, article in enumerate(articles, 1):
            score_str = f"{article.ai_score:.1f}/10" if article.ai_score is not None else "N/A"
            print(f"\n{i:2d}. Score: {score_str}")
            print(f"    Titel: {article.title}")
            print(f"    Quelle: {article.source}")
            print(f"    Begründung: {article.ai_reasoning or 'Keine verfügbar'}")
            print(f"    Link: {article.link}")
            print("-" * 80)
    
    def run_analysis(self):
        """Führt die komplette Nachrichtenanalyse durch"""
        start_time = time.time()
        
        self._print("🚀 Starte intelligente Nachrichtenanalyse...", "bold green")
        
        # 1. RSS-Feeds laden
        articles = self.fetch_rss_articles()
        self._print(f"✅ {len(articles)} Artikel geladen", "green")
        
        if not articles:
            self._print("❌ Keine Artikel gefunden!", "red")
            return
        
        # 2. KI-Analyse
        articles = self.analyze_articles_with_ai(articles)
        
        # 3. Sortierung nach Wichtigkeit
        sorted_articles = self.sort_articles_by_importance(articles)
        
        # 4. Ergebnisse anzeigen
        self.display_results(sorted_articles)
        
        # 5. Mobile Benachrichtigungen senden (für wichtige Artikel)
        self.send_mobile_notifications(sorted_articles)
        
        # Timing
        end_time = time.time()
        duration = end_time - start_time
        self._print(f"\n⏱️  Analyse abgeschlossen in {duration:.1f} Sekunden", "bold blue")

    def send_mobile_notifications(self, articles: List[NewsArticle]):
        """Sendet Mobile Benachrichtigungen für wichtige Artikel"""
        # Check if notifications are enabled
        enabled = os.getenv('ENABLE_MOBILE_NOTIFICATIONS', 'false').lower() == 'true'
        api_key = os.getenv('PUSHBULLET_API_KEY', '')
        threshold = float(os.getenv('NOTIFICATION_THRESHOLD', '7.5'))
        
        if not enabled or not api_key:
            return
        
        # Filter important articles
        important_articles = [a for a in articles if a.ai_score >= threshold]
        
        if not important_articles:
            self._print("📱 Keine Artikel über Notification-Threshold gefunden", "yellow")
            return
        
        try:
            import requests
            from datetime import datetime
            
            # Send timestamp message first
            now = datetime.now()
            timestamp_msg = f"📰 Hier kommen die Nachrichten vom {now.strftime('%d.%m.%Y')} um {now.strftime('%H:%M')} Uhr:"
            
            url = "https://api.pushbullet.com/v2/pushes"
            headers = {
                'Access-Token': api_key,
                'Content-Type': 'application/json'
            }
            
            # Send timestamp notification
            timestamp_data = {
                'type': 'note',
                'title': '📅 News-Update',
                'body': timestamp_msg
            }
            
            response = requests.post(url, headers=headers, json=timestamp_data)
            if response.status_code == 200:
                self._print("📱 Timestamp-Nachricht gesendet", "green")
            
            # Send individual article notifications
            sent_count = 0
            for article in important_articles[:10]:  # Max 10 notifications
                body = f"Score: {article.ai_score}/10\n{article.description[:200]}..."
                if article.ai_reasoning and "Nur Titel-Analyse" not in article.ai_reasoning:
                    body += f"\n\nBegründung: {article.ai_reasoning[:150]}..."
                
                data = {
                    'type': 'link',
                    'title': f"📰 {article.title}",
                    'body': body,
                    'url': article.link
                }
                
                response = requests.post(url, headers=headers, json=data)
                if response.status_code == 200:
                    sent_count += 1
                    time.sleep(0.5)  # Rate limiting
            
            # Send overview of all articles as simple list
            self._send_all_articles_overview(articles, url, headers)
            
            self._print(f"📱 {sent_count} Notifications erfolgreich gesendet", "green")
            
        except Exception as e:
            self._print(f"❌ Notification Fehler: {e}", "red")
    
    def _send_all_articles_overview(self, articles: List[NewsArticle], url: str, headers: dict):
        """Sendet Übersicht aller Artikel als einfache Liste"""
        try:
            # Alle Artikel nach Score sortiert
            all_articles = sorted(articles, key=lambda x: x.ai_score, reverse=True)
            
            # Erstelle Liste ohne Links (nur Titel + Score)
            overview_lines = ["📊 Alle Artikel im Überblick:", ""]
            
            for i, article in enumerate(all_articles, 1):
                if article.ai_score >= 9:
                    score_emoji = "🔴"
                elif article.ai_score >= 8:
                    score_emoji = "🟡"
                elif article.ai_score >= 7:
                    score_emoji = "🟢"
                else:
                    score_emoji = "🔵"
                    
                overview_lines.append(f"{i:2d}. [{article.ai_score:.1f}] {score_emoji} {article.title}")
            
            # Teile in Chunks auf (Pushbullet hat Limits)
            chunk_size = 25
            for i in range(0, len(overview_lines), chunk_size):
                chunk = overview_lines[i:i+chunk_size]
                overview_text = "\n".join(chunk)
                
                data = {
                    'type': 'note',
                    'title': f'📋 Artikel-Übersicht (Teil {i//chunk_size + 1})',
                    'body': overview_text
                }
                
                response = requests.post(url, headers=headers, json=data)
                if response.status_code == 200:
                    self._print(f"📱 Artikel-Übersicht Teil {i//chunk_size + 1} gesendet", "green")
                    time.sleep(0.5)  # Rate limiting
                
        except Exception as e:
            self._print(f"❌ Artikel-Übersicht Fehler: {e}", "red")


def main():
    """Hauptfunktion"""
    try:
        analyzer = NewsAnalyzer()
        analyzer.run_analysis()
    except KeyboardInterrupt:
        print("\n❌ Analyse abgebrochen durch Benutzer")
    except Exception as e:
        print(f"❌ Unerwarteter Fehler: {e}")


if __name__ == "__main__":
    main()
