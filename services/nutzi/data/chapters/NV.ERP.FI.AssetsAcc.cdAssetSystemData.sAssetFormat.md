---
chapter_id: "NV.ERP.FI.AssetsAcc.cdAssetSystemData.sAssetFormat"
topics: []
source: eNVenta 4.5 Onlinehilfe
---

# Kapitel NV.ERP.FI.AssetsAcc.cdAssetSystemData.sAssetFormat

Geben Sie das Format für die automatische Nummerierung der Anlagen an. Bei einer manuellen Eingabe der Anlagennummer zieht dieser Parameter nicht. 

Hier sind als Standardwerte ausschließlich numerische Werte vorgegeben. Es ist davon abzuraten, andere als numerische Nummernkreise zu verwenden. 

Als Bezeichnung in den Format-Feldern bedeutet: 

N = Nummer (für jede Stelle ein N, bei einer 5-stelligen Zahl also NNNNN) 

Des Weiteren ist es möglich in den Parametern für das Anlagenformat die Jahreszahl festzulegen. Dann könnte ein Eintrag im Feld Anlagenformat z.B. so aussehen: 

JJJJNNNNN, d.h. für das Jahr 2019 z.B. 201900695 
Oder 
JJNNNNN, d.h. für das Jahr 2019 z.B. 1900695 

Zusätzlich können Tag und Monat eingefügt werden. 

Dabei ist unbedingt zu beachten, dass die Nummernkreise, d.h. die Anzahl der zu vergebenden Nummern vom Startwert bis zu dem Wert, bei dem der nächste Nummernkreis beginnt, so groß angesetzt werden, dass sie nicht überlaufen. Dann würden evtl. Nummern vergeben werden, die zu einem anderen Nummernkreis gehören. 

Ist ein Nummernkreis fast gefüllt, kann der Startwert jederzeit angepasst werden, indem z.B. eine weitere Stelle hinzugefügt bzw. der Startwert eines neuen, bisher nicht belegten Nummernbereichs eingetragen wird. Im fortlaufenden Betrieb wird dann, bei der Vergabe der nächsten Nummer, der Wert im entsprechenden Feld des Dialogs um 1 Einheit hochgesetzt, so dass hier immer die zuletzt vergebenen und nicht die anfangs festgelegten Nummern sichtbar sind. 

Startwerte der Nummernkreise unbedingt notieren und aufbewahren. Überprüfen Sie anhand Ihrer Notizen regelmäßig, ob ein Nummernkreis an seine obere Grenze zu laufen droht. Es kann sonst zu einem Systemstillstand kommen. 

Tooltip: 

Bestimmt das Format für die automatische Nummerierung der Anlagen.