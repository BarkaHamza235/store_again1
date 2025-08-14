# apps/accounts/forms.py

from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate, get_user_model
from datetime import date
import logging

from .models import User
from apps.core.models import Supplier, Category, Product, Sale, SaleItem

logger = logging.getLogger(__name__)


class LoginForm(AuthenticationForm):
    """Formulaire de connexion personnalisé avec logging"""
    username = forms.CharField(
        label="Nom d'utilisateur ou Email",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': "Votre nom d'utilisateur ou email",
            'autofocus': True
        })
    )
    password = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': "Votre mot de passe"
        })
    )
    remember_me = forms.BooleanField(
        label="Se souvenir de moi",
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    error_messages = {
        'invalid_login': 'Nom d\'utilisateur/email ou mot de passe incorrect.',
        'inactive': 'Ce compte est inactif.',
    }

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')
        if username and password:
            if '@' in username:
                try:
                    user = User.objects.get(email=username)
                    username = user.username
                    cleaned_data['username'] = username
                except User.DoesNotExist:
                    logger.warning(f"Tentative de connexion avec email inexistant: {username}")
            if not authenticate(username=username, password=password):
                logger.warning(f"Échec de connexion pour: {username}")
        return cleaned_data


class RegisterForm(UserCreationForm):
    """Formulaire d'inscription avec validation complète"""
    first_name = forms.CharField(label="Prénom", max_length=30,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': "Votre prénom"}))
    last_name = forms.CharField(label="Nom de famille", max_length=30,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': "Votre nom de famille"}))
    username = forms.CharField(label="Nom d'utilisateur", max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': "Choisissez un nom d'utilisateur"}))
    email = forms.EmailField(label="Email", required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': "votre.email@exemple.com"}))
    role = forms.ChoiceField(label="Rôle", choices=User.Role.choices,
        initial=User.Role.CASHIER, widget=forms.Select(attrs={'class': 'form-select'}),
        help_text="Sélectionnez le rôle approprié")
    password1 = forms.CharField(label="Mot de passe",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': "Choisissez un mot de passe sécurisé"}))
    password2 = forms.CharField(label="Confirmation",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': "Confirmez votre mot de passe"}))

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'username', 'email', 'role', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            raise ValidationError("Un compte avec cet email existe déjà.")
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username and User.objects.filter(username=username).exists():
            raise ValidationError("Ce nom d'utilisateur est déjà pris.")
        return username

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.role = self.cleaned_data['role']
        if commit:
            user.save()
            logger.info(f"Nouvel utilisateur créé: {user.username} ({user.get_role_display()})")
        return user


# ===== EMPLOYES ===== #

class EmployeeCreateForm(UserCreationForm):
    first_name = forms.CharField(max_length=150, required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'}), label="Prénom")
    last_name = forms.CharField(max_length=150, required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'}), label="Nom de famille")
    email = forms.EmailField(required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control'}), label="Email")
    phone = forms.CharField(max_length=20, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}), label="Téléphone")
    address = forms.CharField(required=False,
        widget=forms.Textarea(attrs={'class': 'form-control','rows':3}), label="Adresse")
    role = forms.ChoiceField(choices=User.Role.choices,
        widget=forms.Select(attrs={'class':'form-control'}), label="Rôle")
    hire_date = forms.DateField(required=False, initial=date.today,
        widget=forms.DateInput(attrs={'class':'form-control','type':'date'}), label="Date d'embauche")

    class Meta:
        model = User
        fields = ('username','first_name','last_name','email',
                  'phone','address','role','hire_date','password1','password2')

    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.fields['username'].widget.attrs.update({'class':'form-control'})
        self.fields['password1'].widget.attrs.update({'class':'form-control'})
        self.fields['password2'].widget.attrs.update({'class':'form-control'})

    def clean_email(self):
        email=self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email déjà utilisé.")
        return email


class EmployeeUpdateForm(forms.ModelForm):
    first_name = forms.CharField(max_length=150, required=True,
        widget=forms.TextInput(attrs={'class':'form-control'}), label="Prénom")
    last_name = forms.CharField(max_length=150, required=True,
        widget=forms.TextInput(attrs={'class':'form-control'}), label="Nom de famille")
    email = forms.EmailField(required=True,
        widget=forms.EmailInput(attrs={'class':'form-control'}), label="Email")
    phone = forms.CharField(max_length=20, required=False,
        widget=forms.TextInput(attrs={'class':'form-control'}), label="Téléphone")
    address = forms.CharField(required=False,
        widget=forms.Textarea(attrs={'class':'form-control','rows':3}), label="Adresse")
    role = forms.ChoiceField(choices=User.Role.choices,
        widget=forms.Select(attrs={'class':'form-control'}), label="Rôle")
    hire_date = forms.DateField(required=False,
        widget=forms.DateInput(attrs={'class':'form-control','type':'date'}), label="Date d'embauche")
    is_active = forms.BooleanField(required=False,
        widget=forms.CheckboxInput(attrs={'class':'form-check-input'}), label="Compte actif")

    class Meta:
        model = User
        fields = ('username','first_name','last_name','email',
                  'phone','address','role','hire_date','is_active')

    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.fields['username'].widget.attrs.update({'class':'form-control'})

    def clean_email(self):
        email=self.cleaned_data.get('email')
        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Email déjà utilisé.")
        return email


class EmployeeSearchForm(forms.Form):
    search = forms.CharField(max_length=100, required=False,
        widget=forms.TextInput(attrs={'class':'form-control','placeholder':'Rechercher par nom, email...'}), label="")
    role = forms.ChoiceField(choices=[('','Tous les rôles')]+list(User.Role.choices),
        required=False, widget=forms.Select(attrs={'class':'form-control'}), label="")
    status = forms.ChoiceField(choices=[('','Tous les statuts'),('active','Actifs'),('inactive','Inactifs')],
        required=False, widget=forms.Select(attrs={'class':'form-control'}), label="")


# ===== FOURNISSEURS ===== #

class SupplierCreateForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = [
            'name', 'contact_person', 'email', 'phone',
            'address', 'notes', 'status'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class':'form-control'}),
            'contact_person': forms.TextInput(attrs={'class':'form-control'}),
            'email': forms.EmailInput(attrs={'class':'form-control'}),
            'phone': forms.TextInput(attrs={'class':'form-control'}),
            'address': forms.Textarea(attrs={'class':'form-control','rows':2}),
            'notes': forms.Textarea(attrs={'class':'form-control','rows':3}),
            'status': forms.Select(attrs={'class':'form-select'}),
        }
        labels = {
            'name': 'Nom du fournisseur',
            'contact_person': 'Personne de contact',
            'email': 'Email',
            'phone': 'Téléphone',
            'address': 'Adresse',
            'notes': 'Notes',
            'status': 'Statut',
        }


class SupplierSearchForm(forms.Form):
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class':'form-control','placeholder':'Rechercher par nom, email…'}),
        label=""
    )
    status = forms.ChoiceField(
        required=False,
        choices=[('', 'Tous les statuts')] + list(Supplier.Status.choices),
        widget=forms.Select(attrs={'class':'form-select'})
    )


# ===== CATEGORIE ===== #

class CategoryCreateForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class':'form-control'}),
            'description': forms.Textarea(attrs={'class':'form-control','rows':3}),
        }
        labels = {
            'name': 'Nom',
            'description': 'Description',
        }


class CategorySearchForm(forms.Form):
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class':'form-control','placeholder':'Rechercher par nom…'}),
        label=""
    )


# ===== PRODUIT ===== #

class ProductCreateForm(forms.ModelForm):
    """
    Formulaire de création et modification de produits.
    Le champ `image` accepte désormais toutes les extensions d'image.
    """
    image = forms.FileField(
        required=False,
        widget=forms.ClearableFileInput(attrs={'accept': 'image/*'}),
        help_text="Sélectionnez une image (toutes extensions supportées)."
    )

    class Meta:
        model = Product
        fields = ['name', 'category', 'price', 'stock_quantity', 'description', 'status', 'image']
        widgets = {
            'name': forms.TextInput(attrs={'class':'form-control'}),
            'category': forms.Select(attrs={'class':'form-select'}),
            'price': forms.NumberInput(attrs={'class':'form-control','step':'0.01'}),
            'stock_quantity': forms.NumberInput(attrs={'class':'form-control'}),
            'description': forms.Textarea(attrs={'class':'form-control','rows':3}),
            'status': forms.Select(attrs={'class':'form-select'}),
        }
        labels = {
            'name': 'Nom du produit',
            'category': 'Catégorie',
            'price': 'Prix (€)',
            'stock_quantity': 'Stock',
            'description': 'Description',
            'status': 'Statut',
            'image': 'Image du produit',
        }

    def clean_image(self):
        """
        Autorise toutes les extensions d'image.
        Vous pouvez ajouter ici des vérifications supplémentaires (taille, MIME).
        """
        uploaded = self.cleaned_data.get('image')
        return uploaded


class ProductSearchForm(forms.Form):
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class':'form-control','placeholder':'Rechercher produit…'}),
        label=""
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=False,
        empty_label="Toutes les catégories",
        widget=forms.Select(attrs={'class':'form-select'})
    )
    status = forms.ChoiceField(
        required=False,
        choices=[('', 'Tous les statuts')] + list(Product.Status.choices),
        widget=forms.Select(attrs={'class':'form-select'})
    )


# ===== VENTES ===== #

class SaleSearchForm(forms.Form):
    invoice_number = forms.CharField(
        required=False,
        label="N° facture",
        widget=forms.TextInput(attrs={'class':'form-control','placeholder':'N° facture…'})
    )
    cashier = forms.ModelChoiceField(
        queryset=Sale._meta.get_field('cashier').remote_field.model.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class':'form-select'}),
        label="Caissier"
    )
    product_name = forms.CharField(
        required=False,
        label="Produit",
        widget=forms.TextInput(attrs={'class':'form-control','placeholder':'Nom produit…'})
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type':'date','class':'form-control'}),
        label="Du"
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type':'date','class':'form-control'}),
        label="Au"
    )
    status = forms.ChoiceField(
        required=False,
        choices=[('', 'Tous')] + list(Sale.Status.choices),
        widget=forms.Select(attrs={'class':'form-select'}),
        label="Statut"
    )


class SaleForm(forms.ModelForm):
    class Meta:
        model = Sale
        fields = ['invoice_number', 'cashier', 'customer_name', 'status']
        widgets = {
            'invoice_number': forms.TextInput(attrs={'class':'form-control'}),
            'cashier': forms.Select(attrs={'class':'form-select'}),
            'customer_name': forms.TextInput(attrs={'class':'form-control'}),
            'status': forms.Select(attrs={'class':'form-select'}),
        }


SaleItemFormSet = forms.inlineformset_factory(
    Sale, SaleItem,
    fields=['product', 'quantity', 'unit_price'],
    extra=1, can_delete=True,
    widgets={
        'product': forms.Select(attrs={'class':'form-select'}),
        'quantity': forms.NumberInput(attrs={'class':'form-control','min':1}),
        'unit_price': forms.NumberInput(attrs={'class':'form-control','step':'0.01'}),
    }
)
