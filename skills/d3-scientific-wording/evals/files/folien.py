from d3deck import Deck, slide

deck = Deck("Netzengpässe und Redispatch")

slide("Redispatch-Kosten sind nicht nur hoch, sondern steigen auch rasant",
      bullets=["Die Kosten für Redispatch haben sich zwischen 2019 und 2023 von 1,2 auf 3,1 Mrd. Euro mehr als verdoppelt – ein dramatischer Anstieg, der die Energiewende gefährdet",
               "Bisherige Ansätze scheitern daran, Unsicherheiten in der Einspeisung zu berücksichtigen",
               "Unser innovativer Ansatz löst dieses Problem ganzheitlich und nahtlos"],
      notes="Es ist wichtig zu beachten, dass die Kosten nicht nur durch den Netzausbau, sondern vor allem durch die verzögerte Einführung von Flexibilitätsmärkten getrieben werden. Unser Modell zeigt eine signifikante Reduktion der Kosten um 23 Prozent.")

slide("Ergebnisse",
      bullets=["23 % geringere Redispatch-Kosten im Szenario 2030",
               "Rechenzeit unter 4 Minuten für das deutsche Übertragungsnetz"],
      notes="Das Szenario 2030 nimmt den Netzausbauplan der Übertragungsnetzbetreiber als gegeben an.")
