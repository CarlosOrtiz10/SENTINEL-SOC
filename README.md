# SENTINEL-SOC | Laboratorio de estructuras abstractas

**Estructura de Datos · Momento evaluativo 1 · Trabajo individual**

Proyecto académico en **Python 3.10+**, basado en un problema verosímil de ingeniería de software: recibir alertas simuladas de ciberseguridad, atenderlas respetando el orden de llegada e indexar los incidentes activos para consultarlos por identificador. **No es un SIEM operativo ni procesa eventos reales.**

## Arquitectura

```text
              DATOS SINTÉTICOS
                     |
                submit()
                     v
             +----------------+
             | QueueADT[T]    |  << protocolo genérico >>
             +----------------+
             | ListQueue[T]   |  append / pop(0)
             | DequeQueue[T]  |  append / popleft
             +----------------+
                     |
                process_next()
                     v
              +--------------+
              | AVLTree[K,V] |  << índice genérico >>
              +--------------+
               |            |
           find(id)      remove(id)
               |            |
          incidencia     resolución
            activa
```

Un identificador de incidente es único. La **cola** mantiene el orden FIFO (la severidad no modifica el orden), y el **AVL** ordena por ID las alertas que ya salieron de la cola y siguen sin resolver. Esta separación evita confundir una cola de atención con un árbol de búsqueda.

## Requisitos

- Python 3.10 o superior. Sin instalaciones externas para ejecutar pruebas, aplicación o benchmark.
- Las gráficas se conservan en `documentacion/`; las mediciones y evidencias técnicas, en `resultados/`.

## Instalación y ejecución

Desde la carpeta raíz del repositorio:

```bash
python --version
python main.py demo --queue deque
python main.py demo --queue list
python -m unittest discover -s tests -v
python main.py benchmark --out resultados_locales
```

En Windows, si `python` no existe, probar `py -3`. El benchmark crea `benchmark.json`, `colas.csv`, `busquedas.csv`. Los resultados varían según procesador, carga del equipo y versión de Python.

## Contratos e implementación

- `sentinel_soc/adt.py`: `QueueADT[T]` e `IndexADT[K,V]` mediante `typing.Protocol`; excepciones explícitas.
- `sentinel_soc/queues.py`: dos estrategias intercambiables FIFO con `list` y `collections.deque`.
- `sentinel_soc/avl.py`: árbol AVL genérico con rotaciones LL, RR, LR y RL; búsqueda, inserción, eliminación, recorrido inorden y comprobación de invariantes.
- `sentinel_soc/models.py`: entidad inmutable y validada (`Incident`), severidad tipada.
- `sentinel_soc/service.py`: flujo de ciclo de vida e inyección de dependencias.
- `sentinel_soc/benchmark.py`: medición repetida de tiempo y asignación de memoria, además de consultas AVL frente a barrido lineal.
- `tests/`: suite de regresión con escenarios aleatorios reproducibles y pruebas de integridad.

## Hipótesis, teoría y alcance

| Operación | ListQueue | DequeQueue | AVL por ID |
|---|---|---|---|
| Insertar alerta (extremo final) | O(1) amortizado | O(1) amortizado | no aplica |
| Extraer primera alerta | **O(n)** | **O(1)** | no aplica |
| Consultar primera alerta | O(1) | O(1) | no aplica |
| Insertar incidente activo | no aplica | no aplica | **O(log n)** |
| Buscar incidente activo | barrido de lista O(n) | no aplica | **O(log n)** |
| Eliminar incidente activo | no aplica | no aplica | **O(log n)** |

La ocupación del índice AVL es **O(n)**. Además de los registros, almacena nodos, enlaces y altura, por lo que hay sobrecarga de memoria. `deque` **no garantiza** menor memoria que `list`; depende de la carga y del intérprete.

### Diseño de medición

- Tamaños: 1.000, 3.000, 6.000 y 12.000 elementos.
- Trabajo FIFO: encolar los enteros `0...n-1`, después desencolar todos y verificar el orden.
- Tiempos: una corrida de calentamiento, siete corridas independientes, mediana en milisegundos usando `perf_counter_ns`.
- Memoria: `tracemalloc` registra el **pico de asignaciones rastreadas en Python**; no representa la memoria física total ni el RSS.
- Búsqueda: 240 consultas deterministas, para claves existentes del último cuarto del rango. Mismo conjunto de claves para barrido lineal y AVL.
- Índice AVL: se construye insertando IDs crecientes para probar que mantiene el equilibrio incluso en una entrada desfavorable para un BST simple.

**Limitación:** cronómetro y `tracemalloc` se ejecutan por separado para evitar que la instrumentación de memoria distorsione las comparaciones temporales. Los microbenchmarks no representan un SOC productivo.

## Criterios de validación

- Orden FIFO idéntico en ambas estrategias.
- Duplicados de incidente rechazados, incluso después de su resolución.
- Rotaciones y borrados de AVL mantienen orden, altura, equilibrio y tamaño.
- Conteos `recibidos = pendientes + activos + resueltos` tras el flujo completo.
- Búsquedas con resultado correcto y tratamiento de elementos ausentes.

## Evidencias y límites

`resultados/benchmark.json` identifica el entorno histórico: Python 3.13.5 sobre Linux x86_64. Los CSV contienen las mismas observaciones; las gráficas de `documentacion/` y las evidencias de ejecución se conservan sin modificar. Estos tiempos no representan mediciones del equipo actual.

Para repetir el experimento sin sobrescribir el histórico, utilizar una carpeta distinta:

```bash
python main.py benchmark --out resultados_locales
```

El centro requiere una cola y un índice inicialmente vacíos y de uso exclusivo. Opera en memoria y sin concurrencia; conserva los identificadores recibidos para impedir su reutilización incluso después de resolverlos. Este registro crece con el total de incidentes recibidos. El índice requiere un comparador de orden total; `find` devuelve `None` para una clave ausente (un valor almacenado `None` resulta indistinguible mediante esa consulta).

GitHub Actions ejecuta las pruebas y ambas demos en Python 3.10, 3.11, 3.12 y 3.13. La ejecución local solo acredita la versión instalada; la matriz se verificará al ejecutarse en GitHub.

Los datos, escenarios y mediciones son didácticos y no comprometen infraestructuras ni credenciales reales.
