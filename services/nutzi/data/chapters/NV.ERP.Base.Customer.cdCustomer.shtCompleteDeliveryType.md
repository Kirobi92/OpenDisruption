---
chapter_id: "NV.ERP.Base.Customer.cdCustomer.shtCompleteDeliveryType"
topics: []
source: eNVenta 4.5 Onlinehilfe
---

# Kapitel NV.ERP.Base.Customer.cdCustomer.shtCompleteDeliveryType

eNVenta unterstützt das Komplettlieferverfahren nur bis zum Packlistendruck! 

Hier wird das Komplettlieferverfahren ausgewählt. 

Die Combobox bietet folgende Selektionsmöglichkeiten: 

- Leer - Komplett kommissionieren und liefern - Vorab kommissionieren und komplett liefern - Erstlieferung normal, Rückstand komplett liefern 
Wird in der Combobox Kom.lief.verfahren nichts ausgewählt (bleibt leer), bedeutet dies Einzellieferung. 

Dabei ist zu beachten, dass als Prüfrahmen für die Komplettlieferlogik stets der einzelne Auftrag berücksichtigt wird. 

Die gewählte Einstellung in der Auftragsart wird in den Auftrag übernommen. 

Die Vorbelegung in den Auftragsarten hat Vorrang vor der Einstellung im Kundenstamm. D.h., ist in der Auftragsart nichts gewählt, wird geprüft, ob im Kundenstamm eine Auswahl getroffen wurde. 

Das Komplettlieferverfahren klammert Artikel aus, für die das Dispoverfahren 'kein Lager' gesetzt ist ( Artikel , Dispoverfahren 'kein Lager'). D.h. der Lieferschein kann gedruckt werden, auch wenn die Position 'ohne Lager' nicht kommissioniert wurde. Dies gilt nur, wenn für die anderen Positionen die Kriterien des Komplettlieferverfahrens erfüllt sind. 

Definition Komplett kommissionieren und liefern : 

Bei Komplett kommissionieren und liefern darf eine Packliste bzw. ein Lieferschein erst gedruckt werden, wenn ALLE Positionen den Status 2 haben (also genügend Ware für alle Positionen vorhanden ist). Teillieferungen sind damit komplett ausgeschlossen. 

Definition Vorabkommissionieren und komplett liefern : 

- Packliste darf immer gedruckt werden. Lieferschein erst, wenn alle Positionen des Auftrags enthalten sind (Status 2). - Keine Berücksichtigung von Sammelpacklisten. 
Definition Erstlieferung normal, Rückstand komplett liefern : 

Bei der Ausprägung 4 (Erstlieferung normal, Rückstand komplett liefern) werden alle lieferfähigen Auftragspositionen für den Erstpacklistendruck oder Erstlieferscheindruck zugelassen (wie Einzellieferung). Sobald es eine Position mit einer Lieferscheinnummer gibt, werden die restlichen Positionen erst komplett (wenn alle Positionen im Status 2 sind) ausgeliefert. 

Wenn das LVS im Einsatz ist, ist zwingend an einen Komplettplatz zu kommissionieren. 

Wenn in den Verkaufsparametern (Registerkarte Druck ) der Haken bei Sammelpackliste / Sammellieferschein gesetzt ist, werden die Varianten 3 und 4 ausgeblendet. 

Wenn für die Verfahren 2 und 3 auch nur eine Position mit einem Rückstandskennzeichen vorhanden ist, kann kein Lieferschein gedruckt werden! 

Außerdem findet eine Prüfung statt, falls bereits Werte zugeordnet waren und die Kennung in den Parametern gesetzt wurde. 

Weitere Informationen: 

- Gehört ein bestimmter Beleg logisch zu einer Sammel-Belegdrucksituation und verstoßen einzelne Positionen desselben gegen die 'Komplettlogik', dann werden ALLE in Frage kommenden Positionen dieses Beleges komplett aus dem Sammeldruck-Vorgang herausgenommen. - Ein nachträgliches Umschalten der Komplettlieferungs-Combobox auf einen anderen Modus ist zu jedem Zeitpunkt uneingeschränkt erlaubt, da sich die dadurch ergebenden neuen Restriktionen erst beim nächsten LS-Druck auswirken und dann zu diesem Zeitpunkt abgeprüft werden können. - Der Fall 3 (vorab kommissionieren und komplett liefern) wird zunächst nur als Option der vorgenannten Combobox angeboten, ohne dass hier eine besondere Logik damit verbunden ist. 
Aufgrund dieses Komplettkennzeichens gibt es in der Positionsübersicht die Möglichkeit, nach diesem zu selektieren (Combobox Kom.lief.verfahr. ). 

Mehr Informationen hierzu finden Sie im Kapitel Komplettlieferverfahren . 

Tooltip: 

Hier wählen Sie das Komplettlieferverfahren aus: 

• komplett kommissionieren und liefern 
• vorab kommissionieren und später komplett liefern (bei Massendruck nicht berücksichtigt) 
• Erstlieferung normal, Rückstand komplett liefern (bei Massendruck nicht berücksichtigt)