---
chapter_id: "NV.ERP.Base.Common.cdSystemMM.shtExtendedPPGeneration"
topics: []
source: eNVenta 4.5 Onlinehilfe
---

# Kapitel NV.ERP.Base.Common.cdSystemMM.shtExtendedPPGeneration

Wenn Sie diese Checkbox aktivieren, können Bestellvorschläge unabhängig vom Lagersatz generiert werden. 

Wenn dieser Parameter gesetzt ist, erfolgt nachfolgende Prüfung: 
- Gibt es bereits einen Lagersatz für diesen Artikel? - Ist ein Meldebestand > 0 (im Artikelstamm) gesetzt? - Ist das Dispoverfahren (im Artikelstamm) entweder auf Deterministisch, Bestellpunkt oder Reichweite gesetzt? 
Werden alle Bedingungen erfüllt, wird ein neuer Lagereintrag für den Artikel erzeugt. 

Als Lagernummer wird der Wert aus dem Feld Materiallager des Artikelstamms verwendet. Ist dort kein Wert gesetzt, wird stattdessen das Feld Zentrallager aus System >> Parameter Einkauf >> Registerkarte Allgemein verwendet. Ist dieses Feld ebenfalls nicht gesetzt, wird der erste Wert aus der Datenbank herangezogen. 

Mit Klick auf den Button Lager im Artikelstamm können Sie prüfen, ob ein Eintrag angelegt wurde. 

Tooltip: 

Wenn Sie diese Checkbox aktivieren, können Bestellvorschläge unabhängig vom Lagersatz generiert werden.