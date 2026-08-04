# RF-003: Roles y Permisos de Usuario

**Tipo:** Requerimiento funcional
**Fuente:** RFP-AgroInteligente-Colombia.md — Sección 4 (Actores del sistema) y Sección 5.2
**Prioridad:** Alta

## Descripción
El sistema debe implementar un modelo de control de acceso basado en roles (RBAC) con al menos cuatro perfiles diferenciados:

- **Administrador:** monitorea infraestructura, usuarios, membresías y configuración general de la plataforma. Acceso total a la administración.
- **Cliente (Agricultor):** consulta alertas, recomendaciones y dashboard sobre sus propias fincas y cultivos. Acceso limitado a sus propios datos.
- **Técnico Agrónomo:** analiza los modelos y valida las predicciones/recomendaciones generadas por la IA. Puede tener acceso a datos agregados/anónimos para fines de validación.
- **Investigador IES:** administra modelos y experimentos de Machine Learning; soporta el componente de investigación. Acceso a datasets, experimentos y configuración de modelos.

## Actores involucrados
- Administrador (gestiona roles)
- Todos los actores (heredan permisos según su rol)

## Criterios de aceptación
- Cada rol tiene permisos claramente definidos y diferenciados.
- Un usuario solo puede tener un rol activo a la vez (a definir si puede tener múltiples roles).
- El administrador puede crear, editar y desactivar usuarios.
- El administrador puede asignar y cambiar roles.
- No especificados en el RFP — definir matriz de permisos detallada por rol y recurso con el cliente.

## Dependencias / relacionados
- RF-002: Gestión de usuarios
- RF-004: Aislamiento de datos entre clientes
- RNF-004: Seguridad — autenticación/autorización

## Notas del analista
- El RFP inicial solo menciona Administrador y Cliente. El RFP consolidado agrega Técnico Agrónomo e Investigador IES. Se asume el modelo de 4 roles como requerimiento válido.
- El rol "Investigador IES" está ligado al componente de investigación aplicada del proyecto (posible financiación MinCiencias/ColombIA Inteligente) y debe poder gestionar experimentos de ML sin acceder a datos personales de agricultores.
