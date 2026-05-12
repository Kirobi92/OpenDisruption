---
chapter_id: "NV.ERP.Base.Common.cdPaymentCondCustomer.decCashDiscount3"
topics: []
source: eNVenta 4.5 Onlinehilfe
---

# Kapitel NV.ERP.Base.Common.cdPaymentCondCustomer.decCashDiscount3

Skonto 1, Skonto 2, Skonto 3 legt die Prozentsätze der gewährten Skonti fest, z.B. Skonto 1 –3-, Skonto 2 –2-, Skonto 3 –1-. 

In Verbindung mit den Tagen bedeutet dies, dass bei einem Beleg, der diese Zahlungsbedingung hat, der erste Skonto-Abzug innerhalb Bezahlung von 7 Tagen 3%, Zahlung innerhalb von 10 Tagen 2% und Zahlung innerhalb von 14 Tagen 1% beträgt. 

Bezahlt der Kunde innerhalb dieser Fristen, errechnet eNVenta ERP den Skonto-Abzug beim Debitoren-Ausgleich automatisch, bzw. wird dieser beim Bankeinzug automatisch ermittelt. 

Der skontierfähige Betrag errechnet sich aus dem Bruttobetrag (inkl. MwSt.) minus Rabatt-Prozentsatz. 

Tooltip: 

Geben Sie einen Prozentsatz für das Skonto ein.