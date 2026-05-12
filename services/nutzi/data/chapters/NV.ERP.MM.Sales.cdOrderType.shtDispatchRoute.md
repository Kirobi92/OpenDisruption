---
chapter_id: "NV.ERP.MM.Sales.cdOrderType.shtDispatchRoute"
topics: []
source: eNVenta 4.5 Onlinehilfe
---

# Kapitel NV.ERP.MM.Sales.cdOrderType.shtDispatchRoute

Hier kann der Versandweg vorbelegt werden. Ist in der Auftragsart kein Versandweg vorgegeben, so wird standardmäßig leer = „Zufuhr/Anlieferung“ im Auftragskopf vorbelegt und damit auf die Auftragsposition übertragen. Dies kann in der einzelnen Auftragsposition nochmals übersteuert werden. Die Steuerungslogik des Versandwegs kann pro Position definiert werden. 

Versandweg Strecke: 

Ist eine Auftragsposition (nur Auftragsposition) mit Versandweg „Strecke“ gekennzeichnet, so werden mit Auftragsabschluss im Hintergrund automatisch alle notwendigen „Vorgänge“ erzeugt. Hierbei müssen folgende Fälle unterschieden werden: 

- Interne Strecke: das Bezugslager (das Lager, das auch über die Ware verfügt) und das Versandlager (von dem Lager soll die Ware versendet werden) weichen voneinander ab. Die Läger sind alle „eigene Läger“, damit keine IC-Läger (Läger eines Verbands) und der Versandweg ist ‚Strecke‘. So wird das Versandlager = Bezugslager und die Ware wird vom Bezugslager per Strecke direkt zum Kunden geschickt. Dies hat keinerlei Auswirkung auf zusätzliche Belege. Hier sind keine zusätzlichen Belege notwendig. - Lieferantenstrecke : das Bezugslager und das Versandlager weichen nicht voneinander ab. D.h. ist das Bezugslager leer und der Versandweg ist Strecke, soll die Ware vom Lieferanten direkt per Strecke zum Kunden geschickt werden. Mit dem Auftragsabschluss wird nun automatisch auf Basis der Positionsdaten (Lieferant, Einkaufsart, LEK,…) eine Streckenbestellung angelegt. Wobei hier für jeden Lieferanten jeweils eine Bestellung angelegt wird. Dabei wird ein „Verbundobjekt“ generiert, das die Vorgänge Auftrag und Bestellung zusammenhält. - Zentrallagerstrecke: ist das Lieferlager ein Lager, das als Autobestelllager definiert ist, z.B. EDE und ist dann der Versandweg ‚Strecke‘, soll die Ware vom Lieferanten (hier EDE) direkt per Strecke zum Kunden geschickt werden. Aus dem Lager werden der Lieferant, die Einkaufsart und der Versandweg in die Auftragsposition vorbelegt. Mit dem Auftragsabschluss wird nun auf Basis der Positionsdaten (Lieferant, Einkaufsart, LEK,…) automatisch eine Streckenbestellung angelegt. Dabei wird ein „Verbundobjekt“ generiert, das die Vorgänge Auftrag und Bestellung zusammenhält. - IC-Strecke: ist das Bezugslager ein Lager, das als IC-Lager (IC-Lager = Intercompany-Lager = Verbandslager) klassifiziert ist und der Versandweg ist Strecke, dann soll die Ware vom Verbandsmitglied direkt per Strecke zum Kunden geschickt werden. Aus dem Lager werden der Lieferant und die Einkaufsart in die Auftragsposition übernommen. Mit dem Auftragsabschluss wird nun automatisch auf Basis der Positionsdaten (Lieferant, Einkaufsart, LEK,…) eine Streckenbestellung angelegt und per IC-Adapter sofort an das Verbandsmitglied gesendet. Dabei wird ein „Verbundobjekt“ generiert, das die Vorgänge Auftrag, IC-Bestellung und IC-Auftrag zusammenhält. 
Über die Multileiste können für jeden Versandweg unterschiedliche „Preisgestaltungen“ vorgenommen werden. 

Frachtkosten fallen je nach Fall unterschiedlich an. 

Mehr zum Thema Streckengeschäft erhalten Sie im Kapitel Globalabschluss und Strecke . 

Versandweg Abholung: 

Ist eine Auftragsposition mit Versandweg „Abholung“ gekennzeichnet, so will der Kunde die Ware im Versandlager abholen. Hierbei müssen folgende Fälle unterschieden werden: 
- „eigenes Lager“: Für eine Abholung auf das eigene Lager muss nur der Logistikprozess soweit umgestellt werden, damit die kommissionierte Ware in dem Abholbereich bereitgestellt wird. Hierbei muss natürlich auf die Logik der „Express-Kommissionierung“, etc. geachtet werden. - „interne Lieferung auf Abhollager“: Das Bezugslager (das Lager, das die Ware auch verfügbar hat) und das Versandlager (von dem Lager soll die Ware versendet werden) weichen voneinander ab. Die Läger sind alle „eigene Läger“ und damit keine IC-Läger (Läger eines Verbands). Ist der Versandweg „Abholung“, werden - wie im Umlagerungskonzept - die entsprechenden Belege automatisch erzeugt. Beim Wareneingang wird aber sofort auf den Abholbereich umgelagert. - „Lieferung auf Abhollager“: läuft analog der Logik „interne Lieferung auf Abhollager“, nur dass hier ein IC-Prozess die Basis ist. 
Im Fall der Abholung werden keine Frachten (KIS) in den Datenbestand eingerechnet. Dafür werden die kalkulatorischen Kosten aus der „Werkslieferung“ eingesetzt. 

Versandweg Zufuhr/Anlieferung 

Ist eine Auftragsposition ( nur Auftragsposition) mit Versandweg „Zufuhr/Anlieferung“ gekennzeichnet, so kann der Kunde per Paketdienst oder eigenem LKW beliefert werden. 
- „eigenes Lager“: wird die Ware aus dem Lager (Bezugslager = Versandlager) entnommen, gilt der „normale Logistik-Prozess“. Der Prozess wird entsprechend in der Logistik beschrieben. - „interne Lieferung“: das Bezugslager (das Lager, das die Ware auch verfügbar hat) und das Versandlager (von dem Lager soll die Ware versendet werden) weichen voneinander ab. Die Läger sind alle „eigene Läger“ und damit keine IC-Läger (Läger eines Verbands) und der Versandweg ist Zufuhr/Anlieferung. Dann werden - wie bei der Umlagerung - die entsprechenden Belege automatisch erzeugt. Beim Wareneingang wird aber sofort per Cross Docking in den Versand/Tourenbereich umgelagert. 

Tooltip: 

Hier kann der Versandweg vorbelegt werden. Ist in der Auftragsart kein Versandweg vorgegeben, 
so wird standardmäßig leer = „Zufuhr/Anlieferung“ im Auftragskopf vorbelegt und 
damit auf die Auftragsposition übertragen. Dies kann in der einzelnen Auftragsposition nochmals übersteuert werden. 
Die Steuerungslogik des Versandwegs kann pro Position definiert werden.