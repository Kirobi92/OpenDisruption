---
chapter_id: "NV.ERP.Base.Common.cdSystemBase.shtPPriceRefreshOfBilledSOItems"
topics: []
source: eNVenta 4.5 Onlinehilfe
---

# Kapitel NV.ERP.Base.Common.cdSystemBase.shtPPriceRefreshOfBilledSOItems

Aktualisierungen von EK und NK an fakturierten (oder abgeschlossenen) Auftragspositionen aus der Rechnungsprüfung heraus, finden grundsätzlich nur dann statt, wenn dieser Systemparameter gesetzt ist. 

Wenn nach einer Rechnungsprüfung die Wareneinsatzkosten von den bereits verbuchten Wareneinsatzkosten einer Auftragsposition abweichen, wird bei der Übernahme in die Kostenrechnung ( Kore-Übernahme ) eine Korrekturbuchung ausgelöst. Diese Korrekturbuchung wird mit dem Systemdatum ausgeführt. 

Mit der Buchung in die Kostenrechnung wird eine TNR Nummer in die Kore-Schnittstelle mit übergeben. Solch eine Buchung ist jetzt selektiv in der Kostenrechnung auswählbar. Die Herkunft dieser Buchungen ist mit VK gekennzeichnet. 

Siehe nachfolgendes Beispiel: 

Kore-Übernahme Wareneinsatz 

Die Herkunft VK steht im Kostenarten-Journal als Selektionskriterium zur Verfügung. Siehe nachfolgender Screenshot. 
Kostenarten-Journal 

Aktualisierungen von EK und NK an gelieferten Auftragspositionen aus der Rechnungsprüfung heraus, finden NICHT statt, wenn das Lieferschein-Identitätspreisverfahren ( Parameter Verkauf Registerkarte Allgemein , Checkbox Lief. Identität und Faktura-Lager ) und das Dispoverfahren ungleich Kein Lager ist. 

Siehe Kapitel Parameter Verkauf . 

Tooltip: 

EK-/NK-Aktualisierung fakturierter Auftragspositionen aus der Rechnungsprüfung heraus.