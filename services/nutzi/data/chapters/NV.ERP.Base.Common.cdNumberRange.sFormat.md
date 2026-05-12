---
chapter_id: "NV.ERP.Base.Common.cdNumberRange.sFormat"
topics: []
source: eNVenta 4.5 Onlinehilfe
---

# Kapitel NV.ERP.Base.Common.cdNumberRange.sFormat

Hier wird das Zahlenformat für die jeweiligen Nummernkreise festgelegt. Hier sind als Standardwerte ausschließlich numerische Werte vorgegeben. Es ist davon abzuraten, andere als numerische Nummernkreise zu verwenden. 

N = Nummer (für jede Stelle ein N, bei einer 5-stelligen Zahl also NNNNN) 
J = Jahr (entweder 2- oder 4-stellig) 
M = Monat (2-stellig) 
T = Tag (2-stellig) 
P = Prüfziffer nach Modulo10 (1-stellig, muss letztes Zeichen im Format sein) 

Insgesamt maximal 18-stellig 

C als Kennung für Zähler: 
Ein C wird wie ein N interpretiert, bewirkt jedoch, dass bei Monats- /Jahreswechsel die Nummer auf 1 zurückgesetzt wird. 
Enthält eine Formatvorgabe mindestens ein C, gilt: 
- M enthalten – Nummer = 1 bei Monatswechsel - J enthalten – Nummer = 1 bei Jahreswechsel 

Tooltip: 

Legen Sie das Zahlenformat für die jeweiligen Nummernkreise fest. 

N = Nummer (für jede Stelle ein N, bei einer 5-stelligen Zahl also NNNNN) 
J = Jahr (entweder 2- oder 4-stellig) 
M = Monat (2-stellig) 
T = Tag (2-stellig) 
P = Prüfziffer nach Modulo10 (1-stellig, muss letztes Zeichen im Format sein) 

Insgesamt maximal 18-stellig 

C als Kennung für Zähler: 
Ein C wird wie ein N interpretiert, bewirkt jedoch, dass bei Monats- /Jahreswechsel die Nummer auf 1 zurückgesetzt wird. 
Enthält eine Formatvorgabe mindestens ein C, gilt: 
• M enthalten – Nummer = 1 bei Monatswechsel 
• J enthalten – Nummer = 1 bei Jahreswechsel