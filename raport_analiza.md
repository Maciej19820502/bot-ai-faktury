# Raport z analizy materiałow projektowych -- Grupa 3 AIFINC2

**Projekt:** Bot AI do obsługi zapytań AP/AR dotyczących statusu faktur
**Data analizy:** 28 marca 2026
**Perspektywa:** Mentor oceniający gotowość projektu do realizacji

---

## 1. Przegląd dostarczonych materiałów

| Plik | Typ | Opis zawartości |
|------|-----|-----------------|
| `Bot_AI_Przewodnik_Copilot_Studio.docx` | Przewodnik techniczny | Instrukcja krok po kroku budowy prototypu w Microsoft Copilot Studio. Zawiera architekturę, strukturę pliku Excel (kolumny danych faktur), konfigurację tematów, eskalację, scenariusze testowe, harmonogram 8-tygodniowy, metryki sukcesu. |
| `Branża motoryzacyjna_Konspekt_PKG_Grupa 3.pdf` | Konspekt projektu | Identyfikacja problemu biznesowego, cel i zakres projektu, metodyka (LLM + RAG), harmonogram (XII 2025 -- VI 2026), oczekiwane rezultaty, ryzyka i ograniczenia. |
| `Prezentacja AI Bot Grupa 3 AIFINC2 - wersja z notatkami.pdf` | Prezentacja (15 slajdów) | Profil spółki (branża motoryzacyjna), problem biznesowy z danymi liczbowymi, cel i zakres rozwiązania, komponenty AI (NLP, RAG, intent classification), wymagania danych, benchmarki rynkowe, mapa wartości, ryzyka, zgodność regulacyjna. |
| `Mapa procesu.pdf` | Diagram procesowy | Jednostronicowa mapa procesu (format graficzny -- tekst nieekstrahowalny automatycznie). |
| `checklista_praca.docx` | Checklista pracy dyplomowej | 47 tabel weryfikacyjnych pokrywających rozdziały 1--8 pracy. Wszystkie pozycje niezaznaczone (status: do realizacji). |

---

## 2. Zgodność z założeniami projektu

| Element projektu | Status pokrycia | Źródło |
|-----------------|----------------|--------|
| **Odbiór wiadomości e-mail** | Częściowo | Przewodnik wspomina e-mail i Teams jako kanały; brak szczegółów integracji mailowej (IMAP/SMTP, polling). |
| **Klasyfikacja zapytania (LLM)** | Dobrze udokumentowane | Konspekt i prezentacja opisują intent classification; przewodnik definiuje trigger phrases i temat "Status faktury". |
| **Autoryzacja nadawcy** | Słabo udokumentowane | Prezentacja wspomina "autoryzację i uwierzytelnianie" w checkliście; brak projektu mechanizmu weryfikacji domeny e-mail nadawcy. |
| **Wyszukiwanie faktury (Excel)** | Dobrze udokumentowane | Przewodnik definiuje strukturę pliku Excel (kolumny: Numer faktury, Dostawca, Kwota, Waluta, Data wystawienia, Termin płatności, Status, Data płatności). Podejście RAG opisane. |
| **Określenie statusu płatności** | Dobrze udokumentowane | Statusy zdefiniowane: Opłacona / Oczekująca / Przeterminowana. Scenariusze testowe przewidziane. |
| **Obsługa przypadków brzegowych** | Częściowo | Przewodnik obsługuje scenariusz "nieznana faktura" (eskalacja). Brak projektu obsługi: błędnego formatu numeru, wariantów zapisu, wykrywania przeterminowanych faktur tego samego klienta. |
| **Odpowiedź mailowa** | Częściowo | Przewodnik opisuje wysyłkę e-mail przez Power Automate, ale tylko w kontekście eskalacji -- brak opisu automatycznej odpowiedzi na zapytanie klienta. |
| **Konfigurowalność odpowiedzi** | Słabo udokumentowane | Instrukcja systemowa w przewodniku jest sztywna. Brak mechanizmu konfiguracji tonu, języka czy szablonu wiadomości. |
| **Logowanie i audyt** | Słabo udokumentowane | Prezentacja wymienia "audytowalność" jako wartość, checklista wymaga opisu. Brak projektu architektury logowania. |

---

## 3. Luki i rekomendacje

### Luki krytyczne (blokujące realizację)

1. **Brak przykładowego pliku Excel z danymi.** Przewodnik definiuje wymagane kolumny, ale w materiałach nie ma pliku z danymi testowymi. Bez niego nie da się zbudować ani przetestować prototypu. **Rekomendacja:** Przygotować plik z min. 50 zanonimizowanymi rekordami pokrywającymi wszystkie statusy i przypadki brzegowe.

2. **Autoryzacja nadawcy -- brak projektu.** System musi weryfikować, czy pytający ma prawo uzyskać informację o fakturze (np. sprawdzenie domeny e-mail vs. przypisanie klienta). Żaden z materiałów nie opisuje tej logiki. **Rekomendacja:** Zaprojektować tabelę mapowania domen e-mail do kontrahentów i opisać algorytm weryfikacji.

3. **Integracja e-mailowa -- brak szczegółów.** Projekt zakłada odbiór i wysyłanie e-maili, ale przewodnik skupia się na Microsoft Teams. Brak opisu jak bot będzie monitorował skrzynkę, parsował treść i wysyłał odpowiedzi. **Rekomendacja:** Opisać przepływ e-mailowy (Power Automate + Outlook connector lub dedykowany trigger).

### Luki istotne (wymagające uzupełnienia)

4. **Konfigurowalność odpowiedzi** -- brak projektu szablonów, wyboru tonu i języka. Rekomendacja: zdefiniować zestaw parametrów konfiguracyjnych (język, formalność, szablon) i sposób ich przechowywania.

5. **Przypadki brzegowe** -- brak obsługi wariantów formatu numeru faktury (np. FV/2025/001 vs 2025/001 vs FV-2025-001), brak mechanizmu informowania o przeterminowanych fakturach klienta. Rekomendacja: opisać reguły normalizacji numerów i logikę dodatkowych alertów.

6. **Architektura logowania** -- brak projektu struktury logów, miejsca ich przechowywania i narzędzi do analizy. Rekomendacja: zdefiniować co jest logowane (zapytanie, klasyfikacja, wynik, czas, eskalacja) i gdzie.

7. **Mapa procesu** -- plik jest czysto graficzny i nie zawiera tekstu. Nie da się zweryfikować jej spójności z opisem bez wizualnej inspekcji. Rekomendacja: uzupełnić o wersję tekstową lub opis kroków pod diagramem.

### Mocne strony materiałów

- Dobrze zdefiniowany problem biznesowy z danymi liczbowymi (20--40% czasu na zapytania).
- Realistyczne metryki sukcesu (>=90% automatyzacja, >=95% dokładność, <10s czas odpowiedzi).
- Przemyślany harmonogram dwufazowy (Excel -> API SAP).
- Uwzględnienie aspektów regulacyjnych (RODO, AI Act) i etycznych.
- Benchmarki rynkowe (PKO BP, TransMobil) uzasadniające wykonalność.
- Kompletna checklista pracy dyplomowej (47 obszarów weryfikacji) stanowi solidną ramę do systematycznej realizacji.

### Dodatkowe założenia i ograniczenia wynikające z materiałów

- Narzędzie docelowe to **Microsoft Copilot Studio** (nie wspominano o tym w ustnym opisie -- implikuje ekosystem Microsoft 365 i jego ograniczenia).
- Faza I zakłada **ręczny eksport danych z SAP do Excela** z opóźnieniem kilku godzin -- system nie będzie działał na danych czasu rzeczywistego.
- Bot w Fazie I jest dostępny **tylko wewnętrznie** (Teams) -- udostępnienie zewnętrznym kontrahentom wymaga dodatkowej konfiguracji IT (Faza II).
- Konspekt wspomina o modelu **GPT/Claude**, podczas gdy przewodnik bazuje na wbudowanym LLM Copilot Studio -- potencjalna niespójność w wyborze modelu.

---

## 4. Podsumowanie

Materiały projektowe stanowią **solidną bazę koncepcyjną** -- problem jest dobrze zdefiniowany, zakres realistyczny, a harmonogram ambitny, lecz wykonalny. Największe ryzyko realizacyjne leży w **lukach implementacyjnych**: brak danych testowych, brak projektu autoryzacji nadawcy oraz niedostatecznie opisana integracja e-mailowa. Są to elementy kluczowe dla działania systemu zgodnie z założeniami.

**Priorytet na najbliższe tygodnie:** (1) przygotowanie pliku Excel z danymi testowymi, (2) zaprojektowanie mechanizmu autoryzacji, (3) opisanie pełnego przepływu e-mailowego end-to-end. Dopiero po uzupełnieniu tych elementów zespół będzie gotowy do skutecznej budowy prototypu.
