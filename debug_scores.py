#!/usr/bin/env python3
"""
Debug Script - Zeigt alle AI-Scores ohne Filter
"""

from dotenv import load_dotenv
import sys
import importlib.util

# Load environment variables
load_dotenv()

def show_all_scores():
    """Zeigt alle Artikel mit ihren AI-Scores"""
    try:
        # Load analyzer
        spec = importlib.util.spec_from_file_location("news_module", "P-News.py")
        news_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(news_module)
        
        analyzer = news_module.NewsAnalyzer()
        
        print("🔍 Lade aktuelle Artikel...")
        articles = analyzer.fetch_rss_articles()
        print(f"📰 Gefunden: {len(articles)} Artikel")
        print()
        
        print("🤖 Analysiere mit AI...")
        analyzed_articles = analyzer.analyze_articles_with_ai(articles)
        
        print("\n" + "="*80)
        print("📊 ALLE AI-SCORES (unsortiert):")
        print("="*80)
        
        # Gruppiere nach Score-Bereichen
        score_groups = {
            "🔴 BREAKING (9.0+)": [],
            "🟡 SEHR WICHTIG (8.0-8.9)": [],
            "🟢 WICHTIG (7.0-7.9)": [],
            "🔵 RELEVANT (6.0-6.9)": [],
            "⚪ NORMAL (5.0-5.9)": [],
            "⚫ UNWICHTIG (<5.0)": []
        }
        
        for article in analyzed_articles:
            score = article.ai_score or 0.0
            title = article.title[:60] + "..." if len(article.title) > 60 else article.title
            entry = f"{score:.1f} | {article.source} | {title}"
            
            if score >= 9.0:
                score_groups["🔴 BREAKING (9.0+)"].append(entry)
            elif score >= 8.0:
                score_groups["🟡 SEHR WICHTIG (8.0-8.9)"].append(entry)
            elif score >= 7.0:
                score_groups["🟢 WICHTIG (7.0-7.9)"].append(entry)
            elif score >= 6.0:
                score_groups["🔵 RELEVANT (6.0-6.9)"].append(entry)
            elif score >= 5.0:
                score_groups["⚪ NORMAL (5.0-5.9)"].append(entry)
            else:
                score_groups["⚫ UNWICHTIG (<5.0)"].append(entry)
        
        # Zeige Statistiken
        total = len(analyzed_articles)
        print(f"\n📈 SCORE-VERTEILUNG ({total} Artikel):")
        print("-" * 50)
        
        for category, articles in score_groups.items():
            count = len(articles)
            percentage = (count / total * 100) if total > 0 else 0
            print(f"{category}: {count} ({percentage:.1f}%)")
        
        print("\n" + "="*80)
        
        # Zeige Details pro Kategorie
        for category, articles in score_groups.items():
            if articles:
                print(f"\n{category}:")
                print("-" * 60)
                for article in articles:
                    print(f"  {article}")
        
        print("\n" + "="*80)
        print("💡 WARUM MEIST 7.0-8.0 SCORES?")
        print("="*80)
        print("• AI bewertet konservativ - extreme Scores sind selten")
        print("• Echte Breaking News (9.0+) passieren nicht täglich")
        print("• GUI zeigt nur ≥7.0 - das sind bereits die wichtigsten 20-30%")
        print("• 7.0-8.0 = 'sehr relevante News' - das ist normal!")
        print("• 9.0+ = 'Weltbewegende Ereignisse' - sehr selten!")
        
    except Exception as e:
        print(f"❌ Fehler: {e}")

if __name__ == "__main__":
    show_all_scores()
