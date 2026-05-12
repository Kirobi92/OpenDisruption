---
chapter_id: "NV.ERP.Base.Common.cdSystemBase.shtCheckVATRegNoViaWS"
topics: []
source: eNVenta 4.5 Onlinehilfe
---

# Kapitel NV.ERP.Base.Common.cdSystemBase.shtCheckVATRegNoViaWS

Wenn diese Checkbox aktiviert ist, wird die Umsatzsteuer Identifikationsnummber bei Eingabe in den nachfolgenden Dialogen via Webservice geprüft: 

- Firmenstamm - Versandanschrift - Kunde - Kunde erfassen - Projekt - Adresse - Vertreter - Lieferant - Journal Detail - Auftrag - Angebot - Gutschrift - Buchen - OP Anlage - OP-Übernahme - Adressimport - Benutzerübernahme im Webshop 
Diese Checkbox kann auch deaktiviert werden! 

Allgemein und Warenwirtschaft: Findet die Überprüfung einen Fehler, erhalten Sie eine Meldung, können aber trotzdem eine abweichende Nummer eingeben. 

Der verwendete Webservice hat folgende Adresse: 
http://ec.europa.eu/taxation_customs/vies/services/checkVatService 

Der Webservice wird bereits beim Veröffentlichen der Anwendung (Publish) angegeben. 

Finanzbuchhaltung >> Buchen: Die Angabe der UST-ID ist in den Vorgängen Pflicht, falls ein Steuerschlüssel im Vorgang enthalten ist, welcher Keine ZM deaktiviert hat. 

Siehe Kapitel Steuerschlüssel . 

Diese Prüfung ersetzt nicht die gesetzlich geforderte Prüfung der UST-ID, sondern dient nur der ersten Prüfung. Wenn die UST-ID nicht korrekt ist, verweigert das Finanzamt unter Umständen die Anerkennung und es wird zu einer Rückforderung kommen. Bitte wenden Sie sich im Zweifelsfall immer an Ihren Steuerberater. 

Beispiele: 

Dialog Kunde , geprüft auf MwSt.-Kz. 

Kunde auf MwSt.-Kz. geprüft 

Dialog Firmenstamm 

MwSt.-Kz. im Firmenstamm 

Dialog Vertreter 

MwSt.-Kz. Vertreter 

Tooltip: 

Umsatzsteuer Identifikationsnummer via Webservice prüfen: 

Ist diese Funktion aktiviert, so wird die Umsatzsteuer Identifikationsnummer bei 
der Eingabe in den Dialogen Kunde, Lieferant, Angebot, Auftrag, Gutschrift, ... , 
per Webservice geprüft.