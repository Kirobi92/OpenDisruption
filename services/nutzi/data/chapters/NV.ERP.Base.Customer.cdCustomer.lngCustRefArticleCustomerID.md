---
chapter_id: "NV.ERP.Base.Customer.cdCustomer.lngCustRefArticleCustomerID"
topics: []
source: eNVenta 4.5 Onlinehilfe
---

# Kapitel NV.ERP.Base.Customer.cdCustomer.lngCustRefArticleCustomerID

Dieses Feld spielt eine Rolle in der Zusammenführung von Unternehmen in einer Gruppe. 

Wird ein Unternehmen in eine Gruppe integriert, so kommt es häufig vor, dass die Materialstämme zusammengeführt werden sollen. Hierbei kann es vorkommen, dass zum Teil noch mit alten Materialnummern bestellt wird und zum Teil schon mit Materialnummern des Mutter-Unternehmens. 

Aus diesem Grund ist es möglich, im Kundenstamm des Kunden A eine Referenz auf einen anderen Kunden B zu hinterlegen. So wird z.B. bei der Eingabe einer Materialnummer in der Auftragsposition, zunächst die Liste der Kundenartikelnummern des gewählten Kunden A durchsucht. Sollte hier keine Übereinstimmung gefunden werden, so wird zusätzlich in den Kundenartikelnummern des Kunden B nach der eingegebenen Kundenartikelnummer gesucht. 

Tooltip: 

Referenz-Kundennummer für die Artikelsuche über die Kundenartikelnummern.