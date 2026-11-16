"""Portable AUTO entry contract; projects may supply a focused instructions adapter."""

from pathlib import Path


def render_instructions(entry: dict) -> str:
    cli = Path(__file__).with_name("auto.py")
    return f"""# ⚙️ AUTO

📌 Czat {entry['thread_id']}, run {entry['run_id']}, projekt {entry['repo']}.
🎯 Zakres: {entry['scope']}. Źródła: {', '.join(entry['sources'])}. Limit: {entry['batch_size']} kroków.
🧰 CLI: python -B "{cli}". Nie zgaduj czatu po dacie ani nazwie.

## 🔁 Wznowienie

📌 CONTINUE-AUTO odczytuje context i wskazane thread.json, progress.json, tasks.json oraz tę instrukcję.
🛑 stopped, needs_input, batch_complete, queue_complete i pilot_complete nie uruchamiają pracy. STOP ma pierwszeństwo.
🔎 Pobierz list_threads i get_usage_limits. Przy pełnej liście 50 uzupełnij project-roster i natywne wait_threads(timeoutMs=0) osobno dla brakujących ID. Zapisz świeży native-snapshot. Prywatny App Server nie dowodzi bezczynności desktopu.
📋 Przygotuj listę z kanonicznych źródeł: id, source (ścieżka względna zatwierdzona w START), source_sha256, status, depends_on. Tylko todo/progress wykonuje pracę; test/open/done/other nie są implementacją. Nie rozszerzaj zgody START. Stosuj workflow projektu i kontekst prompt_context={entry.get('prompt_context', '')!r}.
🔐 Wywołaj native-begin z dokładnymi --thread-id, --run-id, --wake-id (ID bieżącej tury + :auto: + aktualne completed), --snapshot-file i --tasks-file. Dla heartbeat dodaj zapisany --scheduler-id; transport manual go nie wymaga. native-begin potwierdza odbiór ręcznego wznowienia i atomowo sprawdza rezerwacje projektu. Zachowaj ten sam wake_id przy ponowieniu tej samej jednostki.
🛠️ Tylko action=execute autoryzuje jedną jednostkę. reconcile oznacza dokończenie już zarezerwowanej pracy; nie kasuj jej i nie zaczynaj drugiej. LIMIT wymaga dowodu przerwania limitem. Inne aktywne czaty lub brak limitów oznaczają czekanie.
🧾 Po zweryfikowanej pracy użyj finalizera projektu, a potem auto.py finalize --thread-id ID --run-id RUN --repo PROJEKT --report-file RAPORT. Raport: receipt_id, wake_id zgodne z rezerwacją, decision=continue|needs_input, checkpoint, progress={{summary,verification,evidence}}, needs i pending_needs. needs_input wymaga potrzeb id/needed/how/blocks. Commit i wyniki muszą być rzeczywiste.
📊 Pokaż cały report bieżącego runu. Finalizer zapisuje completed i recovery.run_finished/queue_finished/batch_finished/needs_input. Ręczne testy pozostają osobno. Samo zakończenie partii nie oznacza końca całej kolejki.
🔁 Gdy finalizer zwraca continuation.action=continue_current_turn, od razu kontynuuj w tym samym czacie: odśwież projekcję i natywny snapshot, po czym native-begin dla następnego completed. Nie kończ tury tylko po to, żeby czekać na watchdog. Nie wysyłaj wiadomości do siebie i nie zakładaj natywnego heartbeat. STOP, potrzeba decyzji, limit, zajęty projekt oraz koniec partii/kolejki kończą tę pętlę; nie omijaj bramek.
⏱️ START AUTO otwiera jeden widoczny scheduler CMD. Zewnętrzny watchdog odzyskuje urwaną kontynuację co5min; przy limicie kontroluje co10min i pokazuje czas odnowienia. Po świeżym potwierdzeniu dostępności wysyła CONTINUE-AUTO (limit reached previously, continue); zwykłe odzyskanie wysyła CONTINUE-AUTO. Dopisek jest informacją, nigdy zgodą na pominięcie native-begin. Zamknięcie CMD kończy watchdog, a już pracujące AUTO kontynuuje niezależnie. heartbeat pozostaje wyłącznie jawnym trybem legacy.
🔒 Nie powtarzaj wysyłki z niepotwierdzonym wake_dispatch. Brak potwierdzenia wymaga uzgodnienia stanu, a nie timeoutu.
"""
