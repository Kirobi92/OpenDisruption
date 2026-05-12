---
chapter_id: "NV.ERP.Base.Common.cdSystemBase.shtProportionalWorthCorrCalc"
topics: []
source: eNVenta 4.5 Onlinehilfe
---

# Kapitel NV.ERP.Base.Common.cdSystemBase.shtProportionalWorthCorrCalc

Wenn diese Checkbox aktiviert ist, wird bei der Berechnung eines Lagerwertkorrekturbetrages nicht nur der eigentlich zu korrigierende historische Lagerbuchungssatz zu Grunde gelegt, sondern es werden auch alle auf diese folgenden Lagerbuchungen mitberücksichtigt. 

Andernfalls errechnet sich der Korrekturbetrag aus dem historische Lagerbuchungssatz allein.Mehr Informationen zur Lagerwertkorrektur erhalten Sie im Kapitel Lagerjournal . 

Wenn diese Checkbox gesetzt ist (nur zugänglich, wenn die Checkbox Lagerspez. GEK-Ermittlung aktiviert ist), dann werden alle Wertkorrekturen auf dem zu korrigierenden historischen Lagerbuchungssatz mitberücksichtigt. Andernfalls errechnet sich der Wertkorrekturbetrag ausschließlich aus dem zu korrigierenden historischen Lagerbuchungssatz, indem dieser in einer Parallelkalkulation (Zwischenrechnung) mit dem jetzt bekannten aktuellen Korrekturpreis versehen wird. Dann wird mit diesem ein alternativer neuer Lagerwert berechnet wird. Die Differenz zwischen diesem fiktiven ‚neuen Lagerwert‘ und dem tatsächlichen historischen Lagerwert ergibt dann den Wertkorrekturbetrag. 

Tooltip: 

Wenn aktiviert, dann wird bei der Berechnung eines Lagerwertkorrekturbetrages nicht nur 
der eigentlich zu korrigierende historische Lagerbuchungssatz zu Grunde gelegt, 
sondern es werden auch alle auf diesen folgenden Lagerbuchungen mitberücksichtigt. 
Andernfalls errechnet sich der Korrekturbetrag aus dem historische Lagerbuchungssatz allein. 
(Bem. diese Logik zieht erst für Daten die in Vers. >= 4.5 erfasst wurden)