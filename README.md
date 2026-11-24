# PS5 Preisradar 5.0 – iPhone + Freund + Cloud

Dies ist ein **veröffentlichbares Projekt**, kein bereits bereitgestellter Cloud-Dienst. Du musst **einmalig** ein eigenes GitHub-Repository anlegen und die Dateien hochladen. Danach ist **kein ständig laufender PC nötig**: GitHub Actions prüft die Produktseiten und GitHub Pages zeigt das Dashboard auf dem iPhone an. Dein Freund kann dieselbe Web-App über den Link öffnen und mit einem zusätzlichen ntfy-Abonnement dieselben Push-Preisalarme erhalten.

## Enthalten

- PS5 Slim **Digital oder Disc** (mit oder ohne Laufwerk); keine Pro, Bundles oder gebrauchte Ware
- Zielpreis **750 EUR** (anpassbar)
- 12 Start-Produktlinks: PlayStation Direct, MediaMarkt, Saturn, OTTO, expert, Smyths Toys, Galaxus und Coolblue
- Automatische Jobs ca. alle **30 Minuten** (GitHub-Zeitpläne sind nicht garantiert pünktlich)
- Preis- und Lagerstatus, 120 Messungen Verlauf
- iPhone-Web-App (PWA): In Safari **Teilen → Zum Home-Bildschirm**
- Push-Nachrichten über ntfy.sh, wenn ein verifizierbar lieferbarer Preis höchstens dem Zielpreis entspricht
- Gemeinsame Nutzung mit einem Freund
- Keine Passwörter, Tokens oder privaten ntfy-Kanäle in der öffentlich sichtbaren Seite

## Einmalige Einrichtung (GitHub)

1. Erstelle ein **öffentliches** GitHub-Repository, z. B. `ps5-preisradar`, mit Hauptbranch **`main`**. Kostenfreie GitHub Pages stehen für öffentliche Repositories zur Verfügung; prüfe die Bedingungen deines GitHub-Tarifs.
2. Lade **alle Dateien und Unterordner** aus diesem Projekt in das Repository hoch, einschließlich `.github/workflows/radar.yml`. Die ZIP-Datei nicht nur als eine einzelne ZIP-Datei hochladen! GitHub erwartet die entpackten Projektdateien. Das lässt sich auch am iPhone über GitHub im Browser durchführen, ist dort wegen der Ordnerstruktur jedoch umständlicher als am Desktop.
3. Gehe zu **Settings → Pages → Build and deployment → Source: GitHub Actions**.
4. Gehe zu **Settings → Actions → General → Workflow permissions** und aktiviere **Read and write permissions**, damit der Prüfjob `docs/data.json` speichern darf. Wenn GitHub eine Bestätigung verlangt, genehmige die Workflow-Ausführung.
5. Erzeuge einen langen zufälligen ntfy-Kanal, beispielsweise mit einem Passwortgenerator (mindestens 24 zufällige Zeichen). Gehe zu **Settings → Secrets and variables → Actions → New repository secret**. Name: `NTFY_TOPIC`, Wert: dein selbst erzeugter **privater** Kanal, z. B. `ps5-radar-` plus zufällige Zeichen. **Niemals** den echten Kanal in `config.json`, eine öffentliche Datei oder den GitHub-Verlauf schreiben.
6. Gehe zu **Actions → PS5 Preisradar – Cloud-Check und Webseite → Run workflow**. Warte auf den ersten erfolgreichen Lauf. Öffne deine GitHub-Pages-Adresse: `https://DEIN-BENUTZERNAME.github.io/DEIN-REPO-NAME/`.
7. Installiere auf deinem iPhone die App **ntfy** (https://ntfy.sh) und abonniere dort bei `ntfy.sh` den Kanal aus Schritt 5. Erlaube Benachrichtigungen in iOS.
8. Öffne das Dashboard mit Safari und wähle **Teilen → Zum Home-Bildschirm**. Die Web-App lässt sich nun wie eine App öffnen.

### Freund hinzufügen

- Sende deinem Freund die GitHub-Pages-Adresse oder tippe im Dashboard **„Dashboard teilen“**.
- Für Push-Nachrichten braucht er ebenfalls die ntfy-App und muss **denselben privaten Kanal** abonnieren. Teile den Kanal separat und vertraulich über einen privaten Messenger. **Jede Person mit dem Kanal kann Pushs sehen und selbst Nachrichten an diesen Kanal senden.**
- Beide sehen dieselben Preisprüfungen; Änderungen in `config.json` betreffen beide.

## Was und wie überwacht wird

Die Konfiguration liegt in `config.json`. `max_price_eur` ist die Preisobergrenze; `watches` enthält konkrete Produktseiten. Der Monitor wertet nur **eindeutige JSON-LD-Produktdaten** aus, wenn Produktnamen explizit die PS5 Slim Digital Edition belegen, `EUR` angegeben ist und der Lagerstatus explizit „InStock“, „OnlineOnly“ oder „LimitedAvailability“ ist. PS5 Pro, gebrauchte Produkte, Bundle und Controller werden ausgeschlossen. Digital und Disc werden getrennt über die erwartete Produktvariante des jeweiligen Links geprüft. Wenn eine Seite die Daten nicht so zur Verfügung stellt, wird **kein Alarm** ausgelöst. Drittanbieter, Marktplatzverkäufer, Versandkosten, Lieferzeiten und Gutscheine werden **nicht** verlässlich berücksichtigt. Das Dashboard sortiert zunächst passende lieferbare Angebote nach Preis und kennzeichnet <= 600 EUR als besonders interessant; 601–750 EUR bleibt unter dem Limit, ist aber ausdrücklich kein Schnäppchen. Prüfe das Angebot vor Kauf.

**Wichtig:** Die drei Startseiten sind plausible Produktlinks, aber ihre Live-Auslesbarkeit ist nicht gewährleistet. Gerade MediaMarkt/Saturn sowie Amazon können Shop-Abfragen von GitHub-Servern blockieren. Es gibt **keine Garantie**, dass alle Shops ausgelesen werden können. Die Anfangsoberfläche zeigt erst nach erfolgreichem ersten Monitor-Lauf Daten.

## Push testen

Am einfachsten sende eine Nachricht über die Oberfläche https://ntfy.sh/ zu **deinem privaten Kanal** und kontrolliere den Eingang auf beiden iPhones. Alternativ kannst du einen manuell ausgelösten GitHub Actions-Lauf starten: Pushs gehen **nur** bei einem neuen oder günstigeren passenden Angebot raus, nicht bei jedem Testlauf.

## Betrieb und Grenzen

- GitHub-Workflows können verzögert oder ausgelassen werden. GitHub kann automatische Zeitpläne in einem öffentlichen Repository nach längerer Inaktivität deaktivieren (laut GitHub etwa 60 Tage). Prüfe den Actions-Tab regelmäßig.
- **GitHub Pages ist öffentlich**: Jeder mit dem Link (oder der Repo-Adresse) kann Produkte und öffentlich gespeicherte Preise sehen. Privater Push-Kanal bleibt ein GitHub Secret.
- Der ntfy.sh-Kanal ist nicht authentifiziert und als Geheimnis durch Nichtweitergabe geschützt. Wer den Kanal kennt, kann auch fremde Nachrichten senden. Für echtes Mehrnutzer-Login, echte private Daten und dauerhaft garantierten Cloud-Betrieb wäre ein dedizierter Hosting-Dienst mit Backend erforderlich.
- Im PWA-Dashboard werden keine nativen Web-Pushs verschickt. Pushs erfolgen ausschließlich über die **separate ntfy-App**.
- Automatischer Kauf ist nicht Bestandteil des Projekts. Keine garantierte Verfügbarkeit oder Alarmzustellung.
- Bei einem neuen Preisalarm nach vorheriger Fehlerphase kann ein erneut erkanntes Angebot einen neuen Push auslösen.
- Monitor beachtet Domain-Allowlist, öffentliche DNS-Adressen und verweigert Redirects. Keine Geheimnisse in `docs/data.json`.

## Dateien

- `monitor.py`: Cloud-Preisprüfungen und Pushs
- `config.json`: Modell, Shops und Preislimit
- `docs/index.html`: iPhone-Dashboard, Teilen, Verlauf
- `docs/data.json`: automatisch aktualisierte, **öffentliche** Messdaten
- `docs/manifest.webmanifest`, `docs/sw.js`, `docs/icon.svg`: Home-Screen-App
- `.github/workflows/radar.yml`: Scheduler + Hosting-Veröffentlichung
- `tests/test_monitor.py`: Offline-Tests

## Lokal prüfen (optional)

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
```

## Kosten

Die verwendeten Dienste bieten kostenfreie Nutzungsmöglichkeiten, soweit du die Bedingungen und Kontingente erfüllst. Die Cloud ist nicht von uns gehostet; Verfügbarkeit und Gebühren richten sich nach den aktuellen Bedingungen der Anbieter.

## Händler und Preisgestaltung

Die `config.json` enthält ausschließlich konkrete Produktseiten (keine allgemeinen Suchergebnisse), mit `variant: Digital` oder `Disc`. Weitere Händler lassen sich durch zusätzliche eindeutige Produktlinks und einen Eintrag in `ALLOWED_HOSTS` ergänzen. Shopseitige HTML-Sperren, fehlendes JSON-LD oder Marktplatzdaten führen zu `nicht_auslesbar`; nicht als lagernd behandeln. Da Versand und Lieferzeit nicht verifiziert werden, gilt 750 EUR nur für den erkannten Artikelpreis, nicht für einen garantierten Endpreis.
