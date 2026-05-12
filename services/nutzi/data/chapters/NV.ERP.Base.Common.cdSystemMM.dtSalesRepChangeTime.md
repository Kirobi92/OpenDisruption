---
chapter_id: "NV.ERP.Base.Common.cdSystemMM.dtSalesRepChangeTime"
topics: []
source: eNVenta 4.5 Onlinehilfe
---

# Kapitel NV.ERP.Base.Common.cdSystemMM.dtSalesRepChangeTime

Hier kann ein genauer Zeitpunkt eingetragen werden, wann der Wechsel auf einen anderen Vertreter über den Job-Server stattfinden soll. Dies vor dem Hintergrund, dass es nicht zu Überschneidungen in der Zuordnung kommt, da diese Änderungen nachts, zeitgesteuert über den Job-Server laufen. Der Vertreterwechsel erfolgt für Bestandsdaten automatisch, wenn zusätzlich auch die Checkbox Vetreterwechsel soll Bestandsdaten aktualisieren gesetzt ist. 

Der Umsatz des Vorjahrs ist bei Vertretern für die Zielvorgabe des jeweils folgenden Jahres. In eNVenta wird die Änderung der Vertreterzuordnung zu einem Kunden in genau diesem Moment wirksam. Alle Aufträge werden ab dem Zeitpunkt dem neu zugeordneten Vertreter zugerechnet, alle Aufträge davor dem alten Vertreter. 

Diese Herangehensweise kann zur Folge haben, dass der ursprünglich zugeordnete Vertreter "bestraft" wird, weil der Umsatz, den er bis zum Zeitpunkt der Umstellung gemacht hat, im folgenden Jahr Teil der Zielvorgabe wird, obwohl er mit dem Kunden keinen Umsatz mehr machen kann. Im umgekehrten Fall hat derjenige Vertreter, der den Kunden zugeschrieben bekommt, einen Vorteil, weil der Umsatz, den er mit dem neu zugeordneten Kunden machen wird, automatisch zu seinem Umsatz dazukommt. Dadurch kann er das Umsatzziel für das folgende Jahr leichter erreichen. Um dieses Problem zu umgehen, erfolgt mittels des Job-Eintrags eine nachträgliche Umstellung der Vertreterzuordnung auf den alten Vorgängen. (Die entsprechenden Vertreterabrechnungen sollten zuvor getätigt sein – eine Rückumstellung ist nicht machbar.) 

Der eigentliche Job-Eintrag erfolgt dann bei Änderung des Vertreters im Kundenstamm und mit Speichern. In dem Moment werden alte und neue Vertreternummer im Job mit der in den Parametern hinterlegten Uhrzeit abgesetzt. 

Dieser Job wird ohne Job-Server-Gruppe angelegt! Dazu muss sichergestellt sein, dass ein Job-Server existiert, der guppenlose Jobs bearbeitet. 

Ist keine Uhrzeit gepflegt, wird ein Job ohne Uhrzeit angelegt. Dieser ist dann zwingend manuell auszuführen. 

Wird im selben Kundenstammdatensatz der Vertrter erneut geändert, bevor die zuvor gemachte Änderung (durch den Job) in den Belegen aktualisiert wurde, wird ein weiterer Job als Folge-Job angelegt. So wird sichergestellt, dass die Aktualisierung in den Belegen immer in der korrekten Reihenfolge durchgeführt wird. 

Es werden alle Aufträge (Angebote und Gutschriften) des Kunden geladen, bei denen der ursprüngliche Vertreter (vor der Änderung im Kundenstamm) in den Feldern Vertreter 1-3 hinterlegt ist. Diese werden mit der neuen Vertreternumer überschrieben. 

Schlägt die Aktualisierung eines Belegs fehl (eine Fehlermeldung erscheint dann beim Speichern), wird die Änderung für alle Belege des Kunden rückgängig gemacht. Die Fehlermeldung wird im Job-Protokoll aufgeführt. Der Job wird als fehlerhaft gekennzeichnet. Diese Fehlermeldung lautet: "Der Vertreterwechsel von Kunde xy konnte nicht durchgeführt werden." 

Der Job kann jederzeit manuell über den Dialog Job Übersicht neu angestoßen werden. 

Alle Vorgänge werden dann zur vorgesehenen Zeit von der alten auf die neue Nummer umgeschlüsselt. 

Gab es bei dem Kunden bisher keine Vertreterzuordnung, so ist auch kein Eintrag in die bestehenden Vorgänge vorzunehmen und demzufolge auch kein Job zu erstellen. 

Tooltip: 

Um diese Uhrzeit werden Vertreterwechsel in Bestandsdaten aktualisiert.