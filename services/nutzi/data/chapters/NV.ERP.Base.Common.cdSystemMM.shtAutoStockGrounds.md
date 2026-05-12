---
chapter_id: "NV.ERP.Base.Common.cdSystemMM.shtAutoStockGrounds"
topics: []
source: eNVenta 4.5 Onlinehilfe
---

# Kapitel NV.ERP.Base.Common.cdSystemMM.shtAutoStockGrounds

Für die automatische Lieferzuteilung bei Lagerplätzen für ein chaotisches Lager kann folgendes ausgewählt werden. 

- keine - alphabetisch - Plätze leeren - Logistik zweistufig - Individuell - LVS lagerspezfisch (wird dieses Verfahren gewählt, so ist zwingend eine sinnvolle Auslagerungsstrategie am Lagerort zu hinterlegen (Registerkarte LVS Entnahme ) 
Bei der Lieferfreigabe einer Auftragsposition auf einem chaotischen Lager erfolgt automatisch die Zuweisung, von welchem Lagerplatz die Artikel zu entnehmen sind. Hierbei erfolgt die Zuordnung auch verteilt über mehrere Lagerplätze, wenn nicht genügend Bestand des Artikels auf einem Lagerplatz vorhanden ist. 

Bei der alphabetischen Zuordnung erfolgt die Freigabe unter der Annahme, dass die Lagerplätze entsprechend physisch vorhanden sind, damit eine effektive Kommissionierung erfolgen kann, z.B. Gang A, Platz 5 wurde als Lagerplatz A5 im System hinterlegt. 

Bei der Einstellung „Plätze leeren“ wird immer versucht den Bestand der Lagerplätze zu minimieren, unabhängig der Angabe wo dieser Lagerplatz sich befindet. Dieses Verfahren hilft möglichst wenig Lagerplätze zu nutzen, sorgt aber meist für längere Wege in der Kommissionierung. 

Für die optimierte Kommissionierung über den Pickpool muss im Bereich Automatische Zuordnung bei Lieferfreigabe das Verfahren Logistik zweistufig eingestellt werden. 

Das Zuordnungsverfahren für Lagerplätze Logistik zweistufig ist folgendermaßen definiert: 

Zuerst wird aus dem Pickbereich des chaotischen Lagers Ware zugeordnet, wenn die Liefermenge 50% des Maximal-Bestands im Pickbereich nicht überschreitet. Sonst wird die Ware aus einem anderen Bereich, z.B. aus dem Hochregal zugewiesen. 

Der Pickbereich ist der Bereich des chaotischen Lagers, in dem die Fixplätze definiert sind. Auf diesem Platz muss auch der Maximal-Bestand gepflegt sein, damit die Berechnung der Liefermenge von 50% korrekt durchgeführt werden kann. 

Die Zuordnung der Plätze erfolgt mit der Lieferfreigabe der Auftragsposition. 

Plätze können, für den Fall, dass es sich nicht um Chargenartikel handelt, eine negative Verfügbarkeit bekommen. Um dies zu verhindern, empfehlen wir den Mindestbestand auf den Lagerplätzen zu pflegen. 

Bei der Einstellung „Logistik zweistufig“ müssen entsprechende Prioritäten der Lagerplätze vorhanden sein. So kann ein Lagerplatz als „Fixplatz“ für einen Artikel definiert sein und es wird versucht erst von diesem Lagerplatz die Ware zu entnehmen und ggf. diesen Lagerplatz zu einem späteren Zeitpunkt wieder aufzufüllen. Nur wenn eine Auftragsposition mehr Menge benötigt als auf dem Fixplatz vorhanden, so erfolgt die Zuordnung des Lagerplatzes direkt auf einen „Reserverplatz“. 

Tooltip: 

Für die automatische Lieferzuteilung bei Plätzen kann folgendes ausgewählt werden: 
- keine 
- alphabetisch 
- Plätze leeren 
- Logistik zweistufig 
- individuell 
- LVS lagerspezifsch