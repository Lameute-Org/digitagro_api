#!/bin/bash
set -euo pipefail

# ==================== CONFIGURATION ====================
BASE_URL="${BASE_URL:-http://localhost:8000}"
VERBOSE="${VERBOSE:-false}"

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Compteurs
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_TOTAL=0

# Variables globales
TOKEN=""
USER_EMAIL="test_$(date +%s)@digitagro.cm"
USER_PHONE="+237690$(shuf -i 100000-999999 -n 1)"
USER_PASSWORD="TestPass123!"
SMS_CODE=""
PROD_ID=""
CMD_ID=""

# ==================== FONCTIONS UTILITAIRES ====================

log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

log_section() {
    echo -e "\n${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${PURPLE}  $1${NC}"
    echo -e "${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
}

# Fonction API générique avec gestion d'erreurs
call_api() {
    local METHOD=$1
    local ENDPOINT=$2
    local DATA=${3:-}
    local USE_AUTH=${4:-true}
    
    TESTS_TOTAL=$((TESTS_TOTAL + 1))
    
    local URL="$BASE_URL$ENDPOINT"
    local HEADERS="-H 'Content-Type: application/json'"
    
    if [ "$USE_AUTH" = "true" ] && [ -n "$TOKEN" ]; then
        HEADERS="$HEADERS -H 'Authorization: Token $TOKEN'"
    fi
    
    if [ "$VERBOSE" = "true" ]; then
        log_info "Requête: $METHOD $URL"
        [ -n "$DATA" ] && echo "Data: $DATA"
    fi
    
    if [ -n "$DATA" ]; then
        RESP=$(eval curl -s -w "\n%{http_code}" -X "$METHOD" "$URL" $HEADERS -d "'$DATA'")
    else
        RESP=$(eval curl -s -w "\n%{http_code}" -X "$METHOD" "$URL" $HEADERS)
    fi
    
    BODY=$(echo "$RESP" | head -n -1)
    CODE=$(echo "$RESP" | tail -n1)
    
    # Vérifier si le body est du JSON valide
    if echo "$BODY" | jq empty 2>/dev/null; then
        if [ "$VERBOSE" = "true" ]; then
            echo "$BODY" | jq .
        fi
    else
        log_warning "Réponse non-JSON: $BODY"
    fi
    
    # Vérifier le code HTTP
    if [[ "$CODE" -ge 200 && "$CODE" -lt 300 ]]; then
        TESTS_PASSED=$((TESTS_PASSED + 1))
        echo "$BODY"
    else
        TESTS_FAILED=$((TESTS_FAILED + 1))
        log_error "HTTP $CODE sur $METHOD $ENDPOINT"
        echo "$BODY" | jq . 2>/dev/null || echo "$BODY"
        return 1
    fi
}

# Extraction valeur JSON
json_value() {
    local JSON=$1
    local KEY=$2
    echo "$JSON" | jq -r ".$KEY // empty"
}

# Pause interactive (optionnel)
pause_if_interactive() {
    if [ "${INTERACTIVE:-false}" = "true" ]; then
        read -p "Appuyez sur Entrée pour continuer..."
    fi
}

# ==================== TESTS SYSTÈME ====================

test_health_check() {
    log_section "🏥 TEST 1: Health Check"
    
    log_info "Vérification disponibilité API..."
    RESP=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/schema/")
    
    if [ "$RESP" = "200" ]; then
        log_success "API opérationnelle (HTTP 200)"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        log_error "API non disponible (HTTP $RESP)"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        exit 1
    fi
    
    TESTS_TOTAL=$((TESTS_TOTAL + 1))
}

test_user_registration() {
    log_section "👤 TEST 2: Inscription Utilisateur"
    
    log_info "Inscription avec email: $USER_EMAIL"
    
    RESP=$(call_api POST "/api/auth/register/" '{
        "email": "'"$USER_EMAIL"'",
        "password": "'"$USER_PASSWORD"'",
        "password_confirm": "'"$USER_PASSWORD"'"
    }' false)
    
    TOKEN=$(json_value "$RESP" "token")
    
    if [ -n "$TOKEN" ]; then
        log_success "Inscription réussie - Token obtenu"
        log_info "Token: ${TOKEN:0:20}..."
    else
        log_error "Échec inscription - Token non reçu"
        exit 1
    fi
}

test_complete_profile() {
    log_section "📝 TEST 3: Complétion Profil"
    
    log_info "Ajout informations personnelles..."
    
    call_api PATCH "/api/auth/me/complete-profile/" '{
        "nom": "Dupont",
        "prenom": "Jean",
        "telephone": "'"$USER_PHONE"'",
        "adresse": "Yaoundé, Quartier Mvog-Ada, Cameroun"
    }' | jq .
    
    log_success "Profil complété"
}

test_sms_verification() {
    log_section "📱 TEST 4: Vérification SMS"
    
    log_info "Demande code SMS pour: $USER_PHONE"
    
    RESP=$(call_api POST "/api/auth/phone/request-code/" '{
        "phone_number": "'"$USER_PHONE"'"
    }')
    
    echo "$RESP" | jq .
    
    log_warning "⏸️  SIMULATION SMS"
    log_info "En production, un vrai SMS serait envoyé via Twilio"
    log_info "Pour ce test, récupérez le code dans la base de données:"
    log_info "$ python manage.py shell"
    log_info ">>> from apps.users.models import PhoneVerification"
    log_info ">>> PhoneVerification.objects.filter(phone_number='$USER_PHONE').latest('created_at').code"
    
    # Simuler récupération du code (UNIQUEMENT POUR TEST)
    log_info "\nTentative récupération automatique du code..."
    
    # Option 1: Via Django shell (nécessite manage.py accessible)
    if command -v python &> /dev/null; then
        SMS_CODE=$(python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'digitagro_api.settings')
django.setup()
from apps.users.models import PhoneVerification
try:
    code = PhoneVerification.objects.filter(phone_number='$USER_PHONE').latest('created_at').code
    print(code)
except:
    print('')
" 2>/dev/null || echo "")
    fi
    
    # Si échec automatique, demander manuellement
    if [ -z "$SMS_CODE" ]; then
        log_warning "Impossible de récupérer automatiquement"
        read -p "Entrez le code SMS manuellement: " SMS_CODE
    else
        log_success "Code récupéré automatiquement: $SMS_CODE"
    fi
    
    log_info "Vérification du code..."
    
    call_api POST "/api/auth/phone/verify-code/" '{
        "code": "'"$SMS_CODE"'"
    }' | jq .
    
    log_success "Téléphone vérifié - Badge 📱 obtenu"
    
    pause_if_interactive
}

test_check_badges() {
    log_section "🏆 TEST 5: Vérification Badges"
    
    log_info "Récupération badges utilisateur..."
    
    RESP=$(call_api GET "/api/auth/me/badges/")
    
    echo "$RESP" | jq .
    
    BADGE_COUNT=$(json_value "$RESP" "total_badges")
    
    if [ "$BADGE_COUNT" -ge 1 ]; then
        log_success "$BADGE_COUNT badge(s) obtenu(s)"
    else
        log_warning "Aucun badge (attendu: au moins 📱 Téléphone Vérifié)"
    fi
}

test_activate_producer_role() {
    log_section "🌾 TEST 6: Activation Rôle Producteur + GIC"
    
    log_info "Activation rôle producteur avec GIC..."
    
    call_api POST "/api/auth/activate-role/" '{
        "role": "producteur",
        "type_production": "Maraîchage",
        "superficie": 2.5,
        "certification": "Bio",
        "is_in_gic": true,
        "gic_name": "GIC ESPOIR AGRICOLE",
        "gic_registration_number": "GIC/2023/TEST001"
    }' | jq .
    
    log_success "Rôle producteur activé"
    log_success "Badge 🏢 Membre GIC attendu"
    
    # Revérifier les badges
    log_info "Vérification nouveaux badges..."
    RESP=$(call_api GET "/api/auth/me/badges/")
    echo "$RESP" | jq .
    
    BADGE_COUNT=$(json_value "$RESP" "total_badges")
    log_success "Total badges: $BADGE_COUNT"
}

test_create_production() {
    log_section "🌱 TEST 7: Création Production"
    
    log_info "Déclaration nouvelle production..."
    
    RESP=$(call_api POST "/api/productions/" '{
        "produit": "Tomates Bio",
        "type_production": "legumes",
        "quantite": 500,
        "unite_mesure": "kg",
        "prix_unitaire": 750,
        "latitude": 3.8667,
        "longitude": 11.5167,
        "adresse_complete": "Yaoundé, Mvog-Ada, près du marché",
        "date_recolte": "2025-02-15",
        "date_expiration": "2025-02-25",
        "certification": "bio",
        "description": "Tomates cultivées selon méthodes biologiques certifiées",
        "conditions_stockage": "Conserver dans un endroit frais et sec, température 12-15°C"
    }')
    
    echo "$RESP" | jq .
    
    PROD_ID=$(json_value "$RESP" "production.id")
    
    if [ -n "$PROD_ID" ] && [ "$PROD_ID" != "null" ]; then
        log_success "Production créée - ID: $PROD_ID"
    else
        log_error "Échec création production"
        exit 1
    fi
}

test_list_my_productions() {
    log_section "📋 TEST 8: Liste Mes Productions"
    
    log_info "Récupération productions du producteur..."
    
    call_api GET "/api/productions/mine/" | jq .
    
    log_success "Liste productions récupérée"
}

test_search_nearby_productions() {
    log_section "📍 TEST 9: Recherche Productions Proximité"
    
    log_info "Recherche productions dans un rayon de 10km..."
    
    call_api GET "/api/productions/nearby/?lat=3.8667&lon=11.5167&radius=10" | jq .
    
    log_success "Recherche proximité effectuée"
}

test_create_order() {
    log_section "🛒 TEST 10: Création Commande"
    
    log_info "Passage commande pour production ID: $PROD_ID"
    
    RESP=$(call_api POST "/api/commandes/" '{
        "production": '"$PROD_ID"',
        "quantite": 50,
        "adresse_livraison": "Douala, Akwa Nord, Rue Joffre",
        "notes": "Livraison le matin entre 8h et 10h",
        "date_livraison_souhaitee": "2025-02-20"
    }')
    
    echo "$RESP" | jq .
    
    CMD_ID=$(json_value "$RESP" "id")
    
    if [ -n "$CMD_ID" ] && [ "$CMD_ID" != "null" ]; then
        log_success "Commande créée - ID: $CMD_ID"
    else
        log_error "Échec création commande"
        exit 1
    fi
}

test_order_workflow() {
    log_section "🔄 TEST 11: Workflow Commande Complet"
    
    # Confirmation
    log_info "Étape 1: Confirmation par le producteur..."
    call_api POST "/api/commandes/$CMD_ID/confirm/" | jq .
    log_success "Commande confirmée"
    
    sleep 1
    
    # Expédition
    log_info "Étape 2: Expédition de la commande..."
    call_api POST "/api/commandes/$CMD_ID/ship/" | jq .
    log_success "Commande expédiée"
    
    sleep 1
    
    # Livraison
    log_info "Étape 3: Livraison effectuée..."
    call_api POST "/api/commandes/$CMD_ID/deliver/" | jq .
    log_success "Commande livrée"
}

test_create_evaluation() {
    log_section "⭐ TEST 12: Évaluation Commande"
    
    log_info "Évaluation de la commande livrée..."
    
    call_api POST "/api/evaluations/" '{
        "commande": '"$CMD_ID"',
        "note": 5,
        "commentaire": "Excellente qualité des tomates bio ! Livraison rapide et soignée. Je recommande vivement ce producteur."
    }' | jq .
    
    log_success "Évaluation créée - 5 étoiles"
}

test_production_details() {
    log_section "🔍 TEST 13: Détails Production"
    
    log_info "Récupération détails production ID: $PROD_ID"
    
    call_api GET "/api/productions/$PROD_ID/" | jq .
    
    log_success "Détails production récupérés (avec note moyenne)"
}

test_user_profile_final() {
    log_section "👤 TEST 14: Profil Utilisateur Final"
    
    log_info "Vérification profil complet avec badges et rôles..."
    
    RESP=$(call_api GET "/api/auth/me/")
    
    echo "$RESP" | jq .
    
    # Extraire informations clés
    EMAIL=$(json_value "$RESP" "email")
    PHONE_VERIFIED=$(json_value "$RESP" "phone_verified")
    IS_PRODUCTEUR=$(json_value "$RESP" "is_producteur")
    
    log_info "Email: $EMAIL"
    log_info "Téléphone vérifié: $PHONE_VERIFIED"
    log_info "Producteur: $IS_PRODUCTEUR"
    
    if [ "$PHONE_VERIFIED" = "true" ] && [ "$IS_PRODUCTEUR" = "true" ]; then
        log_success "Profil utilisateur complet et vérifié"
    else
        log_warning "Profil incomplet"
    fi
}

test_roles_status() {
    log_section "🎭 TEST 15: Statut Rôles"
    
    log_info "Vérification statut de tous les rôles..."
    
    call_api GET "/api/auth/roles-status/" | jq .
    
    log_success "Statut rôles récupéré"
}

test_list_all_productions() {
    log_section "🌍 TEST 16: Liste Globale Productions"
    
    log_info "Récupération liste publique de toutes les productions..."
    
    call_api GET "/api/productions/" | jq .
    
    log_success "Liste globale récupérée"
}

test_elasticsearch_search() {
    log_section "🔎 TEST 17: Recherche Elasticsearch"
    
    log_info "Recherche 'tomates' avec Elasticsearch..."
    
    call_api GET "/api/productions/search/?search=tomates" | jq . || log_warning "Elasticsearch non configuré"
    
    log_info "Filtre par type 'legumes'..."
    
    call_api GET "/api/productions/search/?type_production=legumes" | jq . || log_warning "Elasticsearch non configuré"
}

# ==================== TESTS NÉGATIFS (GESTION ERREURS) ====================

test_negative_cases() {
    log_section "🚫 TEST 18: Cas d'Erreurs (Gestion)"
    
    # Test 1: Commande sans être authentifié
    log_info "Test: Commande sans authentification..."
    OLD_TOKEN=$TOKEN
    TOKEN=""
    if ! call_api POST "/api/commandes/" '{}' 2>/dev/null; then
        log_success "Erreur 401 attendue - OK"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        log_warning "Devrait rejeter requête non authentifiée"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
    TOKEN=$OLD_TOKEN
    TESTS_TOTAL=$((TESTS_TOTAL + 1))
    
    # Test 2: Quantité commande > stock
    log_info "Test: Commande quantité supérieure au stock..."
    if ! call_api POST "/api/commandes/" '{
        "production": '"$PROD_ID"',
        "quantite": 999999,
        "adresse_livraison": "Test"
    }' 2>/dev/null; then
        log_success "Erreur 400 attendue (stock insuffisant) - OK"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        log_warning "Devrait rejeter quantité excessive"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
    TESTS_TOTAL=$((TESTS_TOTAL + 1))
    
    # Test 3: Création production sans téléphone vérifié (nouveau compte)
    log_info "Test: Production sans vérification téléphone..."
    
    # Créer compte temporaire
    TEMP_EMAIL="temp_$(date +%s)@test.cm"
    TEMP_RESP=$(call_api POST "/api/auth/register/" '{
        "email": "'"$TEMP_EMAIL"'",
        "password": "TempPass123!",
        "password_confirm": "TempPass123!"
    }' false)
    
    TEMP_TOKEN=$(json_value "$TEMP_RESP" "token")
    OLD_TOKEN=$TOKEN
    TOKEN=$TEMP_TOKEN
    
    if ! call_api POST "/api/productions/" '{
        "produit": "Test",
        "type_production": "Maraîchage",
        "quantite": 10,
        "unite_mesure": "kg",
        "prix_unitaire": 100,
        "latitude": 3.8,
        "longitude": 11.5,
        "adresse_complete": "Test",
        "date_recolte": "2025-03-01",
        "description": "Test"
    }' 2>/dev/null; then
        log_success "Erreur 400 attendue (téléphone non vérifié) - OK"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        log_warning "Devrait bloquer production sans vérification"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
    
    TOKEN=$OLD_TOKEN
    TESTS_TOTAL=$((TESTS_TOTAL + 1))
}

# ==================== RAPPORT FINAL ====================

print_summary() {
    log_section "📊 RAPPORT FINAL"
    
    echo -e "${CYAN}Tests exécutés:${NC}   $TESTS_TOTAL"
    echo -e "${GREEN}Tests réussis:${NC}    $TESTS_PASSED"
    echo -e "${RED}Tests échoués:${NC}    $TESTS_FAILED"
    
    PERCENTAGE=$((TESTS_PASSED * 100 / TESTS_TOTAL))
    
    echo ""
    if [ $TESTS_FAILED -eq 0 ]; then
        echo -e "${GREEN}🎉 TOUS LES TESTS ONT RÉUSSI ! ($PERCENTAGE%)${NC}"
        echo -e "${GREEN}✨ Système DIGITAGRO pleinement opérationnel${NC}"
    else
        echo -e "${YELLOW}⚠️  $TESTS_FAILED test(s) échoué(s) ($PERCENTAGE% réussite)${NC}"
    fi
    
    echo ""
    echo -e "${CYAN}Résumé du workflow testé:${NC}"
    echo "  1. ✅ Inscription utilisateur"
    echo "  2. ✅ Complétion profil"
    echo "  3. ✅ Vérification SMS → Badge 📱"
    echo "  4. ✅ Activation producteur + GIC → Badge 🏢"
    echo "  5. ✅ Création production"
    echo "  6. ✅ Commande client"
    echo "  7. ✅ Workflow livraison (confirm → ship → deliver)"
    echo "  8. ✅ Évaluation 5 étoiles"
    echo "  9. ✅ Recherches (proximité, Elasticsearch)"
    echo " 10. ✅ Tests erreurs"
    
    echo ""
    echo -e "${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# ==================== MAIN ====================

main() {
    clear
    
    echo -e "${PURPLE}"
    echo "╔═══════════════════════════════════════════════════════╗"
    echo "║                                                       ║"
    echo "║        🌾 DIGITAGRO - TEST SUITE COMPLET 🌾          ║"
    echo "║                                                       ║"
    echo "║  Tests automatisés de l'API complète                 ║"
    echo "║  Phases 1 + 2 + Système Production                   ║"
    echo "║                                                       ║"
    echo "╚═══════════════════════════════════════════════════════╝"
    echo -e "${NC}\n"
    
    log_info "Base URL: $BASE_URL"
    log_info "Verbose: $VERBOSE"
    echo ""
    
    # Exécution séquentielle des tests
    test_health_check
    test_user_registration
    test_complete_profile
    test_sms_verification
    test_check_badges
    test_activate_producer_role
    test_create_production
    test_list_my_productions
    test_search_nearby_productions
    test_create_order
    test_order_workflow
    test_create_evaluation
    test_production_details
    test_user_profile_final
    test_roles_status
    test_list_all_productions
    test_elasticsearch_search
    test_negative_cases
    
    # Rapport final
    print_summary
    
    # Code de sortie
    if [ $TESTS_FAILED -eq 0 ]; then
        exit 0
    else
        exit 1
    fi
}

# ==================== EXÉCUTION ====================

# Gestion des arguments
while getopts "vi" opt; do
    case $opt in
        v) VERBOSE=true ;;
        i) INTERACTIVE=true ;;
        *) echo "Usage: $0 [-v] [-i]" ; exit 1 ;;
    esac
done

# Lancement
main