---
chapter_id: "NV.ERP.Base.Common.cdSystemMM.shtLotSizingProcedure"
topics: []
source: eNVenta 4.5 Onlinehilfe
---

# Kapitel NV.ERP.Base.Common.cdSystemMM.shtLotSizingProcedure

Hier wird das Verfahren zur Ermittlung der Dispomenge beim Bestellvorschlag festgelegt. Folgende Berechnungen erfolgen: 

kein Verfahren: 
Anhand des Lagerbestands, der Reservierung bereits bestellter Mengen und den Mengen aus dem Dispo-Pool wird die Differenz zum Meldebestand ermittelt und zur Bestellung vorgeschlagen. 

bis Maximalbestand: 
Anhand des Lagerbestands, der Reservierung bereits bestellter Mengen und den Mengen aus dem Dispo-Pool wird die Differenz zum Maximalbestand des Artikels auf dem Lager ermittelt und zur Bestellung vorgeschlagen. 

nach Andler: 
Berechnung der Dispomenge nach dem Andler-Verfahren. 

Definition Andler (x bedeutet multiplizieren, / bedeutet dividieren): 

Gesamtmenge = Gesamt-Lagerabgang des aktuellen Datums minus 1 Jahr als Summe (bezogen auf das Lager bzw. alle Lager der Lagergruppe) 

Lagerwert = Wert der Gesamtmenge 

Losgröße = (200 x Gesamtmenge x Bestellfixe Kosten) / (Lagerwert x Zins Losgröße) 

Wurzel aus der Losgröße ziehen und auf den nächsthöheren Wert mit 2 Nachkommastellen runden. 

individuell: 
Hier kann die Berechnung über das Customizing individuell ausprogrammiert werden. 

Siehe Kapitel Reichweitenoptimierung in der Bestellung . 

Siehe Kapitel Automatisches Bestellwesen Absatz Reichweitenoptimierung. 

Tooltip: 

Verfahren zur Losgrößenermittlung