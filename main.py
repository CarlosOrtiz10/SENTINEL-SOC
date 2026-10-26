"""Ejecutar: python main.py demo --queue deque | python main.py benchmark"""
from __future__ import annotations
import argparse
from pathlib import Path
from sentinel_soc import DequeQueue, Incident, IncidentCenter, ListQueue, Severity
from sentinel_soc.benchmark import run_benchmarks

EXAMPLES = (
    Incident(420, "SRV-IDENTIDAD", "Autenticaciones fallidas", Severity.HIGH),
    Incident(210, "API-PAGOS", "Tráfico anómalo", Severity.CRITICAL),
    Incident(640, "SRV-ARCHIVOS", "Acceso irregular", Severity.MEDIUM),
    Incident(105, "VPN-CORP", "Intentos de fuerza bruta", Severity.HIGH),
    Incident(310, "ENDPOINT-07", "Ejecutable sospechoso", Severity.MEDIUM),
    Incident(550, "BD-OPERACIONES", "Conexión no autorizada", Severity.CRITICAL),
    Incident(730, "CORREO", "Suplantación de identidad", Severity.LOW),
)


def demo(queue_kind: str) -> None:
    center = IncidentCenter(DequeQueue() if queue_kind == "deque" else ListQueue())
    print("\nSENTINEL-SOC | SIMULACIÓN DIDÁCTICA SIN INCIDENTES REALES")
    print(f"Implementación de cola: {queue_kind}\n")
    for event in EXAMPLES:
        center.submit(event)
        print(f"[RECIBIDO] #{event.id:<3} {event.asset:<17} prioridad={event.severity.value}")
    print(f"\nEn espera: {center.pending_count}. Inicia el triaje FIFO:")
    for _ in range(7):
        event = center.process_next()
        print(f"[EN ATENCIÓN] #{event.id} {event.category}")
    print("\nÍNDICE AVL DE INCIDENTES ACTIVOS (ordenado por ID)")
    print(" -> ".join(str(event.id) for event in center.active_ordered()))
    print(f"Altura del AVL: {center.index_height} | Nodos: {center.active_count}")
    match = center.find_active(550)
    print(f"Consulta por ID 550: {match.asset if match else 'No encontrado'}")
    center.resolve(550)
    print(f"Incidente 550 resuelto. Consulta posterior: {center.find_active(550)}")
    print(f"Estado final: pendiente={center.pending_count}, activo={center.active_count}, "
          f"resuelto={center.resolved_count}, integridad={center.check_integrity()}")


def main() -> None:
    parser = argparse.ArgumentParser(description="SENTINEL-SOC: laboratorio individual de ADT")
    commands = parser.add_subparsers(dest="command", required=True)
    demo_command = commands.add_parser("demo", help="Muestra el flujo operativo con datos sintéticos")
    demo_command.add_argument("--queue", choices=["deque", "list"], default="deque")
    benchmark_command = commands.add_parser("benchmark", help="Mide cola, memoria y búsquedas")
    benchmark_command.add_argument("--out", type=Path, default=Path("resultados"))
    args = parser.parse_args()
    if args.command == "demo":
        demo(args.queue)
    elif args.command == "benchmark":
        results = run_benchmarks(args.out)
        print("\nComparación FIFO (mediana en ms | memoria pico en KiB):")
        for record in results["queues"]:
            print(f"{record['n']:>6} | {record['queue']:<5} | {record['median_ms']:>10.4f} ms | {record['peak_kib']:>10.1f} KiB")
        print("\nBúsquedas por ID: barrido lineal vs AVL (240 consultas)")
        for record in results["searches"]:
            print(f"{record['n']:>6} | lineal {record['linear_ms']:>9.4f} ms | "
                  f"AVL {record['avl_ms']:>9.4f} ms | altura {record['avl_height']}")
        print(f"\nDatos reproducibles guardados en: {args.out.resolve()}")


if __name__ == "__main__":
    main()
