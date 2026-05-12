---
chapter_id: "NV.ERP.MM.Production.cdProductionType.shtTransferPTAsLPP"
topics: []
source: eNVenta 4.5 Onlinehilfe
---

# Kapitel NV.ERP.MM.Production.cdProductionType.shtTransferPTAsLPP

Diese Checkbox steht zur Verfügung, da es aus Vertriebsgründen sinnvoll ist, dass Selbstkosten im Betriebsauftrag kalkuliert werden. So kann es dem Kunden überlassen werden, ob bei auftragsbezogener Produktion die Selbstkosten (im Sinne der Ermittlung des Deckungsbeitrags) als Herstellkosten betrachtet und gezogen werden. 

Wenn Sie diese Checkbox setzen, werden alle Herstellkosten als LEK in den Artikelstamm übertragen. 

Im Betriebsauftrag werden die Herstell- und Selbstkosten separat ausgewiesen. 

Diese Funktion ist allerdings aus steuerlichen Gründen mit Vorsicht zu benutzen, da im Fall einer Bestandsbewertung nur die Herstellkosten angesetzt werden dürfen. 

Ablauf: 
Die Kalkulation läuft unabhängig des Parameters immer im Betriebsauftrag mit. Nur bei der Buchung der EK-Kosten in den Auftrag bzw. in den Artikelstamm erfolgt eine Unterscheidung, ob die Sollkosten (letzte Zeile) oder die Herstellkosten (ohne Gemeinkostenzuschlag für Verwaltung und Vertrieb) als EK gebucht werden sollen. 

Tooltip: 

Ist diese Checkbox aktiviert, dann werden die Herstellkosten als LEK übertragen.