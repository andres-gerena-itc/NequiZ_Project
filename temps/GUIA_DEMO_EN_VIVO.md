# Guion y Paso a Paso para la Demo en Vivo - NequiZ (7 Minutos)

**Objetivo Central de la Exposición:** Demostrar ante el profesor/jurado cómo el patrón de *Arquitectura Hexagonal (Puertos y Adaptadores)* permite intercambiar libremente componentes de infraestructura (Bases de datos, CLI, APIs completas) de manera instantánea, sin alterar ni una sola línea del código que compone el núcleo financiero (`domain/` y `application/`).

---

## 🕒 Min. 0:00 - 1:30 | Modo 1: Dependencia en Memoria (Testing Ágil)

*Objetivo: Demostrar que el sistema vive e interactúa sin bases de datos ajenas, confirmando el aislamiento.*
**Archivos involucrados:** Implementaciones de adaptadores *Fake* en `tests/fakes/fake_transaccion_repository.py` (y `fake_usuario_repository.py`), y el ensamblador central `infrastructure/config/container.py` que permite la inyección de estas dependencias al vuelo.

**Paso a paso literal:**
1. Muestra tu archivo de configuración `.env` en pantalla.
2. Modifica o asegúrate de que diga:
   `MODO_REPOSITORIO=memoria`
3. Arranca el servidor local en la terminal:
   `python app.py`
4. **Registro (Postman):** Crea un nuevo POST hacia `http://localhost:5000/api/auth/registro`
   - **Body (JSON):**
     ```json
     {
         "nombre": "Juan",
         "numeroTelefono": "3001112233",
         "email": "juan@test.com",
         "password": "123"
     }
     ```
   - **Acción:** Presiona *Send* y **copia el `accessToken`** largo que devuelve la respuesta.
5. **Transferencia (Postman):** Crea un POST hacia `http://localhost:5000/api/transferencias/enviar`
   - **Auth / Headers:** Selecciona `Bearer Token` y pega el token recién copiado.
   - **Body (JSON):**
     ```json
     {
         "numeroDestino": "3009876543",
         "monto": 15000,
         "mensaje": "Prueba en memoria"
     }
     ```
   - **Acción:** Presiona *Send* y muestra el saldo descontado.
6. **Discurso:** *"Como pueden observar, transferimos dinero sin Docker o MongoDB. Esto ocurre porque inyectamos un `FakeTransaccionRepository` en la Capa de Aplicación alojado en la RAM."*
7. Cierra la ejecución del servidor web (pulsa `Ctrl+C`).

---

## 🕒 Min. 1:30 - 3:30 | Modo 2: Conmutación a MongoDB (El Mundo Real)

*Objetivo: Inyectar la robusta tecnología real sin reescribir ni tocar el Casos de Uso del negocio.*
**Archivos involucrados:** Creación del adaptador real en `infrastructure/adapters/secondary/mongodb/transaccion_repository.py` (que usa PyMongo), y el cambio condicional en `infrastructure/config/container.py` que inyecta esta clase cuando el `.env` cambia.

**Paso a paso literal:**
1. Abre tu archivo `.env` y cambia la variable frente a ellos:
   `MODO_REPOSITORIO=mongodb`
2. Arranca de nuevo el servidor local:
   `python app.py` (o tu comando Docker).
3. **Registro (Postman):** Vuelve al endpoint `http://localhost:5000/api/auth/registro` pero cambia los datos para que MongoDB los tome frescos por primera vez:
   - **Body (JSON):**
     ```json
     {
         "nombre": "Maria",
         "numeroTelefono": "3004445566",
         "email": "maria@test.com",
         "password": "123"
     }
     ```
   - **Acción:** Presiona *Send*.
4. MÁGIA EN VIVO: Abre *MongoDB Compass* o la web de *Mongo Atlas*.
5. Selecciona la database de `nequiz` y abre la colección `usuarios`.
6. Presiona el botón *Refresh* y señala el documento "Maria" inyectado.
7. **Discurso:** *"Acabamos de cambiar el cerebro de almacenamiento total del proyecto de la RAM hacia MongoDB en la nube. Cambiamos literalmente 1 variable, el `EnviarDineroUseCase` de negocio o el de Registro jamás se enteraron o fueron tocados."*

---

## 🕒 Min. 3:30 - 5:00 | Modo 3: Interfaz de Línea de Comandos (CLI)

*Objetivo: Demostrar que se puede girar dinero por consola usando el mismo caso de uso sin pasar por HTTP.*
**Archivos involucrados:** Creación nativa del adaptador de entrada en `infrastructure/entrypoints/cli.py` utilizando la librería `click`. Este archivo traduce los argumentos de la terminal y los envía directamente al `RealizarTransferenciaUseCase`.

**Paso a paso literal:**
1. Con la consola abierta (puedes detener `app.py`, el CLI arranca su propio hilo directo a la Base de Datos).
2. Pega literalmente el siguiente comando en la terminal:
   ```bash
   python infrastructure/entrypoints/cli.py transferir --origen "3004445566" --destino "3001234567" --monto 25000 --mensaje "Pago secreto CLI"
   ```

   python infrastructure/entrypoints/cli.py transferir --origen "3004445566" --destino "3001234567" --monto 25000 --mensaje "Pago secreto CLI"


3. Presiona Enter y muestra en pantalla cómo se retorna exitosamente: "✅ ¡Transferencia Exitosa!", con el recibo y balance.
4. **Discurso:** *"En 10 segundos despachamos dinero sin recurrir a rutas Web de Flask. Hemos instaurado un Segundo Adaptador Primario (CLI), que inyecta los datos llamando exactamente al mismo caso de uso y reglas estrictas."*

---

## 🕒 Min. 5:00 - 7:00 | El Segundo Canal de Entrada (GraphQL Avanzado)

*Objetivo: Exponer canales paralelos e interconectabilidad para clientes institucionales desacoplando el transporte.*
**Archivos involucrados:** Construcción estructural del adaptador GraphQL en `infrastructure/adapters/primary/graphql/queries.py` y `types.py`. Estos archivan decodifican el lenguaje GraphQL y delegan el trabajo matematico a los casos de uso originales (`ObtenerMovimientosUseCase`).

**Paso a paso literal:**
0. **Login previo (Postman):** Antes de ir a GraphQL, realiza un POST a `http://localhost:5000/api/auth/login` para obtener el token de Fabián (Usuario Semilla).
   - **Body (JSON):**
     ```json
     {
         "numeroTelefono": "3009876543",
         "password": "nequiz2025"
     }
     ```
   - **Acción:** Presiona *Send* y **copia el `accessToken`** de la respuesta.
1. Asegúrate de tener la aplicación activa: `python app.py`.
2. Dirígete a tu navegador en la URL directa: [http://localhost:5000/graphql](http://localhost:5000/graphql)
3. Borra lo que haya en el panel izquierdo de GraphiQL y pega **esta Query exacta:**
   ```graphql
   query {
     misMovimientos(tipo: "TODOS") {
       monto
       fecha
       tipo
     }
   }
   ```
   **Opción 2 (Consultar Saldo):**
   ```graphql
   query {
     miPerfil {
       nombre
       saldo
     }
   }
   ```
4. **IMPORTANTE:** Haz clic en el botón de la parte inferior que dice **"HTTP Headers"** y pega lo siguiente (reemplazando con tu token real obtenido en el paso 0):
   ```json
   {
     "Authorization": "Bearer TU_ACCESS_TOKEN_AQUI"
   }
   ```
5. Presiona el botón circular de **Play** (Ejecutar).
6. Muestra a la audiencia el JSON formateado de la derecha que te devuelve únicamente los tres campos delimitados (o el saldo).
7. **Discurso/Cierre:** *"Para cerrar demostramos la resiliencia tecnológica de NequiZ al proveer una API paralela web a base de esquemas tipados (GraphQL). El Resolver (Adaptador de Entrada) solo encapsuló la respuesta y delegó de nuevo las matemáticas corporativas al `ObtenerMovimientosUseCase` inalterable o al de Perfil. La arquitectura permite hoy reemplazar la Base de Datos y la API sin destrozar nuestro Dominio de Cuentahabientes. Muchas gracias."*
