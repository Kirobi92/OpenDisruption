---
chapter_id: "NV.ERP.Base.Common.cdSystemMM.shtExtendedIndustryRepre"
topics: []
source: eNVenta 4.5 Onlinehilfe
---

# Kapitel NV.ERP.Base.Common.cdSystemMM.shtExtendedIndustryRepre

Ein Industrievertreter entspricht ungefähr einem Vertreter aus dem Verkauf. 

Wenn Sie diesen Parameter aktivieren, werden die Daten des Industrievertreters nicht nur in der Rechnungsprüfung angegeben, sondern werden bereits vor der Rechnungsprüfung in die Bestellung übernommen. 

Folgende Felder werden laut Verschlüsselung des Industrievertreters gedreht: 

- Steuerschlüssel - Aufwandskonto - MwSt.-Kennzeichen - Zahlungsbedingung - Versandart - Lieferung - Einkaufart (nur bis zum ersten Speichern) 
Des Weiteren werden Mahnungen laut Industrievertreter oder laut Lieferant (wenn kein Industrievertreter gesetzt ist) erzeugt. 

Wird ein Industrievertreter in Bestellung oder Rechnungsprüfung ausgewählt oder geändert, werden automatisch die Steuersätze und Aufwandskonten laut Verschlüsselung des Lieferanten „gedreht“. Dies gilt auch für das Mahnwesen im Einkauf. 

Wird ein Industrievertreter gelöscht (entfernt), werden wieder die Einstellungen des Lieferanten gezogen. Im Einzelnen sind dies die Einkaufart, Zahlungsbedingung, Lieferbedingung, Versandart, MwSt.KZ, Steuerschlüssel und Aufwandskonto. 

Diese Funktion ist notwendig bei Lieferungen aus dem Ausland, damit direkt bei der Erfassung der Bestellung die korrekten Daten gezogen werden und nicht erst in der Rechnungsprüfung. 

Tooltip: 

Wenn gesetzt, 
- wird ein Industrievertreter in der Bestellung oder Rechnungsprüfung ausgewählt, 
werden noch zusätzlich folgende Felder laut Verschlüsselung des Industrievertreters gedreht 
(Steuerschlüssel, Aufwandskonto, MwSt-Kennzeichen, Zahlungsbedingung, Versandart, 
Lieferung und Einkaufart – Einkaufart nur bis zum ersten Speichern) 
- werden Mahnungen laut Industrievertreter oder laut Lieferant 
(wenn kein Industrievertreter gesetzt) erzeugt.