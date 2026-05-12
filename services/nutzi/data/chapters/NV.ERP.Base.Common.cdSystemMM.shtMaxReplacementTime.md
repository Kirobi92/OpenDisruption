---
chapter_id: "NV.ERP.Base.Common.cdSystemMM.shtMaxReplacementTime"
topics: []
source: eNVenta 4.5 Onlinehilfe
---

# Kapitel NV.ERP.Base.Common.cdSystemMM.shtMaxReplacementTime

Hier geben Sie ein Limit für die maximale Wiederbeschaffungszeit ein. Dieser Parameter wirkt nur zusammen mit der dynamischen Verfügbarkeit und setzt alle Auftragspositionen automatisch auf Status 1, welche ein Lieferdatum größer dem aktuellen Tagesdatum + Max. WBZ haben, da das System hier genügend Vorlauf für die Beschaffung hat. Sollte das Lieferdatum der Auftragsposition kleiner der WBZ sein, so bleibt die Auftragsposition in Status 2, wenn dies in der Auftragsart entsprechend hinterlegt ist. Ist das Lieferdatum größer der WBZ, so wird der Positionsstatus der Auftragsposiion immer auf Status 1 gesetzt, da genügend Zeit für die Wiederbeschaffung vorhanden ist. 

Mehr zum Thema Wiederbeschaffungszeit (WBZ) und deren Berechnung erfahren Sie im Kapitel Wiederbeschaffungszeit . 

Siehe Kapitel Wiederbeschaffungszeit . 

Tooltip: 

Hier geben Sie ein Limit für die maximale Wiederbeschaffungszeit ein, diese hat Einfluss auf die dynamische Verfügbarkeit.