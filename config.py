"""
Konfigurationsdatei für den News-Analyzer
Hier können Sie verschiedene RSS-Feeds und Einstellungen anpassen.
"""

# Standard RSS-Feeds (Sie können weitere hinzufügen)
DEFAULT_RSS_FEEDS = [
    # Deutsche Nachrichtenquellen
    "https://www.tagesschau.de/xml/rss2/",
    "https://www.spiegel.de/schlagzeilen/index.rss",
    "https://rss.zeit.de/politik/index",
    
    # Internationale Quellen
    "https://feeds.reuters.com/Reuters/PoliticsNews",
    "https://feeds.bbci.co.uk/news/world/rss.xml",
    "https://rss.cnn.com/rss/edition.rss",
    
    # Wirtschaftsnachrichten
    "https://feeds.reuters.com/reuters/businessNews",
    "https://www.handelsblatt.com/contentexport/feed/schlagzeilen",
]

# Bewertungskriterien für die KI
AI_EVALUATION_CRITERIA = """
Bewerte jeden Artikel nach folgenden Kriterien (Skala 1-10):

Politische Relevanz:
- 1-2: Lokale Ereignisse ohne überregionale Bedeutung
- 3-4: Regionale Politik, kleinere Änderungen
- 5-6: Nationale Politik, mittlere Bedeutung
- 7-8: Internationale Politik, große Auswirkungen
- 9-10: Historische Ereignisse, weltweite Bedeutung

Gesellschaftliche Auswirkungen:
- Wie viele Menschen sind betroffen?
- Welche langfristigen Folgen sind zu erwarten?
- Ist dies ein Wendepunkt oder Routine?

Aktualität und Dringlichkeit:
- Wie zeitkritisch ist die Information?
- Entwickelt sich die Situation noch?
"""

# OpenAI Modell-Optionen
OPENAI_MODELS = {
    "gpt-3.5-turbo": "Schnell und kostengünstig",
    "gpt-4": "Höhere Qualität, langsamer",
    "gpt-4-turbo": "Guter Kompromiss zwischen Geschwindigkeit und Qualität"
}

# Ollama lokale Modelle
OLLAMA_MODELS = {
    "llama2": "Standard LLaMA 2 Modell",
    "llama2:13b": "Größeres LLaMA 2 Modell (bessere Qualität)",
    "mistral": "Mistral 7B Modell",
    "neural-chat": "Intel Neural Chat Modell"
}

# Standard-Einstellungen
DEFAULT_SETTINGS = {
    "max_articles": 20,
    "ai_model_type": "openai",  # "openai" oder "ollama"
    "openai_model": "gpt-3.5-turbo",
    "ollama_model": "llama2",
    "request_timeout": 30,
    "rate_limit_delay": 0.5,  # Sekunden zwischen API-Aufrufen
}
