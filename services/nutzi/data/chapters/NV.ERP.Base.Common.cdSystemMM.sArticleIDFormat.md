---
chapter_id: "NV.ERP.Base.Common.cdSystemMM.sArticleIDFormat"
topics: []
source: eNVenta 4.5 Onlinehilfe
---

# Kapitel NV.ERP.Base.Common.cdSystemMM.sArticleIDFormat

Dieses Feld steht zur Verfügung, damit eine Artikelnummer nicht nur in eNVenta verwendet werden kann, sondern auch bei der Kommunikation mit anderen internen und externen Systemen korrekt erkannt und genutzt werden kann. Die Prüfung der Artikelnummer erfolgt bei der Neuanlage direkt im Artikelstamm wie auch beim Import neuer Artikeldaten in den Artikelstamm, z.B. über den Artikel Schattenstamm. Das Format unterstützt hierbei die korrekte Angabe der Artikelnummer als eindeutiges Feld 

Dieses neue Format definieren Sie hier in diesem Feld. Der Sachbearbeiter darf bei der Neuerfassung eines Artikels nur den Zeichenbereich eingeben, welcher dem angegebenen Format entspricht; z.B. [A-z0-9]. Die eckigen Klammern, wie hier angezeigt, werden vom System automatisch eingefügt. 

Im Feld Format wird per Regular Expression (RegEx) eine Formatdefinition angegeben, welche bei jedem Einfügen einer Artikelnummer prüft, ob die neue Artikelnummer diesem Format entspricht. 

Beispiel für die Vorgabe Artikelnr Format: 

| a-z0-9. | -> Es dürfen nur Kleinbuchstaben sowie Ziffern verwendet werden, aber keine Sonderzeichen. |
| --- | --- |
| a-zA-z0-9 | -> Es dürfen Klein- und Großbuchstaben sowie Ziffern verwendet werden, aber keine Sonderzeichen. |
| a-zA-z0-9_\-\s | -> Es dürfen Klein- und Großbuchstaben sowie Ziffern verwendet werden sowie Unterstrich, Bindestrich und Leerzeichen. |

Artikelnummern, die neu vergeben werden, dürfen keine führenden und folgenden Leerzeichen beinhalten! Gegebenenfalls eingegebene Leerzeichen werden automatisch beim Einfügen des Artikels entfernt, bereits bestehende Artikelnummern bleiben erhalten. 

Um zu prüfen, ob neu angelegte Artikelnummern den neuen Kriterien entsprechen, gibt es im Dialog Artikelnummer ändern (im Modul Werkzeuge ) die Option Artikelnummer prüfen . Damit Sie diese Funktion nutzen können, hat der Dialog Artikelnr ändern leer zu sein! 

Wenn Sie dieses Feld freilassen, kann die Artikelnummer beliebig angegeben werden. 

Tooltip: 

Geben Sie hier eine Regular-Expression ein, um nur bestimmte Zeichen in der Artikelnummer zu erlauben, z.B.: A-Z0-9 (nur Großbuchstaben und Zahlen erlaubt). Es ist nur die Eingabe von Zeichenbereichen erlaubt!