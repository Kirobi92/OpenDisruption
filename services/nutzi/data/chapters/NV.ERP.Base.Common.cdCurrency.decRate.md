---
chapter_id: "NV.ERP.Base.Common.cdCurrency.decRate"
topics: []
source: eNVenta 4.5 Onlinehilfe
---

# Kapitel NV.ERP.Base.Common.cdCurrency.decRate

Hier wird der aktuelle Kurs zur Landeswährung hinterlegt. Der Kurs bezieht sich immer auf eine Einheit der Währung. Der Kurs für die Landeswährung ist immer exakt 1, da er die Vergleichsbasis für die anderen Kurse darstellt. 

Die Terminprüfung für die Berechnung des Kurses einer Fremdwährung erfolgt in der Finanzbuchhaltung auf das Belegdatum! 

Tooltip: 

Hinterlegen Sie den aktuellen Kurs zur Landeswährung. 
- Wenn Sie den Kurs als 'Preisnotierung' pflegen wollen, dürfen Sie die Checkbox 'Division' nicht setzen. 
- Wenn Sie aber den Kurs als 'Mengennotierung' pflegen wollen, dann müssen Sie die Checkbox 'Division' setzen. 
Bemerkung: Die 'Preisnotierung' gibt an, wieviel EINE Fremd-Währungseinheit in Landeswährung wert ist. 
(Beispiel: LW = Euro, FW = US-Dollar: 1 US-Dollar kostet 0,80 Euro, d.h. Preisnotierung = 0,8) 
(Die Mengennotierung ist der Kehrwert der Preisnotierung, hier also 1/0,8 = 1,25)