from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.users.models import Producteur, CustomUser
from decimal import Decimal
from math import radians, cos, sin, asin, sqrt

class Production(models.Model):
    TYPE_CHOICES = [
        ('fruits', 'Fruits'),
        ('legumes', 'Légumes'),
        ('cereales', 'Céréales'),
        ('tubercules', 'Tubercules'),
        ('elevage', 'Élevage'),
        ('produits_transformes', 'Produits Transformés'),
    ]
    
    UNITE_CHOICES = [
        ('kg', 'Kilogramme'),
        ('tonne', 'Tonne'),
        ('unite', 'Unité'),
        ('litre', 'Litre'),
        ('sac', 'Sac'),
    ]
    
    CERTIFICATION_CHOICES = [
        ('bio', 'Bio'),
        ('standard', 'Standard'),
        ('agroecologique', 'Agroécologique'),
    ]
    
    producteur = models.ForeignKey(Producteur, on_delete=models.CASCADE, related_name='productions')
    produit = models.CharField(max_length=100, db_index=True)
    type_production = models.CharField(max_length=30, choices=TYPE_CHOICES, db_index=True)
    quantite = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    unite_mesure = models.CharField(max_length=20, choices=UNITE_CHOICES)
    prix_unitaire = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    
    # Géolocalisation (sans PostGIS)
    latitude = models.DecimalField(max_digits=10, decimal_places=7, db_index=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, db_index=True)
    adresse_complete = models.TextField()
    
    disponible = models.BooleanField(default=True, db_index=True)
    date_recolte = models.DateField()
    date_expiration = models.DateField(null=True, blank=True)
    certification = models.CharField(max_length=20, choices=CERTIFICATION_CHOICES, default='standard')
    description = models.TextField()
    conditions_stockage = models.TextField(blank=True)
    
    date_creation = models.DateTimeField(auto_now_add=True, db_index=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date_creation']
        indexes = [
            models.Index(fields=['produit', 'disponible']),
            models.Index(fields=['type_production', 'disponible']),
            models.Index(fields=['producteur', 'disponible']),
            models.Index(fields=['-date_creation']),
        ]
    
    def __str__(self):
        return f"{self.produit} - {self.quantite}{self.unite_mesure}"
    
    @property
    def quantite_disponible(self):
        """Quantité restante après commandes"""
        commandes_validees = self.commandes.filter(
            statut__in=['confirmee', 'en_preparation', 'expediee']
        ).aggregate(total=models.Sum('quantite'))['total'] or 0
        return self.quantite - commandes_validees
    
    @property
    def note_moyenne(self):
        """Note moyenne des évaluations"""
        evaluations = self.commandes.filter(evaluation__isnull=False)
        if not evaluations.exists():
            return None
        return evaluations.aggregate(avg=models.Avg('evaluation__note'))['avg']


class PhotoProduction(models.Model):
    production = models.ForeignKey(Production, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField(upload_to='productions/%Y/%m/')
    ordre = models.PositiveSmallIntegerField(default=0)
    date_ajout = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['ordre', 'date_ajout']
        constraints = [
            models.CheckConstraint(
                check=models.Q(ordre__lte=4),
                name='max_5_photos'
            )
        ]


class Commande(models.Model):
    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('confirmee', 'Confirmée'),
        ('en_preparation', 'En préparation'),
        ('expediee', 'Expédiée'),
        ('livree', 'Livrée'),
        ('annulee', 'Annulée'),
    ]
    
    production = models.ForeignKey(Production, on_delete=models.CASCADE, related_name='commandes')
    client = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='commandes_production')
    
    quantite = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    montant_total = models.DecimalField(max_digits=12, decimal_places=2)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_attente', db_index=True)
    
    adresse_livraison = models.TextField()
    notes = models.TextField(blank=True)
    date_livraison_souhaitee = models.DateField(null=True, blank=True)
    
    date_creation = models.DateTimeField(auto_now_add=True, db_index=True)
    date_confirmation = models.DateTimeField(null=True, blank=True)
    date_expedition = models.DateTimeField(null=True, blank=True)
    date_livraison = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-date_creation']
        indexes = [
            models.Index(fields=['client', '-date_creation']),
            models.Index(fields=['production', '-date_creation']),
            models.Index(fields=['statut', '-date_creation']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.montant_total:
            self.montant_total = self.quantite * self.production.prix_unitaire
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Commande #{self.id} - {self.production.produit}"


class Paiement(models.Model):
    METHODE_CHOICES = [
        ('orange_money', 'Orange Money'),
        ('mtn_money', 'MTN Money'),
        ('virement', 'Virement'),
        ('cash', 'Espèces'),
    ]
    
    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('valide', 'Validé'),
        ('echoue', 'Échoué'),
        ('rembourse', 'Remboursé'),
    ]
    
    commande = models.OneToOneField(Commande, on_delete=models.CASCADE, related_name='paiement')
    montant = models.DecimalField(max_digits=12, decimal_places=2)
    methode = models.CharField(max_length=20, choices=METHODE_CHOICES)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_attente', db_index=True)
    reference_transaction = models.CharField(max_length=100, unique=True)
    
    date_creation = models.DateTimeField(auto_now_add=True)
    date_paiement = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-date_creation']
    
    def __str__(self):
        return f"Paiement #{self.id} - {self.montant} FCFA"


class Evaluation(models.Model):
    commande = models.OneToOneField(Commande, on_delete=models.CASCADE, related_name='evaluation')
    note = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    commentaire = models.TextField()
    date_creation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date_creation']
    
    def __str__(self):
        return f"Évaluation {self.note}/5 - Commande #{self.commande.id}"


class PhotoEvaluation(models.Model):
    evaluation = models.ForeignKey(Evaluation, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField(upload_to='evaluations/%Y/%m/')
    date_ajout = models.DateTimeField(auto_now_add=True)

