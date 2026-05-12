---
chapter_id: "NV.ERP.Base.Customer.cdCustomer.sEMailAddressEC"
topics: []
source: eNVenta 4.5 Onlinehilfe
---

# Kapitel NV.ERP.Base.Customer.cdCustomer.sEMailAddressEC

In dieses Feld geben Sie die E-Mail-Adresse für den Versand der Gelangensbestätigung ein. 

Bleibt dieses Feld leer, wird in folgender Reihenfolge eine gültige E-Mail-Adresse ermittelt: 

- Es wird die E-Mail-Adresse des Ansprechpartners aus dem Auftrag gezogen. Ist hier nichts hinterlegt, - die Rechnungs-E-Mail-Adresse aus dem Kundenstamm. Ist hier nichts hinterlegt, - wird die allgemeine E-Mail-Adresse aus dem Kundenstamm gezogen. 
Um sicherzugehen, dass eine E-Mail an die richtige Adresse gesendet wird, prüft eNVenta beim Speichern oder Ändern einer Mailadresse, ob die Mail-Adresse der „Norm“ entspricht. Falls nicht wird ein Hinweis ausgegeben. Dabei wird das Speichern nicht grundsätzlich verhindert. Auf diese Weise werden z.B. Outlook-Adressbucheinträge wie z.B. „#EW_ERP“ bei Bedarf gespeichert und genutzt. 

Dabei läuft die Prüfung ausschließlich bei Anlage und Änderung einer Mail-Adresse. Werden andere Einträge, z.B. des Kundenstammsatzes geändert, so kommt diese Meldung nicht. 

Werden Stammdaten über das Gateway importiert, so werden u.U. fehlerhafte Mailadressen importiert (ggfs. mit Warnung). Bei einem Import unter Verwendung des Jobservers erfolgt dies ebenfalls in Form einer Warnung (im Jobprotokoll). 

Tooltip: 

Hier geben Sie die E-Mail-Adresse für den Versand der Gelangensbestätigung ein.