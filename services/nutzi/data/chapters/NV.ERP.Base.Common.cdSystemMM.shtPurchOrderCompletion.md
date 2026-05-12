---
chapter_id: "NV.ERP.Base.Common.cdSystemMM.shtPurchOrderCompletion"
topics: []
source: eNVenta 4.5 Onlinehilfe
---

# Kapitel NV.ERP.Base.Common.cdSystemMM.shtPurchOrderCompletion

Wenn Sie diesen Parameter aktivieren, wird die Abschlusslogik aktiviert. Beim Speichern des Vorgangs wird automatisch die Gesamtsperre gesetzt, sie kann nicht manuell verändert werden. In Bestellung , Anfrage und Belastung wird die Registerkarte Abschluss aktiv. 

Folgendes wird dabei geprüft: 

- Bei auftragsbezogenen Bestellungen wird die Übereinstimmung der bestellten Mengen geprüft. - Überprüfung der Wiederbeschaffungszeit im Vergleich zum Soll-Liefertermin. - Ist der Mindestbestellwert erreicht? - Werden die Frachtfreigrenzen erreicht? 
Gibt es keine Fehler, kann mit dem Button Abschluss die Bestellung freigegeben werden. 

Die Sperre kann manuell nicht aufgehoben werden; sie kann nur über den Button Abschluss aufgehoben werden. 

Tooltip: 

Hiermit aktivieren Sie den Bestellabschluss. In der Bestellung wird die Registerkarte 'Abschluss' aktiviert.