# apps/accounts/views.py

import logging
from django.shortcuts import redirect, get_object_or_404, render
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import JsonResponse
from django.utils.timezone import localtime
from django.views.generic import View, ListView, CreateView, UpdateView, DetailView, DeleteView
from django.contrib.auth.views import (
    LoginView, PasswordResetView, PasswordResetDoneView,
    PasswordResetConfirmView, PasswordResetCompleteView
)
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth import logout

from apps.core.models import Supplier, Category, Product, Sale
from .models import User, ActivityLog
from .forms import (
    LoginForm, RegisterForm,
    EmployeeCreateForm, EmployeeUpdateForm, EmployeeSearchForm,
    SupplierCreateForm, SupplierSearchForm,
    CategoryCreateForm, CategorySearchForm,
    ProductCreateForm, ProductSearchForm,
    SaleForm, SaleSearchForm, SaleItemFormSet
)

logger = logging.getLogger(__name__)


class UserLoginView(LoginView):
    form_class = LoginForm
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        user = self.request.user
        if hasattr(user, 'is_admin') and user.is_admin():
            return reverse_lazy('core:dashboard')
        return reverse_lazy('core:caisse')


class UserRegisterView(CreateView):
    model = User
    form_class = RegisterForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('accounts:login')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Compte créé avec succès, vous pouvez vous connecter.")
        ActivityLog.objects.create(
            user=self.object,
            verb='Compte créé',
            level='success',
            icon='user-plus'
        )
        return response

    def form_invalid(self, form):
        messages.error(self.request, "Erreur dans le formulaire, vérifiez vos informations.")
        return super().form_invalid(form)


class UserLogoutView(View):
    def get(self, request, *args, **kwargs):
        logout(request)
        messages.success(request, "Vous êtes bien déconnecté.")
        return redirect('accounts:login')


class CustomPasswordResetView(PasswordResetView):
    template_name = 'accounts/password_reset.html'
    email_template_name = 'registration/password_reset_email.html'
    subject_template_name = 'registration/password_reset_subject.txt'
    success_url = reverse_lazy('accounts:password_reset_done')

    def form_valid(self, form):
        messages.success(self.request, "Un email de réinitialisation a été envoyé, vérifiez vos mails & spams.")
        return super().form_valid(form)


class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'accounts/password_reset_done.html'


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'accounts/password_reset_confirm.html'
    success_url = reverse_lazy('accounts:password_reset_complete')


class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'accounts/password_reset_complete.html'


PasswordResetView = CustomPasswordResetView
PasswordResetDoneView = CustomPasswordResetDoneView
PasswordResetConfirmView = CustomPasswordResetConfirmView
PasswordResetCompleteView = CustomPasswordResetCompleteView


class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_admin()

    def handle_no_permission(self):
        messages.error(self.request, "Accès refusé : administrateurs uniquement.")
        return redirect('accounts:login')


# ====================== CRUD EMPLOYÉS ======================


class EmployeeListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = User
    template_name = 'accounts/employees/employee_list.html'
    context_object_name = 'employees'
    paginate_by = 15

    def get_queryset(self):
        qs = User.objects.exclude(pk=self.request.user.pk).order_by('-date_joined')
        form = EmployeeSearchForm(self.request.GET)
        if form.is_valid():
            search = form.cleaned_data.get('search')
            role = form.cleaned_data.get('role')
            status = form.cleaned_data.get('status')
            if search:
                qs = (qs.filter(first_name__icontains=search) |
                      qs.filter(last_name__icontains=search) |
                      qs.filter(email__icontains=search))
            if role:
                qs = qs.filter(role=role)
            if status == 'active':
                qs = qs.filter(is_active=True)
            elif status == 'inactive':
                qs = qs.filter(is_active=False)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        form = EmployeeSearchForm(self.request.GET)
        qs = self.get_queryset()
        ctx['search_form'] = form
        ctx['total'] = qs.count()
        ctx['active'] = qs.filter(is_active=True).count()
        ctx['inactive'] = qs.filter(is_active=False).count()
        return ctx


class EmployeeCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = User
    form_class = EmployeeCreateForm
    template_name = 'accounts/employees/employee_form.html'
    success_url = reverse_lazy('accounts:employee_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Employé {self.object.get_full_name()} créé !")
        ActivityLog.objects.create(
            user=self.request.user,
            verb='Employé ajouté',
            level='success',
            icon='user-plus'
        )
        return response


class EmployeeUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = User
    form_class = EmployeeUpdateForm
    template_name = 'accounts/employees/employee_form.html'
    success_url = reverse_lazy('accounts:employee_list')

    def get_queryset(self):
        return User.objects.exclude(pk=self.request.user.pk)

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Employé {self.object.get_full_name()} mis à jour !")
        ActivityLog.objects.create(
            user=self.request.user,
            verb='Employé modifié',
            level='info',
            icon='edit'
        )
        return response


class EmployeeDetailView(LoginRequiredMixin, AdminRequiredMixin, DetailView):
    model = User
    template_name = 'accounts/employees/employee_detail.html'
    context_object_name = 'employee'

    def get_queryset(self):
        return User.objects.exclude(pk=self.request.user.pk)


class EmployeeDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    model = User
    template_name = 'accounts/employees/employee_confirm_delete.html'
    success_url = reverse_lazy('accounts:employee_list')

    def get_queryset(self):
        return User.objects.exclude(pk=self.request.user.pk)

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        name = obj.get_full_name()
        response = super().delete(request, *args, **kwargs)
        messages.success(request, f"Employé {name} supprimé !")
        ActivityLog.objects.create(
            user=self.request.user,
            verb='Employé supprimé',
            level='danger',
            icon='trash'
        )
        return response


# ====================== CRUD FOURNISSEURS ======================


class SupplierListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = Supplier
    template_name = 'accounts/suppliers/supplier_list.html'
    context_object_name = 'suppliers'
    paginate_by = 15

    def get_queryset(self):
        qs = Supplier.objects.all().order_by('-created_at')
        self.form = SupplierSearchForm(self.request.GET)
        if self.form.is_valid():
            search = self.form.cleaned_data.get('search', '')
            status = self.form.cleaned_data.get('status', '')
            if search:
                qs = qs.filter(name__icontains=search)
            if status:
                qs = qs.filter(status=status)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        form = getattr(self, 'form', SupplierSearchForm())
        qs = ctx['page_obj'].paginator.object_list
        ctx['search_form'] = form
        ctx['total'] = qs.count()
        if form.is_valid():
            ctx['status_filter'] = form.cleaned_data.get('status', '')
        else:
            ctx['status_filter'] = ''
        ctx['status_choices'] = Supplier.Status.choices
        ctx['active'] = qs.filter(status=Supplier.Status.ACTIVE).count()
        ctx['inactive'] = qs.filter(status=Supplier.Status.INACTIVE).count()
        ctx['suspended'] = qs.filter(status=Supplier.Status.SUSPENDED).count()
        return ctx


class SupplierCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = Supplier
    form_class = SupplierCreateForm
    template_name = 'accounts/suppliers/supplier_form.html'
    success_url = reverse_lazy('accounts:supplier_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Fournisseur {form.instance.name} créé !")
        ActivityLog.objects.create(
            user=self.request.user,
            verb='Fournisseur créé',
            level='success',
            icon='truck'
        )
        return response


class SupplierUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = Supplier
    form_class = SupplierCreateForm
    template_name = 'accounts/suppliers/supplier_form.html'
    success_url = reverse_lazy('accounts:supplier_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Fournisseur {form.instance.name} mis à jour !")
        ActivityLog.objects.create(
            user=self.request.user,
            verb='Fournisseur modifié',
            level='info',
            icon='edit'
        )
        return response


class SupplierDetailView(LoginRequiredMixin, AdminRequiredMixin, DetailView):
    model = Supplier
    template_name = 'accounts/suppliers/supplier_detail.html'
    context_object_name = 'supplier'


class SupplierDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    model = Supplier
    template_name = 'accounts/suppliers/supplier_confirm_delete.html'
    success_url = reverse_lazy('accounts:supplier_list')

    def delete(self, request, *args, **kwargs):
        name = self.get_object().name
        response = super().delete(request, *args, **kwargs)
        messages.success(request, f"Fournisseur {name} supprimé !")
        ActivityLog.objects.create(
            user=self.request.user,
            verb='Fournisseur supprimé',
            level='danger',
            icon='trash'
        )
        return response


# ====================== CRUD CATÉGORIES ======================


class CategoryListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = Category
    template_name = 'accounts/categories/category_list.html'
    context_object_name = 'categories'
    paginate_by = 15

    def get_queryset(self):
        qs = Category.objects.all().order_by('name')
        form = CategorySearchForm(self.request.GET)
        if form.is_valid() and form.cleaned_data.get('search'):
            qs = qs.filter(name__icontains=form.cleaned_data['search'])
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        form = CategorySearchForm(self.request.GET)
        qs = self.get_queryset()
        ctx['search_form'] = form
        ctx['total'] = qs.count()
        return ctx


class CategoryCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = Category
    form_class = CategoryCreateForm
    template_name = 'accounts/categories/category_form.html'
    success_url = reverse_lazy('accounts:category_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Catégorie '{form.instance.name}' créée !")
        ActivityLog.objects.create(
        user=self.request.user,  # ✅ CORRECT : self.request.user
        verb='Catégorie créée',
        level='success',
        icon='tags'
        )
        return response


class CategoryUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = Category
    form_class = CategoryCreateForm
    template_name = 'accounts/categories/category_form.html'
    success_url = reverse_lazy('accounts:category_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Catégorie '{form.instance.name}' mise à jour !")
        ActivityLog.objects.create(
            user=self.request.user,
            verb='Catégorie modifiée',
            level='info',
            icon='edit'
        )
        return response


class CategoryDetailView(LoginRequiredMixin, AdminRequiredMixin, DetailView):
    model = Category
    template_name = 'accounts/categories/category_detail.html'
    context_object_name = 'category'


class CategoryDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    model = Category
    template_name = 'accounts/categories/category_confirm_delete.html'
    success_url = reverse_lazy('accounts:category_list')

    def delete(self, request, *args, **kwargs):
        name = self.get_object().name
        response = super().delete(request, *args, **kwargs)
        messages.success(request, f"Catégorie '{name}' supprimée !")
        ActivityLog.objects.create(
            user=self.request.user,
            verb='Catégorie supprimée',
            level='danger',
            icon='trash'
        )
        return response


# ====================== CRUD PRODUITS ======================


class ProductListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = Product
    template_name = 'accounts/products/product_list.html'
    context_object_name = 'products'
    paginate_by = 15

    def get_queryset(self):
        qs = Product.objects.select_related('category').order_by('-created_at')
        self.form = ProductSearchForm(self.request.GET)
        if self.form.is_valid():
            search = self.form.cleaned_data.get('search', '')
            category = self.form.cleaned_data.get('category')
            status = self.form.cleaned_data.get('status')
            if search:
                qs = qs.filter(name__icontains=search)
            if category:
                qs = qs.filter(category=category)
            if status:
                qs = qs.filter(status=status)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        form = getattr(self, 'form', ProductSearchForm())
        qs = ctx['page_obj'].paginator.object_list
        ctx['search_form'] = form
        ctx['total'] = qs.count()
        if form.is_valid():
            ctx['search_filter'] = form.cleaned_data.get('search', '')
            ctx['category_filter'] = form.cleaned_data.get('category')
            ctx['status_filter'] = form.cleaned_data.get('status')
        else:
            ctx['search_filter'] = ''
            ctx['category_filter'] = None
            ctx['status_filter'] = None
        ctx['status_choices'] = Product.Status.choices
        ctx['active'] = qs.filter(status=Product.Status.ACTIVE).count()
        ctx['out_of_stock'] = qs.filter(status=Product.Status.OUT_OF_STOCK).count()
        ctx['inactive'] = qs.filter(status=Product.Status.INACTIVE).count()
        return ctx


class ProductCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = Product
    form_class = ProductCreateForm
    template_name = 'accounts/products/product_form.html'
    success_url = reverse_lazy('accounts:product_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Produit '{form.instance.name}' créé !")
        ActivityLog.objects.create(
            user=self.request.user,
            verb='Produit ajouté',
            level='success',
            icon='plus'
        )
        return response


class ProductUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = Product
    form_class = ProductCreateForm
    template_name = 'accounts/products/product_form.html'
    success_url = reverse_lazy('accounts:product_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Produit '{form.instance.name}' mis à jour !")
        ActivityLog.objects.create(
            user=self.request.user,
            verb='Produit modifié',
            level='info',
            icon='edit'
        )
        return response


class ProductDetailView(LoginRequiredMixin, AdminRequiredMixin, DetailView):
    model = Product
    template_name = 'accounts/products/product_detail.html'
    context_object_name = 'product'


class ProductDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    model = Product
    template_name = 'accounts/products/product_confirm_delete.html'
    success_url = reverse_lazy('accounts:product_list')

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        obj.items.all().delete()
        name = obj.name
        response = super().delete(request, *args, **kwargs)
        messages.success(request, f"Produit '{name}' et ses éléments de vente associés ont été supprimés.")
        ActivityLog.objects.create(
            user=self.request.user,
            verb='Produit et éléments de vente supprimés',
            level='danger',
            icon='trash'
        )
        return response


# ====================== CRUD VENTES ======================

class SaleListView(LoginRequiredMixin, ListView):
    model = Sale
    template_name = 'accounts/sales/sale_list.html'
    paginate_by = 7
    queryset = (
        Sale.objects
            .select_related('cashier')
            .prefetch_related('items__product')
            .order_by('-date')
    )

    def get_queryset(self):
        qs = super().get_queryset()
        form = SaleSearchForm(self.request.GET)
        if form.is_valid():
            # Filtre par nom de produit
            pn = form.cleaned_data.get('product_name')
            if pn:
                qs = qs.filter(items__product__name__icontains=pn).distinct()
            # Filtres existants
            if form.cleaned_data['invoice_number']:
                qs = qs.filter(invoice_number__icontains=form.cleaned_data['invoice_number'])
            if form.cleaned_data['cashier']:
                qs = qs.filter(cashier=form.cleaned_data['cashier'])
            if form.cleaned_data['status']:
                qs = qs.filter(status=form.cleaned_data['status'])
            if form.cleaned_data['date_from']:
                qs = qs.filter(date__date__gte=form.cleaned_data['date_from'])
            if form.cleaned_data['date_to']:
                qs = qs.filter(date__date__lte=form.cleaned_data['date_to'])
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['search_form'] = SaleSearchForm(self.request.GET)
        ctx['total_revenue'] = sum(s.total_amount for s in ctx['page_obj'])
        return ctx


class SaleBulkDeleteView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        ids = request.POST.getlist('sale_ids')
        if ids:
            sales = Sale.objects.filter(pk__in=ids)
            count = sales.count()
            sales.delete()
            messages.success(request, f"{count} vente(s) supprimée(s).")
            ActivityLog.objects.create(
                user=self.request.user,
                verb=f"{count} vente(s) supprimée(s) en masse",
                level='danger',
                icon='trash'
            )
        else:
            messages.info(request, "Aucune vente sélectionnée.")
        return redirect('accounts:sale_list')


def sale_create(request):
    if request.method == 'POST':
        form = SaleForm(request.POST)
        formset = SaleItemFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            sale = form.save()
            formset.instance = sale
            formset.save()
            sale.total_amount = sum(item.line_total for item in sale.items.all())
            sale.save()
            messages.success(request, f"Vente {sale.invoice_number} enregistrée.")
            ActivityLog.objects.create(
                user=request.user,
                verb='Vente créée',
                level='success',
                icon='shopping-cart'
            )
            return redirect('accounts:sale_list')
    else:
        form = SaleForm()
        formset = SaleItemFormSet()
    return render(request, 'accounts/sales/sale_form.html', {'form': form, 'formset': formset})


def sale_update(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    if request.method == 'POST':
        form = SaleForm(request.POST, instance=sale)
        formset = SaleItemFormSet(request.POST, instance=sale)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            sale.total_amount = sum(item.line_total for item in sale.items.all())
            sale.save()
            messages.success(request, f"Vente {sale.invoice_number} mise à jour.")
            ActivityLog.objects.create(
                user=request.user,
                verb='Vente modifiée',
                level='info',
                icon='edit'
            )
            return redirect('accounts:sale_list')
    else:
        form = SaleForm(instance=sale)
        formset = SaleItemFormSet(instance=sale)
    return render(request, 'accounts/sales/sale_form.html', {'form': form, 'formset': formset})


class SaleDetailView(LoginRequiredMixin, DetailView):
    model = Sale
    template_name = 'accounts/sales/sale_detail.html'
    context_object_name = 'sale'


class SaleDeleteView(LoginRequiredMixin, DeleteView):
    model = Sale
    template_name = 'accounts/sales/sale_confirm_delete.html'
    success_url = reverse_lazy('accounts:sale_list')

    def delete(self, request, *args, **kwargs):
        sale = self.get_object()
        response = super().delete(request, *args, **kwargs)
        messages.success(request, f"Vente {sale.invoice_number} supprimée.")
        ActivityLog.objects.create(
            user=request.user,
            verb='Vente supprimée',
            level='danger',
            icon='trash'
        )
        return response


def sale_detail_json(request, pk):
    sale = get_object_or_404(
        Sale.objects
            .select_related('cashier')
            .prefetch_related('items__product'),
        pk=pk
    )
    subtotal = sum(item.line_total for item in sale.items.all())
    discount = getattr(sale, 'discount', 0)
    return JsonResponse({
        'invoice_number': sale.invoice_number,
        'date': localtime(sale.date).strftime('%d/%m/%Y %H:%M'),
        'cashier': sale.cashier.get_full_name(),
        'subtotal': f'{subtotal:.2f}',
        'discount': f'{discount:.2f}',
        'total_amount': f'{sale.total_amount:.2f}',
        'items': [
            {
                'product':    item.product.name,
                'quantity':   item.quantity,
                'unit_price': f'{item.unit_price:.2f}',
                'line_total': f'{item.line_total:.2f}',
            } for item in sale.items.all()
        ],
    })