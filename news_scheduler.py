#!/usr/bin/env python3
"""
Automatischer News Scheduler - Mehrmals tägliche Ausführung mit Mobile Notifications
Speziell für Politics, Business, Science/AI, Law & Justice
"""

import schedule
import time
import threading
import logging
from datetime import datetime, timedelta
import sys
import os
from typing import List
import importlib.util
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('news_scheduler.log'),
        logging.StreamHandler()
    ]
)

class NewsScheduler:
    """Automatischer Scheduler für News-Analyse mit mehrfachen täglichen Läufen"""
    
    def __init__(self):
        self.analyzer = None
        self.notification_service = None
        self.is_running = False
        self.last_articles = []
        
        # Load configurations
        self.schedule_times = [
            "06:00",  # Morgendliche News
            "09:00",  # Business Opening
            "12:00",  # Mittagsupdate
            "15:00",  # Nachmittagsupdate
            "18:00",  # Abendnews
            "21:00"   # Späte Breaking News
        ]
        
        self.emergency_threshold = 9.5  # Sofortige Notification
        self.min_score_for_notification = float(os.getenv('NOTIFICATION_THRESHOLD', '7.5'))
        
        self.setup_components()
        self.setup_schedule()
    
    def setup_components(self):
        """Lädt News Analyzer und Notification Service"""
        try:
            # Load main analyzer
            spec = importlib.util.spec_from_file_location("news_module", "P-News.py")
            news_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(news_module)
            
            self.analyzer = news_module.NewsAnalyzer()
            logging.info("✅ News Analyzer loaded successfully")
            
            # Load notification service
            spec = importlib.util.spec_from_file_location("gui_module", "news_gui.py")
            gui_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(gui_module)
            
            self.notification_service = gui_module.MobileNotificationService()
            logging.info("✅ Mobile Notification Service loaded successfully")
            
            # Check if notifications are properly configured
            if self.notification_service.enabled and self.notification_service.api_key:
                logging.info("📱 Pushbullet notifications: ENABLED")
            else:
                logging.warning("📱 Pushbullet notifications: DISABLED (check .env file)")
            
        except Exception as e:
            logging.error(f"❌ Failed to load components: {e}")
            raise
    
    def setup_schedule(self):
        """Konfiguriert den Zeitplan"""
        # Reguläre Analysen
        for time_str in self.schedule_times:
            schedule.every().day.at(time_str).do(self.run_scheduled_analysis)
            logging.info(f"📅 Scheduled analysis for {time_str}")
        
        # Breaking News Check alle 30 Minuten
        schedule.every(30).minutes.do(self.run_emergency_check)
        logging.info("🚨 Emergency check every 30 minutes")
        
        # Täglicher Status Report
        schedule.every().day.at("08:00").do(self.send_daily_summary)
        logging.info("📊 Daily summary at 08:00")
    
    def run_scheduled_analysis(self):
        """Führt geplante Analyse durch"""
        logging.info("🔄 Starting scheduled news analysis...")
        
        try:
            # Fetch and analyze articles
            articles = self.analyzer.fetch_rss_articles()
            analyzed_articles = self.analyzer.analyze_articles_with_ai(articles)
            sorted_articles = self.analyzer.sort_articles_by_importance(analyzed_articles)
            
            # Filter new important articles
            new_important_articles = self.get_new_important_articles(sorted_articles)
            
            if new_important_articles:
                logging.info(f"📱 Found {len(new_important_articles)} new important articles")
                self.send_notifications(new_important_articles)
                self.update_article_cache(sorted_articles)
            else:
                logging.info("ℹ️ No new important articles found")
            
            # Log summary
            high_priority = len([a for a in sorted_articles if a.ai_score >= 8.0])
            medium_priority = len([a for a in sorted_articles if 7.0 <= a.ai_score < 8.0])
            
            logging.info(f"📊 Analysis complete: {high_priority} high priority, {medium_priority} medium priority")
            
        except Exception as e:
            logging.error(f"❌ Error in scheduled analysis: {e}")
    
    def run_emergency_check(self):
        """Prüft auf Breaking News mit extrem hohem Score"""
        logging.info("🚨 Running emergency breaking news check...")
        
        try:
            articles = self.analyzer.fetch_rss_articles()
            
            # Quick scan for emergency articles
            emergency_articles = []
            for article in articles[:10]:  # Check only newest articles
                if hasattr(article, 'ai_score') and article.ai_score >= self.emergency_threshold:
                    emergency_articles.append(article)
            
            if emergency_articles:
                logging.warning(f"🚨 EMERGENCY: {len(emergency_articles)} breaking news articles!")
                self.send_emergency_notifications(emergency_articles)
            
        except Exception as e:
            logging.error(f"❌ Error in emergency check: {e}")
    
    def get_new_important_articles(self, articles):
        """Filtert neue wichtige Artikel"""
        new_articles = []
        
        for article in articles:
            if article.ai_score >= self.min_score_for_notification:
                # Check if we've seen this article before
                is_new = True
                for old_article in self.last_articles:
                    if (article.title == old_article.title or 
                        article.link == old_article.link):
                        is_new = False
                        break
                
                if is_new:
                    new_articles.append(article)
        
        return new_articles
    
    def update_article_cache(self, articles):
        """Aktualisiert den Artikel-Cache"""
        # Keep only articles from last 24 hours
        cutoff_time = datetime.now() - timedelta(hours=24)
        self.last_articles = [a for a in articles if a.ai_score >= 7.0]
        
        # Limit cache size
        if len(self.last_articles) > 100:
            self.last_articles = self.last_articles[:100]
    
    def send_notifications(self, articles):
        """Sendet Benachrichtigungen für wichtige Artikel"""
        for article in articles:
            if self.notification_service:
                # Convert to NewsArticle format for GUI compatibility
                from news_gui import NewsArticle
                
                news_article = NewsArticle(
                    title=article.title,
                    description=article.description,
                    link=article.link,
                    published=article.published,
                    source=article.source,
                    ai_score=article.ai_score or 0.0,
                    ai_reasoning=article.ai_reasoning or "No analysis available"
                )
                
                success = self.notification_service.send_notification(news_article)
                if success:
                    logging.info(f"📱 Notification sent: {article.title[:50]}... (Score: {article.ai_score})")
                else:
                    logging.warning(f"⚠️ Failed to send notification: {article.title[:50]}...")
    
    def send_emergency_notifications(self, articles):
        """Sendet Eilmeldungs-Benachrichtigungen"""
        for article in articles:
            logging.warning(f"🚨 BREAKING: {article.title} (Score: {article.ai_score})")
            # Emergency notifications bypass normal threshold
            if self.notification_service:
                from news_gui import NewsArticle
                
                news_article = NewsArticle(
                    title=f"🚨 BREAKING: {article.title}",
                    description=article.description,
                    link=article.link,
                    published=article.published,
                    source=article.source,
                    ai_score=article.ai_score or 0.0,
                    ai_reasoning=article.ai_reasoning or "Emergency breaking news"
                )
                
                self.notification_service.send_notification(news_article)
    
    def send_daily_summary(self):
        """Sendet tägliche Zusammenfassung"""
        try:
            # Get yesterday's top articles
            articles = self.analyzer.fetch_rss_articles()
            analyzed_articles = self.analyzer.analyze_articles_with_ai(articles)
            top_articles = [a for a in analyzed_articles if a.ai_score >= 8.0][:5]
            
            if top_articles:
                summary_text = f"📊 Daily News Summary ({datetime.now().strftime('%d.%m.%Y')})\n\n"
                summary_text += f"🔥 Top {len(top_articles)} stories:\n\n"
                
                for i, article in enumerate(top_articles, 1):
                    summary_text += f"{i}. {article.title} (Score: {article.ai_score:.1f})\n"
                    summary_text += f"   Source: {article.source}\n\n"
                
                # Send as special summary notification
                if self.notification_service:
                    from news_gui import NewsArticle
                    
                    summary_article = NewsArticle(
                        title="📊 Daily News Summary",
                        description=summary_text,
                        link="",
                        published=str(datetime.now()),
                        source="News Analyzer",
                        ai_score=8.0,
                        ai_reasoning="Daily summary of top news stories"
                    )
                    
                    self.notification_service.send_notification(summary_article)
                    logging.info("📊 Daily summary sent")
            
        except Exception as e:
            logging.error(f"❌ Error sending daily summary: {e}")
    
    def start(self):
        """Startet den Scheduler"""
        self.is_running = True
        logging.info("🚀 News Scheduler started")
        logging.info(f"📱 Notifications enabled: {self.notification_service.enabled if self.notification_service else False}")
        logging.info(f"🎯 Notification threshold: {self.min_score_for_notification}")
        logging.info(f"⏰ Scheduled times: {', '.join(self.schedule_times)}")
        
        # Initial analysis
        logging.info("🔄 Running initial analysis...")
        self.run_scheduled_analysis()
        
        # Start scheduler loop
        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except KeyboardInterrupt:
                logging.info("👋 Scheduler stopped by user")
                self.is_running = False
            except Exception as e:
                logging.error(f"❌ Error in scheduler loop: {e}")
                time.sleep(60)  # Continue after error
    
    def stop(self):
        """Stoppt den Scheduler"""
        self.is_running = False
        logging.info("⏹️ Scheduler stopped")


class SchedulerManager:
    """Manager für den News Scheduler mit verschiedenen Modi"""
    
    def __init__(self):
        self.scheduler = None
    
    def start_interactive(self):
        """Startet im interaktiven Modus"""
        print("\n" + "="*50)
        print("🗞️  PREMIUM NEWS ANALYZER - SCHEDULER")
        print("="*50)
        print()
        print("Automatische News-Analyse mit Mobile Notifications")
        print("Mehrmals täglich: 06:00, 09:00, 12:00, 15:00, 18:00, 21:00")
        print("Breaking News Check: Alle 30 Minuten")
        print()
        
        # Check configuration
        notifications_enabled = os.getenv('ENABLE_MOBILE_NOTIFICATIONS', 'false').lower() == 'true'
        pushbullet_key = os.getenv('PUSHBULLET_API_KEY', '')
        threshold = os.getenv('NOTIFICATION_THRESHOLD', '7.5')
        
        print(f"📱 Mobile Notifications: {'✅ Enabled' if notifications_enabled and pushbullet_key else '❌ Disabled'}")
        print(f"🎯 Notification Threshold: {threshold}")
        print()
        
        if not notifications_enabled or not pushbullet_key:
            print("⚠️  Warning: Mobile notifications are not properly configured!")
            print("   Check your .env file:")
            print("   - ENABLE_MOBILE_NOTIFICATIONS=true")
            print("   - PUSHBULLET_API_KEY=your_api_key_here")
            print()
        
        response = input("Start scheduler? (y/N): ").strip().lower()
        if response in ['y', 'yes', 'j', 'ja']:
            self.start_scheduler()
        else:
            print("👋 Cancelled by user")
    
    def start_scheduler(self):
        """Startet den Scheduler"""
        try:
            self.scheduler = NewsScheduler()
            
            print("\n🚀 Starting News Scheduler...")
            print("Press Ctrl+C to stop")
            print("-" * 50)
            
            # Start in separate thread to allow graceful shutdown
            scheduler_thread = threading.Thread(target=self.scheduler.start)
            scheduler_thread.daemon = True
            scheduler_thread.start()
            
            # Keep main thread alive
            try:
                while scheduler_thread.is_alive():
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n👋 Stopping scheduler...")
                self.scheduler.stop()
                
        except Exception as e:
            print(f"❌ Error starting scheduler: {e}")
    
    def start_background(self):
        """Startet als Background Service"""
        logging.info("🚀 Starting News Scheduler in background mode...")
        
        try:
            self.scheduler = NewsScheduler()
            self.scheduler.start()
        except Exception as e:
            logging.error(f"❌ Error in background mode: {e}")


def main():
    """Hauptfunktion"""
    manager = SchedulerManager()
    
    # Check if running as background service
    if len(sys.argv) > 1 and sys.argv[1] == '--background':
        manager.start_background()
    else:
        manager.start_interactive()


if __name__ == "__main__":
    main()
