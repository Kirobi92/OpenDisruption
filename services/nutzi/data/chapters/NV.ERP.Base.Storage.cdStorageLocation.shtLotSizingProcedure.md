---
chapter_id: "NV.ERP.Base.Storage.cdStorageLocation.shtLotSizingProcedure"
topics: []
source: eNVenta 4.5 Onlinehilfe
---

# Kapitel NV.ERP.Base.Storage.cdStorageLocation.shtLotSizingProcedure

Hier wird das Verfahren zur Ermittlung der Dispomenge beim Bestellvorschlag festgelegt. 

Zur Verfügung stehen die Einträge: 
- bis Maximalbestand - individuell - kein Verfahren - nach Andler 
bis Maximalbestand: 

Anhand des Lagerbestands, der Reservierung bereits bestellter Mengen und den Mengen aus dem Dispo-Pool wird die Differenz zum Maximalbestand ermittelt und zur Bestellung vorgeschlagen. 

individuell: 

Hier kann die Berechnung über das Customizing individuell ausprogrammiert werden. 

kein Verfahren: 

Anhand des Lagerbestands, der Reservierung bereits bestellter Mengen und den Mengen aus dem Dispo-Pool wird die Differenz zum Meldebestand ermittelt und zur Bestellung vorgeschlagen. 

nach Andler: 

Berechnung der Dispomenge nach Andler-Verfahren 

Definition Andler: 

Gesamtmenge = Gesamt-Lagerabgang des aktuellen Datums – 1 Jahr als Summe (bezogen auf das Lager bzw. alle Lager der Lagergruppe) 

Lagerwert = Wert der Gesamtmenge 

Losgröße = (200 * Gesamtmenge * Bestellfixe Kosten) / Lagerwert * Zins Losgröße) 

Wurzel aus der Losgröße ziehen und auf den nächsthöheren Wert mit 2 Nachkommastellen runden. 

Der Eintrag im Lagerort hat Priorität vor einem Eintrag in den Parametern des Einkaufs. 

Siehe Kapitel Automatisches Bestellwesen . 

Tooltip: 

Wählen Sie das Verfahren zur Losgröße aus.