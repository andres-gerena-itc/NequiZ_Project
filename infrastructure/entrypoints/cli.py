# infrastructure/entrypoints/cli.py
# Adaptador de entrada CLI para NequiZ - Fase 4 (Puertos y Adaptadores)
# Demuestra cómo otro canal distinto a HTTP puede reusar la misma lógica de negocio.

import click
import sys
import os
import logging

# Resolver problema de imports cuando se ejecuta standalone:
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Deshabilitar logs molestos de terceros si los hay
logging.getLogger("pymongo").setLevel(logging.WARNING)

@click.group()
def nequiz():
    """
    📱 NequiZ CLI
    Prueba de Evolución Hexagonal: Mismos Casos de Uso, diferente Entrypoint.
    """
    pass

@nequiz.command()
@click.option('--origen', prompt='Tu número (origen)', help='Tu número de teléfono.')
@click.option('--destino', prompt='Número a transferir (destino)', help='Número de teléfono a quien le envías dinero.')
@click.option('--monto', prompt='Monto a transferir', type=float, help='Dinero a enviar.')
@click.option('--mensaje', default='', help='Mensaje de la transferencia.')
def transferir(origen, destino, monto, mensaje):
    """Realiza una transferencia de dinero P2P."""
    click.echo(f"Iniciando transferencia de {origen} a {destino} por ${monto}...")
    
    # ── Fase 4: Instanciamos implementaciones de Infraestructura ─────────
    try:
        from infrastructure.adapters.mongodb_repository import MongoUsuarioRepository, MongoTransaccionRepository
        from application.use_cases.transferencias.enviar_dinero import EnviarDineroUseCase, EnviarDineroInput
    except ImportError as e:
        click.secho(f"Error de importación estructural: {e}", fg="red")
        sys.exit(1)

    usuario_repo = MongoUsuarioRepository()
    transaccion_repo = MongoTransaccionRepository()
    
    # Inyectamos dependencias al Caso de Uso (Inversión de Dependencias)
    use_case = EnviarDineroUseCase(usuario_repo, transaccion_repo)
    
    # ── Ejecutamos el Caso de Uso puro de Dominio ──────────────────────────
    try:
        resultado = use_case.ejecutar(EnviarDineroInput(
            numero_origen=origen,
            numero_destino=destino,
            monto=monto,
            mensaje=mensaje
        ))
        
        click.secho("\n✅ ¡Transferencia Exitosa!", fg="green", bold=True)
        click.echo(f"ID Transacción:  {resultado.id_transaccion}")
        click.echo(f"Fecha:           {resultado.fecha}")
        click.echo(f"Tu Nuevo Saldo:  ${resultado.nuevo_saldo_origen}")
        click.echo(f"Destinatario:    {resultado.nombre_destino}")
        click.echo(f"Estado:          {resultado.estado}")
        
    except Exception as e:
        click.secho(f"\n❌ Error al transferir: {str(e)}", fg="red")
        sys.exit(1)


@nequiz.command()
@click.option('--numero', prompt='Tu número de teléfono', help='Tu número de celular NequiZ.')
@click.option('--limite', default=5, type=int, help='Últimos movimientos a consultar.')
def historial(numero, limite):
    """Consulta el historial de las últimas transferencias."""
    click.echo(f"Consultando movimientos para {numero}...\n")
    
    # ── Fase 4: Reusamos el adaptador y validamos desacoplamiento ─────────
    try:
        from infrastructure.adapters.mongodb_repository import MongoTransaccionRepository
        from application.use_cases.movimientos.obtener_movimientos import ObtenerMovimientosUseCase, ObtenerMovimientosInput
        from domain.entities.transaccion import TipoMovimiento
    except ImportError as e:
        click.secho(f"Error de importación estructural: {e}", fg="red")
        sys.exit(1)
        
    transaccion_repo = MongoTransaccionRepository()
    use_case = ObtenerMovimientosUseCase(transaccion_repo)
    
    try:
        movimientos = use_case.ejecutar(ObtenerMovimientosInput(
            numero_telefono=numero,
            limite=limite,
            tipo=TipoMovimiento.TODOS
        ))
        
        if not movimientos:
            click.secho("No tienes movimientos aún.", fg="yellow")
            return
            
        click.secho(f"📊 Últimos {len(movimientos)} movimientos:\n", fg="blue", bold=True)
        
        for i, m in enumerate(movimientos, 1):
            es_ingreso = (m['numero_destino'] == numero)
            signo = "+" if es_ingreso else "-"
            color = "green" if es_ingreso else "red"
            
            tercero = m['nombre_origen'] if es_ingreso else m['nombre_destino']
            accion = "De" if es_ingreso else "Para"
            
            click.secho(
                f"{i}. [{m['fecha'][:10]}] {signo}${m['monto']} "
                f"| {accion}: {tercero} | Msg: {m['mensaje']} "
                f"| Estado: {m['estado']}",
                fg=color
            )
            
    except Exception as e:
        click.secho(f"\n❌ Error al consultar el historial: {str(e)}", fg="red")
        sys.exit(1)


if __name__ == '__main__':
    nequiz()
