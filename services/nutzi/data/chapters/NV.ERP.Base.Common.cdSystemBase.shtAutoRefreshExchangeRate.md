---
chapter_id: "NV.ERP.Base.Common.cdSystemBase.shtAutoRefreshExchangeRate"
topics: []
source: eNVenta 4.5 Onlinehilfe
---

# Kapitel NV.ERP.Base.Common.cdSystemBase.shtAutoRefreshExchangeRate

Im Verkauf: 
Zum Zeitpunkt der Fakturierung eines Fremdwährungsauftrags wird bei gesetztem Parameter der Kurs neu in den Auftrag bzw. in die Bestellung eingetragen. Es wird keine Neukonditionierung des Auftrags vorgenommen, aber eine Neukalkulation auf Positionsebene. Enthält der Auftrag bzw. die Bestellung bereits andere Positionen in Status 4, darf keine Aktualisierung stattfinden. Hierbei wird der zum Zeitpunkt des Drucks gültige Kurs aus der Währungstabelle gelesen und im Vorgang gespeichert. 

Bei Sammelrechnung / -bestellung wird jeder Auftrag / jede Bestellung einzeln auf Teilfakturierung geprüft und auch der Kurs wird entsprechend eingetragen. 

Die Kursaktualisierung findet nicht nur beim Rechnungsdruck statt, sondern auch beim Druck der Proforma-Rechnung. Im Einkauf erfolgt die Aktualisierung analog bei Freigabe der Rechnungsprüfung. 

Ebenso werden der EK und die Nebenkosten in der Positionskalkulation neu eingelesen; diese werden nur umgerechnet angezeigt, in der Datenbank stehen die Beträge in Systemwährung. 

Im Einkauf: 
Der Parameter wird genutzt, um bei einer Fremdwährungsrechnung bei der Rechnungsprüfung einen aktuellen Kurs zu erhalten. 

Da eine Rechnungsprüfung mehrere Bestellungen beinhalten kann, die evtl. bereits teilgeliefert oder teilberechnet sind, muss der Kurs zu jeder Bestellung, die in der Rechnungsprüfung aufgeführt ist, eingetragen werden. Allerdings nur wenn eine Berechnung in den einzelnen Bestellungen noch nicht erfolgt ist, d.h. es darf keine Position mit Status > 3 sein. 

Das gilt auch für Belastungen! 

Tooltip: 

Wird die Checkbox gesetzt, wird der Kurs zum Zeitpunkt der Fakturierung neu in den Auftrag oder die Bestellung eingetragen.