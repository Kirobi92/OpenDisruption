---
chapter_id: "NV.ERP.Base.Common.cdParameterFI.shtReversalForNegativeOpenItems"
topics: []
source: eNVenta 4.5 Onlinehilfe
---

# Kapitel NV.ERP.Base.Common.cdParameterFI.shtReversalForNegativeOpenItems

Wenn dieser Parameter aktiviert ist, werden bei der Übernahme der Daten aus der Warenwirtschaft nur bei Debitoren-Gutschriften, analog deren Stornos, und Kreditoren-Belastungen das Soll/Haben-Kennzeichen im OP, sowie die Darstellung im Journal gedreht. 

Wenn dieser Parameter nicht aktiviert ist, werden alle Daten aus der Warenwirtschaft bei den Debitoren-Konten auf der Sollseite gebucht bzw. im OP mit Soll dargestellt, bei den Kreditoren-Konten auf der Habenseite gebucht bzw. im OP mit Haben dargestellt. D.h. auf der einen Seite werden die Belege gebucht und auf der anderen Seite die Zahlungsvorgänge. 

nicht aktiviert 
| Checkbox | = Standard | ==> aus der Wawi gibt es den Buchungskreis DG und KG nicht! | Wawi-Belege alle auf einer Kontoseite (Debitor im Soll / Kreditor im Haben |
| --- | --- | --- | --- |
| Checkbox aktiviert | = Ausnahme | ==> aus der Wawi gibt es den Buchungskreis DG und KG | Wawi-Belege für Rechnungen und Gutschriften bei Debitor und Kreditor auf verschiedenen Kontoseiten |

Tooltip: 

Wenn diese Checkbox aktiviert ist, werden bei der Übernahme der Daten aus der Warenwirtschaft nur bei Debitoren-Gutschriften, 
analog deren Stornos, und Kreditoren-Belastungen das Soll/Haben-Kennzeichen im OP, sowie die Darstellung im Journal gedreht. 

Wenn diese Checkbox nicht aktiviert ist, werden alle Daten aus der Warenwirtschaft bei den Debitoren-Konten auf der Sollseite 
gebucht bzw. im OP mit Soll dargestellt, bei den Kreditoren-Konten auf der Habenseite gebucht bzw. im OP mit Haben dargestellt. 
D.h. auf der einen Seite werden die Belege gebucht und auf der anderen Seite die Zahlungsvorgänge.