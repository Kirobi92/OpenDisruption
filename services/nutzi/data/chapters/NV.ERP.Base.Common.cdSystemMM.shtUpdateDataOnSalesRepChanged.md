---
chapter_id: "NV.ERP.Base.Common.cdSystemMM.shtUpdateDataOnSalesRepChanged"
topics: []
source: eNVenta 4.5 Onlinehilfe
---

# Kapitel NV.ERP.Base.Common.cdSystemMM.shtUpdateDataOnSalesRepChanged

Wenn Sie diese Checkbox aktivieren, erfolgt der Vertreterwechsel für Bestandsdaten automatisch. Bei Wechsel der Zuständigkeit für den Kunden können auf Basis dieses Parameters die bestehenden Vorgänge auf den geänderten Vertreter übernommen werden. (Lesen Sie dazu noch die Dokumentation zum Feld Zeit Vertreterwechsel (hh:mm) . ) 

Die Aktualisierung der Bestandsdaten erfolgt asynchron mittels Job-Server, meist außerhalb der Arbeitszeiten, siehe Feld Zeit Vertreterwechsel . Der Job-Eintrag erfolgt bei Änderung des Vertreters im Kundenstamm. Dieser Job wird ohne Job-Server-Gruppe angelegt! Dazu muss sichergestellt sein, dass ein Job-Server existiert, der gruppenlose Jobs bearbeitet. 

Ist keine Uhrzeit gepflegt, wird ein Job ohne Uhrzeit angelegt. Dieser ist dann zwingend manuell auszuführen (Feld Zeit Vertreterwechsel ). 

Wird im selben Kundenstammdatensatz der Vertreter erneut geändert, bevor die zuvor gemachte Änderung (durch den Job) in den Belegen aktualisiert wurde, wird ein weiterer Job als Folge-Job angelegt. So wird sichergestellt, dass die Aktualisierung in den Belegen immer in der korrekten Reihenfolge durchgeführt wird. 

Der Job kann jederzeit manuell über den Dialog Job Übersicht neu angestoßen werden. 

Jobs werden nicht automatisch gelöscht. 

Wenn der Parameter nicht gesetzt ist, müssen die Daten manuell oder per Skript angepasst werden. 

Bei einem Vertreterwechsel ohne diesen gesetzten Parameter zur Aktivierung, wird an den Bestandsdaten keine Änderung vorgenommen / kein Job angelegt. Der Vertreter wird dann nur bei Neuerfassung gezogen. 

Tooltip: 

Vertreterwechsel soll Bestandsdaten aktualisieren