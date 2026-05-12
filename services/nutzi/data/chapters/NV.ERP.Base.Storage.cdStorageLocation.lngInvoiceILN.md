---
chapter_id: "NV.ERP.Base.Storage.cdStorageLocation.lngInvoiceILN"
topics: []
source: eNVenta 4.5 Onlinehilfe
---

# Kapitel NV.ERP.Base.Storage.cdStorageLocation.lngInvoiceILN

Hier können Sie eine ILN für Rechnungen eingeben. Dieses Feld ist dafür gedacht, dass Unternehmen für eigene oder andere Standorte einkaufen können (auch auf elektronischem Weg). 

Diese ILN wird zusammen mit der Lieferadresses des Lagerorts an den jeweiligen EDI-Partner übermittelt. Maßgeblich ist dabei die Lagernummer der jeweils ersten Bestellposition. 

Ist dieses Feld gefüllt, wird als Rechnungs-ILN nicht die ILN des Haupthauses übermittelt sondern die Rechnungs-ILN des jeweiligen Lagerortes. Ist auf Lagerortebene keine Rechnungs-ILN hinterlegt, so zieht der Standard (ILN des Haupthauses). 

Ausnahme: Es wird eine Lieferanschrift in der Bestellung hinterlegt. Dann wird diese übertragen und es findet keine Übermittlung der Lagerort-ILN/Firmenstamm-ILN statt. 

Hierbei dürfen die Rechnungs-ILNs für verschiedene Lagerorte identisch sein. 

Hintergrund: Es kann vorkommen, dass ein Lager als Rechnungsadresse auch für verschiedene "Unterläger" fungiert. In dem Fall wird die Rechnungs-ILN des Lagers, an das die Rechnung ausgestellt werden soll, übermittelt. So kann z.B. das Lager 10 mit der Rechnungs-ILN 4711 Rechungsadresse für das Lager 11 und 12 sein. In dem Fall würde bei Lager 11 und 12 ebenfalls die Rechnungs-ILN 4711 hinterlegt. 

Tooltip: 

Angabe der Internationalen Lokationsnummer (ILN)