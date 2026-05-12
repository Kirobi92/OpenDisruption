---
chapter_id: "NV.ERP.Base.Common.cdSystemMM.shtPostProcessingStorage"
topics: []
source: eNVenta 4.5 Onlinehilfe
---

# Kapitel NV.ERP.Base.Common.cdSystemMM.shtPostProcessingStorage

Hier erfolgt eine Vorbelegung des Nachbearbeitungslagers für den zweistufigen Wareneingang. Nach der Buchung der 1. Stufe des Wareneingangs wird bei einer QKZ > 1 die Ware nicht auf das Lager der Bestellposition, sondern auf dieses angegebene Nachbearbeitungslager gebucht. 

Um die Ware wieder an den Lieferanten zurückzusenden, muss eine entsprechende Belastung auf das Nachbearbeitungslager erfasst werden. Sollte die Ware "verschrottet" werden, so muss dies ebenfalls als Belastung über einen "Dummy-Lieferanten" gebucht werden. 

Die Angabe des Lagers wird im Wareneingang, in der Einlagerung bei der Retoure und bei Abschluss der Produktion übernommen. 

Das Nachbearbeitungslager darf nicht eines der Wareneingangslager sein und ist als Sperrlager in den Lagerorten zu kennzeichnen. Nachbearbeitungslager und Qualitätssicherungslager dürfen identisch sein. Beide Lager müssen eine statische Lagerverwaltung haben. 

Siehe Kapitel Buchen des Wareneingangs . 

Tooltip: 

Hier erfolgt eine Vorbelegung des Nachbearbeitungslagers für den zweistufigen Wareneingang.