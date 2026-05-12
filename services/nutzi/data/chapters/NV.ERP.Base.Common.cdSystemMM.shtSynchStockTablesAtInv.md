---
chapter_id: "NV.ERP.Base.Common.cdSystemMM.shtSynchStockTablesAtInv"
topics: []
source: eNVenta 4.5 Onlinehilfe
---

# Kapitel NV.ERP.Base.Common.cdSystemMM.shtSynchStockTablesAtInv

Wenn diese Checkbox aktiviert ist, sorgt sie bei der Inventur automatisch für eine Synchronisation der Bestandstabellen. 

Die Synchronisation erfolgt immer mit der kleinsten zählbaren Einheit als führende Einheit. Dies ist immer der Lagerplatz bei einem chaotischen Lager. Liegt auf einem Lagerplatz eine Charge so gilt Charge+Lagerplatz als kleinste Einheit und basierend darauf erfolgt die Summenbildung, welche dann in die entsprechenden Referenztabellen synchronisiert wird. 

Bei einem statischen Lager gilt der gesamte Lagerbestand, hier ist keine Synchronisation notwendig, außer es handelt sich um einen Chargen-Artikel – in diesem Fall ist die Charge führend und die Aufsummierung ergibt den neuen Bestand. 

Wichtig: Durch die Synchronisation bei der Initialisierung der Inventur und anschließender Bestätigung durch die Zählung, ist der Bestand wieder synchron über die verschiedenen Datenbank-Tabellen mit den korrekten Beständen. 

Wenn Sie diese Checkbox aktivieren, so wird beim Initialisieren der Inventur folgender Prozess durchgeführt: 

- Prüfung der Tabellen Lager, Charge und Chaot. Lager, ob die Bestände voneinander abweichen. - Korrektur der Tabellen Lager und Charge in Abhängigkeit der Bestände in der detail-liertesten Tabelle (statisches Lager: Tabelle Charge, chaotisches Lager: Tabelle Lagerchaos) - Anschließende Information über die angepassten Artikel über eine Meldung. 
Diese Funktion läuft nur dann, wenn die Inventur nicht auf bestimmte Lagerbereiche oder Plätze eingeschränkt ist und wenn das Lager kein LVS Lager ist. 

Tooltip: 

Ist dieser Parameter aktiviert, so wird beim Initialisieren der Inventur folgende Tätigkeit durchgeführt: 

- Prüfung der Tabellen 'Lager', 'Charge' und 'Lagerchaos', ob die Bestände voneinander abweichen 
- Korrektur der Tabellen 'Lager' und 'Charge', Abhängigkeit der Bestände in der detailliertesten Tabelle (statisches Lager: Tabelle 'Charge', chaotisches Lager: Tabelle 'Lagerchaos') 
- Anschließende Information über die angepassten Artikel über eine Post Message 

Diese Funktion läuft nur dann, wenn die Inventur nicht auf bestimmte Lagerbereiche oder Plätze eingeschränkt ist und wenn das Lager kein LVS Lager ist.