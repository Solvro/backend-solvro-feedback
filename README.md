# backend-solvro-feedback

Backend do obsługi zgłoszeń feedbacku i bug reportów, z panelem moderacji oraz integracją z GitHub Issues.

## 🚀 Instalacja

1. **Sklonuj repozytorium**

   ```bash
   git clone https://github.com/Solvro/backend-solvro-feedback
   cd backend-solvro-feedback
   ```

2. **Utwórz i aktywuj środowisko wirtualne**

   ```bash
   python -m venv .venv
   source .venv/bin/activate        # Linux / macOS
   .venv\Scripts\activate           # Windows
   ```

3. **Zainstaluj zależności**

   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

4. **Skopiuj plik środowiskowy**

   ```bash
   cp .env.example .env
   ```

   > Jeśli projekt nie zawiera jeszcze pliku `.env.example`, utwórz `.env` ręcznie.

5. **Wykonaj migracje bazy danych**

   ```bash
   python manage.py migrate
   ```

6. **(Opcjonalnie) Stwórz konto administratora**

   ```bash
   python manage.py createsuperuser
   ```

7. **Uruchom serwer deweloperski**

   ```bash
   python manage.py runserver
   ```

---

## 🤝 Kontrybucja

Chcesz pomóc w rozwoju projektu? Super!

1. Sforkuj repozytorium (jeśli nie jesteś członkiem organizacji)
2. Stwórz branch dla swojej funkcji (`git checkout -b feat/123-amazing-feature`)
3. Commituj zmiany (`git commit -m "feat(api): add report endpoint validation"`)
4. Wypchnij branch (`git push origin feat/123-amazing-feature`)
5. Otwórz Pull Request

Aby współpraca była płynna, trzymajmy się poniższych zasad.

### 🪾 Nazewnictwo branchy

Każdy branch powinien zawierać **prefiks typu zmiany** i **numer GitHub Issue**.

**Format**

```text
<prefix>/<issue>-short-description
```

**Dostępne prefiksy**

- `feat/` - nowe funkcje
- `fix/` - poprawki błędów
- `hotfix/` - krytyczne poprawki produkcyjne
- `design/` - zmiany UI/UX
- `refactor/` - poprawa kodu bez zmiany działania
- `test/` - testy
- `docs/` - dokumentacja

**Przykłady**

```text
feat/123-add-github-integration
fix/87-report-validation-error
refactor/210-cleanup-services
```

---

### 🧹 Pre-commit i jakość kodu

W projekcie używamy [pre-commit](https://pre-commit.com/) oraz [ruff](https://docs.astral.sh/ruff/) do automatycznego lintowania i formatowania kodu.

**Instalacja narzędzi deweloperskich**

```bash
pip install -r requirements-dev.txt
```

**Instalacja hooków pre-commit**

```bash
pre-commit install
```

**Ręczne uruchomienie wszystkich hooków**

```bash
pre-commit run --all-files
```

Po instalacji hooków, przy każdym `git commit` automatycznie uruchomią się:
- `ruff` – linting i sortowanie importów
- `ruff-format` – formatowanie kodu

---

### ✍️ Format commitów

Stosujemy [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/).

**Format**

```text
<type>(opcjonalny scope): opis w czasie teraźniejszym
```

**Typy commitów**

- `feat:` - nowa funkcjonalność
- `fix:` - naprawa błędu
- `docs:` - dokumentacja
- `refactor:` - poprawa struktury kodu
- `test:` - testy
- `chore:` - zmiany konfiguracyjne, dependency itp.

**Przykłady**

```bash
feat(auth): add Solvro auth integration
fix(report): validate max 5 attachments
docs: update README with local setup
```
