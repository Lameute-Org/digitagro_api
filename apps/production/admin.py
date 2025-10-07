from django.contrib import admin
from .models import Production, PhotoProduction, Commande, Paiement, Evaluation

class PhotoProductionInline(admin.TabularInline):
    model = PhotoProduction
    extra = 1
    max_num = 5

@admin.register(Production)
class ProductionAdmin(admin.ModelAdmin):
    list_display = ['produit', 'producteur', 'quantite', 'prix_unitaire', 'disponible', 'date_creation']
    list_filter = ['type_production', 'disponible', 'certification']
    search_fields = ['produit', 'producteur__user__nom']
    inlines = [PhotoProductionInline]

@admin.register(Commande)
class CommandeAdmin(admin.ModelAdmin):
    list_display = ['id', 'production', 'client', 'quantite', 'montant_total', 'statut', 'date_creation']
    list_filter = ['statut', 'date_creation']
    search_fields = ['production__produit', 'client__nom']

admin.site.register(Paiement)
admin.site.register(Evaluation)