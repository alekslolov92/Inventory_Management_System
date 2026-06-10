document.addEventListener("DOMContentLoaded", function () {
    const searchInput = document.getElementById("searchInput");
    if (searchInput) {
        searchInput.addEventListener("keyup", function () {
            const filter = this.value.toLowerCase();
            const rows = document.querySelectorAll("#productTable tbody tr");
            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(filter) ? "" : "none";
            });
        });
    }

    setTimeout(() => {
        document.querySelectorAll(".alert").forEach(el => el.remove());
    }, 4000);
});

function confirmDelete(name) {
    return confirm(`Are you sure you want to delete "${name}"? This cannot be undone.`);
}

function updatePrice(select) {
    const option = select.options[select.selectedIndex];
    const price = option.dataset.price;
    const stock = option.dataset.stock;
    const priceDisplay = document.getElementById("unit_price_display");
    const totalDisplay = document.getElementById("total_display");

    if (price) {
        priceDisplay.value = "₹" + parseFloat(price).toFixed(2) + "  (Stock: " + stock + ")";
    } else {
        priceDisplay.value = "";
    }
    totalDisplay.value = "";
    const qtyInput = document.getElementById("quantity_sold");
    if (qtyInput) qtyInput.max = stock;
}

function updateTotal() {
    const select = document.getElementById("product_id");
    const qty = parseInt(document.getElementById("quantity_sold").value);
    const option = select.options[select.selectedIndex];
    const price = parseFloat(option.dataset.price);
    const totalDisplay = document.getElementById("total_display");

    if (qty > 0 && price) {
        totalDisplay.value = "₹" + (qty * price).toFixed(2);
    } else {
        totalDisplay.value = "";
    }
}