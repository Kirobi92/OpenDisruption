---
chapter_id: "NV.ERP.Base.Common.cdSystemBase.sEmail"
topics: []
source: eNVenta 4.5 Onlinehilfe
---

# Kapitel NV.ERP.Base.Common.cdSystemBase.sEmail

Hier wird die E-Mail-Adresse angegeben. Bei der Angabe mehrerer Adressen, müssen diese durch Semikolon getrennt werden. 

Beim Import von E-Mails, beim Vergleich / der Prüfung der E-Mail-Adressen, werden Leerzeichen am Ende und Beginn ignoriert. So können Absender leichter ermittelt werden und die E-Mail wird problemlos importiert. Ebenso werden bereits beim Speichern neuer oder geänderter E-Mail-Adressen automatisch die unnötigen Leerzeichen am Beginn und Ende der Mail-Adresse entfernt. 

Sammelverteiler wie z.B. Mail-Adresse Mahnung im Kundenstamm sind davon ausgenommen. 

Um sicherzugehen, dass eine E-Mail an die richtige Adresse gesendet wird, prüft eNVenta beim Speichern oder Ändern einer Mailadresse, ob die Mail-Adresse der „Norm“ entspricht. Falls nicht wird ein Hinweis ausgegeben. Dabei wird das Speichern nicht grundsätzlich verhindert. Auf diese Weise werden z.B. Outlook-Adressbucheinträge wie z.B. „#EW_ERP“ gespeichert und genutzt. Die Auswertung des Eintrags erfolgt wie gewohnt im Outlook Client. 

Dabei läuft die Prüfung ausschließlich bei Anlage und Änderung einer Mail-Adresse. Werden andere Einträge, z.B. des Kundenstammsatzes geändert, so kommt diese Meldung nicht. 

Werden Stammdaten über das Gateway importiert, so werden u.U. fehlerhafte Mailadressen importiert (ggfs. mit Warnung). Bei einem Import unter Verwendung des Jobservers erfolgt dies ebenfalls in Form einer Warnung (im Jobprotokoll). 

Tooltip: 

Allgemeine E-Mail-Adresse Ihres Unternehmens.