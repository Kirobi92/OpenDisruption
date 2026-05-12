---
chapter_id: "NV.ERP.Base.Common.cdSystemBase.shtMaxDateDeviation"
topics: []
source: eNVenta 4.5 Onlinehilfe
---

# Kapitel NV.ERP.Base.Common.cdSystemBase.shtMaxDateDeviation

Über dieses Feld kann die Anzahl der Jahre angegeben werden, um die maximale Abweichung in Jahren zu definieren. Auf diese Weise kann es bei nachgelagerten Analysen und Verarbeitung nicht zu einem "Überlauf" der Datenbank kommen, wenn z.B. Karenztage aufgerechnet werden sollen. 

Beispiel: 
- Parameter auf 10 gesetzt. - Wenn am 28.09.2019 ein Auftrag erfasst wird, können sowohl Lieferdatum als auch Wunschdatum nur im Zeitraum 28.9.2009 – 28.09.2029 liegen. - Selbiges gilt für die anderen Hauptbelege im EK und VK. - Also Angebot, Auftrag, Gutschrift, Anfrage, Bestellung, Belastung. - Selbiges gilt für Wareneingangsdatum, Rechnungsdatum (in der Rechnungsprüfung) 
Bei jedem Speichern eines EK/VK Belegs muss geprüft werden, ob das Liefer-/Wunschdatum geändert wurde. Wenn es außerhalb des zulässigen Bereiches liegt, wird das Speichern unterbunden. 

Tooltip: 

Dieser Wert definiert die maximal erlaubte Datumsabweichung vom Tagesdatum in Jahren in Verkauf und Einkauf. Der Maximalwert beträgt 100 Jahre und bezieht sich auf folgende Datumsfelder: 
Einkauf: Anfrage, Bestellung, Belastung, Wareneingang, Rechnungsprüfung (Lieferdatum, Wunschdatum, Rechnungsdatum, Wareneingangsdatum). 
Verkauf: Auftrag, Angebot, Gutschrift (Lieferdatum, Wunschdatum, Rechnungsdatum).