# apps/core/models.py

from django.db import models
from django.urls import reverse
from django.core.validators import RegexValidator
from django.contrib.auth import get_user_model

User = get_user_model()


class Supplier(models.Model):
    """Modèle pour gérer les fournisseurs"""

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Actif"
        INACTIVE = "INACTIVE", "Inactif"
        SUSPENDED = "SUSPENDED", "Suspendu"

    name = models.CharField(max_length=200, verbose_name="Nom du fournisseur")
    contact_person = models.CharField(max_length=150, verbose_name="Personne de contact")
    email = models.EmailField(verbose_name="Email")
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Le numéro doit être au format: '+999999999'. 15 chiffres maximum."
    )
    phone = models.CharField(validators=[phone_regex], max_length=17, verbose_name="Téléphone")
    address = models.TextField(verbose_name="Adresse complète")
    city = models.CharField(max_length=100, verbose_name="Ville")
    postal_code = models.CharField(max_length=20, verbose_name="Code postal")
    country = models.CharField(max_length=100, default="France", verbose_name="Pays")
    tax_number = models.CharField(max_length=50, blank=True, verbose_name="Numéro TVA")
    payment_terms = models.CharField(max_length=100, default="30 jours", verbose_name="Conditions de paiement")
    credit_limit = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="Limite de crédit (€)")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE, verbose_name="Statut")
    notes = models.TextField(blank=True, verbose_name="Notes internes")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Modifié le")

    class Meta:
        verbose_name = "Fournisseur"
        verbose_name_plural = "Fournisseurs"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} - {self.city}"

    def get_absolute_url(self):
        return reverse('core:supplier_detail', kwargs={'pk': self.pk})

    def is_active(self):
        return self.status == self.Status.ACTIVE

    def get_status_badge_class(self):
        return {
            self.Status.ACTIVE: "badge-success",
            self.Status.INACTIVE: "badge-secondary",
            self.Status.SUSPENDED: "badge-warning",
        }.get(self.status, "badge-secondary")


class Category(models.Model):
    """Modèle pour les catégories de produits"""

    name = models.CharField(max_length=100, unique=True, verbose_name="Nom de la catégorie")
    description = models.TextField(blank=True, verbose_name="Description")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")

    class Meta:
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"
        ordering = ['name']

    def __str__(self):
        return self.name


class Product(models.Model):
    """Modèle pour les produits"""

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Actif"
        INACTIVE = "INACTIVE", "Inactif"
        OUT_OF_STOCK = "OUT_OF_STOCK", "Rupture de stock"

    name = models.CharField(max_length=200, verbose_name="Nom du produit")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name="Catégorie")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Prix (€)")
    stock_quantity = models.PositiveIntegerField(default=0, verbose_name="Quantité en stock")
    description = models.TextField(blank=True, verbose_name="Description")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE, verbose_name="Statut")
    image = models.ImageField(upload_to='products/', blank=True, null=True, verbose_name="Image produit")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Modifié le")

    class Meta:
        verbose_name = "Produit"
        verbose_name_plural = "Produits"
        ordering = ['name']

    def __str__(self):
        return self.name

    def is_in_stock(self):
        return self.stock_quantity > 0 and self.status == self.Status.ACTIVE


class Sale(models.Model):
    """Modèle pour les ventes"""

    class Status(models.TextChoices):
        PAID = "PAID", "Payé"
        REFUNDED = "REFUNDED", "Remboursé"
        CANCELLED = "CANCELLED", "Annulé"

    invoice_number = models.CharField(max_length=20, unique=True, verbose_name="N° facture")
    date = models.DateTimeField(auto_now_add=True, verbose_name="Date de vente")
    cashier = models.ForeignKey(User, on_delete=models.PROTECT, verbose_name="Caissier")
    customer_name = models.CharField(max_length=100, verbose_name="Client")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PAID, verbose_name="Statut")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Montant total")

    class Meta:
        verbose_name = "Vente"
        verbose_name_plural = "Ventes"
        ordering = ['-date']

    def __str__(self):
        return f"{self.invoice_number} - {self.customer_name}"


class SaleItem(models.Model):
    """Éléments d'une vente"""

    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, verbose_name="Produit")
    quantity = models.PositiveIntegerField(verbose_name="Quantité")
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Prix unitaire")

    class Meta:
        verbose_name = "Élément de vente"
        verbose_name_plural = "Éléments de vente"

    def __str__(self):
        return f"{self.product.name} x{self.quantity}"

    @property
    def line_total(self):
        return self.quantity * self.unit_price
