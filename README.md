# Bot AI — Prototyp obsługi zapytań AP/AR

System automatycznej obsługi zapytań klientów o status faktur, oparty na LLM (Claude) z integracją Gmail.

## Szybki start

### 1. Zainstaluj zależności

```bash
pip install -r requirements.txt
```

### 2. Skonfiguruj klucz Anthropic

Utwórz plik `.env` (skopiuj z `.env.example`):

```
ANTHROPIC_API_KEY=sk-ant-twoj-klucz
FLASK_SECRET_KEY=losowy-ciag-znakow
```

### 3. Skonfiguruj Gmail API

1. Wejdź na [Google Cloud Console](https://console.cloud.google.com/)
2. Utwórz nowy projekt (lub wybierz istniejący)
3. Włącz **Gmail API** (APIs & Services > Enable APIs)
4. Utwórz dane uwierzytelniające:
   - APIs & Services > Credentials > Create Credentials > **OAuth Client ID**
   - Typ: **Desktop application**
   - Pobierz plik JSON i zapisz jako `credentials.json` w katalogu projektu
5. Dodaj swój adres Gmail jako użytkownika testowego:
   - OAuth consent screen > Test users > Add users

### 4. Uruchom aplikację

```bash
python run.py
```

Przy pierwszym uruchomieniu:
- Wygeneruje się plik `invoices.xlsx` z 60 testowymi fakturami
- Otworzy się okno przeglądarki do autoryzacji Gmail (OAuth2)
- Token zostanie zapisany w `token.json`

### 5. Otwórz panel

Przejdź do **http://localhost:5000** w przeglądarce.

## Struktura panelu

| Strona | Opis |
|--------|------|
| **Dashboard** | Status systemu, ostatnia aktywność, przycisk "Sprawdź maile teraz" |
| **Konfiguracja** | Interwał pollingu, autoryzowane domeny, ton odpowiedzi, model AI |
| **Prompty** | Edycja promptów klasyfikacji i odpowiedzi, test sanityzacji |
| **Logi** | Pełny audyt z filtrami (data, nadawca) |

## Jak działa bot

1. Co X sekund sprawdza skrzynkę Gmail (nieprzeczytane wiadomości)
2. Sanityzuje treść (ochrona przed prompt injection)
3. Klasyfikuje wiadomość przez Claude (czy dotyczy faktury?)
4. Sprawdza autoryzację nadawcy (domena e-mail vs. dozwolone domeny)
5. Wyszukuje fakturę w pliku Excel
6. Generuje odpowiedź przez Claude (konfigurowalny prompt i ton)
7. Wysyła odpowiedź e-mail i loguje całą operację

## Pliki projektu

```
run.py                  # Punkt wejścia
config.json             # Konfiguracja (domeny, prompty, ustawienia)
invoices.xlsx           # Dane faktur (auto-generowane)
bot/
  app.py                # Flask UI
  poller.py             # Pętla sprawdzania maili
  gmail_client.py       # Integracja Gmail API
  classifier.py         # Klasyfikacja LLM
  responder.py          # Generowanie odpowiedzi LLM
  authorizer.py         # Autoryzacja nadawcy
  invoice_lookup.py     # Wyszukiwanie w Excel
  sanitizer.py          # Ochrona przed prompt injection
  logger_db.py          # Logowanie SQLite
  generate_test_data.py # Generator danych testowych
  config.py             # Loader konfiguracji
templates/              # Szablony HTML (Flask/Jinja2)
static/                 # CSS
```
