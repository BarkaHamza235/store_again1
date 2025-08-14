# apps/core/views.py

import io
import json
from datetime import date
from django.shortcuts import redirect, get_object_or_404, render
from django.views.generic import (
    TemplateView, View, ListView, CreateView, UpdateView, DeleteView, DetailView
)
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db import transaction
from django.http import JsonResponse, FileResponse, Http404
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q, Sum, F
from django.utils import timezone
from reportlab.pdfgen import canvas

from .models import Supplier, Category, Product, Sale, SaleItem
from apps.accounts.forms import ProductCreateForm
from apps.accounts.models import ActivityLog


def generate_invoice_number():
    """
    Génère un numéro de facture unique au format FYYYYMMDDNNNN.
    Chaque jour, la séquence redémarre à 0001.
    """
    today_str = timezone.now().date().strftime('%Y%m%d')
    prefix = f"F{today_str}"
    with transaction.atomic():
        last = Sale.objects.filter(invoice_number__startswith=prefix).order_by('-invoice_number').first()
        if last:
            try:
                last_seq = int(last.invoice_number[-4:])
            except (ValueError, IndexError):
                last_seq = 0
            seq = last_seq + 1
        else:
            seq = 1
        return f"{prefix}{seq:04d}"


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'core/dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        
        # 1. Ventes du jour
        today = timezone.now().date()
        ctx['sales_today'] = (
            Sale.objects.filter(date__date=today)
            .aggregate(total=Sum('total_amount'))['total'] or 0
        )

        # 2. Produits totaux
        ctx['count_products'] = Product.objects.count()

        # 3. Commandes (utilise le nombre total de ventes)
        ctx['count_orders'] = Sale.objects.count()

        # 4. Alertes stock (produits en rupture de stock)
        ctx['count_alerts'] = Product.objects.filter(
            stock_quantity__lte=3
        ).count()

        # Préparation des données pour le graphique des ventes (7 derniers jours)
        dates = []
        values = []
        for i in range(6, -1, -1):
            day = today - timezone.timedelta(days=i)
            dates.append(day.strftime('%d/%m'))
            total = (
                Sale.objects.filter(date__date=day)
                .aggregate(sum_amount=Sum('total_amount'))['sum_amount'] or 0
            )
            values.append(float(total))
        ctx['sales_dates'] = json.dumps(dates)
        ctx['sales_values'] = json.dumps(values)

        # Date et heure actuelles
        ctx['current_datetime'] = timezone.now()

        ctx['recent_activities'] = ActivityLog.objects.filter(
            user=self.request.user
        ).order_by('-timestamp')[:5]

        return ctx


@method_decorator(login_required, name='dispatch')
class HomeRedirectView(View):
    """Redirige selon le rôle de l'utilisateur"""
    def get(self, request):
        role = getattr(request.user, 'role', None)
        if role == 'ADMIN':
            return redirect('core:dashboard')
        if role == 'CASHIER':
            return redirect('core:caisse')
        return redirect('core:dashboard')


class CaisseView(LoginRequiredMixin, TemplateView):
    template_name = 'core/caisse.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['page_title'] = 'Point de Vente - Store Manager'
        ctx['user_role'] = 'Caissier'

        q = self.request.GET.get('q', '').strip()
        category_id = self.request.GET.get('category', '')

        produits = Product.objects.filter(status=Product.Status.ACTIVE)
        if q:
            produits = produits.filter(name__icontains=q)
        if category_id:
            try:
                produits = produits.filter(category_id=int(category_id))
            except (ValueError, TypeError):
                pass

        paginator = Paginator(produits.order_by('name'), 6)
        ctx['products_page'] = paginator.get_page(self.request.GET.get('page'))
        ctx['search_query'] = q
        ctx['selected_category'] = category_id
        ctx['categories'] = Category.objects.all().order_by('name')
        return ctx


class SupplierListView(LoginRequiredMixin, ListView):
    model = Supplier
    template_name = 'accounts/suppliers/supplier_list.html'
    context_object_name = 'suppliers'
    paginate_by = 10

    def get_queryset(self):
        qs = Supplier.objects.all()
        search = self.request.GET.get('search')
        if search:
            qs = qs.filter(
                Q(name__icontains=search) |
                Q(contact_person__icontains=search) |
                Q(email__icontains=search) |
                Q(city__icontains=search)
            )
        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(status=status)
        return qs.order_by('-created_at')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update({
            'page_title': 'Gestion des Fournisseurs',
            'search_query': self.request.GET.get('search', ''),
            'status_filter': self.request.GET.get('status', ''),
            'status_choices': Supplier.Status.choices,
            'total_suppliers': Supplier.objects.count(),
            'active_suppliers': Supplier.objects.filter(status=Supplier.Status.ACTIVE).count(),
            'inactive_suppliers': Supplier.objects.filter(status=Supplier.Status.INACTIVE).count(),
            'suspended_suppliers': Supplier.objects.filter(status=Supplier.Status.SUSPENDED).count(),
        })
        return ctx


class SupplierCreateView(LoginRequiredMixin, CreateView):
    model = Supplier
    template_name = 'core/suppliers/supplier_form.html'
    fields = [
        'name', 'contact_person', 'email', 'phone',
        'address', 'city', 'postal_code', 'country',
        'tax_number', 'payment_terms', 'credit_limit',
        'status', 'notes'
    ]
    success_url = reverse_lazy('core:supplier_list')

    def form_valid(self, form):
        messages.success(self.request, f"Fournisseur '{form.instance.name}' créé avec succès.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update({
            'page_title': 'Ajouter un Fournisseur',
            'form_title': 'Nouveau Fournisseur',
            'submit_text': 'Créer le Fournisseur'
        })
        return ctx


class SupplierUpdateView(LoginRequiredMixin, UpdateView):
    model = Supplier
    template_name = 'core/suppliers/supplier_form.html'
    fields = [
        'name', 'contact_person', 'email', 'phone',
        'address', 'city', 'postal_code', 'country',
        'tax_number', 'payment_terms', 'credit_limit',
        'status', 'notes'
    ]
    success_url = reverse_lazy('core:supplier_list')

    def form_valid(self, form):
        messages.success(self.request, f"Fournisseur '{form.instance.name}' modifié avec succès.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update({
            'page_title': f"Modifier {self.object.name}",
            'form_title': f"Modifier {self.object.name}",
            'submit_text': 'Sauvegarder les Modifications'
        })
        return ctx


class SupplierDetailView(LoginRequiredMixin, DetailView):
    model = Supplier
    template_name = 'core/suppliers/supplier_detail.html'
    context_object_name = 'supplier'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['page_title'] = f"Détails - {self.object.name}"
        return ctx


class SupplierDeleteView(LoginRequiredMixin, DeleteView):
    model = Supplier
    template_name = 'core/suppliers/supplier_confirm_delete.html'
    success_url = reverse_lazy('core:supplier_list')

    def delete(self, request, *args, **kwargs):
        name = self.get_object().name
        result = super().delete(request, *args, **kwargs)
        messages.success(request, f"Fournisseur '{name}' supprimé avec succès.")
        return result

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['page_title'] = f"Supprimer {self.object.name}"
        return ctx


@login_required
@csrf_exempt
def caisse_checkout(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Méthode non autorisée'}, status=405)

    data = json.loads(request.body)
    items = data.get('items', [])
    payment_mode = data.get('payment_mode')
    cash_received = data.get('cash_received', 0)

    # Utilisation du générateur de numéro unique
    invoice = generate_invoice_number()
    
    sale = Sale.objects.create(
        invoice_number=invoice,
        cashier=request.user,
        customer_name="Client",
        status=Sale.Status.PAID,
        total_amount=0
    )

    total = 0
    for it in items:
        prod = get_object_or_404(Product, pk=it['sku'])
        qty = int(it['qty'])
        up = float(it['price'])
        line = SaleItem.objects.create(
            sale=sale,
            product=prod,
            quantity=qty,
            unit_price=up
        )
        total += line.line_total

    sale.total_amount = total
    sale.save()
    
    ActivityLog.objects.create(
        user=request.user,
        verb='Nouvelle vente',
        level='primary',
        icon='shopping-cart'
    )

    return JsonResponse({
        'success': True, 
        'sale_id': sale.pk,
        'message': f"Vente {invoice} enregistrée avec succès !",
        'toast_type': 'success'
    })


@login_required
def sale_info(request):
    sale_id = request.GET.get('sale_id')
    try:
        sale = Sale.objects.get(pk=sale_id)
    except (Sale.DoesNotExist, TypeError, ValueError):
        return JsonResponse({'error': 'Vente introuvable'}, status=404)

    items = [{
        'product': item.product.name,
        'quantity': item.quantity,
        'unit_price': f"{item.unit_price:.2f}",
        'line_total': f"{item.line_total:.2f}"
    } for item in sale.items.all()]

    return JsonResponse({
        'invoice_number': sale.invoice_number,
        'date': sale.date.strftime('%d/%m/%Y %H:%M'),
        'cashier': sale.cashier.get_full_name(),
        'customer': sale.customer_name,
        'total_amount': f"{sale.total_amount:.2f}",
        'items': items
    })


@login_required
def generate_invoice(request):
    sale_id = request.GET.get('sale_id')
    if not sale_id:
        raise Http404("Aucune vente spécifiée")
    sale = get_object_or_404(Sale, pk=sale_id)

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer)

    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, 800, f"Facture {sale.invoice_number}")

    p.setFont("Helvetica", 12)
    y = 760
    p.drawString(100, y, f"Date : {sale.date.strftime('%d/%m/%Y %H:%M')}")
    y -= 20
    p.drawString(100, y, f"Caissier : {sale.cashier.get_full_name()}")
    y -= 20
    p.drawString(100, y, f"Client : {sale.customer_name}")
    y -= 40

    p.drawString(100, y, "Produit")
    p.drawString(300, y, "Qté")
    p.drawString(350, y, "PU (€)")
    p.drawString(430, y, "Total (€)")
    y -= 20

    for item in sale.items.all():
        if y < 100:
            p.showPage()
            y = 800
        p.drawString(100, y, item.product.name)
        p.drawString(300, y, str(item.quantity))
        p.drawString(350, y, f"{item.unit_price:.2f}")
        p.drawString(430, y, f"{item.line_total:.2f}")
        y -= 20

    y -= 20
    p.setFont("Helvetica-Bold", 12)
    p.drawString(100, y, f"Montant total : {sale.total_amount:.2f} €")

    p.showPage()
    p.save()
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename=f"Facture_{sale.invoice_number}.pdf")


# ===== VUES PRODUITS =====

class ProductListView(LoginRequiredMixin, ListView):
    model = Product
    template_name = 'core/products/product_list.html'
    context_object_name = 'products'
    paginate_by = 15

    def get_queryset(self):
        return Product.objects.order_by('-created_at')


class ProductCreateView(LoginRequiredMixin, CreateView):
    model = Product
    form_class = ProductCreateForm
    template_name = 'core/products/product_form.html'
    success_url = reverse_lazy('core:product_list')

    def form_valid(self, form):
        product = form.save(commit=False)
        if 'image' in self.request.FILES:
            product.image = self.request.FILES['image']
        product.save()
        messages.success(self.request, f"Produit '{product.name}' créé !")
        return super().form_valid(form)


class ProductUpdateView(LoginRequiredMixin, UpdateView):
    model = Product
    form_class = ProductCreateForm
    template_name = 'core/products/product_form.html'
    success_url = reverse_lazy('core:product_list')

    def form_valid(self, form):
        product = form.save(commit=False)
        if 'image' in self.request.FILES:
            product.image = self.request.FILES['image']
        product.save()
        messages.success(self.request, f"Produit '{product.name}' mis à jour !")
        return super().form_valid(form)


class ProductDetailView(LoginRequiredMixin, DetailView):
    model = Product
    template_name = 'core/products/product_detail.html'
    context_object_name = 'product'


class ProductDeleteView(LoginRequiredMixin, DeleteView):
    model = Product
    template_name = 'core/products/product_confirm_delete.html'
    success_url = reverse_lazy('core:product_list')

    def delete(self, request, *args, **kwargs):
        name = self.get_object().name
        result = super().delete(request, *args, **kwargs)
        messages.success(request, f"Produit '{name}' supprimé !")
        return result


# ===== VUES RAPPORTS =====

class ReportsView(LoginRequiredMixin, TemplateView):
    template_name = 'core/reports.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # Statistiques
        ctx.update({
            'total_products': Product.objects.count(),
            'active_products': Product.objects.filter(status=Product.Status.ACTIVE).count(),
            'total_sales': Sale.objects.count(),
            'total_revenue': Sale.objects.aggregate(total=Sum('total_amount'))['total'] or 0,
        })
        # Pagination des ventes récentes
        sales_qs = Sale.objects.order_by('-date')
        paginator = Paginator(sales_qs, 10)  # 10 par page
        page_number = self.request.GET.get('page')
        ctx['recent_sales_page'] = paginator.get_page(page_number)
        return ctx
