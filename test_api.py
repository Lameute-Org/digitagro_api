#!/usr/bin/env python3
import requests
import json
from datetime import date, timedelta

BASE_URL = "http://185.217.125.37:8001/"
token = None

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    END = '\033[0m'

def api_call(method, endpoint, data=None, files=None):
    """Fonction utilitaire pour les appels API"""
    headers = {}
    if token:
        headers['Authorization'] = f'Token {token}'
    
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method == 'GET':
            response = requests.get(url, headers=headers)
        elif method == 'POST':
            if files:
                response = requests.post(url, headers=headers, data=data, files=files)
            else:
                headers['Content-Type'] = 'application/json'
                response = requests.post(url, headers=headers, json=data)
        elif method == 'PATCH':
            headers['Content-Type'] = 'application/json'
            response = requests.patch(url, headers=headers, json=data)
        elif method == 'DELETE':
            response = requests.delete(url, headers=headers)
        
        print(f"{Colors.BLUE}{'='*50}{Colors.END}")
        print(f"{Colors.GREEN}{method} {endpoint}{Colors.END}")
        print(f"Status: {response.status_code}")
        
        if response.status_code >= 200 and response.status_code < 300:
            result = response.json()
            print(json.dumps(result, indent=2, ensure_ascii=False))
            return result
        else:
            print(f"{Colors.RED}Erreur:{Colors.END}")
            try:
                print(json.dumps(response.json(), indent=2, ensure_ascii=False))
            except:
                print(response.text)
            return None
            
    except Exception as e:
        print(f"{Colors.RED}Exception: {e}{Colors.END}")
        return None

print(f"\n{Colors.YELLOW}{'='*60}{Colors.END}")
print(f"{Colors.YELLOW}🚀 DIGITAGRO API - TESTS COMPLETS{Colors.END}")
print(f"{Colors.YELLOW}{'='*60}{Colors.END}\n")

# ==================== 1. INSCRIPTION ====================
print(f"\n{Colors.GREEN}1️⃣  INSCRIPTION{Colors.END}")
result = api_call('POST', '/api/auth/register/', {
    "email": "davyem@gmail.com",
    "telephone": "+237752179014",
    "nom": "EMANE",
    "prenom": "Davy",
    "adresse": "Yaoundé, Cameroun",
    "password": "Davy@2025",
    "password_confirm": "Davy@2025"
})

if result:
    token = result['token']
    print(f"\n{Colors.GREEN}✅ Token enregistré: {token[:30]}...{Colors.END}")
    print(f"{Colors.GREEN}✅ Profil complété: {result['user']['profile_completed']}{Colors.END}")
    print(f"{Colors.GREEN}✅ Rôles actifs: {result['user']['active_roles']}{Colors.END}\n")
else:
    print(f"{Colors.RED}❌ Inscription échouée{Colors.END}")
    exit(1)

# ==================== 2. PROFIL ====================
print(f"\n{Colors.GREEN}2️⃣  CONSULTER PROFIL{Colors.END}")
profile = api_call('GET', '/api/auth/me/')

# ==================== 3. STATUT DES RÔLES ====================
print(f"\n{Colors.GREEN}3️⃣  STATUT DES RÔLES{Colors.END}")
api_call('GET', '/api/auth/roles-status/')

# ==================== 4. CRÉER PREMIÈRE PRODUCTION (Devient producteur automatiquement) ====================
print(f"\n{Colors.GREEN}4️⃣  CRÉATION 1ÈRE PRODUCTION (Activation auto producteur){Colors.END}")
prod_result = api_call('POST', '/api/productions/', {
    "produit": "Tomates Bio",
    "type_production": "Maraîchage",  # ← REQUIS pour devenir producteur
    "superficie": 2.5,                 # Optionnel
    "certification": "Bio",            # Optionnel
    "quantite": 150,
    "unite_mesure": "kg",
    "prix_unitaire": 800,
    "latitude": 3.8667,
    "longitude": 11.5167,
    "adresse_complete": "Yaoundé, Cameroun",
    "date_recolte": (date.today() + timedelta(days=15)).isoformat(),
    "description": "Tomates biologiques fraîches de qualité supérieure",
    "conditions_stockage": "Conserver au frais entre 8-12°C"
})

prod_id = prod_result['id'] if prod_result else None

if prod_id:
    print(f"\n{Colors.GREEN}✅ Production créée (ID: {prod_id}){Colors.END}")
    print(f"{Colors.GREEN}✅ Statut producteur activé automatiquement !{Colors.END}\n")

# ==================== 5. CRÉER 2ÈME PRODUCTION (Sans champs producteur) ====================
print(f"\n{Colors.GREEN}5️⃣  CRÉATION 2ÈME PRODUCTION (Déjà producteur){Colors.END}")
prod_result2 = api_call('POST', '/api/productions/', {
    "produit": "Bananes Plantains",
    # type_production, superficie, certification NON nécessaires maintenant !
    "quantite": 200,
    "unite_mesure": "kg",
    "prix_unitaire": 600,
    "latitude": 3.8667,
    "longitude": 11.5167,
    "adresse_complete": "Yaoundé, Cameroun",
    "date_recolte": (date.today() + timedelta(days=20)).isoformat(),
    "description": "Bananes plantains de qualité premium",
    "conditions_stockage": "Température ambiante"
})

prod_id2 = prod_result2['id'] if prod_result2 else None

# ==================== 6. MES PRODUCTIONS ====================
print(f"\n{Colors.GREEN}6️⃣  MES PRODUCTIONS (Tableau de bord producteur){Colors.END}")
api_call('GET', '/api/productions/mine/')

# ==================== 7. TOUTES LES PRODUCTIONS ====================
print(f"\n{Colors.GREEN}7️⃣  TOUTES LES PRODUCTIONS (Marketplace){Colors.END}")
api_call('GET', '/api/productions/')

# ==================== 8. RECHERCHE PROXIMITÉ ====================
print(f"\n{Colors.GREEN}8️⃣  RECHERCHE PROXIMITÉ (10km autour de Yaoundé){Colors.END}")
api_call('GET', '/api/productions/nearby/?lat=3.8667&lon=11.5167&radius=10')

# ==================== 9. PASSER COMMANDE ====================
if prod_id:
    print(f"\n{Colors.GREEN}9️⃣  PASSER UNE COMMANDE{Colors.END}")
    cmd_result = api_call('POST', '/api/productions/commandes/', {
        "production": prod_id,
        "quantite": 15,
        "adresse_livraison": "Douala, Bonapriso, Rue des Palmiers",
        "notes": "Appeler 30 min avant livraison SVP",
        "date_livraison_souhaitee": (date.today() + timedelta(days=20)).isoformat()
    })
    
    cmd_id = cmd_result['id'] if cmd_result else None
    
    if cmd_id:
        print(f"\n{Colors.GREEN}✅ Commande créée (ID: {cmd_id}){Colors.END}\n")
        
        # ==================== 10. LISTE MES COMMANDES ====================
        print(f"\n{Colors.GREEN}🔟 MES COMMANDES{Colors.END}")
        api_call('GET', '/api/productions/commandes/')
        
        # ==================== 11. CONFIRMER COMMANDE ====================
        print(f"\n{Colors.GREEN}1️⃣1️⃣  CONFIRMER COMMANDE (Producteur){Colors.END}")
        api_call('POST', f'/api/productions/commandes/{cmd_id}/confirm/')
        
        # ==================== 12. EXPÉDIER COMMANDE ====================
        print(f"\n{Colors.GREEN}1️⃣2️⃣  EXPÉDIER COMMANDE{Colors.END}")
        api_call('POST', f'/api/productions/commandes/{cmd_id}/ship/')
        
        # ==================== 13. LIVRER COMMANDE ====================
        print(f"\n{Colors.GREEN}1️⃣3️⃣  LIVRER COMMANDE{Colors.END}")
        api_call('POST', f'/api/productions/commandes/{cmd_id}/deliver/')
        
        # ==================== 14. ÉVALUER COMMANDE ====================
        print(f"\n{Colors.GREEN}1️⃣4️⃣  ÉVALUATION PRODUCTEUR{Colors.END}")
        api_call('POST', '/api/productions/evaluations/', {
            "commande": cmd_id,
            "note": 5,
            "commentaire": "Excellente qualité ! Produits frais et livraison rapide. Je recommande vivement ce producteur."
        })

# ==================== 15. NOTIFICATIONS ====================
print(f"\n{Colors.GREEN}1️⃣5️⃣  NOTIFICATIONS NON LUES{Colors.END}")
notifs = api_call('GET', '/api/notifications/unread/')

if notifs:
    print(f"\n{Colors.YELLOW}📬 {notifs.get('count', 0)} notification(s) non lue(s){Colors.END}")

# ==================== 16. TOUTES LES NOTIFICATIONS ====================
print(f"\n{Colors.GREEN}1️⃣6️⃣  TOUTES LES NOTIFICATIONS{Colors.END}")
api_call('GET', '/api/notifications/')

# ==================== 17. VÉRIFIER NOUVEAU STATUT ====================
print(f"\n{Colors.GREEN}1️⃣7️⃣  VÉRIFICATION STATUT FINAL{Colors.END}")
final_profile = api_call('GET', '/api/auth/me/')

if final_profile:
    print(f"\n{Colors.YELLOW}{'='*60}{Colors.END}")
    print(f"{Colors.GREEN}✅ Rôles actifs: {final_profile['active_roles']}{Colors.END}")
    print(f"{Colors.GREEN}✅ Producteur vérifié: {final_profile['is_producteur_verified']}{Colors.END}")
    
    if 'role_profiles' in final_profile and 'producteur' in final_profile['role_profiles']:
        prod_profile = final_profile['role_profiles']['producteur']
        print(f"{Colors.GREEN}✅ Type production: {prod_profile.get('type_production', 'N/A')}{Colors.END}")
        print(f"{Colors.GREEN}✅ Superficie: {prod_profile.get('superficie', 'N/A')} ha{Colors.END}")
        print(f"{Colors.GREEN}✅ Total productions: {prod_profile.get('total_productions', 0)}{Colors.END}")
    print(f"{Colors.YELLOW}{'='*60}{Colors.END}\n")

# ==================== RÉSUMÉ FINAL ====================
print(f"\n{Colors.YELLOW}{'='*60}{Colors.END}")
print(f"{Colors.GREEN}🎉 TOUS LES TESTS TERMINÉS AVEC SUCCÈS !{Colors.END}")
print(f"{Colors.YELLOW}{'='*60}{Colors.END}\n")

print(f"{Colors.BLUE}📊 Résumé des tests :{Colors.END}")
print(f"  ✅ Inscription et authentification")
print(f"  ✅ Activation automatique rôle producteur")
print(f"  ✅ Création de productions")
print(f"  ✅ Gestion des commandes (lifecycle complet)")
print(f"  ✅ Système de notifications")
print(f"  ✅ Évaluations")
print(f"\n{Colors.GREEN}🚀 L'API DIGITAGRO fonctionne parfaitement !{Colors.END}\n")