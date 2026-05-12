---
chapter_id: "NV.ERP.MM.Production.cdParamProduction.shtConsiderMaterial"
topics: []
source: eNVenta 4.5 Onlinehilfe
---

# Kapitel NV.ERP.MM.Production.cdParamProduction.shtConsiderMaterial

Wenn dieser Parameter gesetzt ist, wird die Terminierung mit einer Materialzuordnung gebucht. Das bedeutet: die Terminierung einer Material- und Ressourcenverfügbarkeit wird unterstützt. Dabei werden 2 Fälle unterschieden: 

- Dem Arbeitsgang ist Material direkt zugeordnet. Es wird nur die Verfügbarkeit dieses Materials geprüft. - Material ist nicht direkt zugeordnet. In diesem Fall wird die Verfügbarkeit des gesamten Materials des entsprechenden Betriebsauftrags geprüft. Ist ein Beschaffungsmaterial nicht vorhanden, so wird die Wiederbeschaffungszeit dynamisch berechnet. Der früheste Termin ist dann der heutige Tag + Wiederbeschaffungszeit. Besteht für ein Material bereits ein laufender Bestellvorgang, so wird das Lieferdatum dieses Bestellvorgangs zugrundegelegt. Handelt es sich bei einem Material um eine Baugruppe mit noch nicht abgeschlossener Produktion, so wird das Enddatum der Terminierung oder ggf. das eingetragene Lieferdatum zugrundegelegt. Teilverfügbarkeiten reichen für den Produktionsstart nicht aus. Es wird immer vollständige Verfügbarkeit vorausgesetzt. 
Achtung: Grundsätzlich kann die Materialverfügbarkeit nur im Fall der Vorwärtsterminierung geprüft werden. 

Siehe Kapitel Materialverfügbarkeit . 

Tooltip: 

Wenn diese Checkbox gesetzt ist, wird die Terminierung mit einer Materialzuordnung gebucht. 
Das bedeutet: die Terminierung einer Material- und Ressourcenverfügbarkeit wird unterstützt.