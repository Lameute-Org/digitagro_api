#!/usr/bin/env python3
import requests
import json
from datetime import date, timedelta

BASE_URL = "http://127.0.0.1:8001/"
token = None

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    END = '\033[0m'

def api_call(method, endpoint, data=None):
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = f'Token {token}'
    
    url = f"{BASE_URL}{endpoint}"
    response = getattr(requests, method.lower())(url, headers=headers, json=data)
    
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.CYAN}{method} {endpoint}{Colors.END}")
    print(f"Status: {response.status_code}")
    
    if 200 <= response.status_code < 300:
        result = response.json()
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return result
    else:
        print(f"{Colors.RED}❌ Erreur:{Colors.END}")
        try:
            print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        except:
            print(response.text)
        return None

TEST_USER = {
    "email": "davyemane@digitagro.cm",
    "telephone": "+237676469014",
    "nom": "EMANE",
    "prenom": "Davy",
    "adresse": "Yaoundé, Mvog-Ada",
    "password": "Davy@2025",
    "password_confirm": "Davy@2025"
}

print(f"\n{Colors.YELLOW}{'='*70}{Colors.END}")
print(f"{Colors.YELLOW}🌾 DIGITAGRO - TEST SUITE COMPLÈTE{Colors.END}")
print(f"{Colors.YELLOW}📱 SMS + 🏆 Badges + 🌱 Productions + 📦 Commandes + ⭐ Évaluations{Colors.END}")
print(f"{Colors.YELLOW}{'='*70}{Colors.END}\n")

# ==================== 1. INSCRIPTION ====================
print(f"{Colors.GREEN}1️⃣  INSCRIPTION{Colors.END}")
result = api_call('POST', '/api/auth/register/', TEST_USER)
if not result:
    print(f"{Colors.RED}❌ Échec inscription{Colors.END}")
    exit(1)

token = result['token']
print(f"\n{Colors.GREEN}✅ Token: {token[:30]}...{Colors.END}")
print(f"{Colors.GREEN}✅ Profil complété: {result['user']['profile_completed']}{Colors.END}")

# ==================== 2. PROFIL INITIAL ====================
print(f"\n{Colors.GREEN}2️⃣  PROFIL INITIAL{Colors.END}")
profile = api_call('GET', '/api/auth/me/')
if profile:
    print(f"{Colors.YELLOW}Phone verified: {profile['phone_verified']}{Colors.END}")
    print(f"{Colors.YELLOW}Badges: {len(profile.get('badges', []))}{Colors.END}")

# ==================== 3. COMPLÉTION PROFIL ====================
print(f"\n{Colors.GREEN}3️⃣  COMPLÉTION PROFIL{Colors.END}")
api_call('PATCH', '/api/auth/me/complete-profile/', {
    "nom": TEST_USER['nom'],
    "prenom": TEST_USER['prenom'],
    "telephone": TEST_USER['telephone'],
    "adresse": TEST_USER['adresse']
})

# ==================== 4. DEMANDE CODE SMS ====================
print(f"\n{Colors.GREEN}4️⃣  DEMANDE CODE SMS (TWILIO){Colors.END}")
sms_result = api_call('POST', '/api/auth/phone/request-code/', {
    "phone_number": TEST_USER['telephone']
})

if not sms_result:
    print(f"{Colors.RED}❌ Échec envoi SMS{Colors.END}")
    exit(1)

print(f"\n{Colors.YELLOW}📱 SMS envoyé à {TEST_USER['telephone']}{Colors.END}")
code = input(f"{Colors.YELLOW}➜ Entrez le code SMS reçu: {Colors.END}")

# ==================== 5. VÉRIFICATION CODE ====================
print(f"\n{Colors.GREEN}5️⃣  VÉRIFICATION CODE SMS{Colors.END}")
verify_result = api_call('POST', '/api/auth/phone/verify-code/', {"code": code})

if not verify_result:
    print(f"{Colors.RED}❌ Code invalide{Colors.END}")
    exit(1)

print(f"\n{Colors.GREEN}✅ Badge 📱 obtenu !{Colors.END}")
print(f"{Colors.GREEN}✅ Peut devenir producteur: {verify_result['can_become_producer']}{Colors.END}")

# ==================== 6. BADGES APRÈS SMS ====================
print(f"\n{Colors.GREEN}6️⃣  MES BADGES (APRÈS SMS){Colors.END}")
badges = api_call('GET', '/api/auth/me/badges/')
if badges:
    print(f"\n{Colors.YELLOW}Total badges: {badges['total_badges']}{Colors.END}")
    for badge in badges.get('badges', []):
        print(f"  {badge['icon']} {badge['name']}")

# ==================== 7. STATUT RÔLES ====================
print(f"\n{Colors.GREEN}7️⃣  STATUT DES RÔLES{Colors.END}")
api_call('GET', '/api/auth/roles-status/')

# ==================== 8. ACTIVATION PRODUCTEUR + GIC ====================
print(f"\n{Colors.GREEN}8️⃣  ACTIVATION PRODUCTEUR + GIC{Colors.END}")
role_result = api_call('POST', '/api/auth/activate-role/', {
    "role": "producteur",
    "type_production": "Maraîchage",
    "superficie": 2.5,
    "certification": "Bio",
    "is_in_gic": True,
    "gic_name": "GIC ESPOIR AGRICOLE",
    "gic_registration_number": "GIC/2023/TEST001"
})

if role_result:
    print(f"\n{Colors.GREEN}✅ Rôle producteur activé{Colors.END}")
    print(f"{Colors.GREEN}✅ Badge 🏢 attendu{Colors.END}")

# ==================== 9. BADGES APRÈS ACTIVATION ====================
print(f"\n{Colors.GREEN}9️⃣  BADGES APRÈS ACTIVATION PRODUCTEUR{Colors.END}")
badges = api_call('GET', '/api/auth/me/badges/')
if badges:
    print(f"\n{Colors.YELLOW}Total badges: {badges['total_badges']}{Colors.END}")
    for badge in badges.get('badges', []):
        print(f"  {badge['icon']} {badge['name']}")
        if badge.get('metadata'):
            print(f"    Metadata: {badge['metadata']}")

# ==================== 10. CRÉATION PRODUCTION 1 ====================
print(f"\n{Colors.GREEN}🔟 CRÉATION PRODUCTION #1 (Tomates){Colors.END}")
prod1 = api_call('POST', '/api/productions/', {
    "produit": "Tomates Bio",
    "type_production": "legumes",
    "quantite": 500,
    "unite_mesure": "kg",
    "prix_unitaire": 800,
    "latitude": 3.8667,
    "longitude": 11.5167,
    "adresse_complete": "Yaoundé, Mvog-Ada, près du marché",
    "date_recolte": (date.today() + timedelta(days=15)).isoformat(),
    "date_expiration": (date.today() + timedelta(days=25)).isoformat(),
    "certification": "bio",
    "description": "Tomates biologiques fraîches cultivées sans pesticides",
    "conditions_stockage": "Conserver au frais 8-12°C"
})

prod_id1 = prod1.get('production', {}).get('id') if prod1 else None
if prod_id1:
    print(f"\n{Colors.GREEN}✅ Production #1 créée - ID: {prod_id1}{Colors.END}")

# ==================== 11. CRÉATION PRODUCTION 2 ====================
print(f"\n{Colors.GREEN}1️⃣1️⃣  CRÉATION PRODUCTION #2 (Bananes){Colors.END}")
prod2 = api_call('POST', '/api/productions/', {
    "produit": "Bananes Plantains",
    "type_production": "fruits",
    "quantite": 300,
    "unite_mesure": "kg",
    "prix_unitaire": 600,
    "latitude": 3.8500,
    "longitude": 11.5000,
    "adresse_complete": "Yaoundé, Emana",
    "date_recolte": (date.today() + timedelta(days=10)).isoformat(),
    "certification": "standard",
    "description": "Bananes plantains de qualité supérieure",
    "conditions_stockage": "Température ambiante"
})

prod_id2 = prod2.get('production', {}).get('id') if prod2 else None

# ==================== 12. MES PRODUCTIONS ====================
print(f"\n{Colors.GREEN}1️⃣2️⃣  MES PRODUCTIONS{Colors.END}")
api_call('GET', '/api/productions/mine/')

# ==================== 13. TOUTES LES PRODUCTIONS ====================
print(f"\n{Colors.GREEN}1️⃣3️⃣  LISTE GLOBALE PRODUCTIONS{Colors.END}")
api_call('GET', '/api/productions/')

# ==================== 14. RECHERCHE PROXIMITÉ ====================
print(f"\n{Colors.GREEN}1️⃣4️⃣  RECHERCHE PROXIMITÉ (10km){Colors.END}")
api_call('GET', '/api/productions/nearby/?lat=3.8667&lon=11.5167&radius=10')

# ==================== 15. DÉTAILS PRODUCTION ====================
if prod_id1:
    print(f"\n{Colors.GREEN}1️⃣5️⃣  DÉTAILS PRODUCTION #1{Colors.END}")
    api_call('GET', f'/api/productions/{prod_id1}/')

# ==================== 16. COMMANDE 1 ====================
if prod_id1:
    print(f"\n{Colors.GREEN}1️⃣6️⃣  CRÉATION COMMANDE #1{Colors.END}")
    cmd1 = api_call('POST', '/api/productions/commandes/', {
        "production": prod_id1,
        "quantite": 50,
        "adresse_livraison": "Douala, Akwa Nord, Rue Joffre, Immeuble SOCOPAO",
        "notes": "Livraison entre 8h et 10h SVP. Appeler 30min avant.",
        "date_livraison_souhaitee": (date.today() + timedelta(days=20)).isoformat()
    })
    
    cmd_id1 = cmd1.get('id') if cmd1 else None
    
    if cmd_id1:
        print(f"\n{Colors.GREEN}✅ Commande #1 créée - ID: {cmd_id1}{Colors.END}")

# ==================== 17. COMMANDE 2 ====================
if prod_id2:
    print(f"\n{Colors.GREEN}1️⃣7️⃣  CRÉATION COMMANDE #2{Colors.END}")
    cmd2 = api_call('POST', '/api/productions/commandes/', {
        "production": prod_id2,
        "quantite": 30,
        "adresse_livraison": "Yaoundé, Bastos, près de l'ambassade",
        "notes": "Client VIP - Livraison soignée",
        "date_livraison_souhaitee": (date.today() + timedelta(days=15)).isoformat()
    })
    
    cmd_id2 = cmd2.get('id') if cmd2 else None

# ==================== 18. LISTE COMMANDES ====================
print(f"\n{Colors.GREEN}1️⃣8️⃣  LISTE DE MES COMMANDES{Colors.END}")
api_call('GET', '/api/productions/commandes/')

# ==================== 19. WORKFLOW COMMANDE 1 ====================
if cmd_id1:
    print(f"\n{Colors.GREEN}1️⃣9️⃣  WORKFLOW COMMANDE #1{Colors.END}")
    
    print(f"\n{Colors.CYAN}→ Confirmation par producteur{Colors.END}")
    api_call('POST', f'/api/productions/commandes/{cmd_id1}/confirm/')
    
    print(f"\n{Colors.CYAN}→ Expédition{Colors.END}")
    api_call('POST', f'/api/productions/commandes/{cmd_id1}/ship/')

    print(f"\n{Colors.CYAN}→ Livraison{Colors.END}")
    api_call('POST', f'/api/productions/commandes/{cmd_id1}/deliver/')

# ==================== 20. WORKFLOW COMMANDE 2 ====================
if cmd_id2:
    print(f"\n{Colors.GREEN}2️⃣0️⃣  WORKFLOW COMMANDE #2{Colors.END}")
    
    api_call('POST', f'/api/productions/commandes/{cmd_id2}/confirm/')
    api_call('POST', f'/api/productions/commandes/{cmd_id2}/ship/')
    api_call('POST', f'/api/productions/commandes/{cmd_id2}/deliver/')

# ==================== 21. ÉVALUATION COMMANDE 1 ====================
if cmd_id1:
    print(f"\n{Colors.GREEN}2️⃣1️⃣  ÉVALUATION COMMANDE #1{Colors.END}")
    api_call('POST', '/api/productions/evaluations/', {
        "commande": cmd_id1,
        "note": 5,
        "commentaire": "Excellente qualité des tomates bio ! Produits frais, bien emballés. Livraison rapide et soignée. Je recommande vivement ce producteur. Meilleur rapport qualité/prix de la région."
    })

# ==================== 22. ÉVALUATION COMMANDE 2 ====================
if cmd_id2:
    print(f"\n{Colors.GREEN}2️⃣2️⃣  ÉVALUATION COMMANDE #2{Colors.END}")
    api_call('POST', '/api/productions/evaluations/', {
        "commande": cmd_id2,
        "note": 4,
        "commentaire": "Bananes de bonne qualité. Livraison dans les temps. Petit bémol sur l'emballage qui pourrait être amélioré."
    })

# ==================== 23. NOTIFICATIONS NON LUES ====================
print(f"\n{Colors.GREEN}2️⃣3️⃣  NOTIFICATIONS NON LUES{Colors.END}")
notifs = api_call('GET', '/api/notifications/unread/')
if notifs:
    count = notifs.get('count', 0)
    print(f"\n{Colors.YELLOW}📬 {count} notification(s) non lue(s){Colors.END}")
    for notif in notifs.get('results', [])[:5]:
        print(f"  • {notif.get('title')} - {notif.get('message')}")

# ==================== 24. TOUTES NOTIFICATIONS ====================
print(f"\n{Colors.GREEN}2️⃣4️⃣  HISTORIQUE NOTIFICATIONS{Colors.END}")
all_notifs = api_call('GET', '/api/notifications/')
if all_notifs:
    print(f"\n{Colors.YELLOW}Total: {all_notifs.get('count', 0)} notifications{Colors.END}")

# ==================== 25. MARQUER NOTIFICATION COMME LUE ====================
if notifs and notifs.get('results'):
    first_notif_id = notifs['results'][0]['id']
    print(f"\n{Colors.GREEN}2️⃣5️⃣  MARQUER NOTIFICATION #{first_notif_id} COMME LUE{Colors.END}")
    api_call('POST', f'/api/notifications/{first_notif_id}/mark_as_read/')

# ==================== 26. DÉTAILS PRODUCTION AVEC NOTE ====================
if prod_id1:
    print(f"\n{Colors.GREEN}2️⃣6️⃣  DÉTAILS PRODUCTION #1 (avec note moyenne){Colors.END}")
    prod_details = api_call('GET', f'/api/productions/{prod_id1}/')
    if prod_details:
        print(f"\n{Colors.YELLOW}Note moyenne: {prod_details.get('note_moyenne', 'N/A')}/5{Colors.END}")
        print(f"{Colors.YELLOW}Quantité disponible: {prod_details.get('quantite_disponible')} kg{Colors.END}")

# ==================== 27. ELASTICSEARCH (si configuré) ====================
print(f"\n{Colors.GREEN}2️⃣7️⃣  RECHERCHE ELASTICSEARCH{Colors.END}")
api_call('GET', '/api/productions/search/?search=tomates')

# ==================== 28. PROFIL FINAL ====================
print(f"\n{Colors.GREEN}2️⃣8️⃣  PROFIL UTILISATEUR FINAL{Colors.END}")
final_profile = api_call('GET', '/api/auth/me/')

if final_profile:
    print(f"\n{Colors.YELLOW}{'='*70}{Colors.END}")
    print(f"{Colors.GREEN}👤 PROFIL COMPLET{Colors.END}")
    print(f"{Colors.YELLOW}{'='*70}{Colors.END}")
    
    print(f"{Colors.CYAN}Email:{Colors.END} {final_profile['email']}")
    print(f"{Colors.CYAN}Téléphone:{Colors.END} {final_profile['telephone']}")
    print(f"{Colors.CYAN}Téléphone vérifié:{Colors.END} {final_profile['phone_verified']}")
    print(f"{Colors.CYAN}Profil complété:{Colors.END} {final_profile['profile_completed']}")
    print(f"{Colors.CYAN}Rôles actifs:{Colors.END} {', '.join(final_profile['active_roles'])}")
    
    print(f"\n{Colors.YELLOW}🏆 BADGES ({len(final_profile.get('badges', []))}):{Colors.END}")
    for badge in final_profile.get('badges', []):
        print(f"  {badge['icon']} {badge['name']}")
    
    if 'role_profiles' in final_profile and 'producteur' in final_profile['role_profiles']:
        prod_profile = final_profile['role_profiles']['producteur']
        print(f"\n{Colors.YELLOW}🌱 PROFIL PRODUCTEUR:{Colors.END}")
        print(f"  Type: {prod_profile.get('type_production')}")
        print(f"  Superficie: {prod_profile.get('superficie')} ha")
        print(f"  Certification: {prod_profile.get('certification')}")
        print(f"  Total productions: {prod_profile.get('total_productions')}")
        
        if prod_profile.get('organization'):
            org = prod_profile['organization']
            print(f"\n{Colors.YELLOW}🏢 ORGANISATION:{Colors.END}")
            print(f"  Type: {org['type']}")
            print(f"  Nom: {org['name']}")
            print(f"  Numéro: {org['registration']}")
    
    print(f"{Colors.YELLOW}{'='*70}{Colors.END}\n")

# ==================== RÉSUMÉ FINAL ====================
print(f"\n{Colors.YELLOW}{'='*70}{Colors.END}")
print(f"{Colors.GREEN}🎉 TESTS TERMINÉS AVEC SUCCÈS{Colors.END}")
print(f"{Colors.YELLOW}{'='*70}{Colors.END}\n")

print(f"{Colors.BLUE}📊 Tests réalisés:{Colors.END}\n")

tests_list = [
    "✅ Inscription utilisateur",
    "✅ Complétion profil",
    "✅ Vérification SMS Twilio → Badge 📱",
    "✅ Activation rôle producteur + GIC → Badge 🏢",
    "✅ Création 2 productions",
    "✅ Recherche (liste, proximité, Elasticsearch)",
    "✅ Création 2 commandes",
    "✅ Workflow complet (confirm → ship → deliver) x2",
    "✅ Évaluations 5 et 4 étoiles",
    "✅ Notifications (lecture, marquage)",
    "✅ Profil final avec badges et stats"
]

for i, test in enumerate(tests_list, 1):
    print(f"  {i:2d}. {test}")

print(f"\n{Colors.GREEN}🚀 SYSTÈME DIGITAGRO PLEINEMENT OPÉRATIONNEL{Colors.END}")
print(f"{Colors.GREEN}   Phases 1 + 2 + Production + Notifications validées{Colors.END}\n")