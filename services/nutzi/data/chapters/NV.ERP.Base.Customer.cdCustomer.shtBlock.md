---
chapter_id: "NV.ERP.Base.Customer.cdCustomer.shtBlock"
topics: []
source: eNVenta 4.5 Onlinehilfe
---

# Kapitel NV.ERP.Base.Customer.cdCustomer.shtBlock

Hier wird der Status des Kunden festgelegt. Folgende Status stehen zur Verfügung: 

- Normal : Alle Funktionen stehen für den Kunden zur Verfügung. - Gesamtsperre : Es können keine Vorgänge zum Kunden erfasst werden. - Liefersperre : Zum Kunden können zwar Aufträge erfasst, aber keine Lieferungen ausgeführt werden. - Fakturasperre : Für den Kunden können Lieferscheine gedruckt werden. Achtung: aber keine Rechnungen. 
In der Finanzbuchhaltung haben diese Status keine Auswirkungen! 

Wird in den Mahnparametern (Combobox Art der Sperre ) eine Sperre für den Kunden gesetzt, wird diese in den Kundenstatus zurückgeschrieben. 

Siehe Kapitel Mahnparameter . 

Tooltip: 

0, leer = Normal 
1 = Gesamtsperre 
2 = Liefersperre 
3 = Fakturasperre