---
chapter_id: "NV.ERP.Base.Common.cdSystemMM.shtEntriesPerInventoryPage"
topics: []
source: eNVenta 4.5 Onlinehilfe
---

# Kapitel NV.ERP.Base.Common.cdSystemMM.shtEntriesPerInventoryPage

Über diesen Parameter können Sie festlegen, wie viele Artikel auf eine Seite gedruckt werden sollen. Die Angabe der Anzahl Artikel sollte entsprechend gewählt werden, damit die passende Anzahl an Artikeln auf einer Seite dargestellt werden kann. Im Zweifelsfall sollte die Zahl entsprechend kleiner gewählt werden. Die Seite wird bereits bei der Initialisierung der Inventur festgeschrieben. 

Beispiel: Ist in den Parametern des Einkaufs die Anzahl Artikel pro Seite mit 9 angegeben, so wird mit dem ersten Datensatz begonnen und die Seite 1 zugewiesen. Alle folgenden Datensätze erhalten ebenso die Seite 1 zugewiesen, bis die „Grenze“ von 9 erreicht ist. Der 10te Datensatz erhält nun die Seite 2, usw. 

Aus diesem Grund gibt es in der Inventur die Spalte ‚Seite gedruckt‘. Hier wird angezeigt, auf welcher Seite sich die Inventurposition befindet. 

Tooltip: 

Einträge pro Inventurseite