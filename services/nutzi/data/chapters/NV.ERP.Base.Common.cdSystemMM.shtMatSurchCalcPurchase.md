---
chapter_id: "NV.ERP.Base.Common.cdSystemMM.shtMatSurchCalcPurchase"
topics: []
source: eNVenta 4.5 Onlinehilfe
---

# Kapitel NV.ERP.Base.Common.cdSystemMM.shtMatSurchCalcPurchase

Ist der Parameter MTZ-Berechnung gesetzt, erfolgt die MTZ-Berechnung analog im Modul Einkauf . Das bedeutet, dass die MTZ-Logik in den nachfolgend aufgeführten Programmteilen zieht: 

- Bestellen oder Disponieren aus dem Auftrag - Erfassung einer Disposition in der Dispo-Maske - Generieren einer Dispo-Position aus dem Bestellvorschlag - Ändern bzw. Löschen eines bestehenden Disposatzes im Dialog Dispo-Pool - Generieren eines Disposatzes aus dem Bestellautomat 
Beim Einfügen einer Position wird – sofern die Bedingungen gegeben sind - der MTZ automatisch berechnet. 

Wenn im Dialog Teuerungszuschlag die Checkbox Fragen gesetzt ist, erscheint beim Einfügen einer neuen Position, die mit einem MTZ versehen ist, der entsprechende MTZ-Berechnungsdialog. Dieser gibt Auskunft über die Höhe des ermittelten MTZ (und seiner Kalkulationsgrundlagen). Wird dieser Dialog mit dem Button OK quittiert, dann wird der vorgeschlagene MTZ in die Position übernommen; andernfalls (Button Zurück ) wird kein MTZ übernommen. Insofern hat der Sachbearbeiter die Entscheidungsfreiheit, den vorgeschlagenen MTZ ggf. zu modifizieren, zu übernehmen oder zu ignorieren (er wird also 'gefragt'). 

Ist die Checkbox Fragen dagegen NICHT gesetzt, wird - falls hinterlegt - ein entsprechender MTZ einfach unsichtbar berechnet und in die Position übernommen. 

Beim Erfassen der Menge eines MTZ-behafteten Artikels erfolgt – in Abhängigkeit der Checkbox Fragen sichtbar oder unsichtbar - die Berechnung und Zuweisung des MTZ. Wird der Button Dispo betätigt, dann wird zugleich ein korrespondierender Schatten-Datensatz generiert. 

Tooltip: 

Hiermit wird die MTZ-Berechnung für den Einkauf aktiviert. Die MTZ-Logik zieht dann in folgenden Programmteilen: 
1. Bestellen oder Disponieren aus dem Auftrag 
2. Erfassung einer Disposition im gleichlautenden Dialog 
3. Generieren einer Dispo-Position aus dem Bestellvorschlag 
4. Ändern bzw. Löschen eines bestehenden Disposatzes im Dialog Dispo-Pool 
5. Generieren eines Disposatzes aus dem Bestellautomat