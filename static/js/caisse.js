// static/js/caisse.js

document.addEventListener('DOMContentLoaded', function() {
  const searchInput      = document.getElementById('product-search');
  const searchBtn        = document.getElementById('search-btn');
  const productList      = document.getElementById('product-list');
  const cartList         = document.getElementById('cart-items');
  const cartCount        = document.getElementById('cart-count');
  const subtotalEl       = document.getElementById('cart-subtotal');
  const taxEl            = document.getElementById('cart-tax');
  const totalEl          = document.getElementById('cart-total');
  const paymentModeBtns  = document.querySelectorAll('[name="payment_mode"]');
  const cashFields       = document.getElementById('cash-fields');
  const cashReceivedInput= document.getElementById('cash-received');
  const finalizeBtn      = document.getElementById('finalize-sale');
  const emptyCartBtn     = document.getElementById('empty-cart');
  const genBtn           = document.getElementById('generate-invoice');
  const printBtn         = document.getElementById('print-invoice');
  let cart               = [];

  // Initialise états des boutons
  function initButtons() {
    finalizeBtn.disabled = true;
    finalizeBtn.classList.replace('btn-success', 'btn-secondary');
    finalizeBtn.innerHTML = '<i class="fas fa-check-circle"></i> Finaliser la vente';
    genBtn.disabled = true;
    genBtn.classList.replace('btn-primary', 'btn-outline-secondary');
    printBtn.disabled = true;
    printBtn.classList.replace('btn-primary', 'btn-outline-secondary');
  }
  initButtons();

  // Recherche de produits
  searchBtn.addEventListener('click', function(e) {
    e.preventDefault();
    const term = searchInput.value.trim();
    const url = new URL(window.location);
    if (term) url.searchParams.set('q', term);
    else url.searchParams.delete('q');
    url.searchParams.delete('page');
    window.location.href = url.toString();
  });
  searchInput.addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
      e.preventDefault();
      searchBtn.click();
    }
  });

  // Ajouter au panier
  productList.addEventListener('click', function(e) {
    const btn = e.target.closest('.add-to-cart');
    if (!btn) return;
    const sku = btn.dataset.sku;
    const name = btn.dataset.name;
    const price = parseFloat(btn.dataset.price);
    const existing = cart.find(item => item.sku === sku);
    if (existing) existing.qty++;
    else cart.push({ sku, name, price, qty: 1 });
    renderCart();
  });

  // Vider panier
  emptyCartBtn.addEventListener('click', function() {
    if (confirm('Vider entièrement le panier ?')) {
      cart = [];
      renderCart();
      finalizeBtn.disabled = false;
      finalizeBtn.classList.replace('btn-secondary', 'btn-success');
    }
  });

  // Mode de paiement
  paymentModeBtns.forEach(rb => {
    rb.addEventListener('change', function() {
      if (this.value === 'CASH') cashFields.style.display = '';
      else {
        cashFields.style.display = 'none';
        cashReceivedInput.value = '';
      }
    });
  });

  // Finaliser vente
  finalizeBtn.addEventListener('click', function() {
    if (cart.length === 0) {
      alert('Le panier est vide.');
      return;
    }
    const mode = document.querySelector('[name="payment_mode"]:checked').value;
    let cashReceived = 0;
    if (mode === 'CASH') {
      cashReceived = parseFloat(cashReceivedInput.value) || 0;
      if (cashReceived < calculateTotal()) {
        alert('Montant en espèces insuffisant.');
        return;
      }
    }
    const data = { items: cart, payment_mode: mode, cash_received: cashReceived };
    fetch('/core/caisse/checkout/', {
      method: 'POST',
      headers: {
        'X-CSRFToken': getCookie('csrftoken'),
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
    })
      .then(resp => resp.json())
      .then(json => {
        if (!json.success) {
          return alert(json.error || 'Erreur lors de la finalisation.');
        }
        finalizeBtn.disabled = true;
        finalizeBtn.classList.replace('btn-success', 'btn-secondary');
        finalizeBtn.innerHTML = '<i class="fas fa-check-circle"></i> Vente finalisée';
        finalizeBtn.dataset.saleId = json.sale_id;
        genBtn.disabled = false;
        genBtn.classList.replace('btn-outline-secondary', 'btn-primary');
        printBtn.disabled = false;
        printBtn.classList.replace('btn-outline-secondary', 'btn-primary');
      })
      .catch(err => {
        console.error(err);
        alert('Erreur réseau. Veuillez réessayer.');
      });
  });

  // Générer facture (affiche modal 5s)
  genBtn.addEventListener('click', function() {
    const saleId = finalizeBtn.dataset.saleId;
    if (!saleId) return alert('Aucune vente sélectionnée.');
    fetch(`/core/caisse/sale-info/?sale_id=${saleId}`)
      .then(res => res.json())
      .then(data => {
        // Organisation du modal en tableau structuré
        document.getElementById('modal-invoice-number').textContent = data.invoice_number;
        document.getElementById('modal-invoice-date').textContent = data.date;
        document.getElementById('modal-invoice-cashier').textContent = data.cashier;
        document.getElementById('modal-invoice-customer').textContent = data.customer;
        document.getElementById('modal-invoice-total').textContent = data.total_amount + ' €';
        
        // Créer tableau organisé pour les produits
        const tbody = document.getElementById('modal-invoice-items');
        tbody.innerHTML = '';
        data.items.forEach(item => {
          const tr = document.createElement('tr');
          tr.innerHTML = `
            <td>${item.product}</td>
            <td class="text-center">${item.quantity}</td>
            <td class="text-end">${(item.line_total / item.quantity).toFixed(2)} €</td>
            <td class="text-end">${item.line_total} €</td>
          `;
          tbody.appendChild(tr);
        });
        
        const invoiceModal = new bootstrap.Modal(document.getElementById('invoiceModal'));
        invoiceModal.show();
        setTimeout(() => invoiceModal.hide(), 5000);
        finalizeBtn.disabled = false;
        finalizeBtn.classList.replace('btn-secondary', 'btn-success');
      })
      .catch(err => {
        console.error(err);
        const invoiceModal = new bootstrap.Modal(document.getElementById('invoiceModal'));
        invoiceModal.show();
        setTimeout(() => invoiceModal.hide(), 5000);
        finalizeBtn.disabled = false;
        finalizeBtn.classList.replace('btn-secondary', 'btn-success');
      });
  });

  // Imprimer facture
  printBtn.addEventListener('click', function() {
    const saleId = finalizeBtn.dataset.saleId;
    if (!saleId) return alert('Aucune vente sélectionnée.');
    window.open(`/core/caisse/generate-invoice/?sale_id=${saleId}`, '_blank');
    genBtn.disabled = true;
    genBtn.classList.replace('btn-primary', 'btn-outline-secondary');
    printBtn.disabled = true;
    printBtn.classList.replace('btn-primary', 'btn-outline-secondary');
    finalizeBtn.disabled = false;
    finalizeBtn.classList.replace('btn-secondary', 'btn-success');
  });

  // Rendu panier
  function renderCart() {
    cartList.innerHTML = '';
    if (cart.length === 0) {
      cartList.innerHTML = '<li class="list-group-item text-center text-muted">Le panier est vide<br>Ajoutez des produits pour commencer</li>';
    } else {
      // === Début insertion gestion quantités et suppression ===
      cart.forEach((item, idx) => {
        const li = document.createElement('li');
        li.className = 'list-group-item d-flex flex-column';
        li.innerHTML = `
          <div class="d-flex justify-content-between">
            <span class="product-name">${item.name}</span>
          </div>
          <div class="d-flex justify-content-end align-items-center mt-2">
            <button class="btn btn-sm btn-outline-secondary qty-btn mx-1" data-index="${idx}" data-action="decrease">−</button>
            <input type="number" min="1" class="form-control form-control-sm qty-input mx-1" style="width:60px;"
                   value="${item.qty}" data-index="${idx}">
            <button class="btn btn-sm btn-outline-secondary qty-btn mx-1" data-index="${idx}" data-action="increase">+</button>
            <button class="btn btn-sm btn-outline-danger remove-btn ms-3" data-index="${idx}">×</button>
          </div>`;
        cartList.appendChild(li);
      });
      // Gestion incrément/décrément
      document.querySelectorAll('.qty-btn').forEach(btn => {
        btn.addEventListener('click', e => {
          const idx = +btn.dataset.index;
          if (btn.dataset.action === 'increase') cart[idx].qty++;
          else if (cart[idx].qty > 1) cart[idx].qty--;
          renderCart();
        });
      });
      // Gestion saisie directe
      document.querySelectorAll('.qty-input').forEach(input => {
        input.addEventListener('change', e => {
          const idx = +e.target.dataset.index;
          cart[idx].qty = Math.max(1, parseInt(e.target.value) || 1);
          renderCart();
        });
      });
      // Gestion suppression
      document.querySelectorAll('.remove-btn').forEach(btn => {
        btn.addEventListener('click', e => {
          cart.splice(+btn.dataset.index, 1);
          renderCart();
        });
      });
      // === Fin insertion ===
    }
    cartCount.textContent = cart.reduce((sum, i) => sum + i.qty, 0);
    const subtotal = cart.reduce((sum, i) => sum + i.price * i.qty, 0);
    const tax = subtotal * 0.2;
    const total = subtotal + tax;
    subtotalEl.textContent = subtotal.toFixed(2) + ' €';
    taxEl.textContent    = tax.toFixed(2) + ' €';
    totalEl.textContent  = total.toFixed(2) + ' €';

    // Active Finaliser si articles présents
    if (cart.length > 0) {
      finalizeBtn.disabled = false;
      finalizeBtn.classList.replace('btn-secondary', 'btn-success');
      finalizeBtn.innerHTML = '<i class="fas fa-check-circle"></i> Finaliser la vente';
    } else {
      initButtons();
    }
  }

  function calculateTotal() {
    const sub = parseFloat(subtotalEl.textContent) || 0;
    const tax = parseFloat(taxEl.textContent) || 0;
    return sub + tax;
  }

  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      document.cookie.split(';').forEach(c => {
        const [k, v] = c.trim().split('=');
        if (k === name) cookieValue = decodeURIComponent(v);
      });
    }
    return cookieValue;
  }

  renderCart();
});
