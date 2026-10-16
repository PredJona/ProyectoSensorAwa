"""Audita CSV ya adquiridos y exporta estadísticas y PNG sin tocar originales.

Ejemplo: python -m python.analisis_sesion --sesion datos/calibracion/.../sesion.json
         --salida datos/calibracion/.../analisis_01
"""
import argparse
import csv
import hashlib
import json
import statistics
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np

from .comunicacion import parsear_linea

RAIZ = Path(__file__).resolve().parents[1]
COLUMNAS = ['timestamp_utc', 't_ms', 'adc1', 'adc2', 'adc3', 'origen']
_RUTAS_RESUELTAS = {}


def _ruta(nombre, base=None):
    if str(nombre) in _RUTAS_RESUELTAS:
        return _RUTAS_RESUELTAS[str(nombre)]
    path = Path(nombre)
    if path.is_absolute():
        return path.resolve()
    candidatos = []
    if base is not None:

        candidatos.append(Path(base) / path)
    candidatos.extend([RAIZ / path, Path.cwd() / path])
    for cand in candidatos:
        if cand.exists():
            return cand.resolve()
    return (Path(base) / path if base is not None else RAIZ / path).resolve()


def _portable(path, base_sesion=None):
    resolved = Path(path).resolve()
    try:
        rel = resolved.relative_to(RAIZ.resolve()).as_posix()
    except ValueError:
        if base_sesion is not None:
            try:
                rel = resolved.relative_to(Path(base_sesion).resolve()).as_posix()
            except ValueError:
                rel = resolved.name
        else:
            rel = resolved.name
    _RUTAS_RESUELTAS[rel] = resolved
    return rel


def _leer(path):
    with path.open(encoding='utf-8', newline='') as source:
        reader = csv.DictReader(source)
        if reader.fieldnames != COLUMNAS:
            raise ValueError(f'Columnas inválidas: {path}')
        rows = list(reader)
    if not rows:
        raise ValueError(f'CSV sin muestras: {path}')
    for row in rows:
        if None in row or any(v is None for v in row.values()):
            raise ValueError(f'Fila incompleta o con columnas adicionales: {path}')
        parsear_linea(','.join(row[k] for k in COLUMNAS[1:5]))
        if row['origen'] not in ('experimental', 'prueba_controlada'):
            raise ValueError(f'Origen desconocido: {path}')
        date = datetime.fromisoformat(row['timestamp_utc'])
        if date.tzinfo is None or date.utcoffset() != timedelta(0):
            raise ValueError(f'Fecha sin UTC: {path}')
    dates = [datetime.fromisoformat(r['timestamp_utc']) for r in rows]
    if any(b < a for a, b in zip(dates, dates[1:])):
        raise ValueError(f'Fechas no ordenadas: {path}')
    return rows


def _estadisticas(values):
    if not values:
        return {k: None for k in ('media', 'minimo', 'maximo', 'desviacion_muestral',
                                  'varianza_muestral', 'rango', 'mediana', 'iqr',
                                  'cambio_media_mitad_final_inicial')}
    split = len(values) // 2
    return {
        'media': statistics.mean(values), 'minimo': min(values), 'maximo': max(values),
        'desviacion_muestral': statistics.stdev(values) if len(values) > 1 else None,
        'varianza_muestral': statistics.variance(values) if len(values) > 1 else None,
        'rango': max(values) - min(values), 'mediana': statistics.median(values),
        'iqr': float(np.percentile(values, 75) - np.percentile(values, 25)),
        'cambio_media_mitad_final_inicial':
            statistics.mean(values[split:]) - statistics.mean(values[:split]) if split else None,
    }


def auditar_sesion(ruta_sesion):
    """Cuenta filas y canales separados; respeta exclusiones del índice vigente."""
    ruta_sesion = _ruta(ruta_sesion)
    base_dir = ruta_sesion.parent
    session = json.loads(ruta_sesion.read_text(encoding='utf-8'))
    selected = None
    if session.get('resumen_preliminar'):
        with _ruta(session['resumen_preliminar'], base_dir).open(encoding='utf-8', newline='') as f:
            selected = {row['ensayo'] for row in csv.DictReader(f)}
    experiments, seen, ids, digests = [], set(), set(), set()
    for entry in session['ensayos']:
        path = _ruta(entry.get('csv') or entry['csv_origen'], base_dir)
        if path in seen or entry['id'] in ids:
            raise ValueError(f'Fuente o identificador duplicado: {path}')
        seen.add(path)
        ids.add(entry['id'])
        metadata = (json.loads(_ruta(entry['metadatos'], base_dir).read_text(encoding='utf-8'))
                    if entry.get('metadatos') else entry)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if metadata.get('sha256') and digest != metadata['sha256']:
            raise ValueError(f'No coincide la huella SHA-256: {path}')
        if digest in digests:
            raise ValueError(f'Contenido CSV duplicado: {path}')
        digests.add(digest)
        rows = _leer(path)
        esperadas = metadata.get('muestras_validas')
        if esperadas is not None and len(rows) != esperadas:
            raise ValueError(f'Recuento de muestras no coincide con metadatos: {path}')
        times = [int(r['t_ms']) for r in rows]
        periods = [(b - a) % 2**32 for a, b in zip(times, times[1:])]
        dates = [datetime.fromisoformat(r['timestamp_utc']) for r in rows]
        state = entry.get('estado', metadata.get('estado', 'sin_estado'))
        included = entry['id'] in selected if selected is not None else not state.startswith('excluido')
        experiments.append({
            'id': entry['id'], 'csv_origen': _portable(path, base_dir), 'sha256': digest,
            'estado': state, 'rol': entry.get('rol'), 'incluido_resumen_preliminar': included,
            'sensor_con_altura_comunicada': entry.get('sensor'),
            'altura_comunicada': entry.get('altura_inmersion'), 'unidad': entry.get('unidad'),
            'filas': len(rows), 'origenes': sorted({r['origen'] for r in rows}),
            'intervalos_arduino_ms': sorted(set(periods)),
            'span_recepcion_s': (dates[-1] - dates[0]).total_seconds() if dates else None,
            'lineas_invalidas_reportadas': metadata.get('lineas_invalidas'),
            'canales': {k: _estadisticas([int(r[k]) for r in rows]) for k in COLUMNAS[2:5]},
        })
    if selected is not None and not selected.issubset(ids):
        raise ValueError('El resumen referencia ensayos ausentes del índice.')
    preparations = []
    for path in sorted(base_dir.glob('*_preparacion.csv')):
        preparations.append({'csv_origen': _portable(path, base_dir), 'filas': len(_leer(path)),
                             'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    total = sum(e['filas'] for e in experiments)
    reported = sum(e['filas'] for e in experiments if e['incluido_resumen_preliminar'])
    return {
        'sesion': _portable(ruta_sesion, base_dir),
        'sha256_indice': hashlib.sha256(ruta_sesion.read_bytes()).hexdigest(),
        'filas_csv_principales': total, 'lecturas_adc_principales': total * 3,
        'filas_resumen_preliminar': reported, 'lecturas_adc_resumen_preliminar': reported * 3,
        'filas_fuera_resumen': total - reported,
        'filas_preparacion_separadas': sum(p['filas'] for p in preparations),
        'ensayos': experiments, 'preparacion': preparations,
        'notas': ['Una fila contiene tres lecturas consecutivas, no simultáneas.',
                  'Solo el sensor indicado tiene altura comunicada; no equivale a calibración válida.',
                  'Desviación muestral n-1; IQR percentiles 75-25, sin eliminar valores.',
                  'Bytes de arranque no se cuentan como filas experimentales completas.'],
    }


def _graficar_curva_exploratoria(usable, output):
    from .calibracion import convertir
    from .graficas import _guardar, plt
    con_altura = [e for e in usable if e.get('altura_comunicada') is not None
                  and e.get('sensor_con_altura_comunicada') in COLUMNAS[2:5]]
    nodos = [e for e in con_altura if not str(e.get('rol') or '').startswith('validacion')]
    validaciones = [e for e in con_altura if str(e.get('rol') or '').startswith('validacion')]
    if len(nodos) < 2:
        return None
    sensor = nodos[0]['sensor_con_altura_comunicada']
    unidad = nodos[0].get('unidad') or 'mm'
    nodos_ord = sorted(nodos, key=lambda e: e['altura_comunicada'])
    pares = [[e['canales'][sensor]['media'], e['altura_comunicada']] for e in nodos_ord]
    try:
        malla_adc = np.linspace(pares[0][0], pares[-1][0], 200)
        malla_h = convertir(malla_adc, pares)
    except ValueError:
        return None
    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    ax.plot(malla_adc, malla_h, '--', color='#1d4ed8', alpha=0.8,
            label='Interpolación lineal exploratoria (nodos S1)')
    for i, e in enumerate(nodos_ord):
        st = e['canales'][sensor]
        ax.errorbar(st['media'], e['altura_comunicada'],
                    xerr=[[st['media'] - st['minimo']], [st['maximo'] - st['media']]],
                    fmt='o', color='#1d4ed8', capsize=4,
                    label='Nodos exploratorios (media y mín.–máx.)' if i == 0 else None)
    colores_val = ('#dc2626', '#d97706')
    for idx, e in enumerate(validaciones):
        st = e['canales'][sensor]
        h_real = e['altura_comunicada']
        color = colores_val[idx % len(colores_val)]
        h_est = float(convertir([st['media']], pares)[0])
        err = h_est - h_real
        ax.errorbar(st['media'], h_real,
                    xerr=[[st['media'] - st['minimo']], [st['maximo'] - st['media']]],
                    fmt='s', color=color, capsize=4,
                    label=f"{e['id']} (25 {unidad} real → {h_est:.2f} {unidad}, error {err:+.2f} {unidad})")
        ax.plot([st['media'], st['media']], [h_real, h_est], ':', color=color, linewidth=1.3)
        ax.plot(st['media'], h_est, 'x', color=color, markersize=7)
    ax.set(title='Sensor 1 (A0) · Curva exploratoria y discrepancia en 25 mm (NO validada)',
           xlabel=f'Lectura {sensor.upper()} [cuentas ADC 0..1023]',
           ylabel=f'Profundidad comunicada [{unidad}]')
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8.5, loc='lower right')
    return _guardar(fig, output / 'curva_exploratoria_sensor1.png')


def exportar(audit, salida):
    """Crea un destino nuevo y reutiliza las gráficas ADC de los tres canales."""
    from .graficas import mediciones, _guardar, plt
    output = Path(salida)
    output.mkdir(parents=True, exist_ok=False)
    with (output / 'auditoria.json').open('x', encoding='utf-8') as f:
        json.dump(audit, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write('\n')
    with (output / 'estadisticas.csv').open('x', encoding='utf-8', newline='') as f:
        w = None
        for entry in audit['ensayos']:
            for channel, stats in entry['canales'].items():
                row = {'ensayo': entry['id'], 'sensor': channel, 'n': entry['filas'],
                       'incluido_resumen': entry['incluido_resumen_preliminar'],
                       'altura_asociada': entry['altura_comunicada'] if channel == entry['sensor_con_altura_comunicada'] else None,
                       'unidad_altura': entry['unidad'] if channel == entry['sensor_con_altura_comunicada'] else None,
                       **stats, 'csv_origen': entry['csv_origen'], 'sha256': entry['sha256']}
                if w is None:
                    w = csv.DictWriter(f, fieldnames=list(row))
                    w.writeheader()
                w.writerow(row)
    usable = [e for e in audit['ensayos'] if e['incluido_resumen_preliminar'] and e['filas']]
    for entry in usable:
        mediciones(_ruta(entry['csv_origen'], output.parent), output / f"adc_{entry['id']}.png")
    if not usable:
        return output
    # Cada fila es un ensayo, cada columna un canal; escalas iguales por columna.
    fig, axes = plt.subplots(len(usable), 3, figsize=(13, 2.2 * len(usable)),
                             sharex=True, sharey='col', squeeze=False)
    for row_axes, entry in zip(axes, usable):
        rows = _leer(_ruta(entry['csv_origen'], output.parent))
        t0 = datetime.fromisoformat(rows[0]['timestamp_utc'])
        times = [(datetime.fromisoformat(r['timestamp_utc']) - t0).total_seconds() for r in rows]
        for ax, channel in zip(row_axes, COLUMNAS[2:5]):
            ax.plot(times, [int(r[channel]) for r in rows], 'o-', color='#2563a6', markersize=3)
            ax.set_title(f"{entry['id']} · {channel}", fontsize=10)
            ax.grid(alpha=.25)
        row_axes[0].set_ylabel('Cuentas ADC')
    for ax in axes[-1]:
        ax.set_xlabel('Desde primera recepción UTC [s]')
    fig.suptitle('Ensayos exploratorios · profundidad variable · sin calibración validada', fontsize=13)
    _guardar(fig, output / 'comparacion_tres_canales.png')
    _graficar_curva_exploratoria(usable, output)
    return output




def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sesion', type=Path, required=True)
    parser.add_argument('--salida', type=Path, required=True, help='Directorio nuevo')
    args = parser.parse_args(argv)
    audit = auditar_sesion(args.sesion)
    exportar(audit, args.salida)
    print(f"CSV principales: {audit['filas_csv_principales']} filas; "
          f"resumen: {audit['filas_resumen_preliminar']} filas, "
          f"{audit['lecturas_adc_resumen_preliminar']} lecturas ADC. Salida: {args.salida}")


if __name__ == '__main__':
    main()
