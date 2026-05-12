---
chapter_id: "NV.ERP.Base.Customer.cdCustomer.shtStorageIDOrder"
topics: []
source: eNVenta 4.5 Onlinehilfe
---

# Kapitel NV.ERP.Base.Customer.cdCustomer.shtStorageIDOrder

Hier werden die Nummer und der Name des Lagers angegeben. 

Da die Auswahl eines Standardlagers an verschiedenen Stellen in eNVenta möglich ist, gilt folgende, in eNVenta festgelegte Prioritätenreihenfolge (1 ist die höchste Priorität): 

I. Für alle Versandwege gilt: 

- Versandlager aus der Auftragsart ( Stamm >> Verkauf >> Auftragsarten >> Lager ) - Wenn nicht, dann Versandlager aus der Tabelle Kunde ( Kunde >> Optionen >> Kundenlager ). - Wenn nicht, dann Lieferanschrift aus dem Auftrag (wird über die Standard-Versandanschrift des Kunden vorbelegt ( Kunde >> Versand ). - Wenn nicht dann Versandlager aus dem Kundenstamm ( Kunde >> Registerkarte Logistik >> Versandlager ). - Wenn nicht, dann PLZ Rechnungsanschrift aus dem Auftrag ( System >> Allgemein >> Postleitzahlen ). - Wenn nicht, dann Versandlager aus dem Sachbearbeiterstamm. - Wenn nicht, dann "Fallback"-Versandlager (erstes Nicht-Sperrlager). 
II. Unterscheidung nach Versandweg: 

Zufuhr: 
Wenn im Dialog Parameter Verkauf die Checkbox Vorgabe ist "Umlagerung Bezugslager" gesetzt ist, so wird versucht das Versandlager zu ermitteln: 

- Lieferanschrift Auftrag (wird über die Standard-Versandanschrift des Kunden vorbelegt ( Kunde >> Versand ). - Wenn nicht, dann Versandlager von LAKunde Auftrag ( Auftrag >> Lieferanschrift >> Versandlager ). - Wenn nicht, dann Versandlager Kundenstamm ( Kunde >> Registerkarte Logistik >> Versandlager ). - Wenn nicht, dann PLZ Lieferanschrift aus dem Auftrag ( System >> Allgemein >> Postleitzahlen ). - Wenn nicht, dann PLZ Rechnungsanschrift aus Auftrag ( System >> Allgemein >> Postleitzahlen ). 
Nur wenn kein Versandlager auf diesem Weg ermittelt werden konnte, zieht das Versandlager aus I. 

Strecke: 
Über das virtuelle Lager. Das virtuelle Streckenlager wird aus dem Default-Versandlager des Sachbearbeiters ermittelt. Sollte am Default-Versandlager kein eigenes Streckenlager definiert sein, so wird das Default-Streckenlager aus den Verkaufsparametern gezogen. 

Abholung: 
Versandlager Sachbearbeiterstamm, falls gegeben, sonst zieht das Versandlager aus I. 

Tooltip: 

Definiert das Lager