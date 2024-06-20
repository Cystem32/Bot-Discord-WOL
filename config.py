# config.py Toute les configurations
TOKEN = '' # Le token discord
BOT_PREFIX = '?' # Le prefix (changer le comme vous le voulez)
WAIT_TIME = '30' # Le temp d'attente pour que le bot verifie que le serveur est bien allumer (Ajuster le en fonction de votre serveur)
ROLE_ID = 123456789 # le role qui peut faire la commande "wake" et "shutdown"
GUILD_ID = 123456789 # L'id de la Guild
OWNER_ID = 123456789 # L'id de l'owner pour fait la commande "stats"
SSH_USER = ''
SSH_PASSWORD = ''

# Horaire Wake commands
START_HOUR = 8   # Exemple 8=8h
END_HOUR = 18    # Exemple 18=18h

#La liste des serveurs
servers = {
    'Serveur-1': {'mac': '00:00:00:00:00:00', 'ip': '127.0.0.1'},
    # Tu peut en ajouter autant que tu veux
}

# Copyright (c) 2024 Cystem32