from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Modèle utilisateur personnalisé avec rôles"""

    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Administrateur"
        CASHIER = "CASHIER", "Caissier"

    role = models.CharField(
        max_length=20, 
        choices=Role.choices, 
        default=Role.CASHIER,
        help_text="Rôle de l'utilisateur dans le système"
    )

    ##### Ajout des champs pour la gestion des employés #####
    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Téléphone"
    )
    address = models.TextField(
        blank=True,
        verbose_name="Adresse"
    )
    hire_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Date d'embauche"
    )
    ##### Fin des champs employés #####

    email = models.EmailField(
        unique=True,
        help_text="Adresse email unique requise pour la récupération de mot de passe"
    )

    first_name = models.CharField(max_length=150, verbose_name="Prénom")
    last_name = models.CharField(max_length=150, verbose_name="Nom de famille")

    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"
        ordering = ['-date_joined']

    def is_admin(self):
        """Vérifie si l'utilisateur est administrateur"""
        return self.role == self.Role.ADMIN

    def is_cashier(self):
        """Vérifie si l'utilisateur est caissier"""
        return self.role == self.Role.CASHIER

    def get_role_display_verbose(self):
        """Retourne l'affichage détaillé du rôle"""
        return self.get_role_display()

    

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    def __str__(self):
        return self.get_full_name()

    def get_full_name(self):
        """Retourne le nom complet"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username

    def is_admin(self):
        """Vérifie si l'utilisateur est administrateur"""
        return self.role == self.Role.ADMIN

    def is_cashier(self):
        """Vérifie si l'utilisateur est caissier"""
        return self.role == self.Role.CASHIER

    @property
    def role_badge_class(self):
        """Classe CSS pour badge rôle"""
        return "badge bg-danger" if self.is_admin() else "badge bg-primary"
    
    
    #description fournisseur
    description = models.TextField(
    blank=True,
    verbose_name="Description",
    help_text="Description détaillée du fournisseur"
)
    
#activité recente 
from django.db import models
from django.conf import settings

class ActivityLog(models.Model):
    LEVEL_CHOICES = [
        ('primary', 'Information'),
        ('success', 'Succès'),
        ('warning', 'Avertissement'),
        ('danger',  'Erreur'),
    ]
    user      = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    verb      = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)
    level     = models.CharField(max_length=10, choices=LEVEL_CHOICES, default='primary')
    icon      = models.CharField(max_length=50, default='info-circle')  # icône FontAwesome

    class Meta:
        ordering = ['-timestamp']
