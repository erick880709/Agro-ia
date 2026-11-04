// Calcula el total de un pedido aplicando las reglas de descuento confirmadas.
// Fixture de evaluación: no modificar.

export const TOPE_DESCUENTO = 0.3;

export function validarItems(items) {
  if (!Array.isArray(items) || items.length === 0) {
    throw new Error('El pedido requiere al menos un ítem');
  }
  for (const item of items) {
    if (!Number.isInteger(item.cantidad) || item.cantidad <= 0) {
      throw new Error(`Cantidad inválida para ${item.sku}`);
    }
    if (typeof item.precio !== 'number' || item.precio < 0) {
      throw new Error(`Precio inválido para ${item.sku}`);
    }
  }
}

export function porcentajePorVolumen(unidades) {
  if (unidades >= 100) return 0.15;
  if (unidades >= 50) return 0.1;
  if (unidades >= 10) return 0.05;
  return 0;
}

export function porcentajePorCliente(tipo) {
  switch (tipo) {
    case 'oro':
      return 0.1;
    case 'plata':
      return 0.05;
    case 'estandar':
      return 0;
    default:
      throw new Error(`Tipo de cliente desconocido: ${tipo}`);
  }
}

export function redondear(valor) {
  return Math.round((valor + Number.EPSILON) * 100) / 100;
}

export function calcularTotal(items, tipoCliente, cupon = null) {
  validarItems(items);
  const subtotal = items.reduce((suma, item) => suma + item.precio * item.cantidad, 0);
  const unidades = items.reduce((suma, item) => suma + item.cantidad, 0);
  let porcentaje = porcentajePorVolumen(unidades) + porcentajePorCliente(tipoCliente);
  if (cupon) {
    if (cupon.vence < cupon.hoy) {
      throw new Error('Cupón vencido');
    }
    porcentaje += cupon.porcentaje;
  }
  porcentaje = Math.min(porcentaje, TOPE_DESCUENTO);
  const descuento = redondear(subtotal * porcentaje);
  return { subtotal: redondear(subtotal), descuento, total: redondear(subtotal - descuento) };
}
