#!/bin/bash
set -euo pipefail

TOKEN="480dbfcfe7ff951cda527abc05ed6e10d811f76a9d4357e810171d3455646d68"
BASE_URL="http://localhost:8000"
AUTH_HEADER="Authorization: Token $TOKEN"

# Petite fonction pour lancer une requête et vérifier si JSON
call_api() {
  local METHOD=$1
  local URL=$2
  local DATA=${3:-}

  if [ -n "$DATA" ]; then
    RESP=$(curl -s -w "\n%{http_code}" -X $METHOD "$URL" \
      -H "$AUTH_HEADER" \
      -H "Content-Type: application/json" \
      -d "$DATA")
  else
    RESP=$(curl -s -w "\n%{http_code}" -X $METHOD "$URL" -H "$AUTH_HEADER")
  fi

  BODY=$(echo "$RESP" | head -n -1)
  CODE=$(echo "$RESP" | tail -n1)

  if [[ "$CODE" -lt 200 || "$CODE" -ge 300 ]]; then
    echo "❌ Erreur HTTP $CODE sur $URL"
    echo "Réponse : $BODY"
    exit 1
  fi

  echo "$BODY"
}

echo "👤 Vérification profil connecté..."
call_api GET "$BASE_URL/api/auth/me/" | jq .

echo "🌱 Création d'une production..."
PROD_BODY=$(call_api POST "$BASE_URL/api/productions/" '{
  "produit": "Tomates",
  "type_production": "legumes",
  "quantite": 100,
  "unite_mesure": "kg",
  "prix_unitaire": 500,
  "latitude": 3.8667,
  "longitude": 11.5167,
  "adresse_complete": "Yaoundé, Cameroun",
  "date_recolte": "2025-02-15",
  "certification": "bio",
  "description": "Tomates fraîches bio",
  "conditions_stockage": "Conserver au frais"
}')
echo "$PROD_BODY" | jq .
PROD_ID=$(echo "$PROD_BODY" | jq -r '.id')

echo "✅ Production ID=$PROD_ID"

echo "📦 Passage d'une commande..."
CMD_BODY=$(call_api POST "$BASE_URL/api/commandes/" '{
  "production": '"$PROD_ID"',
  "quantite": 10,
  "adresse_livraison": "Douala, Akwa Nord",
  "notes": "Livraison le matin",
  "date_livraison_souhaitee": "2025-02-20"
}')
echo "$CMD_BODY" | jq .
CMD_ID=$(echo "$CMD_BODY" | jq -r '.id')

echo "✅ Commande ID=$CMD_ID"

echo "✅ Confirmation de la commande..."
call_api POST "$BASE_URL/api/commandes/$CMD_ID/confirm/" | jq .

echo "🚚 Expédition de la commande..."
call_api POST "$BASE_URL/api/commandes/$CMD_ID/ship/" | jq .

echo "📬 Livraison de la commande..."
call_api POST "$BASE_URL/api/commandes/$CMD_ID/deliver/" | jq .

echo "⭐ Évaluation de la commande..."
call_api POST "$BASE_URL/api/evaluations/" '{
  "commande": '"$CMD_ID"',
  "note": 5,
  "commentaire": "Excellente qualité, livraison rapide"
}' | jq .

echo "🎉 Tous les tests ont réussi sans erreur."
