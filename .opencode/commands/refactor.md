---
description: Refaktoriert Code oder Modul für bessere Qualität, Lesbarkeit und Testbarkeit. Tests müssen danach grün sein.
agent: kirobi-coder
---

Refaktoriere: $ARGUMENTS

**Ziele des Refactorings:**
1. Lesbarkeit verbessern — Code erklärt sich selbst
2. Komplexität reduzieren — Funktionen < 50 Zeilen wenn möglich
3. Testbarkeit erhöhen — saubere Interfaces, keine tiefen Abhängigkeiten
4. Type-Safety — vollständige Type-Hints in Python, kein `any` in TypeScript
5. Fehler-Handling vollständig — kein unbehandelter Exception-Pfad

**Constraints:**
- Verhalten darf sich nicht ändern — nur Struktur
- Alle bestehenden Tests müssen weiterhin grün sein
- Keine neuen Features — reines Refactoring

**Ablauf:**
1. Bestehenden Code lesen und verstehen
2. Tests ausführen (Baseline): `python3 -m pytest tests/unit -q`
3. Refaktorieren
4. Tests erneut ausführen — müssen grün sein
5. Kurze Erklärung: Was wurde geändert und warum?
