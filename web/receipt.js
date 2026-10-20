/** Purpose: render a receipt from its capability URL. Inputs: location path. Returns: Promise<void>. */
async function renderReceipt() {
  const token = location.pathname.split('/')[2];
  const response = await fetch(`/api/receipt/${encodeURIComponent(token)}`);
  const data = await response.json();
  const box = document.getElementById('receipt-details');
  if (!response.ok) { box.textContent = data.error; return; }
  const order = data.order;
  const recipe = order.recipe.config;
  for (const value of [`Order #${order.id}`, order.created, order.recipe.name, `${recipe.milk} milk / ${recipe.strength} / ${recipe.temperature} C`, `Syrup shots: ${recipe.syrup} / Extra espresso shots: ${recipe.extra}`, `Subtotal: SEK ${(order.amount / 100).toFixed(2)}`, `Discount: SEK ${(order.discount / 100).toFixed(2)}`, `Paid: SEK ${(order.paid / 100).toFixed(2)}`, `Payment simulator: ${order.method}`]) {
    const p = document.createElement('p'); p.textContent = value; box.append(p);
  }
  const qr = document.createElement('img'); qr.src = `/receipt/${encodeURIComponent(token)}/qr.svg`; qr.alt = 'QR containing this receipt'; box.append(qr);
}
renderReceipt();
