# Instrucciones para Codex — SENTINEL-SOC

- Mantener el alcance académico (datos simulados; no un SOC productivo).
- Compatibilidad con Python >= 3.10, solo biblioteca estándar salvo autorización expresa.
- Antes de proponer un commit, ejecutar `python -m unittest discover -s tests -v` y ambos tipos de demo.
- Preservar las invariantes de FIFO, unicidad de incidentes y balance AVL.
- No inventar benchmarks ni ajustar resultados sin ejecutar una medición nueva y actualizar documentación de forma coherente.
- Solicitar confirmación antes de crear un repositorio remoto, publicar, subir cambios o eliminar material.
- Documentar claramente decisiones, complejidades y límites del sistema.
