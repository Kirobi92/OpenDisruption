---
chapter_id: "NV.ERP.Base.Common.cdSystemMM.shtCreditFromStatus"
topics: []
source: eNVenta 4.5 Onlinehilfe
---

# Kapitel NV.ERP.Base.Common.cdSystemMM.shtCreditFromStatus

Hier wählen Sie einen Mindeststatus für den Auftrag aus, für welche eine Gutschrift aus der Retoure heraus erstellt werden darf. Der Parameter soll sicherstellen, dass keine Gutschrift generiert wird, welcher nicht eine entsprechende Leistung gegenübersteht. Diese Logik greift nur bei der Generierung der Gutschrift aus der Retoure heraus, die Erstellung manueller Gutschriften oder die Generierung einer Nachlieferung aus der Retoure ist nicht betroffen. 

Der hier gewählte Mindeststatus findet auch Verwendung beim Kopieren eines Auftrags. 

Folgende Status stehen zur Auswahl zur Verfügung: 
1 - Offen 
2 - Lieferfrei 
3 - Fakturafrei 
4 - Fakturiert 

Tooltip: 

Hier wählen Sie einen Mindeststatus für den Auftrag aus. Eine Gutschrift wird erst dann aus der Retoure heraus generiert, 
wenn die zugrunde liegende Auftragsposition einen hinterlegten Mindeststatus erreicht hat. 
Diese Logik greift nur bei der Generierung der Gutschrift aus der Retoure heraus.