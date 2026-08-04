# RF-006: Gestión de Fincas

**Tipo:** Requerimiento funcional
**Fuente:** RFP-AgroInteligente-Colombia.md — Sección 5.4; RFP-inicial.md — Sección 3 (Gestión de Fincas)
**Prioridad:** Alta

## Descripción
Cada cliente debe poder registrar, editar, consultar y eliminar fincas de su propiedad. Por cada finca se debe almacenar la siguiente información:

- Nombre de la finca
- Departamento
- Municipio
- Área (hectáreas)
- Tipo de cultivo actual
- Ubicación GPS: latitud y longitud
- Fotografía de la finca

La información de ubicación GPS debe poder obtenerse manualmente (ingresada por el usuario) o automáticamente mediante integración con Google Maps o un proveedor GIS.

## Actores involucrados
- Cliente (Agricultor) — gestiona sus propias fincas
- Administrador — puede visualizar todas las fincas del sistema

## Criterios de aceptación
- Un cliente puede registrar múltiples fincas hasta el límite de su membresía.
- Los campos de ubicación GPS se validan (rango válido de latitud/longitud para Colombia).
- La fotografía se almacena y se muestra en el perfil de la finca.
- La información de la finca es editable por el cliente propietario.
- No especificados en el RFP — definir: ¿tamaño máximo de fotografía?, ¿formatos aceptados?, ¿geocodificación inversa para validar departamento/municipio?

## Dependencias / relacionados
- RF-004: Aislamiento de datos entre clientes
- RF-005: Gestión de membresías (límite de fincas)
- RF-011: Integración con Google Maps/GIS
- RF-027: Visualización geoespacial

## Notas del analista
- El RFP no especifica si una finca puede tener múltiples cultivos o zonas de cultivo. Se asume inicialmente un cultivo principal por finca; si se requiere soporte multi-cultivo por finca, el modelo de datos debe ajustarse.
- La geocodificación inversa (obtener departamento/municipio desde coordenadas GPS) puede implementarse con la API de Google Maps o con datos abiertos del IGAC/DANE, reduciendo dependencia de servicios de pago.
