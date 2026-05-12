---
chapter_id: "NV.ERP.MM.Sales.cdReturnsType.shtThirdPartyDeal"
topics: []
source: eNVenta 4.5 Onlinehilfe
---

# Kapitel NV.ERP.MM.Sales.cdReturnsType.shtThirdPartyDeal

Im Rahmen eines Streckengeschäfts können auch Retouren erfasst werden. 

Damit die internen Prozesse korrekt abgewickelt werden, wird die Eigenschaft Strecke für Gutschriften und Belastungen benötigt, damit nicht unnötig versucht wird, Ware zu versenden, welche niemals im eigenen Lager angekommen ist. (Der Lieferant hat ja auch ursprünglich die Ware direkt zum Kunden gesendet.) 

Ist diese Checkbox gesetzt, so ist eine "Rücknahme" auf das Streckenlager möglich, obwohl es sich dabei um ein Sperrlager handelt. Ob diese Rücknahme mit oder ohne Lagerbuchung stattfindet, hängt wie bei "normalen" Lageraufträgen vom Setzen der Checkbox Lagerbuchung (bzw. dem Kennzeichen Reklamation) in der Retoure ab. 

Auswählbare Gutschriftsarten auf Basis einer solchen Retoure können nur als "Strecke" geflaggte Belegarten sein. Außerdem ist die Gutschriftsart standardmäßig vom Typ "Wertgutschrift". 

Werden Positionen auf Basis einer Streckenretoure erfasst, so ist eine Mischung von Positionen mit und ohne Lagerbuchung nicht möglich. 

Handelt es sich um eine Retourenposition mit Lagerbuchung, so muss analog einer "normalen" Retourenposition ein Wareneingang gebucht und die Position freigegeben werden. 

Im Anschluss können Gutschrift und Belastung erzeugt werden. 

Die Handhabung dieser Gutschrifts- und Retourenarten sind in der Erweiterten Konditionsfindung ebenso zu handhaben! 

Tooltip: 

Strecke