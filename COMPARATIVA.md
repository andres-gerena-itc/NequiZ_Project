# Comparativa: Monolito vs Arquitectura Hexagonal

## 1. Líneas de Código por Módulo (Métricas Reales)
| Módulo / Capa | Monolito Original (`Nequiz_Monolito`) | Arquitectura Hexagonal (`NequiZ_Project_Hexagonal`) |
|---|---|---|
| **Lógica de Negocio y Reglas** | Embebidas en `routes/` y `graphql_schema/` | `domain/` (243 LOC) y `application/` (444 LOC) |
| **Integración de DB y Utilidades** | `utils/` (543 LOC) | `infrastructure/adapters/secondary/` |
| **Exposición Web (REST/GQL)** | `routes/` (623 LOC) y `graphql_schema/` (376 LOC) | `infrastructure/adapters/primary/` |
| **Configuración y Raíz** | `app.py`, `config.py` (242 LOC) | Configuración e inyección (362 LOC) |
| **Total LOC de la Aplicación** | **~1784 LOC** (Fuente altamente acoplada) | **~2595 LOC** (Desacoplado, Cohesivo y Testeable) |

*Nota: La arquitectura hexagonal incrementa el total de líneas de código debido a la creación explícita de contratos (Puertos), Entidades, Casos de Uso y la inyección de dependencias, pero reduce drásticamente la complejidad ciclomática y el riesgo de regresión por capa.*

## 2. Evidencia de Acoplamiento en el Monolito (Antes)
Durante el análisis de la copia base (`Nequiz_Monolito/routes/transferencias.py`, líneas 60-130), evidenciamos violaciones arquitectónicas graves. El controlador HTTP de Flask es responsable de unificar:
1. **Infraestructura Web:** Deserialización y validación del JWT.
2. **Acceso a Datos:** Lectura y sobreescritura directa usando la instancia local `usuarios_collection` de MongoDB.
3. **Manejo de Reglas Críticas:** Control de pre-condiciones de negocio (`if usuario_origen['saldo'] < monto:`, o el auto-envío).
4. **Respuesta:** Formateo de la salida HTTP.

**Después (Hexagonal):** El controlador HTTP en la nueva arquitectura fue refaccionado para fungir como un **adaptador web hueco**. Ahora se limita estrictamente a recibir el *request*, traducir el protocolo a un Comando, enviarlo a la capa intermedia de `application/` —que carece de código HTTP—, y devolver al cliente la salida estandarizada del DTO.

## 3. Tiempo de Ejecución y Testabilidad
| Métrica | Monolito Original | Arquitectura Hexagonal |
|---|---|---|
| **Velocidad de Pruebas** | Lenta. Se requería obligatoriamente inicializar la base de datos real en un `before_all`. | **< 1 segundo**. Las pruebas de la lógica de negocio y casos de uso evaden las capas externas interactuando con repositorios *Fakes* en Memoria volátil. |
| **Testabilidad del Dominio** | Resultaba imposible testar un cambio de tarifa sin instanciar el servidor de Flask. | Ejecutable aislando el código `domain/` careciendo de librerías exógenas como PyMongo. |

## 4. Evolutividad y Resiliencia Tecnológica
Si el negocio demandara transicionar la base de datos subyacente de **MongoDB a PostgreSQL**, en el antiguo Monolito tendríamos que reescribir docenas de sentencias *find* y *update_one* incrustadas en cada uno de los controladores de ruta, además de modificar los *resolvers* de GraphQL, lo que dispararía la probabilidad de quebrar la lógica de transacciones.

En la **Arquitectura Hexagonal**, el cambio transcurre como una adición y no como una alteración. Se escribiría un nuevo adaptador impulsado por SQLAlchemy en `infrastructure/adapters/secondary/`, y luego se conmutaría en el inyector de dependencias sin tocar ni una sola coma del código residente en `domain/` o `application/`. El núcleo es soberano.
