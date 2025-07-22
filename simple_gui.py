#!/usr/bin/env python3
"""
Einfache News Analyzer GUI mit Live-Updates
Vereinfachte Version für bessere Stabilität
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import time
from datetime import datetime
import sys
import os

# Importiere das Haupt-Analysesystem
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class SimpleNewsGUI:
    """Vereinfachte GUI mit Live-Updates"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🗞️ News Analyzer - Live Updates")
        self.root.geometry("1200x800")
        self.root.configure(bg='#f0f0f0')
        
        self.analyzer = None
        self.setup_gui()
        self.load_analyzer()
        
    def setup_gui(self):
        """Erstellt die GUI-Komponenten"""
        # Header
        header_frame = tk.Frame(self.root, bg='#2c3e50', height=80)
        header_frame.pack(fill='x')
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(
            header_frame,
            text="🗞️ News Analyzer - Live Progress",
            font=('Arial', 18, 'bold'),
            fg='white',
            bg='#2c3e50'
        )
        title_label.pack(pady=20)
        
        # Toolbar
        toolbar_frame = tk.Frame(self.root, bg='#34495e', height=50)
        toolbar_frame.pack(fill='x')
        toolbar_frame.pack_propagate(False)
        
        self.start_btn = tk.Button(
            toolbar_frame,
            text="🚀 Analyse starten",
            command=self.start_analysis,
            bg='#27ae60',
            fg='white',
            font=('Arial', 12, 'bold'),
            relief='flat',
            padx=20
        )
        self.start_btn.pack(pady=10)
        
        # Main Content
        content_frame = tk.Frame(self.root, bg='#f0f0f0')
        content_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Progress Section
        progress_frame = tk.LabelFrame(content_frame, text="📊 Live Progress", font=('Arial', 12, 'bold'))
        progress_frame.pack(fill='x', pady=(0, 10))
        
        self.progress_text = scrolledtext.ScrolledText(
            progress_frame,
            height=15,
            font=('Consolas', 10),
            bg='#1e1e1e',
            fg='#00ff00',
            wrap='word'
        )
        self.progress_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Results Section
        results_frame = tk.LabelFrame(content_frame, text="📰 Ergebnisse", font=('Arial', 12, 'bold'))
        results_frame.pack(fill='both', expand=True)
        
        # Treeview for results
        columns = ('Rang', 'Score', 'Titel', 'Quelle')
        self.results_tree = ttk.Treeview(results_frame, columns=columns, show='headings', height=10)
        
        # Configure columns
        self.results_tree.heading('Rang', text='Rang')
        self.results_tree.heading('Score', text='Score')
        self.results_tree.heading('Titel', text='Titel')
        self.results_tree.heading('Quelle', text='Quelle')
        
        self.results_tree.column('Rang', width=50)
        self.results_tree.column('Score', width=80)
        self.results_tree.column('Titel', width=600)
        self.results_tree.column('Quelle', width=200)
        
        # Scrollbar for treeview
        scrollbar = ttk.Scrollbar(results_frame, orient='vertical', command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=scrollbar.set)
        
        self.results_tree.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        scrollbar.pack(side='right', fill='y')
        
    def log_progress(self, message):
        """Fügt eine Nachricht zum Progress-Log hinzu"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        def update_log():
            self.progress_text.insert(tk.END, log_entry)
            self.progress_text.see(tk.END)
            
        self.root.after(0, update_log)
        
    def load_analyzer(self):
        """Lädt das Analyzer-Modul"""
        try:
            # Import des NewsAnalyzer direkt aus der P-News.py Datei
            import importlib.util
            spec = importlib.util.spec_from_file_location("P_News", "P-News.py")
            p_news_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(p_news_module)
            
            self.analyzer = p_news_module.NewsAnalyzer()
            self.log_progress("✅ News Analyzer geladen")
        except Exception as e:
            self.log_progress(f"❌ Fehler beim Laden: {e}")
            messagebox.showerror("Error", f"Analyzer konnte nicht geladen werden: {e}")
    
    def start_analysis(self):
        """Startet die Nachrichtenanalyse"""
        if not self.analyzer:
            messagebox.showerror("Error", "Analyzer nicht geladen!")
            return
            
        # Button deaktivieren
        self.start_btn.config(state='disabled', text='🔄 Analysiert...')
        
        # Clear previous results
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
            
        # Progress Log leeren
        self.progress_text.delete(1.0, tk.END)
        
        # Analyse in separatem Thread starten
        analysis_thread = threading.Thread(target=self.run_analysis_with_updates, daemon=True)
        analysis_thread.start()
        
    def run_analysis_with_updates(self):
        """Führt die Analyse mit Live-Updates durch"""
        try:
            start_time = time.time()
            self.log_progress("🚀 Starte News-Analyse...")
            
            # Phase 1: RSS Feeds laden
            self.log_progress("📡 Lade RSS-Feeds...")
            articles = self.analyzer.fetch_rss_articles()
            self.log_progress(f"✅ {len(articles)} Artikel geladen")
            
            if not articles:
                self.log_progress("❌ Keine Artikel gefunden!")
                return
                
            # Phase 2: Titel-Analyse
            self.log_progress(f"📊 Phase 1: Schnelle Titel-Analyse von {len(articles)} Artikeln...")
            title_scored_articles = self.analyzer._quick_title_analysis(articles)
            
            # Sortiere und wähle Top-Artikel
            title_scored_articles.sort(key=lambda x: x.score, reverse=True)
            top_articles = title_scored_articles[:10]
            remaining_articles = title_scored_articles[10:]
            
            self.log_progress(f"🎯 Phase 2: Vollanalyse der Top {len(top_articles)} Artikel...")
            
            # Phase 3: AI-Analyse mit Live-Updates
            if self.analyzer.ai_model_type == 'ollama':
                analyzed_top = self.analyze_with_ollama_updates(top_articles)
            else:
                # Fallback für andere AI-Typen
                analyzed_top = top_articles
                for article in analyzed_top:
                    article.ai_score = article.score
                    article.ai_reasoning = "Fallback-Bewertung"
            
            # Phase 4: Alle Artikel kombinieren
            for article in remaining_articles:
                article.ai_score = article.score
                article.ai_reasoning = "Nur Titel-Analyse (nicht in Top 10)"
            
            all_articles = analyzed_top + remaining_articles
            all_articles.sort(key=lambda x: x.ai_score, reverse=True)
            
            # Ergebnisse anzeigen
            self.root.after(0, lambda: self.display_results(all_articles))
            
            # Timing
            end_time = time.time()
            duration = end_time - start_time
            self.log_progress(f"⏱️ Analyse abgeschlossen in {duration:.1f} Sekunden")
            
        except Exception as e:
            self.log_progress(f"❌ Analyse-Fehler: {e}")
        finally:
            # Button wieder aktivieren
            self.root.after(0, lambda: self.start_btn.config(state='normal', text='🚀 Analyse starten'))
    
    def analyze_with_ollama_updates(self, articles):
        """Ollama-Analyse mit Live-Updates"""
        import requests
        
        self.log_progress("🤖 Analysiere Artikel mit Ollama (llama2)...")
        
        for i, article in enumerate(articles, 1):
            short_title = article.title[:60] + "..." if len(article.title) > 60 else article.title
            self.log_progress(f"Analysiere Artikel {i}/{len(articles)}: {short_title}")
            
            try:
                prompt = self.analyzer._create_analysis_prompt(article)
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
                    
                    # Parse das Ergebnis
                    import re
                    score_match = re.search(r'Score:\s*(\d+(?:\.\d+)?)', analysis_text)
                    score = float(score_match.group(1)) if score_match else 5.0
                    
                    reasoning_match = re.search(r'Begründung:\s*(.+)', analysis_text, re.DOTALL)
                    reasoning = reasoning_match.group(1).strip() if reasoning_match else analysis_text[:200]
                    
                    article.ai_score = min(10.0, max(0.0, score))
                    article.ai_reasoning = reasoning
                    
                    self.log_progress(f"✅ Score: {article.ai_score:.1f}/10")
                    
                else:
                    article.ai_score = article.score
                    article.ai_reasoning = f"API-Fehler: {response.status_code}"
                    self.log_progress(f"⚠️ API-Fehler: {response.status_code}")
                    
            except Exception as e:
                article.ai_score = article.score
                article.ai_reasoning = f"Analyse-Fehler: {str(e)[:100]}"
                self.log_progress(f"❌ Fehler: {str(e)[:50]}")
        
        return articles
    
    def display_results(self, articles):
        """Zeigt die Ergebnisse in der Tabelle an"""
        # Clear previous results
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
            
        # Add new results
        for i, article in enumerate(articles[:20], 1):  # Top 20
            score_str = f"{article.ai_score:.1f}/10"
            title = article.title[:80] + "..." if len(article.title) > 80 else article.title
            source = article.source[:25] + "..." if len(article.source) > 25 else article.source
            
            # Color coding based on score
            tags = []
            if article.ai_score >= 9:
                tags = ['high_priority']
            elif article.ai_score >= 7:
                tags = ['medium_priority']
            else:
                tags = ['low_priority']
                
            self.results_tree.insert('', 'end', values=(i, score_str, title, source), tags=tags)
        
        # Configure tag colors
        self.results_tree.tag_configure('high_priority', background='#ffebee')
        self.results_tree.tag_configure('medium_priority', background='#fff3e0')
        self.results_tree.tag_configure('low_priority', background='#f1f8e9')
        
        self.log_progress(f"📊 {len(articles)} Artikel in Tabelle angezeigt")
    
    def run(self):
        """Startet die GUI"""
        self.log_progress("🚀 News Analyzer GUI gestartet")
        self.log_progress("💡 Klicke auf 'Analyse starten' um zu beginnen")
        self.root.mainloop()


def main():
    """Startet die vereinfachte GUI"""
    try:
        app = SimpleNewsGUI()
        app.run()
    except Exception as e:
        print(f"Error starting GUI: {e}")


if __name__ == "__main__":
    main()
