---
chapter_id: "NV.ERP.Base.Common.cdSystemBase.shtDefaultPlanningCode"
topics: []
source: eNVenta 4.5 Onlinehilfe
---

# Kapitel NV.ERP.Base.Common.cdSystemBase.shtDefaultPlanningCode

Wenn Sie aus dieser Combobox einen Eintrag auswählen, legen Sie das Dispositionsverfahren fest, mit dem der Artikel disponiert und am Lager geführt wird. 

Folgende Möglichkeiten stehen zur Verfügung: 

- Deterministisch : Zeitgesteuertes Verfahren zur Minimierung des Lagerbestands. Die Disposition erfolgt auf Basis des aktuellen Auftragsbestands/Bedarfs. - Bestellpunkt : Statisches Verfahren - sobald der Meldebestand des Artikels am Lager unterschritten wird, erfolgt ein Bestellvorschlag. - Reichweite : Bei der Reichweiten-Disposition wird die Reichweite in Tagen ermittelt, die der aktuelle Lagerbestand reicht, um den Bedarf zu decken. 
Hinweis: 
Für das Dispoverfahren Reichweite ist es wichtig, dass für den Artikel eine Prognose vorhanden ist. Eine Prognose erstellen Sie über den Prognosemonitor (auch Stochastische Bedarfsanalyse genannt). Diese Prognosen sollten Sie für die benötigten Lager und/oder Lagergruppen durchführen. 

Fehlende Prognosen können sonst dazu führen, dass keine Bestellvorschläge für die Artikel generiert werden und auch kein Rückfall auf das alternative Dispoverfahren erfolgt. 
Dies ist von großer Bedeutung, wenn Sie mit dem automatischen Bestellwesen / Reichweitenoptimierung arbeiten. - kein Lager : Dieser Artikel wird nicht auf ein Lager gebucht. Die Prüfung, ob ein Artikel für einen Lagerort zugelassen ist, erfolgt nur für lagerführende Artikel. - Beschaffungsartikel : Dieser Artikel wird auftragsbezogen bestellt. 
Die dynamische Verfügbarkeitsprüfung sollte nicht für Artikel genutzt werden, die mit dem Dispoverfahren Determinstisch geführt werden. Die dynamische Verfügbarkeit und das deterministische Verfahren verfolgen beide das Ziel, mit wenig Lagerbestand möglichst viele Aufträge beliefern zu können. Die beiden Verfahren könnten sich in Grenzfällen widersprechen. 

Die Reichweite bzw. verbrauchsbezogene Bedarfsplanung erfolgt durch Prognoseverfahren vor dem Hintergrund des periodisierten Verbrauchs der Vergangenheit. 

Die Einstellung des Dispositionsverfahren erfolgt im Artikelstamm. 

Bei der Berechnung der Wiederbeschaffungszeit werden nur Artikel berücksichtigt, die das Dispoverfahren Reichweite haben! 

Mehr Informationen erhalten Sie in den Kapiteln Dispositionsverfahren in eNVenta , Wiederbeschaffungszeit und Reichweitenoptimierung in der Bestellung . 

Tooltip: 

Dieses Dispokennzeichen wird beim Neuanlegen eines Artikels gesetzt, falls das Dispokennzeichen 
leer gelassen wurde. 
Für Handelsstücklisten gilt immer die Ausnahme "Kein Lager" als Default. 
"Kein Lager" wird nur dann als Default gesetzt, wenn zulässig.