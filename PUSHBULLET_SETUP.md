# Pushbullet Setup Guide für Mobile Benachrichtigungen

## 🚀 Schnellstart mit Pushbullet

### 1. Pushbullet App installieren
- **Android**: [Play Store - Pushbullet](https://play.google.com/store/apps/details?id=com.pushbullet.android)
- **iPhone**: [App Store - Pushbullet](https://apps.apple.com/app/pushbullet/id810352052)
- **Kosten**: ✅ **KOSTENLOS** (Premium optional für mehr Features)

### 2. Account einrichten
1. Account erstellen auf [pushbullet.com](https://www.pushbullet.com)
2. App auf dem Handy mit Account verbinden
3. Pushbullet im Browser öffnen und anmelden

### 3. API Key erstellen
1. Gehe zu [pushbullet.com/account](https://www.pushbullet.com/account)
2. Scrolle zu **"Access Tokens"**
3. Klicke **"Create Access Token"**
4. Kopiere den **API Token** (sieht aus wie: `o.1234567890abcdef...`)

### 4. Konfiguration in .env
Füge diese Zeile zu deiner `.env` Datei hinzu:

```env
# Mobile Notifications (Pushbullet)
ENABLE_MOBILE_NOTIFICATIONS=true
PUSHBULLET_API_KEY=o.1234567890abcdef_dein_echter_api_key_hier
NOTIFICATION_THRESHOLD=7.5
```

### 5. GUI starten und testen
```bash
python news_gui.py
```
1. Klicke **"⚙️ Settings"**
2. Trage deinen **API Key** ein
3. Klicke **"📱 Test Notification"**
4. Prüfe dein Handy! 📱

## ⚙️ Pushbullet vs. andere Services

### ✅ Vorteile Pushbullet:
- 🆓 **Komplett kostenlos** für normale Nutzung
- 📱 **Alle Geräte**: Android, iOS, Desktop
- 🔗 **Direktlinks** zu Artikeln
- 💾 **Offline-Sync** 
- 🌍 **Web-Interface** verfügbar
- ⚡ **Sehr schnell** (meist <3 Sekunden)

### 📊 Limits (Kostenlose Version):
- **500 Pushes/Monat** (mehr als genug für News)
- **Unser System**: Ca. 5-20 Notifications/Tag je nach Threshold
- **Premium**: Unlimited pushes für $5/Monat (optional)

## 📱 Notification Features

### Automatische Benachrichtigungen
- ✅ **Score ≥ 7.5**: Normale Benachrichtigung
- 🚨 **Score ≥ 9.0**: Wichtige Breaking News
- 📰 **Doppelte Pushes**: Text + Link zum Artikel
- 🎯 **Smart Filtering**: Keine Duplikate

### Beispiel-Notifications

#### Breaking News (Score 9.2)
```
📰 Breaking News (Score: 9.2/10)

Fed announces emergency rate cut amid market volatility

🏢 Reuters
🧠 Significant economic policy change with immediate market...
```

#### Follow-up Link:
```
🔗 Read Full Article

Open: Fed announces emergency rate cut amid market...
[Direkter Link zum Artikel]
```

## 🛠️ Troubleshooting

### Keine Benachrichtigungen?
1. ✅ **API Key** korrekt eingegeben?
2. ✅ **Pushbullet App** installiert und angemeldet?
3. ✅ **Internet-Verbindung** verfügbar?
4. ✅ **Notifications** in der App aktiviert?
5. ✅ **Threshold** nicht zu hoch? (Versuche 6.0)

### Test-Benachrichtigung funktioniert nicht?
1. **API Key prüfen**: Gehe zu pushbullet.com/account
2. **Neuen Token erstellen** falls alter nicht funktioniert
3. **Browser-Konsole** prüfen auf pushbullet.com
4. **App neu starten** auf dem Handy

### API Fehler-Codes:
- **401 Unauthorized**: API Key falsch
- **403 Forbidden**: Account deaktiviert
- **429 Too Many Requests**: Rate Limit erreicht
- **500 Server Error**: Pushbullet Server Problem

## 🔒 Datenschutz & Sicherheit

### Was wird gesendet?
- ✅ **Artikel-Titel** (gekürzt auf ~150 Zeichen)
- ✅ **News-Quelle** (Reuters, BBC, etc.)
- ✅ **AI-Score und Begründung** (gekürzt)
- ✅ **Link zum Original-Artikel**
- ❌ **Keine persönlichen Daten**
- ❌ **Kein Tracking oder Analytics**

### Pushbullet Datenschutz:
- 🇺🇸 **Server in USA** (Google Cloud)
- 🔐 **HTTPS-verschlüsselt**
- 📱 **End-to-End optional** (Premium Feature)
- 💾 **Nachrichten nach 30 Tagen gelöscht**
- 🚫 **Kein Verkauf von Daten**

## 📊 Optimale Einstellungen

### Für tägliche Business News:
```env
NOTIFICATION_THRESHOLD=7.5
AUTO_REFRESH_MINUTES=120
```

### Für nur Breaking News:
```env
NOTIFICATION_THRESHOLD=8.5
AUTO_REFRESH_MINUTES=60
```

### Für Tech/Science Focus:
```env
NOTIFICATION_THRESHOLD=7.0
# Mehr Tech-Feeds in RSS_FEEDS aktivieren
```

## 🎨 Pushbullet App Features

### Mobile App:
- 📱 **Push History**: Alle Nachrichten gespeichert
- 🔍 **Suche**: In alten Notifications suchen
- 📂 **Kategorien**: Automatische Sortierung
- 🔕 **Stille Zeiten**: Notifications pausieren
- 📋 **Action Buttons**: Direkt zu Links springen

### Web-Interface:
- 💻 **pushbullet.com**: Alle Pushes im Browser
- 📤 **Manuell senden**: Eigene Nachrichten
- 🔗 **File Sharing**: Dateien zwischen Geräten
- 💬 **SMS Mirror**: SMS am Computer lesen

## 🚀 Erweiterte Features

### Multi-Device Support:
```
📱 iPhone + Android + Desktop
📧 Email-Benachrichtigungen optional
🖥️ Browser-Notifications verfügbar
```

### Integration mit anderen Tools:
- **IFTTT**: Pushbullet kann andere Apps triggern
- **Zapier**: Workflow-Automation
- **Tasker** (Android): Custom Actions
- **Shortcuts** (iOS): Siri-Integration

### Power-User Tipps:
1. **Channels abonnieren**: Öffentliche News-Channels
2. **Stille Zeiten**: 22:00-07:00 für besseren Schlaf
3. **Device-spezifisch**: Nur bestimmte Geräte benachrichtigen
4. **Backup**: API Key sicher speichern

## 📈 Monitoring & Analytics

### In der GUI verfügbar:
- 📊 **Notification-Zähler** in Settings
- 📈 **Success/Failure Rate**
- ⏱️ **Letzte erfolgreiche Benachrichtigung**
- 🎯 **Threshold-Optimierung** basierend auf Feedback

### Logs prüfen:
```bash
# News Scheduler Logs
cat news_scheduler.log | grep "Pushbullet"

# Erfolgreiche Notifications
grep "📱 Notification sent" news_scheduler.log
```

---

## 🎯 Schnell-Setup (2 Minuten):

1. **App installieren** → Pushbullet aus App Store
2. **Account erstellen** → pushbullet.com
3. **Token kopieren** → Settings > Access Tokens
4. **In GUI eintragen** → ⚙️ Settings > API Key
5. **Testen** → 📱 Test Notification
6. **Fertig!** 🎉

💡 **Tipp**: Starte mit Threshold 7.0 und passe nach ein paar Tagen an deine Bedürfnisse an!
