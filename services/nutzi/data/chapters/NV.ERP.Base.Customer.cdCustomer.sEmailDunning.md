---
chapter_id: "NV.ERP.Base.Customer.cdCustomer.sEmailDunning"
topics: []
source: eNVenta 4.5 Onlinehilfe
---

# Kapitel NV.ERP.Base.Customer.cdCustomer.sEmailDunning

Hier wird die E-Mail-Adresse für den Versand von Mahnungen angegeben. 

Um sicherzugehen, dass eine E-Mail an die richtige Adresse gesendet wird, prüft eNVenta beim Speichern oder Ändern einer Mailadresse, ob die Mail-Adresse der „Norm“ entspricht. Falls nicht wird ein Hinweis ausgegeben. Dabei wird das Speichern nicht grundsätzlich verhindert. Auf diese Weise werden z.B. Outlook-Adressbucheinträge wie z.B. „#EW_ERP“ bei Bedarf gespeichert und genutzt. 

Dabei läuft die Prüfung ausschließlich bei Anlage und Änderung einer Mail-Adresse. Werden andere Einträge, z.B. des Kundenstammsatzes geändert, so kommt diese Meldung nicht. 

Werden Stammdaten über das Gateway importiert, so werden u.U. fehlerhafte Mailadressen importiert (ggfs. mit Warnung). Bei einem Import unter Verwendung des Jobservers erfolgt dies ebenfalls in Form einer Warnung (im Jobprotokoll). 

Tooltip: 

Angabe der E-Mail-Adresse für den Versand von Mahnungen