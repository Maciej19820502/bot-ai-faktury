# Jak zbudowaliśmy Bota AI do obsługi faktur — instrukcja krok po kroku

Niniejsza instrukcja opisuje, jak od zera dojść do działającego prototypu systemu,
który automatycznie odpowiada na e-maile klientów pytających o status faktur.
Cały kod został wygenerowany i uruchomiony za pomocą **Claude Code** — narzędzia AI
działającego w terminalu.

---

## Etap 1: Założenie konta i subskrypcji

### 1.1 Konto na Claude.ai

1. Wejdź na stronę **https://claude.ai** i kliknij "Sign up".
2. Zarejestruj się za pomocą e-maila lub konta Google.
3. Aby korzystać z Claude Code, potrzebujesz płatnej subskrypcji — wykup plan **Pro** (20 USD/mies.) lub **Max**.

### 1.2 Instalacja Claude Code

Claude Code to narzędzie terminalowe (CLI), które pozwala rozmawiać z AI bezpośrednio
w terminalu i zlecać mu pisanie kodu, tworzenie plików, uruchamianie komend.

**Na Windows:**

1. Zainstaluj **Node.js** (wersja 18+) ze strony https://nodejs.org
2. Otwórz terminal (PowerShell lub Git Bash) i wpisz:
   ```
   npm install -g @anthropic-ai/claude-code
   ```
3. Uruchom Claude Code:
   ```
   claude
   ```
4. Przy pierwszym uruchomieniu zaloguj się swoim kontem Claude.ai.

**Gotowe!** Jesteś teraz w interaktywnej sesji z AI, które widzi Twoje pliki
i może wykonywać polecenia w terminalu.

---

## Etap 2: Przygotowanie projektu

### 2.1 Utwórz folder projektu

Utwórz folder na dysku, np. `PROJEKT BOT AI`, i w terminalu przejdź do niego:
```
cd "C:\Users\TwojaNazwa\Pulpit\PROJEKT BOT AI"
```

Uruchom Claude Code w tym folderze:
```
claude
```

### 2.2 Przygotuj materiały wejściowe

W naszym przypadku w podfolderze `DANE` umieściliśmy:
- Konspekt projektu (PDF)
- Prezentację (PDF)
- Mapę procesu (PDF)
- Checklistę pracy (DOCX)
- Przewodnik po narzędziach (DOCX)

Dzięki temu Claude mógł najpierw przeanalizować materiały i zrozumieć kontekst projektu.

---

## Etap 3: Analiza materiałów

W sesji Claude Code wpisaliśmy polecenie w stylu:

> "Przejrzyj wszystkie pliki w katalogu DANE. Zidentyfikuj ich typy i zawartość.
> Oceń spójność z kontekstem projektu. Przygotuj raport w języku polskim."

Claude samodzielnie:
- Odczytał pliki PDF i DOCX
- Zainstalował potrzebne biblioteki Pythona
- Przeanalizował strukturę i zawartość
- Wygenerował raport `raport_analiza.md` z sekcjami "Zgodność z założeniami" i "Luki i rekomendacje"

**Wniosek:** nie musieliśmy pisać żadnego kodu — wystarczyło opisać, czego oczekujemy.

---

## Etap 4: Zlecenie budowy prototypu

Następnie wydaliśmy jedno polecenie:

> "Działając autonomicznie, przygotuj prototyp aplikacji:
> - mail: Gmail (logowanie w aplikacji)
> - wygeneruj testowy plik Excel z fakturami
> - odpowiedź też przez Gmail
> - miejsce do edycji promptu odpowiedzi
> - sanacja wpisu (ochrona przed prompt injection)
> - to ma być prototyp, pierwsza wersja"

### Co Claude zrobił sam:

1. **Zaplanował architekturę** — wybrał Flask (panel webowy), IMAP/SMTP (Gmail),
   SQLite (logi), Anthropic API (klasyfikacja i odpowiedzi).

2. **Utworzył 12 modułów Pythona:**
   - `gmail_client.py` — łączenie z Gmailem (odczyt i wysyłka maili)
   - `classifier.py` — klasyfikacja wiadomości przez AI (czy dotyczy faktury?)
   - `authorizer.py` — weryfikacja nadawcy (czy ma prawo pytać?)
   - `invoice_lookup.py` — szukanie faktury w Excelu
   - `responder.py` — generowanie odpowiedzi przez AI
   - `sanitizer.py` — ochrona przed prompt injection
   - `poller.py` — pętla sprawdzająca skrzynkę co 60 sekund
   - `logger_db.py` — zapis logów do bazy SQLite
   - `generate_test_data.py` — generator 60 testowych faktur
   - `config.py` — obsługa konfiguracji
   - `app.py` — panel webowy (Flask)
   - `run.py` — punkt startowy aplikacji

3. **Utworzył szablony HTML** — dashboard, edytor konfiguracji, edytor promptów, przeglądarka logów.

4. **Wygenerował plik Excel** z 60 realistycznymi fakturami (różne statusy, dostawcy, kwoty).

5. **Zainstalował wszystkie zależności** automatycznie.

6. **Przetestował** czy aplikacja się uruchamia.

Wszystko to zajęło ok. 10 minut.

---

## Etap 5: Konfiguracja Gmaila

### 5.1 App Password (hasło aplikacji)

Aby bot mógł czytać i wysyłać maile z konta Gmail:

1. Włącz **weryfikację dwuetapową** na koncie Google:
   https://myaccount.google.com/signinoptions/two-step-verification

2. Wygeneruj **hasło aplikacji**:
   https://myaccount.google.com/apppasswords
   - Wpisz nazwę, np. "Bot AI"
   - Skopiuj wygenerowane 16-znakowe hasło

### 5.2 Wpisanie kluczy w panelu aplikacji

Klucze wpisuje się bezpośrednio w panelu webowym — **nie trzeba edytować żadnych plików**:

1. Uruchom aplikację (`python run.py`)
2. Otwórz **http://localhost:5000/config**
3. W sekcji **Połączenie z Gmail** wpisz adres Gmail i App Password
4. W sekcji **Klucz API Anthropic** wpisz klucz API
5. Kliknij "Zapisz konfigurację"

**Skąd wziąć klucz Anthropic API:**
1. Wejdź na https://console.anthropic.com
2. Utwórz konto (lub zaloguj się)
3. W sekcji API Keys wygeneruj nowy klucz
4. Wklej go w panelu konfiguracji

Klucze zapisują się w pliku `config.json`, który jest wykluczony z GitHuba
(przez `.gitignore`), więc nie trafią do publicznego repozytorium.

---

## Etap 6: Konfiguracja systemu

Plik `config.json` w katalogu projektu zawiera ustawienia bota. Można je edytować
ręcznie lub przez panel webowy. Najważniejsze:

**Autoryzowane domeny** — lista domen e-mail, z których bot akceptuje zapytania:
```json
"allowed_domains": {
    "firma-klienta.pl": "Nazwa Klienta Sp. z o.o.",
    "inna-firma.com": "Inna Firma S.A."
}
```

**Prompty AI** — instrukcje dla modelu AI, jak klasyfikować maile i jak pisać odpowiedzi.
Można je modyfikować w panelu webowym (zakładka "Prompty").

---

## Etap 7: Uruchomienie

W terminalu, w folderze projektu:

```
python run.py
```

Aplikacja:
1. Wygeneruje plik Excel z testowymi fakturami (jeśli nie istnieje)
2. Utworzy bazę danych logów
3. Uruchomi poller sprawdzający skrzynkę co 60 sekund
4. Wystartuje panel webowy na **http://localhost:5000**

### Panel webowy

| Zakładka | Co robi |
|----------|---------|
| **Dashboard** | Status systemu, ostatnie operacje, przycisk "Sprawdź maile teraz" |
| **Konfiguracja** | Klucze Gmail i Anthropic, domeny klientów, ton odpowiedzi, interwał, model AI |
| **Prompty** | Edycja promptów klasyfikacji i odpowiedzi, test sanityzacji |
| **Logi** | Pełna historia operacji z filtrami |

---

## Etap 8: Testowanie

1. Wyślij e-mail na adres bota (ten wpisany w Konfiguracji) z treścią np.:
   > "Dzień dobry, proszę o informację o statusie faktury FV/2025/003."

2. Wyślij go z adresu w autoryzowanej domenie (skonfigurowanej w `config.json`).

3. Po max. 60 sekundach bot powinien:
   - Odebrać maila
   - Sklasyfikować go jako zapytanie o fakturę
   - Sprawdzić autoryzację nadawcy
   - Znaleźć fakturę w Excelu
   - Wygenerować odpowiedź
   - Wysłać odpowiedź e-mailem

4. Sprawdź wynik w panelu (Dashboard) i w skrzynce nadawcy.

### Logika obsługi zapytań

| Nadawca | Sytuacja | Co robi bot |
|---------|----------|-------------|
| Nieautoryzowany | cokolwiek | cisza — mail oznaczony jako przeczytany, zapisany w logach |
| Autoryzowany | faktura znaleziona | odpowiedź z danymi faktury do klienta |
| Autoryzowany | faktura nieznaleziona | odpowiedź do klienta + **eskalacja na e-mail działu AP/AR** |
| Autoryzowany | nie podał numeru faktury | odpowiedź do klienta + **eskalacja** |

E-mail eskalacji konfiguruje się w panelu (zakładka Konfiguracja).

---

## Podsumowanie: co Claude Code zrobił za nas

| Zadanie | Czy Claude to zrobił? |
|---------|----------------------|
| Analiza dokumentów projektowych | Tak |
| Zaplanowanie architektury | Tak |
| Napisanie całego kodu (12 modułów + HTML) | Tak |
| Wygenerowanie danych testowych | Tak |
| Instalacja zależności | Tak |
| Testowanie i debugowanie | Tak |
| Konfiguracja i uruchomienie | Tak (z naszą pomocą przy hasłach) |

**Nasza rola:** opisywaliśmy, czego chcemy, podawaliśmy dane logowania i podejmowaliśmy
decyzje (np. Gmail zamiast Outlook, App Password zamiast OAuth).

Claude Code nie jest magią — to narzędzie, które wymaga precyzyjnych poleceń
i zrozumienia tego, co budujemy. Ale radykalnie przyspiesza przejście od pomysłu
do działającego prototypu.

---

## Wskazówki do pracy z Claude Code

1. **Opisuj cel, nie implementację** — zamiast "utwórz plik X z funkcją Y", powiedz
   "potrzebuję modułu, który sprawdza czy nadawca ma uprawnienia".

2. **Dawaj kontekst** — im więcej Claude wie o projekcie, tym lepsze wyniki.
   Umieść materiały w folderze i każ mu je przeczytać.

3. **Pracuj iteracyjnie** — nie próbuj zlecić wszystkiego na raz.
   Najpierw analiza, potem prototyp, potem poprawki.

4. **Testuj na bieżąco** — po każdym większym kroku proś o uruchomienie i sprawdzenie.

5. **Nie bój się błędów** — jeśli coś nie działa, opisz problem. Claude sam
   znajdzie logi, zdiagnozuje przyczynę i naprawi.

6. **Zdalne sterowanie** — możesz sterować Claude Code z telefonu poleceniem
   `claude remote-control` (wyświetli QR kod do zeskanowania).
