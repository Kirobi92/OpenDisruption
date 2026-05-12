---
chapter_id: "NV.ERP.Base.Common.cdSystemBase.shtChronologicalStockReRating"
topics: []
source: eNVenta 4.5 Onlinehilfe
---

# Kapitel NV.ERP.Base.Common.cdSystemBase.shtChronologicalStockReRating

GEK = gewichteter mittlerer Einkaufspreis 

Dieser Parameter darf nicht im laufenden Betrieb aktiviert bzw. deaktiviert werden, da sonst die Kalkulationen teilweise nicht mehr nachvollziehbar sind! 

Wenn Sie diese Checkbox aktivieren, wird der GEK für jedes Lager einzeln und immer zum Zeitpunkt der Lagerbuchung ermittelt. Für die Kalkulationsbasis GEK im Artikelstamm wird immer der lagerspezifische GEK als Basis in den Auftrag übernommen. 

Wichtig ist, dass bei Aktivierung oder beim Speichern auch gleichzeitig das Fakturalager angegeben ist. Ohne ein Fakturalager kann der Parameter nicht gesetzt werden. 

Für einen GEK pro Artikel wird dieser Parameter nicht gesetzt. 

Mit Aktivierung des lagerspezifischen GEKs wird der Lagerwert geteilt durch den Buchbestand des Lagers je Lager als GEK gerechnet. 

Die Formel lautet: 
Lagerwert / Buchbestand = GEK pro Lager 

Bei jeder Lagerbuchung erfolgt eine Aktualisierung des Lagerwerts und der Nebenkosten in der Tabelle Lagerjournal . 

Lesen Sie dazu das Kapitel Lieferschein-Identitätspreisverfahren . 

Solange zum Beispiel auf einem neuen Lager noch keine Lagerbuchung stattgefunden hat, erfolgt ein Rückfall auf den GEK des Artikelstamms als lagerspezifischer GEK. 

Bei der lagespezifischen GEK-Ermittlung werden auch Nebenkosten pro Lager berechnet. 

Die Formel dafür lautet: 

Summierte Nebenkosten / Buchbestand = Nebenkosten pro Einheit. 

Nebenkosten pro Einheit x EK pro aus Artikelstamm = Nebenkosten in der Lagerliste (auf 2 Nachkommastellen gerundet). 

Siehe Kapitel GEK-Ermittlung . 

Wenn Sie die Checkboxen Zwischenkto EK und Manuelle Lagerbuch. mit GEK setzen möchten, ist zuerst die Checkbox Lagerspez. GEK-Ermittlung zu aktivieren. 

Wenn die Checkbox Lagerspez. GEK-Ermittlung deaktiviert wird, wird das Feld Max. Abw. GEK in den Einkaufsparametern geleert und deaktiviert. 

Tooltip: 

Aktivieren Sie die lagerspezifische GEK-Ermittlung, wenn für jedes Lager der GEK (gewichteter Einkaufspreis) separat ermittelt werden soll. In diesem Fall werden bei jeder Lagerbuchung der komplette Lagerwert und Lagerbestand separat ermittelt und geschrieben. Durch Division der Werte wird dann der lagerspezifische GEK ermittelt.