---
chapter_id: "NV.ERP.Base.Common.cdParameterFI.shtAutomAccountingArea"
topics: []
source: eNVenta 4.5 Onlinehilfe
---

# Kapitel NV.ERP.Base.Common.cdParameterFI.shtAutomAccountingArea

Wenn Sie diesen Parameter aktivieren, wird beim Einfügen der Kontonummer und evtl. des Betrags (positiv bzw. negativ) im Dialog Buchen automatisch der richtige Buchungskreis ermittelt. Der Parameter Buchungskreis im Buchen ist dann unzugänglich. 

Die automatische Buchungskreiserkennung kann im Dialog Buchen über das Menü Optionen >> Autom. Buchungskreiserkennung aktiviert bzw. deaktiviert werden. 

Die Automatische Buchungskreiserkennung macht nur Sinn, wenn die Nummernkreise sauber gepflegt sind, d.h. es darf keine Überschneidungen bei den Konten geben! 

Wenn ein Konto im Hauptbuch und als Personenkonto existiert (bzw. als Debitor und als Kreditor), kann über den Kontoauswahl-Dialog (alle Registerkarten offen) das gewünschte Konto ausgewählt und damit der Kontotyp bestimmt werden. 

Folgende Regeln gelten für die Bestimmung des Buchungskreises: 

Soll Haben Geldkonto* Steuerart* = Buchungskreis 
| | | | | |
| --- | --- | --- | --- | --- |
| Sachkonto | Sachkonto | - | - | FB |
| Sachkonto | Debitor | 1 | - | DA |
| Sachkonto | Debitor | - | M / X | DG |
| Debitor | Sachkonto | - | M / X | DR |
| Debitor | Sachkonto | 1 | - | DZ |
| Sachkonto | Kreditor | 1 | - | KZ |
| Sachkonto | Kreditor | - | V / X | KR |
| Kreditor | Sachkonto | 1 | - | KA |
| Kreditor | Sachkonto | - | V / X | KG |

Zu beachten bei Sachkonto in Verbindung mit einem Personenkonto: 

Das Sachkonto MUSS eine der beiden o.g. Bedingungen erfüllen, ansonsten erhalten Sie eine Fehlermeldung. 

* Bedingung bezieht sich auf das Sachkonto. 

Tooltip: 

Wenn Sie diese Checkbox aktivieren, wird beim Einfügen der Kontonummer und 
evtl. des Betrags (positiv bzw. negativ) im Buchen-Dialog automatisch der richtige Buchungskreis ermittelt. 
Die Combobox 'Buchungskreis' im Buchen ist dann unzugänglich.