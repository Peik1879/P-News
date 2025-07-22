# 🤖 Intelligenter Nachrichten-Analyzer

Ein Python-Programm, das automatisch aktuelle Nachrichtenartikel aus RSS-Feeds abruft und deren Wichtigkeit durch KI bewertet.

## 🚀 Features

- **RSS-Feed Integration**: Lädt Artikel von Reuters, BBC, Tagesschau, Spiegel und anderen Quellen
- **KI-Bewertung**: Nutzt OpenAI GPT oder lokale LLM-Modelle (Ollama) zur Bewertung
- **Intelligente Sortierung**: Sortiert Artikel nach politischer Relevanz (1-10 Skala)
- **Modularer Aufbau**: Einfach erweiterbar und konfigurierbar
- **Schöne Ausgabe**: Rich-Library für formatierte Tabellen und Progress-Bars

## 📋 Installation

### 1. Repository klonen/herunterladen
```bash
git clone <repository-url>
cd P-News
```

### 2. Virtual Environment erstellen (empfohlen)
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate
```

### 3. Abhängigkeiten installieren
```bash
pip install -r requirements.txt
```

## ⚙️ Konfiguration

### Sicherheitshinweis 🔒
**WICHTIG**: Erstellen Sie eine `.env` Datei basierend auf `.env.example` und tragen Sie Ihre eigenen API Keys ein. Commiten Sie niemals echte API Keys zu Git!

```bash
cp .env.example .env
# Dann bearbeiten Sie .env mit Ihren echten API Keys
```

### OpenAI API Setup (empfohlen)
1. Erstellen Sie einen Account bei [OpenAI](https://openai.com)
2. Generieren Sie einen API-Key
3. Bearbeiten Sie die `.env` Datei:
```env
OPENAI_API_KEY=ihr_echter_api_key_hier
AI_MODEL_TYPE=openai
OPENAI_MODEL=gpt-3.5-turbo
```

### Ollama Setup (lokale KI, kostenlos)
1. Installieren Sie [Ollama](https://ollama.ai)
2. Laden Sie ein Modell herunter:
```bash
ollama pull llama2
```
3. Konfigurieren Sie die `.env` Datei:
```env
AI_MODEL_TYPE=ollama
OLLAMA_MODEL=llama2
OLLAMA_BASE_URL=http://localhost:11434
```

### RSS-Feeds anpassen
Bearbeiten Sie die `RSS_FEEDS` in der `.env` Datei:
```env
RSS_FEEDS=https://feeds.reuters.com/Reuters/PoliticsNews,https://www.tagesschau.de/xml/rss2/,https://feeds.bbci.co.uk/news/world/rss.xml
```

## 🚀 Verwendung

### Einfacher Start
```bash
python P-News.py
```

### Ausgabe
Das Programm zeigt:
1. **Ladestatus** der RSS-Feeds
2. **KI-Analyse-Progress** für jeden Artikel
3. **Sortierte Tabelle** mit den wichtigsten Nachrichten
4. **Detailansicht** der Top 3 Artikel

### Beispiel-Ausgabe
```
🗞️  Wichtigste Nachrichten (KI-bewertet)
┏━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Rang ┃ Score  ┃ Titel                                            ┃ Quelle             ┃ Begründung                             ┃
┡━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ 1    │ 9.2/10 │ Ukraine-Konflikt: Neue Entwicklungen            │ Reuters            │ Internationale Krise mit globalen...  │
│ 2    │ 8.7/10 │ Bundestagswahl: Umfragen zeigen Trend           │ Tagesschau         │ Nationale Politik mit großer...        │
│ 3    │ 7.5/10 │ EU-Gipfel: Entscheidung über Sanktionen         │ BBC News           │ Europäische Politik, mittlere...       │
└──────┴────────┴──────────────────────────────────────────────────┴────────────────────┴────────────────────────────────────────┘
```

## 🛠️ Erweiterte Konfiguration

### Weitere RSS-Feeds hinzufügen
Bearbeiten Sie `config.py` und fügen Sie URLs zur `DEFAULT_RSS_FEEDS` Liste hinzu.

### KI-Bewertungskriterien anpassen
Modifizieren Sie die `AI_EVALUATION_CRITERIA` in `config.py`.

### Anzahl der Artikel limitieren
```env
MAX_ARTICLES=50
```

## 🔧 Fehlerbehebung

### "OpenAI API Key nicht gefunden"
- Überprüfen Sie die `.env` Datei
- Stellen Sie sicher, dass der API-Key korrekt ist
- Versuchen Sie `AI_MODEL_TYPE=ollama` für lokale Modelle

### "Ollama nicht erreichbar"
- Starten Sie Ollama: `ollama serve`
- Überprüfen Sie die URL in `.env`: `OLLAMA_BASE_URL=http://localhost:11434`
- Laden Sie ein Modell herunter: `ollama pull llama2`

### RSS-Feed Fehler
- Manche Feeds können temporär nicht verfügbar sein
- Das Programm überspringt fehlerhafte Feeds automatisch
- Prüfen Sie die Feed-URLs in einem Browser

## 📊 Bewertungsskala

Die KI bewertet Artikel auf einer Skala von 1-10:

- **1-3**: Lokale/unwichtige Nachrichten
- **4-6**: Regionale/moderate Wichtigkeit  
- **7-8**: National/international wichtig
- **9-10**: Historisch bedeutsam/gesellschaftsprägend

## 🤝 Beiträge

Verbesserungen sind willkommen! Erstellen Sie gerne Issues oder Pull Requests.

## 📄 Lizenz

MIT License - siehe LICENSE Datei.

## 🙏 Danksagungen

- [feedparser](https://pypi.org/project/feedparser/) für RSS-Parsing
- [OpenAI](https://openai.com) für die GPT-API
- [Ollama](https://ollama.ai) für lokale LLM-Unterstützung
- [Rich](https://rich.readthedocs.io/) für schöne Terminal-Ausgabe
