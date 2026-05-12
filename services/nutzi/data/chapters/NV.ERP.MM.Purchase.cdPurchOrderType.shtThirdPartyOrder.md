---
chapter_id: "NV.ERP.MM.Purchase.cdPurchOrderType.shtThirdPartyOrder"
topics: []
source: eNVenta 4.5 Onlinehilfe
---

# Kapitel NV.ERP.MM.Purchase.cdPurchOrderType.shtThirdPartyOrder

Wenn Sie diesen Parameter aktivieren, können Strecken-Bestellungen bei der Erfassung der Eingangsrechnung gesondert behandelt werden. Dazu ist es notwendig den Prozess datentechnisch identifizieren zu können. 

Bei der Übernahme von Rechnungen nach eNVenta (B2B -> Rechnungsprüfung) findet im Falle von Streckenbestellungen die Anlage und Verbuchung virtueller Wareneingänge statt. 

Hierbei gelten folgende Bedingungen: 

- Lieferscheinnummer aus der Rechnung - Je Lieferscheinnummer ein Wareneingang - Die Einheiten der Rechnungsposition und der Bestellposition müssen übereinstimmen, sonst gibt es einen Fehler. - Die Liefermenge orientiert sich an der Menge aus der B2B-Rechnungsposition (Menge laut Rechnung). 
Teil-Lieferung: 

Ist im Artikelstamm das Feld Teillief. WE % gepflegt, so muss dies bei der Entscheidung, ob es sich um eine Voll- oder Teillieferung handelt, berücksichtigt werden. Hier kann ein Prozentsatz hinterlegt werden, ab dem eine Teillieferung als Volllieferung erkannt wird. D.h. die Bestellposition wird in Status 3 gesetzt und es wird keine Rückstandsposition erzeugt. 

Transaktionssicherheit: 

Es wird gewährleistet, dass sowohl die Übernahme der Rechnung, als auch das Verbuchen der virtuellen Wareneingänge innerhalb einer Transaktion ablaufen. Bei Fehlern in der Rechnungsanlage darf auch kein WE gebucht werden. 

Protokollierung: 

Relevante Informationen / Ereignisse werden protokolliert. Hierfür wird das Rechnungsprüfungsprotokoll verwendet (Button Report in der Rechnungsprüfung ). 

Ablehnung von Strecken-Rechnungen: 

Angenommen die Rechnung konnte übernommen und der virtuelle Wareneingang gebucht werden, die Rechnung soll nun aber abgelehnt werden, so muss im Fall von Streckenrechnungen dafür gesorgt werden, dass der virtuelle Wareneingang storniert wird. Dafür steht der Button Ablehnung in der Rechnungsprüfung zur Verfügung. 

Mehr Informationen zum Thema Streckengeschäft erhalten Sie im Kapitel Globalabschluss und Strecke . 

Tooltip: 

Wenn aktiviert, werden Strecken-Bestellungen bei der Erfassung der Eingangsrechnung gesondert behandelt.