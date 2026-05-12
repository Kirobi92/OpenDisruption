---
chapter_id: "NV.ERP.Base.Common.cdSystemBase.sAddressCheckProvider"
topics: []
source: eNVenta 4.5 Onlinehilfe
---

# Kapitel NV.ERP.Base.Common.cdSystemBase.sAddressCheckProvider

In der Regel sind dem Unternehmen die Lieferadressen der Kunden bekannt. Eine Ausnahme bilden Situationen, in denen dem bestellenden Handwerker die Adresse nicht bekannt ist. Hierzu zählen z.B. Baustellenadressen oder Adressen des Privatkunden, für den der Handwerker Material benötigt. In solchen Situationen kommt es häufiger vor, dass Postleitzahlen genannt werden, die gar nicht zur Straße passen. 

Es kommt ebenso vor, dass der Erfasser des Auftrags die PLZ nach bestem Wissen einträgt, diese aber falsch ist. 

In der Folge wird die Ware mit der falschen Tour gefahren und erreicht den Handwerker nicht wie erwartet. 

Die Daten, die Sie dafür benötigen, erhalten Sie von der Deutschen Post (die Datei heißt „Streetcode“). 

In dieser Combobox stehen 5 Einträge zur Adressprüfung zur Auswahl: 
- Leer - Länderspezifischer Provider - Postleitzahlenspezifischer Provider - Rudimentärer Provider - Straßenspezifischer Provider 
Wird nichts ausgewählt oder deaktiviert, passiert folgendes: 
- Bei Pflege oder Neuanlage einer Anschrift erfolgt die Prüfung gegen den Parameter der Adressprüfung. - Bei der Ermittlung, ob die Lieferadresse gültig ist oder die Rechnungsadresse für die Versendung übernommen werden soll, erfolgt immer mindestens eine rudimentäre Prüfung (Firma 1, Straße, PLZ und Ort), auch wenn die Parameter der Adressprüfung deaktiviert sind! 
In Zusammenhang mit der Checkbox Adresse gültig in den Versandanschriften , prüft die länderpsezifische Prüfung neben den allgemeinen Angaben immer, ob ein LKZ angegeben ist. Sollte kein LKZ angegeben sein, so erfolgt in jedem Fall eine rudimentäre Adressprüfung. 

Siehe Kapitel Adressprüfung in eNVenta . 

Tooltip: 

Hier wählen Sie den Provider für die Adressprüfung aus.