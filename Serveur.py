import socket
import threading

# Configuration du serveur
HOST = "0.0.0.0"  # Écoute sur toutes les interfaces réseau
PORT = 5555

clients = [None, None]  # Deux joueurs max

# Gère la communication avec un client
def handle_client(client, player_id):
    print(f"Thread lancé pour le joueur {player_id + 1}")
    other_id = 1 - player_id
    try:
        while True:
            data = client.recv(1024)
            if not data:
                print(f"Joueur {player_id + 1} s'est déconnecté.")
                break

            if clients[other_id]:
                try:
                    clients[other_id].send(data)
                except Exception as e:
                    print(f"Erreur d'envoi au joueur {other_id + 1} : {e}")
                    break

    except Exception as e:
        print(f"Erreur avec le joueur {player_id + 1} : {e}")

    finally:
        client.close()
        clients[player_id] = None
        print(f"Connexion fermée pour le joueur {player_id + 1}")

# Démarrage du serveur
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Réutilisation du port

try:
    server_socket.bind((HOST, PORT))
    server_socket.listen(2)
    print(f"Serveur lancé sur {HOST}:{PORT}. En attente de joueurs...")

    for i in range(2):
        client, addr = server_socket.accept()
        print(f"Joueur {i + 1} connecté depuis {addr}")
        clients[i] = client
        client.send(str(i).encode())  # Envoie "0" au joueur 1, "1" au joueur 2

        # Lancer un thread pour chaque client
        thread = threading.Thread(target=handle_client, args=(client, i), daemon=True)
        thread.start()

    print("La partie commence !")

    # Garder le serveur actif tant que des joueurs sont connectés
    while any(clients):
        pass  # Boucle principale "vive"

except KeyboardInterrupt:
    print("\nFermeture du serveur...")

except Exception as e:
    print(f"Erreur du serveur : {e}")

finally:
    for c in clients:
        if c:
            try:
                c.close()
            except:
                pass
    server_socket.close()
    print("Serveur arrêté.")
