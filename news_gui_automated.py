#!/usr/bin/env python3
"""
Premium News Analyzer GUI mit integriertem Scheduler
Automatische News-Updates mit Mobile Notifications direkt in der GUI
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import time
import requests
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import webbrowser
import os
from dataclasses import dataclass
import feedparser
from dotenv import load_dotenv
import schedule
import logging

# Load environment variables
load_dotenv()  # Lade Standard .env
load_dotenv('.env.local', override=True)  # Lade private Keys (überschreibt)

# Importiere das Haupt-Analysesystem
import sys
import importlib.util

@dataclass
class NewsArticle:
    """Artikel mit erweiterten Metadaten"""
    title: str
    description: str
    link: str
    published: str
    source: str
    ai_score: float = 0.0
    ai_reasoning: str = ""
    category: str = ""
    notification_sent: bool = False
    score: float = 0.0  # Hinzugefügt für Kompatibilität
    
    # Neue Aktienmarkt-Analyse Felder
    stock_impact_score: float = 0.0      # 1-10 Bewertung der Marktauswirkung
    stock_direction: str = "NEUTRAL"     # "UP", "DOWN", "NEUTRAL"
    affected_stocks: list = None         # Liste der betroffenen Aktien/Sektoren
    stock_reasoning: str = ""            # Begründung der Aktienanalyse
    
    def __post_init__(self):
        if self.affected_stocks is None:
            self.affected_stocks = []


class MobileNotificationService:
    """Service für Mobile Benachrichtigungen via Pushbullet"""
    
    def __init__(self):
        self.api_key = os.getenv('PUSHBULLET_API_KEY', '')
        self.enabled = os.getenv('ENABLE_MOBILE_NOTIFICATIONS', 'false').lower() == 'true'
        self.threshold = float(os.getenv('NOTIFICATION_THRESHOLD', '7.5'))
        
    def send_notification(self, article: NewsArticle) -> bool:
        """Sendet Notification an Handy via Pushbullet"""
        if not self.enabled or not self.api_key:
            return False
            
        if article.ai_score < self.threshold:
            return False
            
        try:
            # Pushbullet API endpoint
            url = "https://api.pushbullet.com/v2/pushes"
            
            # Message content
            title = f"📰 Breaking News (Score: {article.ai_score}/10)"
            body = f"{article.title}\n\n🏢 {article.source}\n🧠 {article.ai_reasoning[:150]}..."
            
            # API request data
            data = {
                "type": "note",
                "title": title,
                "body": body
            }
            
            # Headers with API key
            headers = {
                "Access-Token": self.api_key,
                "Content-Type": "application/json"
            }
            
            # Send notification
            response = requests.post(url, json=data, headers=headers, timeout=10)
            
            # Send link as separate push if article has URL
            if article.link and response.status_code == 200:
                link_data = {
                    "type": "link",
                    "title": "🔗 Read Full Article",
                    "url": article.link,
                    "body": f"Open: {article.title[:50]}..."
                }
                requests.post(url, json=link_data, headers=headers, timeout=10)
            
            return response.status_code == 200
            
        except Exception as e:
            print(f"Pushbullet Notification Error: {e}")
            return False


class IntegratedScheduler:
    """Scheduler integriert in die GUI"""
    
    def __init__(self, gui_instance):
        self.gui = gui_instance
        self.is_running = False
        self.last_articles = []
        
        # Scheduler-Konfiguration
        self.schedule_times = [
            "06:00", "09:00", "12:00", "15:00", "18:00", "21:00"
        ]
        
        self.emergency_threshold = 9.5
        self.min_score_for_notification = float(os.getenv('NOTIFICATION_THRESHOLD', '7.5'))
        
        self.setup_schedule()
    
    def setup_schedule(self):
        """Konfiguriert den Zeitplan"""
        # Reguläre Analysen
        for time_str in self.schedule_times:
            schedule.every().day.at(time_str).do(self.run_scheduled_analysis)
        
        # Breaking News Check alle 30 Minuten
        schedule.every(30).minutes.do(self.run_emergency_check)
        
        # Täglicher Status Report
        schedule.every().day.at("08:00").do(self.send_daily_summary)
    
    def start(self):
        """Startet den Scheduler"""
        self.is_running = True
        self.gui.log_message("🚀 Automatischer Scheduler gestartet")
        self.gui.log_message(f"⏰ Geplante Updates: {', '.join(self.schedule_times)}")
        self.gui.log_message("🚨 Breaking News Check: Alle 30 Minuten")
        
        # Scheduler-Thread starten
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
    
    def stop(self):
        """Stoppt den Scheduler"""
        self.is_running = False
        schedule.clear()
        self.gui.log_message("⏹️ Automatischer Scheduler gestoppt")
    
    def _scheduler_loop(self):
        """Hauptschleife des Schedulers"""
        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except Exception as e:
                self.gui.log_message(f"❌ Scheduler Error: {e}")
                time.sleep(60)
    
    def run_scheduled_analysis(self):
        """Führt geplante Analyse durch"""
        self.gui.log_message("🔄 Automatische News-Analyse gestartet...")
        self.gui.scheduled_refresh()
    
    def run_emergency_check(self):
        """Prüft auf Breaking News"""
        self.gui.log_message("🚨 Breaking News Check...")
        # Quick check - nur erste 10 Artikel
        self.gui.scheduled_refresh(quick_mode=True)
    
    def send_daily_summary(self):
        """Sendet tägliche Zusammenfassung"""
        high_priority_count = len([a for a in self.gui.articles if a.ai_score >= 8.0])
        if high_priority_count > 0:
            self.gui.log_message(f"📊 Tägliche Zusammenfassung: {high_priority_count} wichtige Artikel heute")


class NewsAnalyzerGUI:
    """Hauptfenster der GUI-Anwendung mit integriertem Scheduler"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🗞️ Premium News Analyzer - Automated Edition")
        self.root.geometry("1500x1000")
        self.root.configure(bg='#f0f0f0')
        
        # Services
        self.notification_service = MobileNotificationService()
        self.analyzer = None
        self.articles = []
        self.scheduler = None
        
        # Settings
        self.auto_scheduler_enabled = True
        self.manual_refresh_interval = int(os.getenv('AUTO_REFRESH_MINUTES', '120')) * 60
        
        self.setup_gui()
        self.load_analyzer()
        
        # Integrierter Scheduler
        if self.auto_scheduler_enabled:
            self.scheduler = IntegratedScheduler(self)
            self.scheduler.start()
    
    def setup_gui(self):
        """Erstellt die GUI-Komponenten"""
        # Header
        header_frame = tk.Frame(self.root, bg='#2c3e50', height=80)
        header_frame.pack(fill='x', padx=0, pady=0)
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(
            header_frame,
            text="🗞️ Premium News Analyzer - Automated Edition",
            font=('Arial', 22, 'bold'),
            fg='white',
            bg='#2c3e50'
        )
        title_label.pack(pady=20)
        
        # Toolbar
        toolbar_frame = tk.Frame(self.root, bg='#34495e', height=60)
        toolbar_frame.pack(fill='x')
        toolbar_frame.pack_propagate(False)
        
        # Buttons Row 1
        button_frame1 = tk.Frame(toolbar_frame, bg='#34495e')
        button_frame1.pack(pady=5)
        
        self.refresh_btn = tk.Button(
            button_frame1,
            text="🔄 Manual Refresh",
            command=self.manual_refresh,
            bg='#3498db',
            fg='white',
            font=('Arial', 11, 'bold'),
            relief='flat',
            padx=15
        )
        self.refresh_btn.pack(side='left', padx=5)
        
        self.scheduler_btn = tk.Button(
            button_frame1,
            text="⏰ Stop Scheduler" if self.auto_scheduler_enabled else "⏰ Start Scheduler",
            command=self.toggle_scheduler,
            bg='#e74c3c' if self.auto_scheduler_enabled else '#27ae60',
            fg='white',
            font=('Arial', 11, 'bold'),
            relief='flat',
            padx=15
        )
        self.scheduler_btn.pack(side='left', padx=5)
        
        self.settings_btn = tk.Button(
            button_frame1,
            text="⚙️ Settings",
            command=self.open_settings,
            bg='#95a5a6',
            fg='white',
            font=('Arial', 11, 'bold'),
            relief='flat',
            padx=15
        )
        self.settings_btn.pack(side='left', padx=5)
        
        self.clear_log_btn = tk.Button(
            button_frame1,
            text="🗑️ Clear Log",
            command=self.clear_log,
            bg='#8e44ad',
            fg='white',
            font=('Arial', 11, 'bold'),
            relief='flat',
            padx=15
        )
        self.clear_log_btn.pack(side='left', padx=5)
        
        # Status Label
        self.status_label = tk.Label(
            toolbar_frame,
            text="🚀 Scheduler aktiv - Automatische Updates alle 30min + 6x täglich",
            fg='white',
            bg='#34495e',
            font=('Arial', 10)
        )
        self.status_label.pack(side='bottom', pady=5)
        
        # Main Content Area
        main_frame = tk.Frame(self.root, bg='#f0f0f0')
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Left Panel - Article List (60% width)
        left_frame = tk.Frame(main_frame, bg='white', relief='solid', bd=1)
        left_frame.pack(side='left', fill='both', expand=True, padx=(0, 5))
        
        # Article List Header
        list_header = tk.Frame(left_frame, bg='#ecf0f1', height=40)
        list_header.pack(fill='x')
        list_header.pack_propagate(False)
        
        tk.Label(
            list_header,
            text="📊 Breaking News & Important Stories (Score ≥ 7.0)",
            font=('Arial', 14, 'bold'),
            bg='#ecf0f1'
        ).pack(pady=10)
        
        # Scrollable Article List
        list_frame = tk.Frame(left_frame)
        list_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.article_listbox = tk.Listbox(
            list_frame,
            font=('Arial', 11),
            selectmode='single',
            relief='flat',
            bd=0,
            highlightthickness=0
        )
        self.article_listbox.pack(side='left', fill='both', expand=True)
        self.article_listbox.bind('<<ListboxSelect>>', self.on_article_select)
        
        list_scrollbar = tk.Scrollbar(list_frame, orient='vertical')
        list_scrollbar.pack(side='right', fill='y')
        list_scrollbar.config(command=self.article_listbox.yview)
        self.article_listbox.config(yscrollcommand=list_scrollbar.set)
        
        # Right Panel - Article Details + Log (40% width)
        right_frame = tk.Frame(main_frame, bg='white', relief='solid', bd=1)
        right_frame.pack(side='right', fill='both', padx=(5, 0))
        
        # Notebook for Tabs
        notebook = ttk.Notebook(right_frame)
        notebook.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Tab 1: Article Details
        details_tab = tk.Frame(notebook, bg='white')
        notebook.add(details_tab, text="📋 Article Details")
        
        # Details Content
        details_content = tk.Frame(details_tab, bg='white')
        details_content.pack(fill='both', expand=True, padx=15, pady=15)
        
        # Title
        self.title_label = tk.Label(
            details_content,
            text="Select an article to view details",
            font=('Arial', 16, 'bold'),
            wraplength=400,
            justify='left',
            anchor='w',
            bg='white'
        )
        self.title_label.pack(fill='x', pady=(0, 10))
        
        # Meta Info Frame
        meta_frame = tk.Frame(details_content, bg='white')
        meta_frame.pack(fill='x', pady=(0, 15))
        
        self.score_label = tk.Label(
            meta_frame,
            text="",
            font=('Arial', 12, 'bold'),
            bg='white'
        )
        self.score_label.pack(side='left')
        
        self.source_label = tk.Label(
            meta_frame,
            text="",
            font=('Arial', 11),
            fg='#7f8c8d',
            bg='white'
        )
        self.source_label.pack(side='right')
        
        # Description
        self.description_text = scrolledtext.ScrolledText(
            details_content,
            height=6,
            font=('Arial', 11),
            wrap='word',
            relief='flat',
            bd=1,
            bg='#f8f9fa'
        )
        self.description_text.pack(fill='both', expand=True, pady=(0, 15))
        
        # AI Reasoning
        tk.Label(
            details_content,
            text="🧠 AI Analysis:",
            font=('Arial', 12, 'bold'),
            anchor='w',
            bg='white'
        ).pack(fill='x')
        
        self.reasoning_text = scrolledtext.ScrolledText(
            details_content,
            height=4,
            font=('Arial', 10),
            wrap='word',
            relief='flat',
            bd=1,
            bg='#e8f5e8'
        )
        self.reasoning_text.pack(fill='both', expand=True, pady=(5, 15))
        
        # Stock Market Analysis Section
        tk.Label(
            details_content,
            text="📊 Stock Market Impact:",
            font=('Arial', 12, 'bold'),
            anchor='w',
            bg='white'
        ).pack(fill='x', pady=(0, 5))
        
        # Stock Info Frame
        stock_frame = tk.Frame(details_content, bg='white')
        stock_frame.pack(fill='x', pady=(0, 10))
        
        self.stock_score_label = tk.Label(
            stock_frame,
            text="Impact: N/A",
            font=('Arial', 11, 'bold'),
            bg='white'
        )
        self.stock_score_label.pack(side='left')
        
        self.stock_direction_label = tk.Label(
            stock_frame,
            text="",
            font=('Arial', 11, 'bold'),
            bg='white'
        )
        self.stock_direction_label.pack(side='right')
        
        # Affected Stocks
        tk.Label(
            details_content,
            text="🏢 Affected Stocks/Sectors:",
            font=('Arial', 10, 'bold'),
            anchor='w',
            bg='white'
        ).pack(fill='x')
        
        self.stocks_text = scrolledtext.ScrolledText(
            details_content,
            height=3,
            font=('Arial', 9),
            wrap='word',
            relief='flat',
            bd=1,
            bg='#fff3e0'
        )
        self.stocks_text.pack(fill='x', pady=(5, 15))
        
        # Stock Reasoning
        tk.Label(
            details_content,
            text="💡 Stock Analysis:",
            font=('Arial', 10, 'bold'),
            anchor='w',
            bg='white'
        ).pack(fill='x')
        
        self.stock_reasoning_text = scrolledtext.ScrolledText(
            details_content,
            height=3,
            font=('Arial', 9),
            wrap='word',
            relief='flat',
            bd=1,
            bg='#e3f2fd'
        )
        self.stock_reasoning_text.pack(fill='x', pady=(5, 15))
        
        # Action Buttons
        action_frame = tk.Frame(details_content, bg='white')
        action_frame.pack(fill='x')
        
        self.read_btn = tk.Button(
            action_frame,
            text="🔗 Open Article",
            command=self.open_article,
            bg='#27ae60',
            fg='white',
            font=('Arial', 11, 'bold'),
            relief='flat',
            padx=20
        )
        self.read_btn.pack(side='left')
        
        self.notify_btn = tk.Button(
            action_frame,
            text="📱 Send to Phone",
            command=self.send_notification,
            bg='#3498db',
            fg='white',
            font=('Arial', 11, 'bold'),
            relief='flat',
            padx=20
        )
        self.notify_btn.pack(side='left', padx=(10, 0))
        
        # Tab 2: Live Log
        log_tab = tk.Frame(notebook, bg='white')
        notebook.add(log_tab, text="📝 Live Log")
        
        log_content = tk.Frame(log_tab, bg='white')
        log_content.pack(fill='both', expand=True, padx=10, pady=10)
        
        tk.Label(
            log_content,
            text="🔴 Live Activity Log",
            font=('Arial', 14, 'bold'),
            bg='white'
        ).pack(anchor='w', pady=(0, 10))
        
        self.log_text = scrolledtext.ScrolledText(
            log_content,
            font=('Consolas', 10),
            wrap='word',
            relief='flat',
            bd=1,
            bg='#2c3e50',
            fg='#ecf0f1',
            insertbackground='white'
        )
        self.log_text.pack(fill='both', expand=True)
        
        # Initial log message
        self.log_message("🚀 News Analyzer gestartet")
        self.log_message(f"📱 Pushbullet: {'✅ Aktiviert' if self.notification_service.enabled else '❌ Deaktiviert'}")
    
    def log_message(self, message):
        """Fügt Nachricht zum Live-Log hinzu"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def clear_log(self):
        """Löscht das Log"""
        self.log_text.delete(1.0, tk.END)
        self.log_message("🗑️ Log gelöscht")
    
    def toggle_scheduler(self):
        """Startet/Stoppt den automatischen Scheduler"""
        if self.auto_scheduler_enabled:
            # Scheduler stoppen
            if self.scheduler:
                self.scheduler.stop()
            self.auto_scheduler_enabled = False
            self.scheduler_btn.config(
                text="⏰ Start Scheduler",
                bg='#27ae60'
            )
            self.status_label.config(text="⏸️ Scheduler gestoppt - Nur manuelle Updates")
            self.log_message("⏹️ Automatischer Scheduler gestoppt")
        else:
            # Scheduler starten
            self.scheduler = IntegratedScheduler(self)
            self.scheduler.start()
            self.auto_scheduler_enabled = True
            self.scheduler_btn.config(
                text="⏰ Stop Scheduler",
                bg='#e74c3c'
            )
            self.status_label.config(text="🚀 Scheduler aktiv - Automatische Updates alle 30min + 6x täglich")
            self.log_message("🚀 Automatischer Scheduler gestartet")
    
    def load_analyzer(self):
        """Lädt das Analyse-System"""
        try:
            # Importiere das Hauptsystem dynamisch
            spec = importlib.util.spec_from_file_location("news_module", "P-News.py")
            news_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(news_module)
            
            self.analyzer = news_module.NewsAnalyzer()
            self.log_message("✅ News Analyzer geladen")
        except Exception as e:
            self.log_message(f"❌ Fehler beim Laden: {e}")
            # Fallback: Zeige Warnung aber breche nicht ab
            self.log_message("⚠️ GUI läuft ohne Analyzer - Analyzer-Funktionen deaktiviert")
    
    def manual_refresh(self):
        """Manueller Refresh-Button"""
        self.refresh_btn.config(state='disabled', text="🔄 Loading...")
        self.log_message("🔄 Manuelle Aktualisierung gestartet...")
        
        # Führe Analyse in separatem Thread aus
        thread = threading.Thread(target=self.run_analysis)
        thread.daemon = True
        thread.start()
    
    def scheduled_refresh(self, quick_mode=False):
        """Automatischer Refresh vom Scheduler"""
        mode_text = "Quick Check" if quick_mode else "Vollständige Analyse"
        self.log_message(f"🔄 Automatische {mode_text}...")
        
        # Führe Analyse in separatem Thread aus
        thread = threading.Thread(target=lambda: self.run_analysis(quick_mode))
        thread.daemon = True
        thread.start()
    
    def run_analysis(self, quick_mode=False):
        """Führt die Nachrichtenanalyse mit Live-Updates aus"""
        try:
            if not self.analyzer:
                self.load_analyzer()
            
            # Phase 1: RSS Feeds laden mit Live-Update
            self.root.after(0, lambda: self.log_message("⠋ Lade RSS-Feeds..."))
            articles = self.analyzer.fetch_rss_articles()
            self.root.after(0, lambda: self.log_message(f"✅ {len(articles)} Artikel geladen"))
            
            # Quick mode: nur erste 10 Artikel für Breaking News Check
            if quick_mode:
                articles = articles[:10]
                self.root.after(0, lambda: self.log_message(f"🚨 Breaking News Check - limitiert auf {len(articles)} Artikel"))
            
            # Custom Analysis mit Live-Updates
            analyzed_articles = self.analyze_with_live_updates(articles, quick_mode)
            sorted_articles = self.analyzer.sort_articles_by_importance(analyzed_articles)
            
            # Konvertiere zu unserer Datenstruktur
            new_articles = []
            for article in sorted_articles:
                news_article = NewsArticle(
                    title=article.title,
                    description=article.description,
                    link=article.link,
                    published=article.published,
                    source=article.source,
                    ai_score=article.ai_score or 0.0,
                    ai_reasoning=article.ai_reasoning or "No analysis available"
                )
                new_articles.append(news_article)
            
            # Finde neue wichtige Artikel für Notifications
            if hasattr(self, 'articles') and self.articles:
                new_important_articles = self.get_new_important_articles(new_articles)
            else:
                # Erste Analyse - sende nur sehr wichtige
                new_important_articles = [a for a in new_articles if a.ai_score >= 8.5]
            
            self.articles = new_articles
            
            # Update GUI im Hauptthread
            self.root.after(0, self.update_gui)
            
            # Sende Notifications für neue wichtige Artikel
            if new_important_articles:
                self.root.after(0, lambda: self.send_high_priority_notifications(new_important_articles))
                mode_text = "Quick Check" if quick_mode else "Analyse"
                self.root.after(0, lambda: self.log_message(f"📱 {len(new_important_articles)} neue wichtige Artikel aus {mode_text}"))
            else:
                mode_text = "Quick Check" if quick_mode else "Analyse"
                self.root.after(0, lambda: self.log_message(f"ℹ️ Keine neuen wichtigen Artikel aus {mode_text}"))
            
        except Exception as e:
            error_msg = str(e)
            self.root.after(0, lambda msg=error_msg: self.log_message(f"❌ Analyse-Fehler: {msg}"))
            self.root.after(0, lambda msg=error_msg: messagebox.showerror("Analysis Error", msg))
        finally:
            self.root.after(0, self.reset_refresh_button)
    
    def analyze_with_live_updates(self, articles, quick_mode=False):
        """Custom Analysis-Methode mit Live-GUI-Updates"""
        if not articles:
            return articles
        
        # Phase 1: Titel-Analyse
        self.root.after(0, lambda: self.log_message(f"📊 Phase 1: Schnelle Titel-Analyse von {len(articles)} Artikeln..."))
        title_scored_articles = self.analyzer._quick_title_analysis(articles)
        
        # Sortiere und wähle Top-Artikel für Vollanalyse
        title_scored_articles.sort(key=lambda x: x.score, reverse=True)
        
        if quick_mode:
            # Im Quick-Mode nur Top 10 analysieren
            top_articles = title_scored_articles[:10]
            remaining_articles = title_scored_articles[10:]
            self.root.after(0, lambda: self.log_message(f"🎯 Phase 2: Quick-Analyse der Top {len(top_articles)} Artikel..."))
        else:
            # Normal-Mode: Top 10 für Vollanalyse
            top_articles = title_scored_articles[:10]
            remaining_articles = title_scored_articles[10:]
            self.root.after(0, lambda: self.log_message(f"🎯 Phase 2: Vollanalyse der Top {len(top_articles)} Artikel..."))
        
        # Phase 2: AI-Analyse mit Live-Updates
        if self.analyzer.ai_model_type == 'openai':
            analyzed_top = self.analyze_with_openai_live(top_articles)
        elif self.analyzer.ai_model_type == 'ollama':
            analyzed_top = self.analyze_with_ollama_live(top_articles)
        else:
            self.root.after(0, lambda: self.log_message("❌ Unbekannter AI-Model-Typ"))
            for article in top_articles:
                article.ai_score = article.score
                article.ai_reasoning = "Keine KI-Analyse verfügbar"
            analyzed_top = top_articles
        
        # Phase 3: Restliche Artikel
        for article in remaining_articles:
            article.ai_score = article.score
            article.ai_reasoning = "Nur Titel-Analyse (nicht in Top 10)"
        
        # Kombiniere und sortiere
        all_articles = analyzed_top + remaining_articles
        all_articles.sort(key=lambda x: x.ai_score, reverse=True)
        
        return all_articles
    
    def analyze_with_ollama_live(self, articles):
        """Ollama-Analyse mit Live-Updates inkl. Aktienmarkt-Analyse"""
        self.root.after(0, lambda: self.log_message("🤖 Analysiere Artikel mit Ollama (llama2)..."))
        
        for i, article in enumerate(articles, 1):
            # Live-Update für aktuellen Artikel
            short_title = article.title[:50] + "..." if len(article.title) > 50 else article.title
            self.root.after(0, lambda title=short_title, idx=i, total=len(articles): 
                          self.log_message(f"Analysiere Artikel {idx}/{total}: {title}"))
            
            try:
                # 1. News-Relevanz-Analyse
                news_prompt = self.analyzer._create_analysis_prompt(article)
                response = requests.post(
                    'http://localhost:11434/api/generate',
                    json={
                        'model': 'llama2',
                        'prompt': news_prompt,
                        'stream': False
                    },
                    timeout=120
                )
                
                if response.status_code == 200:
                    result = response.json()
                    analysis_text = result.get('response', '')
                    
                    # Parse News-Analyse
                    try:
                        import re
                        score_match = re.search(r'Score:\s*(\d+(?:\.\d+)?)', analysis_text)
                        if score_match:
                            score = float(score_match.group(1))
                        else:
                            score = 5.0
                        
                        reasoning_match = re.search(r'Begründung:\s*(.+)', analysis_text, re.DOTALL)
                        if reasoning_match:
                            reasoning = reasoning_match.group(1).strip()
                        else:
                            reasoning = analysis_text[:200] + "..." if len(analysis_text) > 200 else analysis_text
                        
                        article.ai_score = min(10.0, max(0.0, score))
                        article.ai_reasoning = reasoning
                        
                    except Exception:
                        article.ai_score = article.score
                        article.ai_reasoning = "Parsing-Fehler bei News-Analyse"
                
                else:
                    article.ai_score = article.score
                    article.ai_reasoning = f"API-Fehler: {response.status_code}"
                
                # 2. Aktienmarkt-Analyse
                stock_prompt = self.analyzer._create_stock_analysis_prompt(article)
                stock_response = requests.post(
                    'http://localhost:11434/api/generate',
                    json={
                        'model': 'llama2',
                        'prompt': stock_prompt,
                        'stream': False
                    },
                    timeout=120
                )
                
                if stock_response.status_code == 200:
                    stock_result = stock_response.json()
                    stock_analysis_text = stock_result.get('response', '')
                    
                    # Parse Aktien-Analyse
                    try:
                        import re
                        
                        # Stock Score
                        stock_score_match = re.search(r'StockScore:\s*(\d+(?:\.\d+)?)', stock_analysis_text)
                        if stock_score_match:
                            stock_score = float(stock_score_match.group(1))
                        else:
                            stock_score = 1.0
                        
                        # Direction
                        direction_match = re.search(r'Direction:\s*(\w+)', stock_analysis_text)
                        if direction_match:
                            direction = direction_match.group(1).upper()
                        else:
                            direction = "NEUTRAL"
                        
                        # Stocks
                        stocks_match = re.search(r'Stocks:\s*(.+)', stock_analysis_text)
                        if stocks_match:
                            stocks_str = stocks_match.group(1).strip()
                            if stocks_str and stocks_str != "None" and stocks_str != "-":
                                stocks = [s.strip() for s in stocks_str.split(',') if s.strip()]
                            else:
                                stocks = []
                        else:
                            stocks = []
                        
                        # Stock Reasoning
                        stock_reasoning_match = re.search(r'StockReasoning:\s*(.+)', stock_analysis_text, re.DOTALL)
                        if stock_reasoning_match:
                            stock_reasoning = stock_reasoning_match.group(1).strip()
                        else:
                            stock_reasoning = "Keine Aktienanalyse verfügbar"
                        
                        article.stock_impact_score = min(10.0, max(1.0, stock_score))
                        article.stock_direction = direction if direction in ['UP', 'DOWN', 'NEUTRAL'] else 'NEUTRAL'
                        article.affected_stocks = stocks
                        article.stock_reasoning = stock_reasoning
                        
                        # Live-Update mit Aktieninfo
                        stock_emoji = "📈" if direction == "UP" else "📉" if direction == "DOWN" else "➡️"
                        self.root.after(0, lambda s=score, ss=stock_score, se=stock_emoji: 
                                      self.log_message(f"  ✅ News: {s:.1f}/10 | 📊 Aktien: {ss:.1f}/10 {se}"))
                        
                    except Exception as parse_error:
                        article.stock_impact_score = 1.0
                        article.stock_direction = "NEUTRAL"
                        article.affected_stocks = []
                        article.stock_reasoning = f"Parsing-Fehler: {str(parse_error)[:100]}"
                
                else:
                    article.stock_impact_score = 1.0
                    article.stock_direction = "NEUTRAL"
                    article.affected_stocks = []
                    article.stock_reasoning = f"Aktien-API-Fehler: {stock_response.status_code}"
                    
            except Exception as e:
                # Netzwerk- oder andere Fehler
                article.ai_score = article.score
                article.ai_reasoning = f"Analyse-Fehler: {str(e)[:100]}"
                article.stock_impact_score = 1.0
                article.stock_direction = "NEUTRAL"
                article.affected_stocks = []
                article.stock_reasoning = f"Fehler bei Aktienanalyse: {str(e)[:100]}"
        
        return articles
    
    def analyze_with_openai_live(self, articles):
        """OpenAI-Analyse mit Live-Updates"""
        self.root.after(0, lambda: self.log_message("🤖 Analysiere Artikel mit OpenAI..."))
        
        for i, article in enumerate(articles, 1):
            short_title = article.title[:50] + "..." if len(article.title) > 50 else article.title
            self.root.after(0, lambda title=short_title, idx=i, total=len(articles): 
                          self.log_message(f"Analysiere Artikel {idx}/{total}: {title}"))
            
            try:
                # OpenAI API Call (hier würde die echte OpenAI-Logik stehen)
                # Fallback für Demo
                article.ai_score = article.score
                article.ai_reasoning = "OpenAI-Analyse (Demo-Modus)"
                time.sleep(0.5)  # Simuliere Verarbeitungszeit
                
            except Exception as e:
                article.ai_score = article.score
                article.ai_reasoning = f"OpenAI-Fehler: {str(e)[:100]}"
        
        return articles
    
    def _create_analysis_prompt(self, article):
        """Erstellt einen Prompt für die News-Relevanz-Analyse"""
        return f"""
Analysiere die Wichtigkeit und Relevanz des folgenden Nachrichtenartikels für ein deutschsprachiges Publikum.

Artikel:
Titel: {article.title}
Beschreibung: {article.description}
Quelle: {article.source}

Bewerte von 0-10 (10 = extrem wichtig, Breaking News):
- Gesellschaftliche Relevanz (Politik, Wirtschaft, Gesellschaft)
- Aktualität und Dringlichkeit
- Reichweite der Auswirkungen
- Nachrichtenwert

Antworte in folgendem Format:
Score: [Zahl zwischen 0-10]
Begründung: [Kurze Erklärung der Bewertung]
"""

    def _create_stock_analysis_prompt(self, article):
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
    
    def get_new_important_articles(self, new_articles):
        """Filtert neue wichtige Artikel"""
        if not hasattr(self, 'articles') or not self.articles:
            return []
        
        new_important = []
        for article in new_articles:
            if article.ai_score >= self.notification_service.threshold:
                # Check if we've seen this article before
                is_new = True
                for old_article in self.articles:
                    if (article.title == old_article.title or 
                        article.link == old_article.link):
                        is_new = False
                        break
                
                if is_new:
                    new_important.append(article)
        
        return new_important
    
    def update_gui(self):
        """Aktualisiert die GUI mit neuen Artikeln inkl. Aktienmarkt-Infos und Alter"""
        # Lösche alte Einträge
        self.article_listbox.delete(0, tk.END)
        
        # Zeige nur Artikel mit Score >= 7.0
        high_priority_articles = [a for a in self.articles if a.ai_score >= 7.0]
        
        for i, article in enumerate(high_priority_articles):
            # News Score Icon
            if article.ai_score >= 9:
                score_color = "🔴"
            elif article.ai_score >= 8:
                score_color = "🟡"
            else:
                score_color = "🟢"
            
            # Stock Impact Icon
            stock_score = getattr(article, 'stock_impact_score', 0) or 0
            direction = getattr(article, 'stock_direction', 'NEUTRAL') or 'NEUTRAL'
            
            if stock_score >= 6:
                if direction == "UP":
                    stock_icon = "📈"
                elif direction == "DOWN":
                    stock_icon = "📉"
                else:
                    stock_icon = "⚡"
            else:
                stock_icon = "➡️"
            
            # Berechne Artikel-Alter
            try:
                from datetime import datetime, timezone
                import dateutil.parser
                
                # Parse published date
                if article.published:
                    published_dt = dateutil.parser.parse(article.published)
                    now = datetime.now(timezone.utc)
                    
                    # Stelle sicher, dass beide Datetimes timezone-aware sind
                    if published_dt.tzinfo is None:
                        published_dt = published_dt.replace(tzinfo=timezone.utc)
                    
                    time_diff = now - published_dt
                    
                    # Formatiere Alter
                    if time_diff.days > 0:
                        age_text = f"{time_diff.days}d"
                    elif time_diff.seconds > 3600:
                        hours = time_diff.seconds // 3600
                        age_text = f"{hours}h"
                    elif time_diff.seconds > 60:
                        minutes = time_diff.seconds // 60
                        age_text = f"{minutes}m"
                    else:
                        age_text = "now"
                else:
                    age_text = "?"
            except Exception:
                age_text = "?"
            
            # Formatierte Anzeige: News-Score | Stock-Icon | Alter | Titel
            entry_text = f"{score_color} {article.ai_score:.1f} {stock_icon} [{age_text}] {article.title[:55]}..."
            
            self.article_listbox.insert(tk.END, entry_text)
            
            # Färbe basierend auf News Score
            if article.ai_score >= 9:
                self.article_listbox.itemconfig(i, {'bg': '#ffebee', 'fg': '#c62828'})
            elif article.ai_score >= 8:
                self.article_listbox.itemconfig(i, {'bg': '#fff3e0', 'fg': '#ef6c00'})
            else:
                self.article_listbox.itemconfig(i, {'bg': '#e8f5e8', 'fg': '#2e7d32'})
        
        # Status Update
        total_articles = len(self.articles)
        high_priority_count = len(high_priority_articles)
        stock_articles = len([a for a in self.articles if getattr(a, 'stock_impact_score', 0) >= 6])
        
        self.log_message(
            f"📊 Analyse komplett: {high_priority_count}/{total_articles} wichtige Artikel | {stock_articles} mit Aktienmarkt-Impact"
        )
    
    def on_article_select(self, event):
        """Wird aufgerufen wenn ein Artikel ausgewählt wird"""
        selection = self.article_listbox.curselection()
        if not selection:
            return
        
        # Finde entsprechenden Artikel
        high_priority_articles = [a for a in self.articles if a.ai_score >= 7.0]
        if selection[0] < len(high_priority_articles):
            article = high_priority_articles[selection[0]]
            self.display_article_details(article)
    
    def display_article_details(self, article: NewsArticle):
        """Zeigt Artikeldetails inkl. Aktienmarkt-Analyse und Alter an"""
        # Titel
        self.title_label.config(text=article.title)
        
        # Score (mit Farbe)
        if article.ai_score >= 9:
            score_color = "#c62828"
        elif article.ai_score >= 8:
            score_color = "#ef6c00"
        else:
            score_color = "#2e7d32"
        
        self.score_label.config(text=f"🎯 News Score: {article.ai_score:.1f}/10", fg=score_color)
        
        # Quelle mit Alter
        try:
            from datetime import datetime, timezone
            import dateutil.parser
            
            # Berechne Artikel-Alter
            if article.published:
                published_dt = dateutil.parser.parse(article.published)
                now = datetime.now(timezone.utc)
                
                # Stelle sicher, dass beide Datetimes timezone-aware sind
                if published_dt.tzinfo is None:
                    published_dt = published_dt.replace(tzinfo=timezone.utc)
                
                time_diff = now - published_dt
                
                # Formatiere Alter detailliert
                if time_diff.days > 1:
                    age_text = f"{time_diff.days} Tage alt"
                elif time_diff.days == 1:
                    age_text = "1 Tag alt"
                elif time_diff.seconds > 3600:
                    hours = time_diff.seconds // 3600
                    age_text = f"{hours} Stunde{'n' if hours > 1 else ''} alt"
                elif time_diff.seconds > 60:
                    minutes = time_diff.seconds // 60
                    age_text = f"{minutes} Minute{'n' if minutes > 1 else ''} alt"
                else:
                    age_text = "gerade veröffentlicht"
            else:
                age_text = "Alter unbekannt"
        except Exception:
            age_text = "Alter unbekannt"
        
        self.source_label.config(text=f"📰 {article.source} • ⏰ {age_text}")
        
        # Beschreibung
        self.description_text.delete(1.0, tk.END)
        self.description_text.insert(tk.END, article.description)
        
        # AI Reasoning
        self.reasoning_text.delete(1.0, tk.END)
        self.reasoning_text.insert(tk.END, article.ai_reasoning)
        
        # Stock Market Analysis
        # Stock Score mit Farbe
        stock_score = getattr(article, 'stock_impact_score', 0) or 0
        if stock_score >= 7:
            stock_color = "#c62828"  # Rot für hohen Impact
        elif stock_score >= 4:
            stock_color = "#ef6c00"  # Orange für mittleren Impact
        else:
            stock_color = "#2e7d32"  # Grün für niedrigen Impact
        
        self.stock_score_label.config(text=f"📊 Impact: {stock_score:.1f}/10", fg=stock_color)
        
        # Stock Direction mit Emoji
        direction = getattr(article, 'stock_direction', 'NEUTRAL') or 'NEUTRAL'
        if direction == "UP":
            direction_text = "📈 BULLISH"
            direction_color = "#27ae60"
        elif direction == "DOWN":
            direction_text = "📉 BEARISH"
            direction_color = "#e74c3c"
        else:
            direction_text = "➡️ NEUTRAL"
            direction_color = "#95a5a6"
        
        self.stock_direction_label.config(text=direction_text, fg=direction_color)
        
        # Affected Stocks
        stocks = getattr(article, 'affected_stocks', []) or []
        self.stocks_text.delete(1.0, tk.END)
        if stocks:
            stocks_display = "\n".join([f"• {stock}" for stock in stocks])
            self.stocks_text.insert(tk.END, stocks_display)
        else:
            self.stocks_text.insert(tk.END, "Keine spezifischen Aktien identifiziert")
        
        # Stock Reasoning
        stock_reasoning = getattr(article, 'stock_reasoning', '') or ''
        self.stock_reasoning_text.delete(1.0, tk.END)
        if stock_reasoning:
            self.stock_reasoning_text.insert(tk.END, stock_reasoning)
        else:
            self.stock_reasoning_text.insert(tk.END, "Keine Aktienmarkt-Analyse verfügbar")
        
        # Speichere aktuellen Artikel für Actions
        self.current_article = article
    
    def open_article(self):
        """Öffnet Artikel im Browser"""
        if hasattr(self, 'current_article') and self.current_article:
            webbrowser.open(self.current_article.link)
            self.log_message(f"🔗 Artikel geöffnet: {self.current_article.title[:50]}...")
    
    def send_notification(self):
        """Sendet manuelle Notification"""
        if hasattr(self, 'current_article') and self.current_article:
            success = self.notification_service.send_notification(self.current_article)
            if success:
                self.log_message(f"📱 Notification gesendet: {self.current_article.title[:50]}...")
                messagebox.showinfo("Success", "Notification sent to your phone!")
            else:
                self.log_message("❌ Notification fehlgeschlagen")
                messagebox.showwarning("Warning", "Failed to send notification. Check your Pushbullet settings.")
    
    def send_high_priority_notifications(self, articles):
        """Sendet automatische Notifications für wichtige Artikel"""
        if not articles:
            return
            
        # Sende zuerst eine Datum/Uhrzeit-Nachricht
        from datetime import datetime
        now = datetime.now()
        timestamp_msg = f"📰 Hier kommen die Nachrichten vom {now.strftime('%d.%m.%Y')} um {now.strftime('%H:%M')} Uhr:"
        
        # Sende Timestamp-Nachricht
        self.send_timestamp_notification(timestamp_msg)
        
        sent_count = 0
        for article in articles:
            if self.notification_service.send_notification(article):
                article.notification_sent = True
                sent_count += 1
                self.log_message(f"📱 Auto-Notification: {article.title[:50]}... (Score: {article.ai_score})")
        
        # Sende Übersicht aller anderen Artikel
        self.send_all_articles_overview()
        
        if sent_count > 0:
            self.log_message(f"✅ {sent_count} Notifications erfolgreich gesendet")
    
    def send_all_articles_overview(self):
        """Sendet Übersicht aller Artikel als einfache Liste"""
        if not self.notification_service.enabled or not self.notification_service.api_key:
            return
            
        try:
            # Alle Artikel nach Score sortiert
            all_articles = sorted(self.articles, key=lambda x: x.ai_score, reverse=True)
            
            # Erstelle Liste ohne Links (nur Titel + Score)
            overview_lines = ["📊 Alle Artikel im Überblick:", ""]
            
            for i, article in enumerate(all_articles, 1):
                score_emoji = "🔴" if article.ai_score >= 9 else "🟡" if article.ai_score >= 8 else "🟢" if article.ai_score >= 7 else "🔵"
                overview_lines.append(f"{i:2d}. [{article.ai_score:.1f}] {score_emoji} {article.title}")
            
            # Teile in Chunks auf (Pushbullet hat Limits)
            chunk_size = 25
            for i in range(0, len(overview_lines), chunk_size):
                chunk = overview_lines[i:i+chunk_size]
                overview_text = "\n".join(chunk)
                
                import requests
                url = "https://api.pushbullet.com/v2/pushes"
                headers = {
                    'Access-Token': self.notification_service.api_key,
                    'Content-Type': 'application/json'
                }
                
                data = {
                    'type': 'note',
                    'title': f'📋 Artikel-Übersicht (Teil {i//chunk_size + 1})',
                    'body': overview_text
                }
                
                response = requests.post(url, headers=headers, json=data)
                if response.status_code == 200:
                    self.log_message(f"📱 Artikel-Übersicht Teil {i//chunk_size + 1} gesendet")
                
        except Exception as e:
            self.log_message(f"❌ Artikel-Übersicht Fehler: {e}")
    
    def send_timestamp_notification(self, message):
        """Sendet eine Timestamp-Nachricht via Pushbullet"""
        if not self.notification_service.enabled or not self.notification_service.api_key:
            return
            
        try:
            import requests
            url = "https://api.pushbullet.com/v2/pushes"
            headers = {
                'Access-Token': self.notification_service.api_key,
                'Content-Type': 'application/json'
            }
            
            data = {
                'type': 'note',
                'title': '📅 News-Update',
                'body': message
            }
            
            response = requests.post(url, headers=headers, json=data)
            if response.status_code == 200:
                self.log_message(f"📱 Timestamp-Nachricht gesendet: {message}")
            else:
                self.log_message(f"❌ Timestamp-Nachricht Fehler: {response.status_code}")
                
        except Exception as e:
            self.log_message(f"❌ Timestamp-Nachricht Fehler: {e}")
    
    def reset_refresh_button(self):
        """Setzt Refresh-Button zurück"""
        self.refresh_btn.config(state='normal', text="🔄 Manual Refresh")
    
    def open_settings(self):
        """Öffnet Einstellungsfenster"""
        SettingsWindow(self.root, self.notification_service, self)
    
    def reload_settings(self):
        """Lädt Einstellungen aus .env neu"""
        from dotenv import load_dotenv
        import os
        
        # Reload environment variables
        load_dotenv(override=True)
        
        # Update notification service
        self.notification_service.enabled = os.getenv('ENABLE_MOBILE_NOTIFICATIONS', 'false').lower() == 'true'
        self.notification_service.threshold = float(os.getenv('NOTIFICATION_THRESHOLD', '7.5'))
        self.notification_service.api_key = os.getenv('PUSHBULLET_API_KEY', '')
        
        # Update scheduler
        if self.scheduler:
            self.scheduler.min_score_for_notification = self.notification_service.threshold
        
        self.log_message(f"🔄 Einstellungen neu geladen - Threshold: {self.notification_service.threshold}")
    
    def run(self):
        """Startet die GUI-Anwendung"""
        # Initial load
        self.log_message("🔄 Initiale Analyse wird gestartet...")
        self.manual_refresh()
        
        # Start main loop
        self.root.mainloop()


class SettingsWindow:
    """Einstellungsfenster für Notifications und Scheduler"""
    
    def __init__(self, parent, notification_service, gui_instance):
        self.parent = parent
        self.notification_service = notification_service
        self.gui = gui_instance
        
        self.window = tk.Toplevel(parent)
        self.window.title("⚙️ Settings - Scheduler & Notifications")
        self.window.geometry("600x500")
        self.window.configure(bg='#f0f0f0')
        
        self.setup_settings_gui()
    
    def setup_settings_gui(self):
        """Erstellt das Einstellungs-Interface"""
        # Header
        header = tk.Label(
            self.window,
            text="⚙️ Scheduler & Notification Settings",
            font=('Arial', 16, 'bold'),
            bg='#f0f0f0'
        )
        header.pack(pady=20)
        
        # Main Frame
        main_frame = tk.Frame(self.window, bg='white', relief='solid', bd=1)
        main_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        
        content_frame = tk.Frame(main_frame, bg='white')
        content_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Scheduler Settings
        tk.Label(
            content_frame,
            text="🕐 Automatischer Scheduler:",
            font=('Arial', 14, 'bold'),
            bg='white'
        ).pack(anchor='w', pady=(0, 10))
        
        scheduler_info = tk.Text(
            content_frame,
            height=4,
            font=('Arial', 10),
            wrap='word',
            bg='#f8f9fa',
            relief='flat',
            bd=1
        )
        scheduler_info.pack(fill='x', pady=(0, 15))
        scheduler_info.insert(tk.END, 
            "Automatische Updates:\n"
            "• 6x täglich: 06:00, 09:00, 12:00, 15:00, 18:00, 21:00\n"
            "• Breaking News Check: Alle 30 Minuten\n"
            "• Tägliche Zusammenfassung: 08:00"
        )
        scheduler_info.config(state='disabled')
        
        # Separator
        separator1 = tk.Frame(content_frame, height=2, bg='#ecf0f1')
        separator1.pack(fill='x', pady=15)
        
        # Mobile Notifications
        tk.Label(
            content_frame,
            text="📱 Mobile Notifications:",
            font=('Arial', 14, 'bold'),
            bg='white'
        ).pack(anchor='w', pady=(0, 5))
        
        self.enable_var = tk.BooleanVar(value=self.notification_service.enabled)
        enable_check = tk.Checkbutton(
            content_frame,
            text="Enable mobile notifications via Pushbullet",
            variable=self.enable_var,
            bg='white',
            font=('Arial', 11)
        )
        enable_check.pack(anchor='w', pady=(0, 15))
        
        # Threshold
        tk.Label(
            content_frame,
            text="🎯 Notification Threshold (AI Score):",
            font=('Arial', 12, 'bold'),
            bg='white'
        ).pack(anchor='w', pady=(0, 5))
        
        threshold_frame = tk.Frame(content_frame, bg='white')
        threshold_frame.pack(fill='x', pady=(0, 15))
        
        self.threshold_var = tk.DoubleVar(value=self.notification_service.threshold)
        threshold_scale = tk.Scale(
            threshold_frame,
            from_=5.0,
            to=10.0,
            resolution=0.1,
            orient='horizontal',
            variable=self.threshold_var,
            bg='white'
        )
        threshold_scale.pack(fill='x')
        
        tk.Label(
            content_frame,
            text="Nur Artikel mit Score über diesem Wert lösen Notifications aus",
            font=('Arial', 9),
            fg='#7f8c8d',
            bg='white'
        ).pack(anchor='w', pady=(0, 15))
        
        # Separator
        separator2 = tk.Frame(content_frame, height=2, bg='#ecf0f1')
        separator2.pack(fill='x', pady=15)
        
        # Pushbullet Settings
        tk.Label(
            content_frame,
            text="🔧 Pushbullet Configuration:",
            font=('Arial', 12, 'bold'),
            bg='white'
        ).pack(anchor='w', pady=(0, 5))
        
        tk.Label(
            content_frame,
            text="API Key:",
            font=('Arial', 11),
            bg='white'
        ).pack(anchor='w')
        
        self.api_key_entry = tk.Entry(content_frame, width=50, font=('Arial', 10))
        self.api_key_entry.pack(fill='x', pady=(0, 15))
        self.api_key_entry.insert(0, self.notification_service.api_key)
        
        # Info Text
        info_text = tk.Text(
            content_frame,
            height=4,
            font=('Arial', 9),
            wrap='word',
            bg='#f8f9fa',
            relief='flat',
            bd=1
        )
        info_text.pack(fill='x', pady=(0, 15))
        info_text.insert(tk.END, 
            "Setup Pushbullet:\n"
            "1. Install Pushbullet app on your phone\n"
            "2. Create account at pushbullet.com\n"
            "3. Go to Settings > Access Tokens and create a token"
        )
        info_text.config(state='disabled')
        
        # Buttons
        button_frame = tk.Frame(content_frame, bg='white')
        button_frame.pack(fill='x')
        
        save_btn = tk.Button(
            button_frame,
            text="💾 Save Settings",
            command=self.save_settings,
            bg='#27ae60',
            fg='white',
            font=('Arial', 11, 'bold'),
            relief='flat',
            padx=20
        )
        save_btn.pack(side='left')
        
        test_btn = tk.Button(
            button_frame,
            text="📱 Test Notification",
            command=self.test_notification,
            bg='#3498db',
            fg='white',
            font=('Arial', 11, 'bold'),
            relief='flat',
            padx=20
        )
        test_btn.pack(side='left', padx=(10, 0))
        
        cancel_btn = tk.Button(
            button_frame,
            text="❌ Cancel",
            command=self.window.destroy,
            bg='#95a5a6',
            fg='white',
            font=('Arial', 11, 'bold'),
            relief='flat',
            padx=20
        )
        cancel_btn.pack(side='right')
    
    def save_settings(self):
        """Speichert die Einstellungen"""
        # Update notification service
        old_threshold = self.notification_service.threshold
        
        self.notification_service.enabled = self.enable_var.get()
        self.notification_service.threshold = self.threshold_var.get()
        self.notification_service.api_key = self.api_key_entry.get().strip()
        
        # Update scheduler threshold
        if self.gui.scheduler:
            self.gui.scheduler.min_score_for_notification = self.threshold_var.get()
        
        # Update .env file
        try:
            self.update_env_file()
            
            # Reload settings in main GUI
            self.gui.reload_settings()
            
            # Log in GUI
            self.gui.log_message("💾 Einstellungen gespeichert")
            self.gui.log_message(f"📱 Notifications: {'✅ Aktiviert' if self.notification_service.enabled else '❌ Deaktiviert'}")
            self.gui.log_message(f"🎯 Threshold: {old_threshold} → {self.threshold_var.get()}")
            
            messagebox.showinfo("Saved", f"Settings saved successfully!\nNotification threshold: {self.threshold_var.get()}")
            self.window.destroy()
            
        except Exception as e:
            self.gui.log_message(f"❌ Fehler beim Speichern: {e}")
            messagebox.showerror("Error", f"Failed to save settings: {e}")
    
    def update_env_file(self):
        """Aktualisiert die .env Datei"""
        import os
        
        # Lese aktuelle .env Datei
        env_lines = []
        if os.path.exists('.env'):
            with open('.env', 'r', encoding='utf-8') as f:
                env_lines = f.readlines()
        
        # Update/Add Einstellungen
        updated_lines = []
        settings_updated = {
            'ENABLE_MOBILE_NOTIFICATIONS': False,
            'NOTIFICATION_THRESHOLD': False,
            'PUSHBULLET_API_KEY': False
        }
        
        for line in env_lines:
            line = line.strip()
            if line.startswith('ENABLE_MOBILE_NOTIFICATIONS='):
                updated_lines.append(f"ENABLE_MOBILE_NOTIFICATIONS={'true' if self.enable_var.get() else 'false'}\n")
                settings_updated['ENABLE_MOBILE_NOTIFICATIONS'] = True
            elif line.startswith('NOTIFICATION_THRESHOLD='):
                updated_lines.append(f"NOTIFICATION_THRESHOLD={self.threshold_var.get()}\n")
                settings_updated['NOTIFICATION_THRESHOLD'] = True
            elif line.startswith('PUSHBULLET_API_KEY='):
                updated_lines.append(f"PUSHBULLET_API_KEY={self.api_key_entry.get().strip()}\n")
                settings_updated['PUSHBULLET_API_KEY'] = True
            else:
                updated_lines.append(line + '\n' if line else '\n')
        
        # Füge fehlende Einstellungen hinzu
        if not settings_updated['ENABLE_MOBILE_NOTIFICATIONS']:
            updated_lines.append(f"ENABLE_MOBILE_NOTIFICATIONS={'true' if self.enable_var.get() else 'false'}\n")
        if not settings_updated['NOTIFICATION_THRESHOLD']:
            updated_lines.append(f"NOTIFICATION_THRESHOLD={self.threshold_var.get()}\n")
        if not settings_updated['PUSHBULLET_API_KEY']:
            updated_lines.append(f"PUSHBULLET_API_KEY={self.api_key_entry.get().strip()}\n")
        
        # Schreibe .env Datei
        with open('.env', 'w', encoding='utf-8') as f:
            f.writelines(updated_lines)
        
        # Reload environment variables
        from dotenv import load_dotenv
        load_dotenv(override=True)
    
    def test_notification(self):
        """Testet die Notification"""
        # Temporäre Aktualisierung für Test
        old_enabled = self.notification_service.enabled
        old_threshold = self.notification_service.threshold
        old_api_key = self.notification_service.api_key
        
        self.notification_service.enabled = True
        self.notification_service.threshold = 0.0
        self.notification_service.api_key = self.api_key_entry.get().strip()
        
        # Test-Artikel
        test_article = NewsArticle(
            title="🧪 Test Notification from Automated GUI",
            description="This is a test notification from your automated News Analyzer GUI to verify Pushbullet setup.",
            link="https://example.com",
            published=str(datetime.now()),
            source="News Analyzer GUI",
            ai_score=10.0,
            ai_reasoning="Test notification to verify automated mobile setup"
        )
        
        success = self.notification_service.send_notification(test_article)
        
        # Restore alte Werte
        self.notification_service.enabled = old_enabled
        self.notification_service.threshold = old_threshold
        self.notification_service.api_key = old_api_key
        
        if success:
            self.gui.log_message("📱 Test-Notification erfolgreich gesendet")
            messagebox.showinfo("Success", "Test notification sent! Check your phone.")
        else:
            self.gui.log_message("❌ Test-Notification fehlgeschlagen")
            messagebox.showerror("Error", "Failed to send test notification. Check your API key.")


def main():
    """Startet die GUI-Anwendung mit integriertem Scheduler"""
    try:
        app = NewsAnalyzerGUI()
        app.run()
    except Exception as e:
        print(f"Error starting GUI: {e}")


if __name__ == "__main__":
    main()
