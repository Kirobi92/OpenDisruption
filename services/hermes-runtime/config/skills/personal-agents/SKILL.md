# Personal Agents Skill — Samira & Sineo

**Zone:** FAMILY_PRIVATE  
**Service:** http://personal-agents:8017  
**Version:** 1.0.0

## Zweck

Fakten-basierte persönliche Agenten für Samira und Sineo.
**Garantie: Keine Halluzinationen** — nur gespeicherte, verifizierte Fakten.

## ⚠️ KRITISCHE REGEL

**VOR JEDER Aussage über Samira oder Sineo**: Profil laden!
```
GET http://personal-agents:8017/{samira|sineo}/profile
```
Dann: NUR Fakten aus dem Profil verwenden. Unbekannte Fakten → NACHFRAGEN.

## API-Referenz

| Methode | Pfad | Beschreibung |
|---------|------|--------------|
| GET | `/{person}/profile` | Alle gespeicherten Fakten |
| GET | `/{person}/intro` | Agent-Vorstellung + nächste Frage |
| GET | `/{person}/interview` | Nächste offene Interview-Fragen |
| POST | `/{person}/chat` | Grounded Chat (nur Fakten) |
| POST | `/{person}/facts` | Neuen Fakt speichern |
| DELETE | `/{person}/facts/{id}` | Falschen Fakt löschen |
| DELETE | `/{person}/unknown/{id}` | Offene Frage als beantwortet markieren |

## Fact-Speicher-Workflow

Wenn Sven etwas über Samira/Sineo erzählt:
```json
POST http://personal-agents:8017/samira/facts
{
  "category": "identity|interests|work|personality|tech|school|social|goals|values|health",
  "fact": "Samira ist 35 Jahre alt",
  "confidence": "verified",
  "source": "sven-confirmed"
}
```

## Anti-Halluzination-Protokoll

```
Falsch ❌: "Sineo ist 20 Jahre alt"
Richtig ✅: "Das weiß ich leider noch nicht. Wie alt ist Sineo?"

Falsch ❌: "Samira arbeitet als Erzieherin"
Richtig ✅: "Darüber habe ich noch keine Informationen. Was macht Samira beruflich?"
```

## Trigger-Beispiele

- "Erzähl mir von Sineo" → Profil laden, bekannte Fakten nennen + nächste Frage stellen
- "Was weiß du über Samira?" → `/samira/profile` → strukturierte Antwort
- "Sineo ist in der 9. Klasse" → `/sineo/facts` POST mit diesem Fakt
- "Fang an Samira kennenzulernen" → `/samira/interview` → erste Fragen stellen
