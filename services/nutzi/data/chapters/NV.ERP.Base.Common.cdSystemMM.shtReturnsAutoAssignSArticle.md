---
chapter_id: "NV.ERP.Base.Common.cdSystemMM.shtReturnsAutoAssignSArticle"
topics: []
source: eNVenta 4.5 Onlinehilfe
---

# Kapitel NV.ERP.Base.Common.cdSystemMM.shtReturnsAutoAssignSArticle

Wenn Sie diese Checkbox aktivieren, wird im Fall einer Retoure die Ursprungs-Bestellung ermittelt (auch bei nicht auftragsbezogener Beschaffung!). Allerdings nur, wenn das Kennzeichen Lagerbuchung gesetzt ist (Checkbox Lagerbuchung in den Auftragsarten ). 

Wenn die Retourenposition eine Lagerbuchung auslöst, wird geprüft, ob bereits eine Ursprungsbestellposition gefunden wurde. Wird keine Lagerbuchung ausgelöst, wird die jüngste Bestellposition zu diesem Artikel ermittelt, die keinen Auftragsbezug hat und Status > 2 und < 6 hat. Außerdem muss die Bestellposition eine größere oder gleich große Menge haben wie die Retourenposition. 

Tooltip: 

Wenn gesetzt, wird bei Retoure eine Ursprungsbestellung ermittelt 
(auch bei nicht auftragsbezogener Beschaffung).