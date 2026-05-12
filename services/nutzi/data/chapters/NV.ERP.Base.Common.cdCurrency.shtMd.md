---
chapter_id: "NV.ERP.Base.Common.cdCurrency.shtMd"
topics: []
source: eNVenta 4.5 Onlinehilfe
---

# Kapitel NV.ERP.Base.Common.cdCurrency.shtMd

Standardmäßig ist der Parameter nicht gesetzt und die Landeswährung wird errechnet mit 

Fremdwährung * Kurs . 

Wird der Parameter gesetzt, errechnet sich die Landeswährung aus 

Fremdwährung / Kurs . 

Der Kurs wird dementsprechend verändert. 

Bei einer neuen Währung ist dieser Parameter zu setzen, damit der neue Kurs zum Euro richtig eingegeben werden kann. 

Wurde die Währung bereits einmal für eine Berechnung genutzt, so kann das Kennzeichen Division nicht geändert werden! 

Tooltip: 

Berechnung der Landeswährung erfolgt bei Parameter 
- Division deaktiv: Fremdwährung * Kurs 
- Division aktiv: Fremdwährung / Kurs 

Wird der Parameter gesetzt, wird die Division für die Berechnung des neuen Währungskurses aktiviert. 
- D.h. der Kurs wird als 'Mengennotierung' interpretiert 
- Andernfalls gilt der Kurs als 'Preisnotierung' 
Bemerkung: Die 'Preisnotierung' gibt an, wieviel EINE Fremd-Währungseinheit in Landeswährung wert ist. 
(Beispiel: LW = Euro, FW = US-Dollar: 1 US-Dollar kostet 0,80 Euro, d.h. Preisnotierung = 0,8) 
(Die Mengennotierung ist der Kehrwert der Preisnotierung, hier also 1/0,8 = 1,25)