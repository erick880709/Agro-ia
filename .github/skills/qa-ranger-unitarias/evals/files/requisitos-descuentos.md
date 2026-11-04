# Descuentos de pedidos — requisitos confirmados

- RF-01 / CA-01: el total es la suma de precio por cantidad menos el descuento, redondeado a dos decimales.
- RF-02 / CA-02: por volumen total de unidades se aplica 5% desde 10, 10% desde 50 y 15% desde 100.
- RF-03 / CA-03: el cliente oro suma 10%, plata 5% y estándar 0%. Un tipo desconocido se rechaza.
- RF-04 / CA-04: un cupón vigente suma su porcentaje. Un cupón vencido se rechaza.
- RF-05 / CA-05: el descuento acumulado nunca supera 30%.
- RF-06 / CA-06: un pedido sin ítems, con cantidad no entera o no positiva, o con precio negativo se rechaza.

Alcance: pruebas unitarias del módulo `descuentos.mjs`, en memoria, con el runner nativo de Node.js.
No hay base de datos, red ni navegador. La meta de cobertura unitaria es la de la política QA.
