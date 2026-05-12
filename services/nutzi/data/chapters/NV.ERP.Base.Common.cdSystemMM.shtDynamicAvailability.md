---
chapter_id: "NV.ERP.Base.Common.cdSystemMM.shtDynamicAvailability"
topics: []
source: eNVenta 4.5 Onlinehilfe
---

# Kapitel NV.ERP.Base.Common.cdSystemMM.shtDynamicAvailability

Wenn Sie diese Checkbox aktivieren, wird die dynamische Verfügbarkeit eingeschaltet. Diese Einstellung empfiehlt sich für Reservierungen, die sehr weit in der Zukunft liegen. Wenn der Parameter aktiv ist, wird die Ware nicht bereits fest für eine Auftragsposition reserviert, wenn noch genügend Zeit besteht, um die Ware rechtzeitig zu beschaffen. Nur, wenn der Liefertermin kleiner der Wiederbeschaffungszeit ist, wird die Reservierung fix zur Auftragsposition festgeschrieben. So wird trotz Reservierung eines Artikels die Verfügbarkeit erst dann reduziert, wenn die WBZ zuzüglich Karenztage erreicht ist. 

Liegt der Liefertermin außerhalb der Wiederbeschaffungszeit, wird der Status der Auftragsposition auf 1 gesetzt; ansonsten auf den Status gemäß der Auftragsart (z.B. 2 für Lieferfreigabe). 

Wichtig hierbei ist, die Beschaffungsprozesse rechtzeitig durchzuführen (z.B. über Bestellautomat und Job-Server), um zum notwendigen Zeitpunkt die Ware am Lager zu haben, bevor der Liefertermin der Auftragsposition erreicht ist. 

Die dynamische Verfügbarkeitsprüfung ist nur für Verfügbarkeitsprüfungen auf einzelne Lager möglich. 

Siehe Kapitel Dynamische Verfügbarkeitsprüfung . 

Tooltip: 

Wenn Sie diese Checkbox aktivieren, wird die dynamische Verfügbarkeit eingeschaltet. Diese Einstellung empfiehlt sich für Reservierungen, die sehr weit in der Zukunft liegen. So wird trotz Reservierung eines Artikels die Verfügbarkeit erst dann reduziert, wenn die WBZ zuzüglich Karenztage erreicht ist. 
Siehe Kapitel 'Dynamische Verfügbarkeitsprüfung'.