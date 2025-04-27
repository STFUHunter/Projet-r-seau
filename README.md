Projet : Jeu TicTacToe en ligne + hors ligne
1. Partie hors-ligne :

Un jeu TicTacToe contre un agent IA (agent d'apprentissage par renforcement DRL) utilisant l'algorithme PPO de la bibliothèque Python Stable Baselines3 (basée sur la bibliothèque PyTorch).
L'interface et les fonctionnalités sont réalisées avec la bibliothèque Pygame.
2. Partie en ligne :
2.1 Partie serveur :

Un code serveur utilisant :

    La bibliothèque Socket pour créer des connexions réseau entre plusieurs ordinateurs (envoi et réception de données),

    La bibliothèque Threading pour permettre le multithreading (exécuter plusieurs tâches en même temps),

    La bibliothèque Time pour contrôler ou mesurer le temps.

2.2 Partie client :

Un code client utilisant :

    Socket et Threading pour la communication réseau et l'exécution simultanée de tâches,

    Pygame pour l'interface graphique,

    Sys pour interagir avec le système d'exécution Python (par exemple pour lire les arguments),

    Queue pour échanger des données entre plusieurs threads de manière sécurisée.
