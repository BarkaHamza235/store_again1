# apps/accounts/urls.py

from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Authentification
    path('login/',           views.UserLoginView.as_view(),        name='login'),
    path('register/',        views.UserRegisterView.as_view(),     name='register'),
    path('logout/',          views.UserLogoutView.as_view(),       name='logout'),

    # Réinitialisation de mot de passe
    path('password-reset/',           views.CustomPasswordResetView.as_view(),      name='password_reset'),
    path('password-reset/done/',      views.CustomPasswordResetDoneView.as_view(),  name='password_reset_done'),
    path('password-reset/confirm/<uidb64>/<token>/', views.CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password-reset/complete/',  views.CustomPasswordResetCompleteView.as_view(), name='password_reset_complete'),

    # CRUD Employés
    path('employees/',        views.EmployeeListView.as_view(),      name='employee_list'),
    path('employees/add/',    views.EmployeeCreateView.as_view(),    name='employee_add'),
    path('employees/<int:pk>/',     views.EmployeeDetailView.as_view(),    name='employee_detail'),
    path('employees/<int:pk>/edit/',views.EmployeeUpdateView.as_view(),    name='employee_edit'),
    path('employees/<int:pk>/delete/',views.EmployeeDeleteView.as_view(),    name='employee_delete'),

    # CRUD Fournisseurs
    path('suppliers/',        views.SupplierListView.as_view(),      name='supplier_list'),
    path('suppliers/add/',    views.SupplierCreateView.as_view(),    name='supplier_add'),
    path('suppliers/<int:pk>/',     views.SupplierDetailView.as_view(),    name='supplier_detail'),
    path('suppliers/<int:pk>/edit/',views.SupplierUpdateView.as_view(),    name='supplier_edit'),
    path('suppliers/<int:pk>/delete/',views.SupplierDeleteView.as_view(),  name='supplier_delete'),

    # CRUD Catégories
    path('categories/',       views.CategoryListView.as_view(),      name='category_list'),
    path('categories/add/',   views.CategoryCreateView.as_view(),    name='category_add'),
    path('categories/<int:pk>/',    views.CategoryDetailView.as_view(),    name='category_detail'),
    path('categories/<int:pk>/edit/',views.CategoryUpdateView.as_view(),    name='category_edit'),
    path('categories/<int:pk>/delete/',views.CategoryDeleteView.as_view(),  name='category_delete'),

    # CRUD Produits
    path('products/',         views.ProductListView.as_view(),       name='product_list'),
    path('products/add/',     views.ProductCreateView.as_view(),     name='product_add'),
    path('products/<int:pk>/',     views.ProductDetailView.as_view(),     name='product_detail'),
    path('products/<int:pk>/edit/',views.ProductUpdateView.as_view(),     name='product_edit'),
    path('products/<int:pk>/delete/',views.ProductDeleteView.as_view(),     name='product_delete'),

    # Ventes
    path('sales/',            views.SaleListView.as_view(),          name='sale_list'),
    path('sales/bulk-delete/',views.SaleBulkDeleteView.as_view(),     name='sale_bulk_delete'),
    path('sales/add/',        views.sale_create,                     name='sale_create'),
    path('sales/<int:pk>/',   views.SaleDetailView.as_view(),        name='sale_detail'),
    path('sales/<int:pk>/edit/',views.sale_update,                   name='sale_update'),
    path('sales/<int:pk>/delete/',views.SaleDeleteView.as_view(),    name='sale_delete'),
    path('sales/<int:pk>/json/',views.sale_detail_json,               name='sale_detail_json'),
]
