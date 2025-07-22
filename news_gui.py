#!/usr/bin/env python3
"""
Premium News Analyzer mit GUI und Mobile Notifications
Speziell konfiguriert für Politik, Wirtschaft, KI, Wissenschaft und Recht
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

# Load environment variables
load_dotenv()

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
            title = f"� Breaking News (Score: {article.ai_score}/10)"
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


class NewsAnalyzerGUI:
    """Hauptfenster der GUI-Anwendung"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🗞️ Premium News Analyzer - International Edition")
        self.root.geometry("1400x900")
        self.root.configure(bg='#f0f0f0')
        
        # Services
        self.notification_service = MobileNotificationService()
        self.analyzer = None
        self.articles = []
        self.auto_refresh = os.getenv('ENABLE_GUI', 'true').lower() == 'true'
        self.refresh_interval = int(os.getenv('AUTO_REFRESH_MINUTES', '120')) * 60
        
        self.setup_gui()
        self.load_analyzer()
        
        # Auto-refresh Timer
        if self.auto_refresh:
            self.schedule_refresh()
    
    def setup_gui(self):
        """Erstellt die GUI-Komponenten"""
        # Header
        header_frame = tk.Frame(self.root, bg='#2c3e50', height=80)
        header_frame.pack(fill='x', padx=0, pady=0)
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(
            header_frame,
            text="🗞️ Premium News Analyzer",
            font=('Arial', 24, 'bold'),
            fg='white',
            bg='#2c3e50'
        )
        title_label.pack(pady=20)
        
        # Toolbar
        toolbar_frame = tk.Frame(self.root, bg='#34495e', height=50)
        toolbar_frame.pack(fill='x')
        toolbar_frame.pack_propagate(False)
        
        # Buttons
        self.refresh_btn = tk.Button(
            toolbar_frame,
            text="🔄 Refresh Now",
            command=self.manual_refresh,
            bg='#3498db',
            fg='white',
            font=('Arial', 12, 'bold'),
            relief='flat',
            padx=20
        )
        self.refresh_btn.pack(side='left', padx=10, pady=10)
        
        self.settings_btn = tk.Button(
            toolbar_frame,
            text="⚙️ Settings",
            command=self.open_settings,
            bg='#95a5a6',
            fg='white',
            font=('Arial', 12, 'bold'),
            relief='flat',
            padx=20
        )
        self.settings_btn.pack(side='left', padx=5, pady=10)
        
        # Status Label
        self.status_label = tk.Label(
            toolbar_frame,
            text="Ready for analysis...",
            fg='white',
            bg='#34495e',
            font=('Arial', 10)
        )
        self.status_label.pack(side='right', padx=10, pady=15)
        
        # Main Content Area
        main_frame = tk.Frame(self.root, bg='#f0f0f0')
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Left Panel - Article List
        left_frame = tk.Frame(main_frame, bg='white', relief='solid', bd=1)
        left_frame.pack(side='left', fill='both', expand=True, padx=(0, 5))
        
        # Article List Header
        list_header = tk.Frame(left_frame, bg='#ecf0f1', height=40)
        list_header.pack(fill='x')
        list_header.pack_propagate(False)
        
        tk.Label(
            list_header,
            text="📊 Top Breaking News (Score ≥ 7.0)",
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
        
        # Right Panel - Article Details
        right_frame = tk.Frame(main_frame, bg='white', relief='solid', bd=1)
        right_frame.pack(side='right', fill='both', expand=True, padx=(5, 0))
        
        # Details Header
        details_header = tk.Frame(right_frame, bg='#ecf0f1', height=40)
        details_header.pack(fill='x')
        details_header.pack_propagate(False)
        
        tk.Label(
            details_header,
            text="📋 Article Details",
            font=('Arial', 14, 'bold'),
            bg='#ecf0f1'
        ).pack(pady=10)
        
        # Details Content
        details_content = tk.Frame(right_frame)
        details_content.pack(fill='both', expand=True, padx=15, pady=15)
        
        # Title
        self.title_label = tk.Label(
            details_content,
            text="Select an article to view details",
            font=('Arial', 16, 'bold'),
            wraplength=500,
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
            height=8,
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
    
    def load_analyzer(self):
        """Lädt das Analyse-System"""
        try:
            # Importiere das Hauptsystem dynamisch
            spec = importlib.util.spec_from_file_location("news_module", "P-News.py")
            news_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(news_module)
            
            self.analyzer = news_module.NewsAnalyzer()
            self.status_label.config(text="Analyzer loaded successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load analyzer: {e}")
    
    def manual_refresh(self):
        """Manueller Refresh-Button"""
        self.refresh_btn.config(state='disabled', text="🔄 Loading...")
        self.status_label.config(text="Analyzing latest news...")
        
        # Führe Analyse in separatem Thread aus
        thread = threading.Thread(target=self.run_analysis)
        thread.daemon = True
        thread.start()
    
    def run_analysis(self):
        """Führt die Nachrichtenanalyse aus"""
        try:
            if not self.analyzer:
                self.load_analyzer()
            
            # Lade und analysiere Artikel
            articles = self.analyzer.fetch_rss_articles()
            analyzed_articles = self.analyzer.analyze_articles_with_ai(articles)
            sorted_articles = self.analyzer.sort_articles_by_importance(analyzed_articles)
            
            # Konvertiere zu unserer Datenstruktur
            self.articles = []
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
                self.articles.append(news_article)
            
            # Update GUI im Hauptthread
            self.root.after(0, self.update_gui)
            
            # Sende Notifications für hochpriorisierte Artikel
            self.send_high_priority_notifications()
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Analysis Error", str(e)))
        finally:
            self.root.after(0, self.reset_refresh_button)
    
    def update_gui(self):
        """Aktualisiert die GUI mit neuen Artikeln"""
        # Lösche alte Einträge
        self.article_listbox.delete(0, tk.END)
        
        # Zeige nur Artikel mit Score >= 7.0
        high_priority_articles = [a for a in self.articles if a.ai_score >= 7.0]
        
        for i, article in enumerate(high_priority_articles):
            # Formatiere Listeneintrag
            score_color = "🔴" if article.ai_score >= 9 else "🟡" if article.ai_score >= 8 else "🟢"
            entry_text = f"{score_color} {article.ai_score:.1f} | {article.title[:60]}..."
            
            self.article_listbox.insert(tk.END, entry_text)
            
            # Färbe basierend auf Score
            if article.ai_score >= 9:
                self.article_listbox.itemconfig(i, {'bg': '#ffebee', 'fg': '#c62828'})
            elif article.ai_score >= 8:
                self.article_listbox.itemconfig(i, {'bg': '#fff3e0', 'fg': '#ef6c00'})
            else:
                self.article_listbox.itemconfig(i, {'bg': '#e8f5e8', 'fg': '#2e7d32'})
        
        # Status Update
        total_articles = len(self.articles)
        high_priority_count = len(high_priority_articles)
        self.status_label.config(
            text=f"Last updated: {datetime.now().strftime('%H:%M')} | "
                 f"{high_priority_count}/{total_articles} priority articles"
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
        """Zeigt Artikeldetails an"""
        # Titel
        self.title_label.config(text=article.title)
        
        # Score (mit Farbe)
        score_color = "#c62828" if article.ai_score >= 9 else "#ef6c00" if article.ai_score >= 8 else "#2e7d32"
        self.score_label.config(text=f"🎯 Score: {article.ai_score:.1f}/10", fg=score_color)
        
        # Quelle
        self.source_label.config(text=f"📰 {article.source}")
        
        # Beschreibung
        self.description_text.delete(1.0, tk.END)
        self.description_text.insert(tk.END, article.description)
        
        # AI Reasoning
        self.reasoning_text.delete(1.0, tk.END)
        self.reasoning_text.insert(tk.END, article.ai_reasoning)
        
        # Speichere aktuellen Artikel für Actions
        self.current_article = article
    
    def open_article(self):
        """Öffnet Artikel im Browser"""
        if hasattr(self, 'current_article') and self.current_article:
            webbrowser.open(self.current_article.link)
    
    def send_notification(self):
        """Sendet manuelle Notification"""
        if hasattr(self, 'current_article') and self.current_article:
            success = self.notification_service.send_notification(self.current_article)
            if success:
                messagebox.showinfo("Success", "Notification sent to your phone!")
            else:
                messagebox.showwarning("Warning", "Failed to send notification. Check your Pushover settings.")
    
    def send_high_priority_notifications(self):
        """Sendet automatische Notifications für hochpriorisierte Artikel"""
        for article in self.articles:
            if article.ai_score >= self.notification_service.threshold and not article.notification_sent:
                if self.notification_service.send_notification(article):
                    article.notification_sent = True
    
    def schedule_refresh(self):
        """Plant nächsten automatischen Refresh"""
        self.root.after(self.refresh_interval * 1000, self.auto_refresh_handler)
    
    def auto_refresh_handler(self):
        """Handler für automatischen Refresh"""
        if self.auto_refresh:
            self.manual_refresh()
            self.schedule_refresh()
    
    def reset_refresh_button(self):
        """Setzt Refresh-Button zurück"""
        self.refresh_btn.config(state='normal', text="🔄 Refresh Now")
    
    def open_settings(self):
        """Öffnet Einstellungsfenster"""
        settings_window = SettingsWindow(self.root, self.notification_service)
    
    def run(self):
        """Startet die GUI-Anwendung"""
        # Initial load
        self.manual_refresh()
        
        # Start main loop
        self.root.mainloop()


class SettingsWindow:
    """Einstellungsfenster für Notifications"""
    
    def __init__(self, parent, notification_service):
        self.parent = parent
        self.notification_service = notification_service
        
        self.window = tk.Toplevel(parent)
        self.window.title("⚙️ Settings")
        self.window.geometry("500x400")
        self.window.configure(bg='#f0f0f0')
        
        self.setup_settings_gui()
    
    def setup_settings_gui(self):
        """Erstellt das Einstellungs-Interface"""
        # Header
        header = tk.Label(
            self.window,
            text="📱 Mobile Notification Settings",
            font=('Arial', 16, 'bold'),
            bg='#f0f0f0'
        )
        header.pack(pady=20)
        
        # Main Frame
        main_frame = tk.Frame(self.window, bg='white', relief='solid', bd=1)
        main_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        
        content_frame = tk.Frame(main_frame, bg='white')
        content_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Enable Notifications
        tk.Label(
            content_frame,
            text="Enable Mobile Notifications:",
            font=('Arial', 12, 'bold'),
            bg='white'
        ).pack(anchor='w', pady=(0, 5))
        
        self.enable_var = tk.BooleanVar(value=self.notification_service.enabled)
        enable_check = tk.Checkbutton(
            content_frame,
            text="Send notifications to mobile device",
            variable=self.enable_var,
            bg='white',
            font=('Arial', 11)
        )
        enable_check.pack(anchor='w', pady=(0, 15))
        
        # Threshold
        tk.Label(
            content_frame,
            text="Notification Threshold (Score):",
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
            text="Only articles with score above this threshold will trigger notifications",
            font=('Arial', 9),
            fg='#7f8c8d',
            bg='white'
        ).pack(anchor='w', pady=(0, 15))
        
        # Pushbullet Settings
        tk.Label(
            content_frame,
            text="Pushbullet Configuration:",
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
            "To enable mobile notifications:\n"
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
        self.notification_service.enabled = self.enable_var.get()
        self.notification_service.threshold = self.threshold_var.get()
        self.notification_service.api_key = self.api_key_entry.get().strip()
        
        # Save to .env file (vereinfacht)
        messagebox.showinfo("Saved", "Settings saved successfully!")
        self.window.destroy()
    
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
            title="🧪 Test Notification from News Analyzer",
            description="This is a test notification from your News Analyzer to verify Pushbullet setup.",
            link="https://example.com",
            published=str(datetime.now()),
            source="News Analyzer",
            ai_score=10.0,
            ai_reasoning="Test notification to verify mobile setup"
        )
        
        success = self.notification_service.send_notification(test_article)
        
        # Restore alte Werte
        self.notification_service.enabled = old_enabled
        self.notification_service.threshold = old_threshold
        self.notification_service.api_key = old_api_key
        
        if success:
            messagebox.showinfo("Success", "Test notification sent! Check your phone.")
        else:
            messagebox.showerror("Error", "Failed to send test notification. Check your API key.")


def main():
    """Startet die GUI-Anwendung"""
    try:
        app = NewsAnalyzerGUI()
        app.run()
    except Exception as e:
        print(f"Error starting GUI: {e}")


if __name__ == "__main__":
    main()
