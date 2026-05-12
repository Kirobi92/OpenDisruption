---
chapter_id: "NV.ERP.Base.Storage.cdStorageLocation.shtCreateArtfromDiv"
topics: []
source: eNVenta 4.5 Onlinehilfe
---

# Kapitel NV.ERP.Base.Storage.cdStorageLocation.shtCreateArtfromDiv

Wenn Sie diesen Parameter aktivieren, kann ein Diversartikel im Wareneingang in ein Lager gebucht werden, wenn es sich um eine auftragsbezogene Bestellung handelt. Der Diversartikel wird dann kurzfristig zu einem "ordentlichen" Artikel mit eigener Artikelnummer und wird entsprechend im Artikelstamm angelegt. (Kurzfristig bedeutet, dass zu dem 'neuen' Artikel die Checkbox Ungewollte Lagerware gesetzt wird und den Status ausgelaufen int. bekommt. Der Artikel wird ja nur für eine gewisse Zeit genutzt.) Damit können Einlagerung, Auslagerung, Bestandsaussagen und Inventur eindeutig gebucht bzw. nachvollzogen werden. 

In Zusammenhang mit dem Mandanten-Management gilt: 

Beim Wareneingang im Mandanten 2 wird aus dem Diversartikel ein neuer Artikel erzeugt und dieser wird auch direkt bis in die Auftragsposition des Mandanten 1 übergeben. 

Achtung : Eine Artikelnummer für solch einen Artikel setzt sich zusammen aus der ursprünglichen Artikelnr + A + Nummer der Auftrags+Belegartnummer. 

Diese Nummer wird gesetzt, wenn der Wareneingang verbucht wird. Ist es eine auftragsbezogene Bestellung, ist der Kundenauftrag die Quelle für die Nummer. Bei Umlagerung werden die APos-Werte verwendet, die an der UB-Position hinterlegt sind. 

Tooltip: 

Erzeuge Artikel aus Diversartikeln