from pyovpn import OpenVPN

# Initialiser la connexion VPN
vpn = OpenVPN(config='/path/to/your/config.ovpn')

# Connecter
vpn.connect()

# Vérifier l'état
if vpn.is_connected():
    print("VPN est connecté")

# Déconnecter
vpn.disconnect()
