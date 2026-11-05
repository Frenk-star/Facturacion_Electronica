# Arquitectura

Se conserva la aplicación `facturacion` y la configuración `FacturacionSunat`. La arquitectura corresponde a Django con una capa de servicios; no utiliza una arquitectura hexagonal ni repositorios artificiales.

```mermaid
flowchart LR
    Navegador[Templates Bootstrap y JavaScript] --> Web[web_views y forms]
    Navegador --> API[views y serializers DRF]
    Integrador[Cliente JWT] --> API
    Web --> Ambito[permissions: empresa y rol]
    API --> Ambito
    API --> Servicio[services: emisión y créditos]
    Servicio --> Modelos[models y transacciones ORM]
    Servicio --> XML[xml_utils]
    XML --> Mock[ose_mock determinista]
    Mock --> Modelos
    Web --> Informes[reportes]
    API --> Informes
    API --> PDF[pdf_utils]
    Modelos --> DB[(SQLite local / PostgreSQL concurrente)]
```

`models.py` define integridad, identidad y snapshots. `services.py` centraliza cálculos decimales, reservas de saldo, numeración y transiciones. `serializers.py` valida entradas REST y transforma resultados. `views.py` maneja HTTP y filtros. `permissions.py` resuelve el ámbito exclusivamente a partir de permisos comprobados. `signals.py` protege el contenido emitido frente a cambios y borrados por ORM ordinario. `reportes.py` comparte las filas de JSON, HTML, CSV y Excel. `web_views.py` renderiza consultas y formularios; la emisión dinámica usa los mismos endpoints que integradores externos.

```mermaid
sequenceDiagram
    actor Usuario
    participant JS as emitir.js
    participant API as API REST
    participant S as FacturacionService
    participant DB as PostgreSQL
    participant OSE as OSE mock
    Usuario->>JS: Selecciona cliente y líneas
    JS->>JS: Calcula vista preliminar
    JS->>API: POST con CSRF e idempotencia
    API->>API: Comprueba membresía, rol y entrada
    API->>S: Emite dentro de atomic
    S->>DB: Bloquea empresa y valida catálogo
    S->>S: Recalcula mediante Decimal
    S->>DB: Guarda detalles y bloquea serie
    S->>DB: Asigna correlativo e historial
    S->>OSE: Procesa XML académico
    OSE-->>S: Aceptado o rechazado simulado
    S->>DB: Guarda intento y estado
    DB-->>API: Commit
    API-->>JS: Documento definitivo
    JS-->>Usuario: Detalle, voucher y descargas
```

Todo el procesamiento mock pertenece a la transacción: no hay efectos de red que puedan quedar fuera de un rollback. Una integración real requeriría una cola/outbox y reconciliación; no se implementan porque no se solicitan envíos reales. Los imports locales de XML/OSE en servicios evitan ciclos con los modelos y mantienen el punto de entrada existente `FacturacionService`.
