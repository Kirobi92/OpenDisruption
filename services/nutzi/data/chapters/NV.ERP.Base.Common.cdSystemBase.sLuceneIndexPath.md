---
chapter_id: "NV.ERP.Base.Common.cdSystemBase.sLuceneIndexPath"
topics: []
source: eNVenta 4.5 Onlinehilfe
---

# Kapitel NV.ERP.Base.Common.cdSystemBase.sLuceneIndexPath

Hier geben Sie den Pfad für die Index-Dateien ein. Dazu sind entsprechende Schreibrechte erforderlich! 

Für jeden Mandanten muss ein separater Pfad festgelegt werden! 

Tooltip: 

Ein Dateiverzeichnis in dem Lucene die eNVenta-Daten indexiert und sucht. 
Achtung: 
- für jeden Mandanten muss ein separater Pfad (d.h. ein eigenes Verzeichnis) festgelegt werden! 
- das Verzeichnis sollte lokal auf dem selben Server liegen auf dem der Lucene Service läuft. Dadurch wird die Performance verbessert. 
(Bei mehreren Mandanten könnte jeweils ein eigenes Laufwerk verwendet werden, um die Performance zu verbessern) 
- der Lucene Service, d.h. der Prozess sollte Schreibrechte auf das Verzeichnis haben. 
- Bei Änderungen ist ein Neustart des Lucene-Service notwendig.