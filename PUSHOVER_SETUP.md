# Pushover Setup Guide für Mobile Benachrichtigungen

## 🚀 Schnellstart

### 1. Pushover App installieren
- **Android**: [Play Store - Pushover](https://play.google.com/store/apps/details?id=net.superblock.pushover)
- **iPhone**: [App Store - Pushover](https://apps.apple.com/app/pushover-notifications/id506088175)
- **Kosten**: Einmalig $4.99 (keine Abo-Kosten)

### 2. Account einrichten
1. Account erstellen auf [pushover.net](https://pushover.net)
2. Notiere dir deinen **User Key** (zu finden im Dashboard)

### 3. App Token erstellen
1. Gehe zu [pushover.net/apps/build](https://pushover.net/apps/build)
2. Erstelle eine neue Application:
   - **Name**: "News Analyzer"
   - **Type**: Application
   - **Description**: "AI-powered news analysis notifications"
3. Kopiere den **API Token/Key**

### 4. Konfiguration in .env
Füge diese Zeilen zu deiner `.env` Datei hinzu:

```env
# Mobile Notifications (Pushover)
ENABLE_MOBILE_NOTIFICATIONS=true
PUSHOVER_TOKEN=your_app_token_here
PUSHOVER_USER_KEY=your_user_key_here
NOTIFICATION_THRESHOLD=7.5
```

### 5. GUI starten
```bash
python news_gui.py
```

## ⚙️ Einstellungen anpassen

### Notification Threshold
- **5.0-6.9**: Alle wichtigen Nachrichten
- **7.0-7.9**: Nur hochrelevante Nachrichten (Standard)
- **8.0-8.9**: Nur sehr wichtige Breaking News
- **9.0-10.0**: Nur kritische Eilmeldungen

### Prioritäten
- **Score 9.0+**: Hohe Priorität (Ton + Vibration)
- **Score 7.0-8.9**: Normale Priorität
- **Score <7.0**: Keine Benachrichtigung

## 📱 Notification Features

### Automatische Benachrichtigungen
- ✅ Werden automatisch bei hohem AI-Score gesendet
- ✅ Enthalten Titel, Quelle und AI-Begründung
- ✅ Direkter Link zum Artikel
- ✅ Emoji-Kategorisierung

### Manuelle Benachrichtigungen
- 📱 "Send to Phone" Button in der GUI
- 🔗 Artikel sofort an Handy weiterleiten
- 💾 Wichtige Artikel für später speichern

## 🎯 Beispiel-Notifications

### Breaking News (Score 9.2)
```
🚨 Breaking News (Score: 9.2/10)

📰 Fed announces emergency rate cut amid market volatility

🏢 Reuters
🧠 Significant economic policy change with immediate market...
```

### High Priority (Score 8.1)
```
🔥 Important Update (Score: 8.1/10)

📰 Major breakthrough in quantum computing announced

🏢 BBC Technology
🧠 Revolutionary technology advancement with potential...
```

## 🛠️ Troubleshooting

### Keine Benachrichtigungen?
1. ✅ Pushover App installiert und angemeldet?
2. ✅ Token und User Key korrekt eingegeben?
3. ✅ `ENABLE_MOBILE_NOTIFICATIONS=true` gesetzt?
4. ✅ Threshold nicht zu hoch (versuche 6.0)?
5. ✅ Internet-Verbindung verfügbar?

### Test-Benachrichtigung
1. GUI öffnen
2. "⚙️ Settings" klicken
3. Token eingeben
4. "📱 Test Notification" klicken

### API-Limits
- **Pushover Free**: 7.500 Nachrichten/Monat
- **Pushover Pro**: 10.000 Nachrichten/Monat
- **Unser System**: Ca. 5-20 Nachrichten/Tag (je nach Threshold)

## 🔒 Datenschutz

### Was wird gesendet?
- ✅ Artikel-Titel (gekürzt)
- ✅ Quelle
- ✅ AI-Score und Begründung (gekürzt)
- ✅ Link zum Artikel
- ❌ Keine persönlichen Daten
- ❌ Keine Tracking-Informationen

### Pushover Datenschutz
- 🇺🇸 Server in den USA
- 🔐 TLS-verschlüsselte Übertragung
- 📱 Nachrichten werden nach 30 Tagen gelöscht
- 💾 Keine Verkauf von Nutzerdaten

## 📊 Optimale Einstellungen

### Für tägliche News (empfohlen)
```env
NOTIFICATION_THRESHOLD=7.5
AUTO_REFRESH_MINUTES=120
```

### Für Breaking News only
```env
NOTIFICATION_THRESHOLD=8.5
AUTO_REFRESH_MINUTES=60
```

### Für Wissenschaft/Tech Focus
```env
NOTIFICATION_THRESHOLD=7.0
# Aktiviere nur Tech-Feeds in RSS_FEEDS
```

## 🎨 GUI Features

### Hauptfenster
- 🗞️ **Links**: Liste aller wichtigen Artikel (Score ≥ 7.0)
- 📋 **Rechts**: Detailansicht mit AI-Analyse
- 🔄 **Toolbar**: Refresh, Settings, Status
- 🎯 **Farbcodierung**: Rot (9+), Orange (8+), Grün (7+)

### Aktionen pro Artikel
- 🔗 **Open Article**: Öffnet im Browser
- 📱 **Send to Phone**: Manuelle Benachrichtigung
- 💾 **Auto-Save**: Wichtige Artikel automatisch markiert

## 🚀 Power-User Tips

### Mehrere Geräte
- Ein Pushover-Account funktioniert auf allen Geräten
- Notifications erscheinen auf Phone, Tablet, Desktop

### Stille Zeiten
- In Pushover App: "Quiet Hours" einrichten
- Notifications werden gesammelt und später zugestellt

### Integration mit anderen Apps
- **IFTTT**: Pushover kann Aktionen in anderen Apps triggern
- **Tasker** (Android): Automatisierte Antworten auf News
- **Shortcuts** (iOS): Custom Actions für Notifications

---

💡 **Tipp**: Starte mit Threshold 7.0 und passe nach ein paar Tagen an deine Präferenzen an!
