---
chapter_id: "NV.ERP.Base.Common.cdSystemMM.shtDeliveryNoteIdentity"
topics: []
source: eNVenta 4.5 Onlinehilfe
---

# Kapitel NV.ERP.Base.Common.cdSystemMM.shtDeliveryNoteIdentity

Ein vorschnelles Setzen dieses Parameters ändert die Kalkulationsbasis für Ihr komplettes Auftragswesen! 

Durch Setzen dieses Systemparameters erfolgen bereits beim Lieferscheindruck die Bestands- und wertmäßige Buchung des Lagerabgangs sowie die Neuermittlung des GEK’s und die bestands- und wertmäßige Reduzierung. 

Wenn Sie diesen Parameter aktivieren, ändern Sie den Buchungszeitpunkt der Lagerbuchung von der Faktura zum Lieferscheindruck. Das bedeutet, eine tiefgreifende Änderung Ihrer Prozesse. 

Für die Sicherstellung der Buchungen erfolgt beim Lieferscheindruck eine Umbuchung vom Versandlager auf ein virtuelles "Fakturalager" - dieses wird dann zum Zeitpunkt des Rechnungsdrucks entlastet. Über dieses Fakturalager erhalten Sie eine Übersicht, welche Ware versendet wurde, aber noch nicht fakturiert ist. 

Vergleichen Sie hierzu das Kapitel Lieferschein-Identitätspreisverfahren . 

Bei aktiviertem Lieferschein Identitätspreisverfahren können Sie in der Kasse beim Kassieren nicht die Funktion auf Rechnung bezahlen verwenden! 

Wenn Sie die Checkbox aktiviert haben und speichern, erhalten Sie nachfolgende Meldung: 

Achtung! 

Bei Aktivierung des Parameters "Lieferschein-Identitätspreisverfahren" werden alle Artikel mit Kennzeichen "Divers Artikel" auf Kalkulationsbasis "LEK" und alle anderen Artikel auf Kalkulationsbasis "GEK" gesetzt. 

Dieser Vorgang kann längere Zeit dauern. 

Dies hat Auswirkungen auf die gesamte Margenberechnung und weitere Prozesse. Wenn Sie sich nicht sicher sind, so wenden Sie sich bitte an Ihren Administrator. 

Wollen Sie trotzdem fortfahren? 

Tooltip: 

Wenn die Checkbox gesetzt ist, erfolgt bereits beim Lieferscheindruck die Ermittlung 
des GEK’s und die bestands- und wertmäßige Reduzierung.