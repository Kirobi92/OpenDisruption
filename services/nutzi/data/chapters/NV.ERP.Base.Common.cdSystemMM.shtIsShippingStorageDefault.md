---
chapter_id: "NV.ERP.Base.Common.cdSystemMM.shtIsShippingStorageDefault"
topics: []
source: eNVenta 4.5 Onlinehilfe
---

# Kapitel NV.ERP.Base.Common.cdSystemMM.shtIsShippingStorageDefault

Mit diesem Parameter können Sie die Vorbelegung der Lagerauswahl für die Verfügbarkeitsprüfung in den Verkaufsbelegen steuern. Ist der Parameter gesetzt, wird die Checkbox Fix beim Öffnen des Dialogs Auftrag aktiv vorbelegt. In diesem Fall soll der Verkaufsmitarbeiter nicht den Lagerort ändern, sondern vom voreingestellten Lager (Ermittlung über Kunde, Kundenanschrift, Sachbearbeiter) die Ware verkaufen. Ziel ist es, dass nur über den Dialog Verfügbarkeit ein Lagerwechsel möglich ist. Nur dort soll entschieden werden, ob eine Direktlieferung von einem abweichenden Lager oder eine Umlagerung oder eine Lieferung per Strecke stattfindet. 

Der Parameter Vorgabe ist „Uml. Bezugslager“ wird durch die Checkbox kein Bezugslager (z.B. in den Auftragsarten oder im Sachbearbeiterstamm ) übersteuert. Ist diese gesetzt, so findet keine Vorbelegung der Checkbox Fix in Auftrag/Angebot/Gutschrift statt. In diesem Fall ist das jeweils eingestellte Lager nur eine Vorbelegung. Jedes Lager kann dann potentiell ein Versandlager sein. 

Falls im Auftrag eine Versandanschrift übernommen wird, für die die Checkbox Kein Bezugslager gesetzt ist, wird die Checkbox Fix ggf. deaktiviert! 

Wird die nachträglich übernommene Lieferadresse wieder gelöscht, erfolgt eine Prüfung entsprechend folgender Hierarchie: 
- Existiert eine gültige Adresse aus der Versandanschrift (Stamm) - egal ob in der Rechnungs- oder Versandanschrift, werden diese Daten vorbelegt. - Wenn nicht, werden die Informationen aus dem Kundenstamm genommen. - Egal, welche Anschrift die Einstellung an der Auftragsart für Versandweg hat (wenn ein Wert enthalten ist), sie übersteuert die Einstellung. 

Tooltip: 

Bei der Auftrags- und Angebotserfassung wird die Funktion zur 
Vorbelegung der Checkbox "fix" - Umlagerung Bezugslager aktiv. 

Dabei wird die Checkbox "fix" nach folgender Hierarchie gesetzt: 
- Versandlager Lieferadresse 
- Versandlager Kundenstamm 
- Dynamische Zuordnung über PLZ