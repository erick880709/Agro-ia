# 03 — `match` y validación de esquemas

## Contenido
1. Operadores de `match`
2. Marcadores difusos (fuzzy)
3. Validaciones con predicado `#?` y referencias cruzadas
4. Arreglos y `match each`
5. Esquemas reutilizables (patrón recomendado)
6. JsonPath y `get`
7. XML
8. Headers, texto, bytes
9. Cuándo usar `assert` y `karate.expect`

---

## 1. Operadores

| Operador | Significado |
|---|---|
| `==` | Igualdad estructural completa (orden de claves irrelevante; orden de arreglos sí importa) |
| `!=` | Distinto |
| `contains` | El actual contiene las claves/elementos esperados (subconjunto, 1 nivel) |
| `contains deep` | Subconjunto recursivo en objetos anidados |
| `contains only` | Mismos elementos de arreglo, cualquier orden |
| `contains only deep` | Ídem recursivo |
| `contains any` | Al menos uno |
| `!contains` | No contiene |
| `each` | Aplica a cada elemento de un arreglo |
| `within` | (v2) El actual está contenido en el esperado |

```gherkin
* match response == { id: '#number', nombre: 'Ana', etiquetas: ['a', 'b'] }
* match response contains { nombre: 'Ana' }
* match response contains deep { cliente: { direccion: { ciudad: 'Medellín' } } }
* match response.etiquetas contains only ['b', 'a']
* match response.etiquetas contains any ['x', 'a']
* match response !contains { password: '#notnull' }
* match response.items[*].id contains [3, 1]
* match response..nombre contains 'Ana'          # búsqueda a cualquier profundidad
```

## 2. Marcadores difusos

| Marcador | Valida |
|---|---|
| `#ignore` | Cualquier cosa (no valida) |
| `#null` / `#notnull` | Nulo / no nulo (con `#null` la clave debe existir) |
| `#present` / `#notpresent` | Clave existe / no existe |
| `#string` `#number` `#boolean` `#array` `#object` | Tipo |
| `#uuid` | UUID válido |
| `#regex <patrón>` | Coincide con regex (string) |
| `#? <expr JS>` | Predicado; `_` es el valor actual |
| `#[]` / `#[n]` / `#[] <marcador>` | Arreglo / de tamaño n / cada elemento cumple |
| `#(expr)` | Valor calculado (igualdad) |
| `##<marcador>` | Opcional: ausente, nulo, o cumple el marcador (`##string`, `##number`, `##(esquema)`) |

```gherkin
* match response ==
  """
  {
    id: '#uuid',
    documento: '#regex [0-9]{6,10}',
    monto: '#? _ > 0 && _ <= 50000000',
    moneda: '#regex (COP|USD)',
    fechaCreacion: '#regex \\d{4}-\\d{2}-\\d{2}T.*',
    referencia: '##string',
    detalles: '#[] #object',
    auditoria: '#ignore'
  }
  """
```

## 3. Predicados y referencias cruzadas

`_` es el valor del campo; `$` es la raíz del JSON actual (permite validar un campo contra otro).

```gherkin
* def esFechaIso = function(s){ try { java.time.OffsetDateTime.parse(s); return true } catch(e) { return false } }
* match response ==
  """
  {
    fechaCreacion: '#? esFechaIso(_)',
    total: '#? _ == $.subtotal + $.impuesto',
    subtotal: '#number',
    impuesto: '#number',
    items: '#[_ > 0]'
  }
  """
```
`'#[_ > 0]'`: arreglo con al menos un elemento (la expresión entre corchetes recibe el tamaño como `_`).

## 4. Arreglos

```gherkin
* match each response.items == { id: '#number', estado: '#regex (ACTIVO|INACTIVO)' }
* match each response.items contains { estado: 'ACTIVO' }
* match response.items == '#[3]'
* match response.items == '#[] item'                # item = esquema definido antes
* match response.items[0] == item
* def ordenados = karate.sort(response.items, x => x.fecha)
* match response.items == ordenados                 # valida ordenamiento
```

## 5. Esquemas reutilizables (patrón recomendado)

Un archivo por entidad en `schemas/`, compuesto por referencia. Mantiene las features cortas y centraliza el contrato.

`schemas/direccion.json`
```json
{ "ciudad": "#string", "linea1": "#string", "codigoPostal": "##string" }
```
`schemas/cliente.json`
```json
{
  "id": "#uuid",
  "nombre": "#string",
  "email": "#regex .+@.+\\..+",
  "direccion": "#(direccion)",
  "telefonos": "#[] #string",
  "segmento": "##string"
}
```
Feature:
```gherkin
* def direccion = read('classpath:clientes/schemas/direccion.json')
* def cliente = read('classpath:clientes/schemas/cliente.json')
* match response == cliente
* match response.items == '#[] cliente'
```
Orden importa: define el sub-esquema antes de leer el que lo referencia (las `#()` se resuelven al hacer `read()`).

Para esquemas con un objeto anidado **opcional/nullable**: `'##(direccion)'`. En v2, si el esquema se construye como literal y debe conservar `##()` sin resolver, envuélvelo en paréntesis: `* def esquema = ({ direccion: '##(direccion)' })`, o léelo con `* json esquema = karate.readAsString('...')`.

**Contrato desde OpenAPI**: Karate open source no valida automáticamente contra un OpenAPI; traduce los `schemas` del spec a archivos `#marcador` (tipos → `#string/#number/...`, `required` ausente → `##`, `enum` → `#regex (A|B)`, `format: uuid` → `#uuid`, `pattern` → `#regex`, `minimum/maximum` → `#?`). En v2 existe una extensión `openapi` activable en `karate-boot.js` para cobertura de operaciones (ver 08), parte de las ofertas comerciales.

## 6. JsonPath y `get`

```gherkin
* def nombres = $response.items[*].nombre
* def activos = $response.items[?(@.estado=='ACTIVO')]
* def primero = get[0] response.items[?(@.estado=='ACTIVO')]
* def total = karate.jsonPath(response, '$.items.length()')
* match response.items[?(@.id==5)].nombre == ['Ana']    # filtros siempre devuelven arreglo
```

## 7. XML

```gherkin
* def xml = <cliente><id>1</id><nombre>Ana</nombre></cliente>
* match xml/cliente/nombre == 'Ana'
* match xml == <cliente><id>#number</id><nombre>#string</nombre></cliente>
* match //nombre == 'Ana'                                # XPath que empieza por / o // se aplica a response
* match response/cliente/nombre == 'Ana'                 # variable/xpath
* def n = karate.xmlPath(response, '/cliente/nombre')
* set xml/cliente/nombre = 'Luis'
* match /Envelope/Body/RespuestaConsulta/Codigo == '00'  # respuestas SOAP (namespaces ignorados por nombre local)
```
Conversión: `* json j = xml` y `* xml x = j`.

## 8. Headers, texto, bytes

```gherkin
* match header Content-Type contains 'application/json'   # case-insensitive
* match responseHeaders['X-Request-Id'][0] == '#notnull'
* match response contains 'operación exitosa'             # texto plano
* match responseBytes == read('data/esperado.pdf')
* match responseTime < 2000                               # SLA funcional, no reemplaza pruebas de carga
```

## 9. `assert` y `karate.expect`

`match` da mensajes de error ricos (ruta exacta, esperado vs actual); prefiérelo siempre. `assert` solo para expresiones booleanas que no son comparación de datos:
```gherkin
* assert response.items.length >= 1
* karate.expect(response.total).to.be.within(1, 10)    # v2, estilo Chai
```
