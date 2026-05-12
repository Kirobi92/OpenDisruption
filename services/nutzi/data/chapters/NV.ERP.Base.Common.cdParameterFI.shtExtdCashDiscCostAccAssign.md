---
chapter_id: "NV.ERP.Base.Common.cdParameterFI.shtExtdCashDiscCostAccAssign"
topics: []
source: eNVenta 4.5 Onlinehilfe
---

# Kapitel NV.ERP.Base.Common.cdParameterFI.shtExtdCashDiscCostAccAssign

(Bedeutung: erweiterte Kostenstellen- und Kostenträgerzuordnung Skontoausbuchung) 

Beim Ausbuchen von Differenzbeträgen für Debitoren und Kreditoren (damit Skontobeträge aus Warenkäufen in die Kostenrechnung einfließen können) über den Button Skonto im Dialog OP-Ausbuchung wird die Verschlüsselung bei aktiviertem Parameter wie folgt geprüft: 

- Sachkontenstamm - Steuerschlüssel - Währung 
Es wird nur auf die erste Kostenstelle / den ersten Kostenträger aus dem Sachkonto geprüft! 

Die Prüfung im Einzelnen: 

Kostenstellen: 
mit Kostenstellen-Zwang 
- Im ausgebuchten Beleg ist keine Kostenstelle hinterlegt. - Jetzt wird geprüft, ob im entsprechenden Skonto-Konto ( Sachkontenstamm , Registerkarte Kostenrechnung ) eine Kostenstellen-Verschlüsselung hinterlegt ist. - Wenn JA, wird diese in Bezug auf den Skonto verwendet. - Wenn NEIN, wird im entsprechenden Steuerschlüssel geprüft, ob dort eine Kostenstelle hinterlegt ist. - Wenn JA, wird diese verwendet. - Wenn NEIN, wird in der entsprechend verwendeten Währung nachgeschaut, ob dort eine Kostenstelle hinterlegt ist. - Wenn JA, wird diese verwendet. - Wenn NEIN, wird die Buchung mit der bereits vorhandenen Meldung abgewiesen. 
ohne Kostenstellen-Zwang 
Ablauf wie oben, dann aber ohne Kostenstelle. 

Kostenträger: 
mit Kostenträger-Zwang 
- Im ausgebuchten Beleg ist kein Kostenträger hinterlegt. - Jetzt wird geprüft, ob im entsprechenden Skonto-Konto ( Sachkontenstamm , Registerkarte Kostenrechnung ) eine Kostenträger-Verschlüsselung hinterlegt ist. - Wenn JA, wird diese in Bezug auf den Skonto verwendet. - Wenn NEIN, wird die Buchung mit der bereits vorhandenen Meldung abgewiesen. 
ohne Kostenträger-Zwang 
Ablauf wie oben, dann aber ohne Kostenträger 

Tooltip: 

Erweiterte Kostenstellen- /Kostenträger-Zuordnung bei Ausbuchung/Rückzahlung in Skonto-/Kursdifferenz-Buchung