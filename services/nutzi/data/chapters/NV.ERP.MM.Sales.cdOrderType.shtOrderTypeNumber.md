---
chapter_id: "NV.ERP.MM.Sales.cdOrderType.shtOrderTypeNumber"
topics: []
source: eNVenta 4.5 Onlinehilfe
---

# Kapitel NV.ERP.MM.Sales.cdOrderType.shtOrderTypeNumber

Hier wird die Nummer der markierten Auftragsart aus der Tabelle angezeigt. 

Sie können auch eine neue Auftragsart definieren. Dazu geben Sie in dieses Feld eine weitere Nummer ein. Da alle bereits angelegten Auftragsarten auf der Registerkarte Tabelle angezeigt werden, können Sie leicht erkennen, welche Nummern noch frei sind. 

Eine separate Auftragsart ist immer dann zu verwenden, wenn der Nutzen einer neuen Auftragsart gegenüber dem dadurch entstehenden Overhead im Know-how-Aufbau überwiegt oder aber ein komplett eigenständiger Prozess damit abgewickelt werden soll. 

Grundsätzlich gilt: 

So viele Auftragsarten wie nötig, aber so wenige wie möglich! 

Beispiel: 
Bei einer Lagerauftragsart geht man normalerweise davon aus, dass ausreichend Ware verfügbar ist. Also wird eine solche Auftragsart üblicherweise so konfiguriert, dass bei der Erfassung vorhandene Ware bereits im Status 2, also Lieferfreigabe, erfasst wird. Ist die Ware bei der Erfassung aber nicht verfügbar, erhalten Sie eine Verfügbarkeitsabfrage. 

Das bedeutet zusätzliche Klicks. 

Bei einem Beschaffungsauftrag geht man davon aus, dass die Ware nicht verfügbar ist. Sie könnten das nun über die normale Lagerauftragsart abbilden, müssten dann aber bei jeder Position die Verfügbarkeitsabfrage durchlaufen. 

Alternativ dazu kann aber auch eine eigene Auftragsart Beschaffungsauftrag definiert werden, bei der die Erfassung der Positionen im Status 1 erfolgt und kein Verfügbarkeitsdialog aufgeht. 

Im Projekt ist nun zu entscheiden, was sinnvoller ist. 

Tooltip: 

Zeigt die Nummer der gewählten Auftragsart aus der Tabelle.