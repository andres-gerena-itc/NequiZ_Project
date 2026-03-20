# NequiZ - Arquitectura Hexagonal 🚀

NequiZ es el proyecto de Ingeniería de Software que simula el núcleo de una billetera digital (estilo Nequi), refactorizado completamente hacia el patrón de arquitectura limpia: **Puertos y Adaptadores (Arquitectura Hexagonal)**.

Esta arquitectura separa drásticamente el modelo de dominio de los detalles de persistencia y de las interfaces de comunicación web, garantizando alta mantenibilidad, escalabilidad e intercambio de tecnologías con impacto `$cero` en el core.

## 🛠️ Tecnologías Utilizadas
* **Backend:** Python 3.11, Flask, Click (CLI).
* **Bases de Datos:** MongoDB 6.0 (PyMongo).
* **API:** API RESTful orientada a endpoints y GraphQL (Graphene).
* **Seguridad:** JWT para el control de acceso, BCrypt para hashing de contraseñas.
* **Infraestructura:** Totalmente contenerizada mediante Docker y Docker Compose.

---

## 🏛️ Estructura Arquitectónica

```text
NequiZ_Project_Hexagonal/
├── domain/            # 🟢 El 'Núcleo'. Entidades (Usuario, Transaccion) y puertos (Contratos/Interfaces)
├── application/       # 🟡 Casos de Uso. Reglas del negocio orquestadas (ej: EnviarDinero, ObtenerPerfil)
├── infrastructure/    # 🔴 El 'Mundo Exterior'. Todo lo relacionado a la tecnología.
│   ├── adapters/      #   ➤ Secundarios: Repositorios MongoDB (Motor y Mapeos Pura -> Docs)
│   ├── entrypoints/   #   ➤ Primarios: Controladores Flask (REST), Resolvers GraphQL y CLI
│   └── config/        #   ➤ Inyección de Dependencias (Container) y Variables de Entorno (.env)
├── tests/             # Tests Unitarios sin BD local que validan los contratos de importación
└── docker-compose.yml # Orquestador nativo
```

---

## 💻 Guía de Instalación para Windows (Vía Docker) 

Hemos estandarizado todo el proyecto a través de contenedores virtuales para **eliminar el uso de entornos virtuales manuales y librerías dispares en tu Windows.** 

> ⚠️ **Aviso de Seguridad sobre la Base de Datos:**
> Por protocolos de seguridad estudiantil y empresarial, **no compartimos nuestra base de datos real (MongoDB Atlas) en el repositorio**.
> - **Si usas la instalación vía Docker Compose (Recomendado):** No debes preocuparte por nada. El orquestador descargará y levantará automáticamente una base de datos local y privada (MongoDB 6.0) exclusivamente para ti y la conectará a la aplicación.
> - **Si ejecutas el proyecto sin Docker (`python app.py`):** **Debes tener tu propia base de datos MongoDB** (instalada localmente o en la nube) y configurar obligatoriamente tu cadena de conexión en la variable `MONGODB_URI` dentro de tu archivo `.env`.

### Prerrequisitos
Asegúrate de contar con los siguientes programas instalados:
1. **Git** para clonar el repositorio.
2. **Docker Desktop para Windows** instalado y encendido.
   - Puedes instalarlo rápidamente abriendo PowerShell y ejecutando: `winget install Docker.DockerDesktop`
   - Recuerda reiniciar el PC luego de instalarlo. Cuando el programa abre, debe mostrar el estatus "Engine Running".

### Pasos para levantar el proyecto

**Paso 1:** Abre tu terminal (PowerShell o Git Bash) y clona este repositorio:
```bash
git clone https://github.com/andres-gerena-itc/NequiZ_Project_Hexagonal.git
cd NequiZ_Project_Hexagonal
```

**Paso 2:** Crea tu archivo de configuración de seguridad basado en el de ejemplo.
```bash
copy .env.example .env
```

**Paso 3:** Configura e Inicia la Aplicación según el Modo de Ejecución:

NequiZ implementa verdaderos *Separation of Concerns*. Puedes ejecutar el núcleo de negocio puro sin base de datos, o el sistema completo.

👉 **Opción A - MODO MEMORIA (Recomendado para Pruebas Ligeras):**
No requiere base de datos. Usa repositorios *fakes* inyectados al vuelo.
1. En tu archivo `.env`, asegúrate de tener: `MODO_REPOSITORIO=memoria`
2. Ejecuta la API localmente rápido y sin dependencias:
```bash
python app.py
```
3. Ejecuta la suite de pruebas unitarias y de integración (Coherencia \> 85%):
```bash
python -m pytest --cov=domain --cov=application --cov=infrastructure tests/
```

👉 **Opción B - MODO REAL CON MONGODB (Entorno Integrado):**
1. En tu archivo `.env`, asegúrate de tener: `MODO_REPOSITORIO=mongodb`
2. Levanta toda la infraestructura con **Docker Compose** (descarga Mongo y expone la API).
```bash
docker compose up --build -d
```
3. Finalizado el proceso, puedes consultar los registros de tu backend para observar la correcta inserción de datos iniciales *(Seed)*:
```bash
docker compose logs -f api_nequiz
```

---

## 🌐 Accesos a la Interfaz Gráfica (Frontend Web)
Además de las APIs y la consola, el proyecto despliega una interfaz web simulando la aplicación interactiva de la billetera. Una vez que el servidor esté corriendo, puedes hacer clic o acceder directamente desde tu navegador a las siguientes rutas:

- 🏠 **Inicio:** [http://localhost:5000/](http://localhost:5000/)
- 🔐 **Iniciar Sesión:** [http://localhost:5000/login](http://localhost:5000/login)
- 📝 **Registro:** [http://localhost:5000/registro](http://localhost:5000/registro)
- 👤 **Mi Perfil:** [http://localhost:5000/perfil](http://localhost:5000/perfil)
- 💸 **Transferir Dinero:** [http://localhost:5000/transferir](http://localhost:5000/transferir)
- 📊 **Historial de Movimientos:** [http://localhost:5000/movimientos](http://localhost:5000/movimientos)

---

## 🧪 ¿Cómo consumo la Billetera Arquitectónica?

NequiZ demuestra su total desacoplamiento al exponer **tres canales totalmente asíncronos y distintos** apuntando hacia la misma lógica de negocio:

### 1. Vía API REST
- Puedes consumir la información de salud de la API en: `http://localhost:5000/api/info`
- Los endpoints como transferencias (`/api/transferencias/enviar`) requieren el Token JWT enviado por Bearer Auth headers.

### 2. Vía GraphQL Panel (GraphiQL)
El servidor expone una interfaz visual unificada para la generación de queries y mutations de datos transaccionales, visítala en:
- Panel Principal GraphQL: [http://localhost:5000/graphql](http://localhost:5000/graphql)

### 3. Vía Consola (CLI Hexagonal Local)
Para administrar cuentas directamente desde el código sin pasar por puertos HTTP:
```bash
# Transferencia en vivo
python infrastructure/entrypoints/cli.py transferir --origen "3001234567" --destino "3009876543" --monto 100

# Últimos Movimientos
python infrastructure/entrypoints/cli.py historial --numero "3001234567"
```

## 📞 Integrantes
Proyecto desarrollado para la materia de Arquitectura de Software.
- Andrés Gerena
- Fabián Suarez
- Camila Mosquera
