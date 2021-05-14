Lancement.

lancer apres le lancement du serveur de jeu. le program se charge du reste

Librairies utilisées:

socket : necessaire a la communication client- serveur
json : permet de de/encoder du json
time : timeout des requetes 
random : generation d'aleatoire pour le choix du mouvement
fonction deepcopy de la librairie copy : permet de copier un tuple

fonctions recieveJSON() et sendJSON() pour directement envoyer et recevoir du JSON au/du serveur

fonctionnement de l'IA

-calcule tous les coups valides

-calcule le "score" que l'on obtient pour chaque coup. (score +1 pour chaque piece du joueur -1 pour chacune de celles de l'opposant.)  

-prends le coup avec le meilleur score (si il y en a plusieurs selectionne au hazard dans les meilleurs)

dans les faits est aleatoire sauf quand un coup d'elimination est possible. dans ce cas il jouera ce coup. le code qui permet de prevoir des coups a l'avance est actuellement trop lent
et les delais sont trop serrés pour optimiser les performances assez que pour le rendre utilisable.
