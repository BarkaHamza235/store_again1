# apps/accounts/signals.py

from django.conf import settings
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import ActivityLog


# 1. Connexion réussie
@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    ActivityLog.objects.create(
        user=user,
        verb='Connexion réussie',
        level='primary',
        icon='sign-in-alt'
    )


# 2. Déconnexion
@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    ActivityLog.objects.create(
        user=user,
        verb='Déconnexion',
        level='info',
        icon='sign-out-alt'
    )


# 3. Création de compte
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def log_user_signup(sender, instance, created, **kwargs):
    if created:
        ActivityLog.objects.create(
            user=instance,
            verb='Compte créé',
            level='success',
            icon='user-plus'
        )
