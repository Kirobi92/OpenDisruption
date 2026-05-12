---
chapter_id: "NV.ERP.Base.Common.cdSystemMM.shtBatchOriginStrict"
topics: []
source: eNVenta 4.5 Onlinehilfe
---

# Kapitel NV.ERP.Base.Common.cdSystemMM.shtBatchOriginStrict

Wenn Sie diesen Parameter setzen, wird geprüft, ob die Kombination Lieferant + Chargennummer + Ursprungscharge lagerübergreifend eindeutig ist. Ist dies nicht der Fall, erhalten Sie eine Fehlermeldung, die Sie auffordert, die Charge mit einer neuen Ursprungschargennummer zu erfassen. 

Des Weiteren wird die eNVenta -Chargennummer beim Chargenzugang nicht mehr manuell angegeben, solange der Parameter gesetzt ist. 

Die Chargennummer wird automatisch über einen Nummernkreis gezogen. 

Siehe Kapitel Nummernkreise Einkauf . 

In der Praxis ist es oft so, dass die gelieferte Chargennummer des Lieferanten alphanumerisch ist und durch den gesamten Lebenszyklus des Artikels bis zum Endkunden nachverfolgbar sein muss. Dies kann die Chargenummer von eNVenta als „reine Verwaltungsebene“ nicht gewährleisten und daher wird mit Hilfe dieses Parameters die Bedeutung der Ursprungscharge hervorgehoben. 

Bei Angabe der Ursprungs-Charge ermittelt eNVenta , ob diese bereits unter einer eNVenta -Charge eingebucht wurde (über alle Läger). Wenn ja , wird diese Chargennummer für die Zubuchung vorbelegt. 

Tooltip: 

Dieser Parameter prüft, ob die Kombination 'Lieferant + Chargennummer + Ursprungscharge' lagerübergreifend eindeutig ist. 
Ist dies nicht der Fall, erhalten Sie eine Fehlermeldung, die Sie auffordert, die Charge mit einer neuen Ursprungschargennummer zu erfassen.