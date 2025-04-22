from flask import Flask, request, jsonify, send_from_directory, make_response
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, get_jwt
from database import db
#from flask_sqlalchemy import SQLAlchemy
from flask import Blueprint
from config import Config
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
import bcrypt
from datetime import datetime, date, timedelta
import calendar
import logging
from io import TextIOWrapper
import csv
from decimal import Decimal
from io import TextIOWrapper, BytesIO
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from sqlalchemy import func, and_
from flask import jsonify, request, send_file
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from datetime import datetime
from pytz import timezone
from contextlib import contextmanager

from datetime import datetime, timezone
from io import BytesIO
from reportlab.lib.pagesizes import letter, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.utils import simpleSplit
from reportlab.lib.styles import getSampleStyleSheet
from decimal import Decimal


# Crear la aplicación Flask
app = Flask(__name__, static_folder='static', static_url_path='')
app.config.from_object(Config)

# Configurar logging para ver errores detallados
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Configurar una clave secreta para la sesión (necesaria para que funcione)
app.secret_key = app.config['SECRET_KEY']  # Usamos la clave del .env se usa para las sesiones
app.config['JWT_SECRET_KEY'] = app.config['SECRET_KEY']  # Para JWT
# Al inicio de app.py, después de app.config.from_object(Config)
#logger.info(f"SECRET_KEY: {app.config['SECRET_KEY']}")
#logger.info(f"JWT_SECRET_KEY: {app.config['JWT_SECRET_KEY']}")

# Inicializar SQLAlchemy con la app
db.init_app(app)

from models import (
    db, Usuarios, Clientes, Perfiles, Permisos, Producto, MaterialProducto, 
    Bodega, InventarioBodega, RegistroMovimientos, Kardex, Venta, EstadoInventario, 
    AjusteInventarioDetalle, OrdenProduccion, DetalleProduccion, EntregaParcial
)

jwt = JWTManager(app)

# Manejador de errores para tokens inválidos
@jwt.invalid_token_loader
def invalid_token_callback(error):
    logger.error(f"Error de token inválido: {str(error)}")
    return jsonify({"msg": str(error)}), 422

# Manejador de errores para token expirado
@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    logger.error("Token expirado")
    return jsonify({"msg": "Token has expired"}), 401

# Manejador de errores para token faltante
@jwt.unauthorized_loader
def unauthorized_callback(error):
    logger.error(f"Error de autorización: {str(error)}")
    return jsonify({"msg": str(error)}), 401

# Configurar CORS para permitir solicitudes desde el frontend
# En desarrollo: localhost:8080 y 192.168.0.47:8080
# En producción: el dominio del frontend en Railway
#allowed_origins = [
#    "http://localhost:8080",
#    "http://192.168.0.47:8080",
#    # Agrega el dominio del frontend en Railway cuando lo tengas
#    "https://frontend.railway.app"  # Placeholder, cámbialo por el dominio real
#]
#CORS(app, resources={r"/*": {"origins": allowed_origins}})


def get_db_connection():
    conn = psycopg2.connect(
        dbname=app.config['DB_NAME'],
        user=app.config['DB_USER'],
        password=app.config['DB_PASSWORD'],
        host=app.config['DB_HOST'],
        port=app.config['DB_PORT']
    )
    return conn



def obtener_hora_utc():
    """Obtiene la hora actual en UTC."""
    return datetime.now(timezone.utc)

def obtener_hora_colombia():
    """Obtiene la hora actual en la zona horaria de Colombia sin zona horaria."""
    return datetime.now(ZoneInfo("America/Bogota")).replace(tzinfo=None)

def convertir_a_hora_colombia(fecha):
    """Convierte una fecha UTC a la hora local de Colombia."""
    if fecha and fecha.tzinfo:
        return fecha.astimezone(ZoneInfo('America/Bogota')).replace(tzinfo=None)
    return None

@contextmanager
def no_autoflush(session):
    session.autoflush = False
    try:
        yield
    finally:
        session.autoflush = True

def recalcular_peso_producto_compuesto(producto_id):
    producto = Producto.query.get(producto_id)

    if not producto or not producto.es_producto_compuesto:
        return

    # Sumar el peso de los materiales que lo componen
    materiales = MaterialProducto.query.filter_by(producto_compuesto_id=producto_id).all()
    peso_total = sum(m.cantidad * m.peso_unitario for m in materiales)

    # ✔ Corregimos: el peso total y el peso por unidad deben ser iguales
    producto.peso_total_gr = peso_total
    producto.peso_unidad_gr = peso_total  # 🟢 Aseguramos que sea igual al total

    db.session.commit()


# Función para convertir mes en español a número
def mes_a_numero(mes):
    meses = {
        'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4, 'mayo': 5, 'junio': 6,
        'julio': 7, 'agosto': 8, 'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
    }
    # return meses[mes.lower()]
    return meses.get(mes.lower(), mes)  # Si ya es número, mantenerlo


def calcular_inventario_producto(producto_id, idcliente):
    try:
        print(f"[DEBUG] Calculando inventario para producto_id={producto_id}, idcliente={idcliente}")
        ultimo_movimiento_por_bodega = db.session.query(
            Kardex.bodega_destino_id,
            func.max(Kardex.fecha).label('ultima_fecha')
        ).filter(
            Kardex.producto_id == producto_id,
            Kardex.idcliente == idcliente,
            Kardex.bodega_destino_id != None
        ).group_by(Kardex.bodega_destino_id).subquery()

        # Log para ver la subconsulta
        subquery_result = db.session.query(ultimo_movimiento_por_bodega).all()
        print(f"[DEBUG] Subconsulta ultimo_movimiento: {subquery_result}")

        inventario = db.session.query(
            Kardex.bodega_destino_id,
            Kardex.saldo_cantidad.label('cantidad')
        ).join(
            ultimo_movimiento_por_bodega,
            and_(
                Kardex.fecha == ultimo_movimiento_por_bodega.c.ultima_fecha,
                Kardex.bodega_destino_id == ultimo_movimiento_por_bodega.c.bodega_destino_id,
                Kardex.producto_id == producto_id,
                Kardex.idcliente == idcliente
            )
        ).all()
        print(f"[DEBUG] Inventario encontrado: {[(i.bodega_destino_id, i.cantidad) for i in inventario]}")

        resultado = []
        for item in inventario:
            bodega = db.session.get(Bodega, item.bodega_destino_id)
            print(f"[DEBUG] Bodega para id={item.bodega_destino_id}: {bodega.nombre if bodega else None}")
            if bodega:
                resultado.append({
                    'bodega': bodega.nombre,
                    'cantidad': float(item.cantidad) if item.cantidad is not None else 0.0
                })
        print(f"[DEBUG] Resultado final: {resultado}")
        return resultado
    except Exception as e:
        print(f"Error en calcular_inventario_producto: {str(e)}")
        return []

#Funcion para actualizar estado inventario cuando se hacentregas parciales o Totales de una orden de produccion
def actualizar_estado_inventario(producto_id, bodega_id, cantidad, es_entrada=True, orden_id=None):
    try:
        inventario = EstadoInventario.query.filter_by(
            producto_id=producto_id,
            bodega_id=bodega_id
        ).first()
        cantidad = float(cantidad)

        if inventario:
            if es_entrada:
                inventario.cantidad += cantidad
            else:
                inventario.cantidad -= cantidad
            inventario.ultima_actualizacion = obtener_hora_colombia()
        else:
            # Obtener idcliente desde la orden
            if not orden_id:
                raise ValueError("Se requiere orden_id para crear un nuevo registro en EstadoInventario")
            orden = db.session.get(OrdenProduccion, orden_id)
            if not orden:
                raise ValueError("Orden no encontrada")
            inventario = EstadoInventario(
                idcliente=orden.idcliente,
                producto_id=producto_id,
                bodega_id=bodega_id,
                cantidad=cantidad if es_entrada else -cantidad,
                ultima_actualizacion=obtener_hora_colombia(),
                costo_unitario=0.0,
                costo_total=0.0
            )
            db.session.add(inventario)

        # Consultar el último Kardex, considerando bodega_origen o bodega_destino
        ultimo_kardex = Kardex.query.filter(
            Kardex.producto_id == producto_id,
            (Kardex.bodega_origen_id == bodega_id) | (Kardex.bodega_destino_id == bodega_id)
        ).order_by(Kardex.fecha.desc()).first()

        if ultimo_kardex:
            inventario.costo_unitario = float(ultimo_kardex.saldo_costo_unitario)
            inventario.costo_total = inventario.cantidad * inventario.costo_unitario

        # No commit aquí, se hace en el endpoint
    except Exception as e:
        print(f"Error al actualizar estado_inventario: {str(e)}")
        raise  # Propagar error al endpoint


# Función auxiliar para verificar permisos
def has_permission(claims, seccion, subseccion, permiso):
    perfilid = claims.get('perfilid')
    logger.info(f"Verificando permiso: seccion={seccion}, subseccion={subseccion}, permiso={permiso}")
    logger.info(f"Claims recibidos: {claims}")
    if perfilid == 1:  # Superadmin tiene acceso total
        logger.info("Usuario es superadmin, permiso concedido")
        return True
    permisos = claims.get('permisos', [])
    logger.info(f"Permisos en claims: {permisos}")
    has_perm = any(
        p['seccion'] == seccion and 
        (p['subseccion'] == subseccion or (not subseccion and not p['subseccion'])) and 
        p['permiso'] == permiso 
        for p in permisos
    )
    logger.info(f"Resultado de verificación: {has_perm}")
    return has_perm

# Función para generar consecutivo que escribe en tabla registro_movimientos
def generar_consecutivo():
    ultimo_consecutivo = db.session.query(
        db.func.max(db.cast(RegistroMovimientos.consecutivo, db.String))
    ).scalar() or "T00000"
    try:
        return f"T{int(ultimo_consecutivo[1:]) + 1:05d}"
    except ValueError:
        return "T00001"

# Función auxiliar para texto envuelto (sin cambios)
def draw_wrapped_text_ajuste(pdf, x, y, text, max_width):
    lines = []
    current_line = ""
    words = text.split()
    font_size = 8  # Coincide con el tamaño ajustado
    pdf.setFont("Helvetica", font_size)

    for word in words:
        test_line = f"{current_line} {word}".strip()
        if pdf.stringWidth(test_line, "Helvetica", font_size) <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)

    for i, line in enumerate(lines):
        pdf.drawString(x, y - i * (font_size + 2), line)
    return y - (len(lines) - 1) * (font_size + 2)


def draw_wrapped_text_traslado(pdf, x, y, text, max_width):
    """Dibuja texto que salta de línea si excede el ancho máximo y devuelve la altura total usada."""
    words = text.split(" ")
    line = ""
    lines = []
    for word in words:
        test_line = f"{line} {word}".strip()
        if pdf.stringWidth(test_line, "Helvetica", 10) <= max_width:
            line = test_line
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    
    y_inicial = y
    for i, line in enumerate(lines):
        pdf.drawString(x, y - (i * 15), line)
    return y - (len(lines) * 15)


# Enpooints para listar las clases de modelos registrados
# Ruta para servir el frontend (index.html)
@app.route('/')
def serve_frontend():
    return send_from_directory(app.static_folder, 'index.html')

# Ruta para servir otros archivos estáticos (css, js, etc.)
@app.route('/<path:path>')
def serve_static(path):
    try:
        return send_from_directory(app.static_folder, path)
    except Exception as e:
        # Si el archivo no existe, devolver index.html para manejar rutas de Vue Router
        return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/debug-models')
def debug_models():
    return jsonify({"models": list(db.Model.registry._class_registry.keys())})
# Endpoint para login
# app.py (endpoint /login)
@app.route('/login', methods=['POST'])
def login():
    try:
        # Obtener el cuerpo de la solicitud
        data = request.get_json()
        logger.info(f"Datos recibidos en /login: {data}")

        # Intentar obtener los campos con diferentes nombres
        username = data.get('username') or data.get('user') or data.get('usuario')
        password = data.get('password') or data.get('pass')

        if not username or not password:
            logger.error("Faltan credenciales en la solicitud")
            return jsonify({"error": "Faltan credenciales"}), 400

        # Conexión a la base de datos con psycopg2
        conn = get_db_connection()
        cursor = conn.cursor()

        # Buscar el usuario
        cursor.execute("SELECT id, idcliente, perfilid, usuario, password FROM usuarios WHERE usuario = %s AND estado = true", (username,))
        usuario = cursor.fetchone()

        if not usuario:
            cursor.close()
            conn.close()
            logger.error(f"Usuario no encontrado: {username}")
            return jsonify({"error": "Usuario no encontrado"}), 401

        # Verificar la contraseña
        stored_password = usuario[4]  # La contraseña hasheada
        if not bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8')):
            cursor.close()
            conn.close()
            logger.error(f"Contraseña incorrecta para el usuario: {username}")
            return jsonify({"error": "Contraseña incorrecta"}), 401

        # Extraer datos del usuario
        user_id, idcliente, perfilid, _, _ = usuario

        # Obtener el estado del cliente si existe idcliente
        cliente_estado = None
        if idcliente:
            cursor.execute("SELECT estado FROM clientes WHERE idcliente = %s", (idcliente,))
            cliente = cursor.fetchone()
            if cliente:
                cliente_estado = cliente[0]  # True o False
            else:
                cursor.close()
                conn.close()
                logger.error(f"Cliente no encontrado para idcliente: {idcliente}")
                return jsonify({"error": "Cliente asociado no encontrado"}), 404

        # Obtener permisos del perfil
        cursor.execute("SELECT seccion, subseccion, permiso FROM permisos WHERE idPerfil = %s", (perfilid,))
        permisos = [{"seccion": p[0], "subseccion": p[1], "permiso": p[2]} for p in cursor.fetchall()]

        # Crear el token con el ID del usuario como identity (como string)
        user_identity = str(user_id)
        additional_claims = {
            'idcliente': idcliente,
            'perfilid': perfilid,
            'permisos': permisos  # Añadir permisos a los claims del token
        }
        access_token = create_access_token(identity=user_identity, additional_claims=additional_claims)

        # Log del token generado para depuración
        logger.info(f"Token generado: {access_token}")

        cursor.close()
        conn.close()

        logger.info(f"Usuario {username} ha iniciado sesión")
        return jsonify({
            'token': access_token,
            'id': user_id,  # Agregar el ID del usuario
            'idcliente': idcliente,
            'perfilid': perfilid,
            'permisos': permisos,
            'clienteEstado': cliente_estado
        }), 200

    except Exception as e:
        logger.error(f"Error en login: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500


@app.route('/clientes/<int:id>', methods=['GET'])
@jwt_required()
def get_cliente_by_id(id):
    user_id = get_jwt_identity()
    claims = get_jwt()
    perfilid = claims.get('perfilid')
    idcliente = claims.get('idcliente')

    if perfilid != 1 and idcliente != id:
        return jsonify({"error": "No autorizado"}), 403

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT nombre, logo, estado FROM clientes WHERE idcliente = %s", (id,))
        cliente = cur.fetchone()
        cur.close()
        conn.close()
        if not cliente:
            return jsonify({"error": "Cliente no encontrado"}), 404
        return jsonify({
            "nombre": cliente[0],
            "logo": cliente[1],
            "estado": cliente[2]  # Añadimos estado
        }), 200
    except Exception as e:
        logger.error(f"Error al obtener cliente: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500

# Endpoint para obtener información del cliente (como el logo)
@app.route('/cliente/<int:idcliente>', methods=['GET'])
@jwt_required()
def get_cliente(idcliente):
    user_id = get_jwt_identity()
    claims = get_jwt()
    if claims['idcliente'] != idcliente and claims['perfilid'] != 1:
        return jsonify({"error": "No autorizado"}), 403

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT nombre, logo, estado FROM clientes WHERE idcliente = %s",
            (idcliente,)
        )
        cliente = cur.fetchone()
        cur.close()
        conn.close()

        if not cliente:
            return jsonify({"error": "Cliente no encontrado"}), 404

        return jsonify({
            "nombre": cliente[0],
            "logo": cliente[1],
            "estado": cliente[2]  # Añadimos estado
        }), 200

    except Exception as e:
        logger.error(f"Error al obtener cliente: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500
    

# Endpoint para obtener todos los clientes
# Endpoint /clientes
@app.route('/clientes', methods=['GET'])
@jwt_required()
def get_clientes():
    try:
        auth_header = request.headers.get('Authorization')
        logger.info(f"Header Authorization recibido: {auth_header}")
        user_id = get_jwt_identity()
        claims = get_jwt()
        perfilid = claims.get('perfilid')
        logger.info(f"Usuario actual: ID={user_id}, PerfilID={perfilid}")
        if perfilid != 1:
            logger.info("Acceso denegado: no es superadmin")
            return jsonify({"error": "No autorizado"}), 403
        logger.info("Consultando clientes en la base de datos...")
        clientes = Clientes.query.all()  # Eliminamos el filtro estado=True
        logger.info(f"Clientes obtenidos: {len(clientes)}")
        response = [{
            "idcliente": c.idcliente,
            "nombre": c.nombre,
            "nit_cc": c.nit_cc,
            "pais": c.pais,
            "ciudad": c.ciudad,
            "direccion_ppal": c.direccion_ppal,
            "tel1": c.tel1,
            "correo": c.correo,
            "logo": c.logo,
            "estado": c.estado  # Añadimos el campo estado
        } for c in clientes]
        logger.info(f"Enviando respuesta al cliente: {response}")
        return jsonify(response), 200
    except Exception as e:
        logger.error(f"Error al obtener clientes: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500

# Endpoint para crear un cliente
@app.route('/clientes', methods=['POST'])
@jwt_required()
def create_cliente():
    claims = get_jwt()  # Cambia current_user por claims
    perfilid = claims.get('perfilid')  # Extrae perfilid de las claims
    if perfilid != 1:  # Solo superadmin
        return jsonify({"error": "No autorizado"}), 403

    data = request.get_json()
    nombre = data.get('nombre')
    nit_cc = data.get('nit_cc')
    pais = data.get('pais')
    ciudad = data.get('ciudad')
    direccion_ppal = data.get('direccion_ppal')
    tel1 = data.get('tel1')
    correo = data.get('correo')
    logo = data.get('logo')
    estado = data.get('estado', True)  # Por defecto True si no se envía

    if not all([nombre, nit_cc, pais, ciudad, direccion_ppal, tel1, correo]):
        return jsonify({"error": "Faltan datos requeridos"}), 400

    try:
        cliente = Clientes(
            nombre=nombre,
            nit_cc=nit_cc,
            pais=pais,
            ciudad=ciudad,
            direccion_ppal=direccion_ppal,
            tel1=tel1,
            correo=correo,
            logo=logo,
            estado=estado
        )
        db.session.add(cliente)
        db.session.commit()
        return jsonify({"idcliente": cliente.idcliente}), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error al crear cliente: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500


# Endpoint para eliminar un cliente
@app.route('/clientes/<int:idcliente>', methods=['DELETE'])
@jwt_required()
def delete_cliente(idcliente):
    claims = get_jwt()  # Cambia current_user por claims
    perfilid = claims.get('perfilid')  # Extrae perfilid de las claims
    if perfilid != 1:  # Solo superadmin
        return jsonify({"error": "No autorizado"}), 403

    try:
        cliente = Clientes.query.get(idcliente)
        if cliente:
            db.session.delete(cliente)
            db.session.commit()
            return jsonify({"message": "Cliente eliminado exitosamente"}), 200
        return jsonify({"error": "Cliente no encontrado"}), 404
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error al eliminar cliente: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500


# Endpoint para actualizar un cliente
@app.route('/clientes/<int:idcliente>', methods=['PUT'])
@jwt_required()
def update_cliente(idcliente):
    try:
        user_id = get_jwt_identity()
        claims = get_jwt()
        perfilid = claims.get('perfilid')

        if perfilid != 1:
            logger.info("Acceso denegado: no es superadmin")
            return jsonify({"error": "No autorizado"}), 403

        data = request.get_json()
        nombre = data.get('nombre')
        nit_cc = data.get('nit_cc')
        pais = data.get('pais')
        ciudad = data.get('ciudad')
        direccion_ppal = data.get('direccion_ppal')
        tel1 = data.get('tel1')
        correo = data.get('correo')
        logo = data.get('logo')
        estado = data.get('estado')  # Añadimos el campo estado

        if not all([nombre, nit_cc, pais, ciudad, direccion_ppal, tel1, correo]):
            return jsonify({"error": "Faltan datos requeridos"}), 400

        cliente = Clientes.query.get(idcliente)
        if not cliente:
            return jsonify({"error": "Cliente no encontrado"}), 404

        cliente.nombre = nombre
        cliente.nit_cc = nit_cc
        cliente.pais = pais
        cliente.ciudad = ciudad
        cliente.direccion_ppal = direccion_ppal
        cliente.tel1 = tel1
        cliente.correo = correo
        cliente.logo = logo
        if estado is not None:  # Solo actualizar estado si se proporciona
            cliente.estado = estado

        db.session.commit()
        logger.info(f"Cliente actualizado: idcliente={idcliente}")
        return jsonify({"message": "Cliente actualizado exitosamente"}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error al actualizar cliente: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500


# Endpoint para obtener todos los perfiles
@app.route('/perfiles', methods=['GET'])
@jwt_required()
def get_perfiles():
    user_id = get_jwt_identity()
    claims = get_jwt()
    idcliente = claims.get('idcliente')

    logger.info(f"User ID: {user_id}, Claims: {claims}")  # Imprime los claims completos

    if not has_permission(claims, 'parametrizacion', 'perfiles', 'editar'):
        logger.warning(f"Acceso denegado para user_id {user_id}. Permisos esperados: parametrizacion_usuarios_y_perfiles:editar")
        return jsonify({"error": "No autorizado"}), 403

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        if claims.get('perfilid') == 1:  # Superadmin ve todos los perfiles
            cur.execute("SELECT perfil_id, idcliente, perfil_nombre FROM perfiles WHERE estado = TRUE")
        else:  # Cliente ve solo sus perfiles
            if not idcliente:
                logger.error("No idcliente en claims")
                return jsonify({"error": "No se proporcionó idcliente"}), 403
            cur.execute(
                "SELECT perfil_id, idcliente, perfil_nombre FROM perfiles WHERE estado = TRUE AND idcliente = %s",
                (idcliente,)
            )
        perfiles = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify([{"perfil_id": p[0], "idcliente": p[1], "perfil_nombre": p[2]} for p in perfiles]), 200
    except Exception as e:
        logger.error(f"Error al obtener perfiles: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500

# Endpoint para crear un perfil
@app.route('/perfiles', methods=['POST'])
@jwt_required()
def create_perfil():
    user_id = get_jwt_identity()
    claims = get_jwt()
    idcliente = claims.get('idcliente')

    if not has_permission(claims, 'parametrizacion', 'perfiles', 'editar'):
        return jsonify({"error": "No autorizado"}), 403

    data = request.get_json()
    perfil_nombre = data.get('perfil_nombre')
    idcliente_data = data.get('idcliente')

    if not perfil_nombre:
        return jsonify({"error": "Falta el nombre del perfil"}), 400
    if claims.get('perfilid') != 1 and idcliente_data != idcliente:  # Cliente solo puede crear para su idcliente
        return jsonify({"error": "No autorizado para crear perfiles para otro cliente"}), 403

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO perfiles (idcliente, perfil_nombre, estado) VALUES (%s, %s, %s) RETURNING perfil_id",
            (idcliente if claims.get('perfilid') != 1 else idcliente_data, perfil_nombre, True)
        )
        perfil_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"perfil_id": perfil_id}), 201
    except psycopg2.IntegrityError as e:
        conn.rollback()
        logger.error(f"Error de integridad al crear perfil: {str(e)}")
        return jsonify({"error": "El perfil no pudo crearse debido a un ID duplicado"}), 400
    except Exception as e:
        conn.rollback()
        logger.error(f"Error al crear perfil: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500



# Endpoint para crear/actualizar permisos en bulk (reemplaza los existentes)
@app.route('/perfiles/<int:perfil_id>/permisos', methods=['PUT'])
@jwt_required()
def update_permisos(perfil_id):
    user_id = get_jwt_identity()
    claims = get_jwt()
    idcliente = claims.get('idcliente')

    if not has_permission(claims, 'parametrizacion', 'perfiles', 'editar'):
        return jsonify({"error": "No autorizado"}), 403

    data = request.get_json()
    if not data:
        return jsonify({"error": "Faltan datos de permisos"}), 400

    # Verificar que el perfil pertenece al cliente (excepto superadmin)
    if claims.get('perfilid') != 1:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT idcliente FROM perfiles WHERE perfil_id = %s", (perfil_id,))
        perfil = cur.fetchone()
        cur.close()
        conn.close()
        if not perfil or perfil[0] != idcliente:
            return jsonify({"error": "No autorizado para modificar este perfil"}), 403

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM permisos WHERE idPerfil = %s", (perfil_id,))
        values = [(perfil_id, p['seccion'], p['subseccion'], p['permiso']) for p in data]
        if values:
            execute_values(
                cur,
                "INSERT INTO permisos (idPerfil, seccion, subseccion, permiso) VALUES %s",
                values
            )
        conn.commit()
        cur.close()
        conn.close()
        logger.info(f"Permisos actualizados para perfil {perfil_id}: {values}")
        return jsonify({"message": "Permisos actualizados exitosamente"}), 200
    except Exception as e:
        logger.error(f"Error al actualizar permisos: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500


# Endpoint para crear permisos en bulk
@app.route('/permisos/bulk', methods=['POST'])
@jwt_required()
def create_permisos_bulk():
    user_id = get_jwt_identity()
    claims = get_jwt()
    perfilid = claims.get('perfilid')
    if perfilid != 1:  # Solo superadmin
        return jsonify({"error": "No autorizado"}), 403

    data = request.get_json()
    if not data:
        return jsonify({"error": "Faltan datos de permisos"}), 400

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        values = [(p['idPerfil'], p['seccion'], p['subseccion'], p['permiso']) for p in data]
        execute_values(
            cur,
            "INSERT INTO permisos (idPerfil, seccion, subseccion, permiso) VALUES %s",
            values
        )
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"message": "Permisos creados exitosamente"}), 201
    except Exception as e:
        logger.error(f"Error al crear permisos: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500
    

# Endpoint para eliminar un perfil
@app.route('/perfiles/<int:perfil_id>', methods=['DELETE'])
@jwt_required()
def delete_perfil(perfil_id):
    user_id = get_jwt_identity()
    claims = get_jwt()
    idcliente = claims.get('idcliente')

    if not has_permission(claims, 'parametrizacion', 'perfiles', 'editar'):
        return jsonify({"error": "No autorizado"}), 403

    if claims.get('perfilid') != 1:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT idcliente FROM perfiles WHERE perfil_id = %s", (perfil_id,))
        perfil = cur.fetchone()
        cur.close()
        conn.close()
        if not perfil or perfil[0] != idcliente:
            return jsonify({"error": "No autorizado para eliminar este perfil"}), 403

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM permisos WHERE idPerfil = %s", (perfil_id,))
        cur.execute("DELETE FROM perfiles WHERE perfil_id = %s", (perfil_id,))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"message": "Perfil eliminado exitosamente"}), 200
    except Exception as e:
        logger.error(f"Error al eliminar perfil: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500
    

# Enpoint para actualizar Perfiles
@app.route('/perfiles/<int:perfil_id>', methods=['PUT'])
@jwt_required()
def update_perfil(perfil_id):
    user_id = get_jwt_identity()
    claims = get_jwt()
    idcliente = claims.get('idcliente')

    if not has_permission(claims, 'parametrizacion', 'perfiles', 'editar'):
        return jsonify({"error": "No autorizado"}), 403

    data = request.get_json()
    perfil_nombre = data.get('perfil_nombre')
    idcliente_data = data.get('idcliente')

    if not perfil_nombre:
        return jsonify({"error": "Falta el nombre del perfil"}), 400
    if claims.get('perfilid') != 1 and idcliente_data != idcliente:
        return jsonify({"error": "No autorizado para modificar perfiles de otro cliente"}), 403

    if claims.get('perfilid') != 1:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT idcliente FROM perfiles WHERE perfil_id = %s", (perfil_id,))
        perfil = cur.fetchone()
        cur.close()
        conn.close()
        if not perfil or perfil[0] != idcliente:
            return jsonify({"error": "No autorizado para modificar este perfil"}), 403

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "UPDATE perfiles SET idcliente = %s, perfil_nombre = %s WHERE perfil_id = %s",
            (idcliente if claims.get('perfilid') != 1 else idcliente_data, perfil_nombre, perfil_id)
        )
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"message": "Perfil actualizado exitosamente"}), 200
    except Exception as e:
        logger.error(f"Error al actualizar perfil: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500
    

# Endpoint para obtener permisos de un perfil
@app.route('/perfiles/<int:perfil_id>/permisos', methods=['GET'])
@jwt_required()
def get_permisos(perfil_id):
    user_id = get_jwt_identity()
    claims = get_jwt()
    idcliente = claims.get('idcliente')

    if not has_permission(claims, 'parametrizacion', 'perfiles', 'editar'):
        return jsonify({"error": "No autorizado"}), 403

    if claims.get('perfilid') != 1:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT idcliente FROM perfiles WHERE perfil_id = %s", (perfil_id,))
        perfil = cur.fetchone()
        cur.close()
        conn.close()
        if not perfil or perfil[0] != idcliente:
            return jsonify({"error": "No autorizado para ver los permisos de este perfil"}), 403

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT seccion, subseccion, permiso FROM permisos WHERE idPerfil = %s",
            (perfil_id,)
        )
        permisos = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify([{"seccion": p[0], "subseccion": p[1], "permiso": p[2]} for p in permisos]), 200
    except Exception as e:
        logger.error(f"Error al obtener permisos: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500




# Endpoint para obtener todos los usuarios
# Endpoint para obtener todos los usuarios
# Endpoint para obtener todos los usuarios
@app.route('/usuarios', methods=['GET'])
@jwt_required()
def get_usuarios():
    user_id = get_jwt_identity()
    claims = get_jwt()
    idcliente = claims.get('idcliente')

    if not has_permission(claims, 'parametrizacion', 'usuarios', 'editar'):
        logger.warning(f"Acceso denegado para user_id {user_id}")
        return jsonify({"error": "No autorizado"}), 403

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        if claims.get('perfilid') == 1:  # Superadmin ve todos los usuarios
            cur.execute("""
                SELECT id, idcliente, perfilid, nombres, apellidos, usuario, estado 
                FROM usuarios
            """)
        else:  # Cliente ve solo sus usuarios
            if not idcliente:
                logger.error("No idcliente en claims")
                return jsonify({"error": "No se proporcionó idcliente"}), 403
            cur.execute("""
                SELECT id, idcliente, perfilid, nombres, apellidos, usuario, estado 
                FROM usuarios 
                WHERE idcliente = %s
            """, (idcliente,))
        usuarios = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify([
            {
                "idusuario": u[0],
                "idcliente": u[1],
                "perfil_id": u[2],
                "nombre": u[3],
                "apellidos": u[4],
                "usuario": u[5],
                "estado": u[6]
            } for u in usuarios
        ]), 200
    except Exception as e:
        logger.error(f"Error al obtener usuarios: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500
    

# Endpoint para crear un usuario
@app.route('/usuarios', methods=['POST'])
@jwt_required()
def create_usuario():
    user_id = get_jwt_identity()
    claims = get_jwt()
    idcliente = claims.get('idcliente')

    if not has_permission(claims, 'parametrizacion', 'usuarios', 'editar'):
        return jsonify({"error": "No autorizado"}), 403

    data = request.get_json()
    idcliente_data = data.get('idcliente')
    perfil_id = data.get('perfil_id')
    nombre = data.get('nombre')
    apellidos = data.get('apellidos')  # Añadimos apellidos
    usuario = data.get('usuario')
    password = data.get('password')
    estado = data.get('estado', True)

    if not all([perfil_id, usuario, password]):
        return jsonify({"error": "Faltan datos requeridos"}), 400
    if claims.get('perfilid') != 1 and idcliente_data != idcliente:
        return jsonify({"error": "No autorizado para crear usuarios para otro cliente"}), 403

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id FROM usuarios WHERE usuario = %s", (usuario,))
        if cur.fetchone():
            cur.close()
            conn.close()
            return jsonify({"error": "El nombre de usuario ya está en uso. Por favor, elige otro."}), 400

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        cur.execute(
            """
            INSERT INTO usuarios (idcliente, perfilid, nombres, apellidos, usuario, password, estado) 
            VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id
            """,
            (idcliente if claims.get('perfilid') != 1 else idcliente_data, perfil_id, nombre, apellidos, usuario, hashed_password, estado)
        )
        user_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"idusuario": user_id}), 201
    except psycopg2.IntegrityError as e:
        conn.rollback()
        logger.error(f"Error de integridad al crear usuario: {str(e)}")
        return jsonify({"error": "El nombre de usuario ya está en uso. Por favor, elige otro."}), 400
    except Exception as e:
        conn.rollback()
        logger.error(f"Error al crear usuario: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500
    

# Endpoint para actualizar un usuario
@app.route('/usuarios/<int:id>', methods=['PUT'])
@jwt_required()
def update_usuario(id):
    user_id = get_jwt_identity()
    claims = get_jwt()
    idcliente = claims.get('idcliente')

    if not has_permission(claims, 'parametrizacion', 'usuarios', 'editar'):
        return jsonify({"error": "No autorizado"}), 403

    data = request.get_json()
    idcliente_data = data.get('idcliente')
    perfil_id = data.get('perfil_id')
    nombre = data.get('nombre')
    apellidos = data.get('apellidos')  # Añadimos apellidos
    usuario = data.get('usuario')
    password = data.get('password')
    estado = data.get('estado')

    if not all([perfil_id, usuario]):
        return jsonify({"error": "Faltan datos requeridos"}), 400
    if claims.get('perfilid') != 1 and idcliente_data != idcliente:
        return jsonify({"error": "No autorizado para modificar usuarios de otro cliente"}), 403

    if claims.get('perfilid') != 1:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT idcliente FROM usuarios WHERE id = %s", (id,))
        user = cur.fetchone()
        cur.close()
        conn.close()
        if not user or user[0] != idcliente:
            return jsonify({"error": "No autorizado para modificar este usuario"}), 403

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id FROM usuarios WHERE usuario = %s AND id != %s", (usuario, id))
        if cur.fetchone():
            cur.close()
            conn.close()
            return jsonify({"error": "El nombre de usuario ya está en uso por otro usuario. Por favor, elige otro."}), 400

        if password:
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            cur.execute(
                """
                UPDATE usuarios SET idcliente = %s, perfilid = %s, nombres = %s, apellidos = %s, usuario = %s, password = %s, estado = %s 
                WHERE id = %s
                """,
                (idcliente_data, perfil_id, nombre, apellidos, usuario, hashed_password, estado, id)
            )
        else:
            cur.execute(
                """
                UPDATE usuarios SET idcliente = %s, perfilid = %s, nombres = %s, apellidos = %s, usuario = %s, estado = %s 
                WHERE id = %s
                """,
                (idcliente_data, perfil_id, nombre, apellidos, usuario, estado, id)
            )
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"message": "Usuario actualizado exitosamente"}), 200
    except psycopg2.IntegrityError as e:
        conn.rollback()
        logger.error(f"Error de integridad al actualizar usuario: {str(e)}")
        return jsonify({"error": "El nombre de usuario ya está en uso. Por favor, elige otro."}), 400
    except Exception as e:
        conn.rollback()
        logger.error(f"Error al actualizar usuario: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500
    

# Endpoint para eliminar un usuario
@app.route('/usuarios/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_usuario(id):
    user_id = get_jwt_identity()
    claims = get_jwt()
    idcliente = claims.get('idcliente')

    if not has_permission(claims, 'parametrizacion', 'usuarios', 'editar'):
        return jsonify({"error": "No autorizado"}), 403

    if claims.get('perfilid') != 1:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT idcliente FROM usuarios WHERE id = %s", (id,))
        user = cur.fetchone()
        cur.close()
        conn.close()
        if not user or user[0] != idcliente:
            return jsonify({"error": "No autorizado para eliminar este usuario"}), 403

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM usuarios WHERE id = %s", (id,))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"message": "Usuario eliminado exitosamente"}), 200
    except Exception as e:
        logger.error(f"Error al eliminar usuario: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500
    

# Endpoint para cambiar el estado de un usuario
@app.route('/usuarios/<int:id>/estado', methods=['PATCH'])
@jwt_required()
def toggle_usuario_estado(id):
    user_id = get_jwt_identity()
    claims = get_jwt()
    perfilid = claims.get('perfilid')
    if perfilid != 1:  # Solo superadmin
        return jsonify({"error": "No autorizado"}), 403

    data = request.get_json()
    estado = data.get('estado')

    if estado is None:
        return jsonify({"error": "Falta el campo estado"}), 400

    try:
        user = Usuarios.query.get(id)
        if not user:
            return jsonify({"error": "Usuario no encontrado"}), 404
        user.estado = estado
        user.fechamodificacion = db.func.current_timestamp()
        db.session.commit()
        return jsonify({"message": "Estado actualizado exitosamente"}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error al actualizar estado del usuario: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500


@app.route('/upload_sales', methods=['POST'])
@jwt_required()
def upload_sales():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        if not file.filename.endswith('.xlsx'):
            return jsonify({"error": "File must be an Excel (.xlsx)"}), 400

        df = pd.read_excel(file, usecols=[
            "Fecha", "Rangos Horarios", "Almacén", "Cliente", 
            "Nombre Vendedor", "Descripción", "Uds.", "Importe"
        ])
        df.columns = ["fecha", "rango_horarios", "almacen", "cliente", 
                      "vendedor", "descripcion", "uds", "importe"]

        df["fecha"] = pd.to_datetime(df["fecha"], errors='coerce')
        df["uds"] = pd.to_numeric(df["uds"], errors='coerce').fillna(0).astype(int)
        df["importe"] = pd.to_numeric(df["importe"], errors='coerce').fillna(0.0)
        df = df.dropna(subset=["almacen"])

        if df.empty:
            return jsonify({"error": "No se encontraron registros válidos en el archivo"}), 400

        conn = psycopg2.connect(
            dbname=app.config['DB_NAME'], user=app.config['DB_USER'],
            password=app.config['DB_PASSWORD'], host=app.config['DB_HOST'],
            port=app.config['DB_PORT']
        )
        cursor = conn.cursor()

        # Reemplazo de user_id = 1 con autenticación
        user_id = get_jwt_identity()
        cursor.execute("SELECT IdCliente FROM Usuarios WHERE Id = %s", (user_id,))
        id_cliente_result = cursor.fetchone()
        if not id_cliente_result:
            conn.close()
            return jsonify({"error": "Usuario no encontrado"}), 404
        id_cliente = id_cliente_result[0]

        cursor.execute("SELECT Data2 FROM PuntosDeVenta WHERE IdCliente = %s AND Estado = 'Activo'", (id_cliente,))
        valid_almacenes = set(row[0] for row in cursor.fetchall())
        invalid_almacenes = set(df["almacen"].unique()) - valid_almacenes
        if invalid_almacenes:
            conn.close()
            return jsonify({"error": f"Almacenes no válidos: {invalid_almacenes}"}), 400

        # Insertar datos diarios en VentaHistoricaHora
        data_to_insert = [
            (id_cliente, row["fecha"], row["rango_horarios"], row["almacen"],
             row["cliente"], row["vendedor"], row["descripcion"], row["uds"], row["importe"])
            for _, row in df.iterrows()
        ]

        query = """
            INSERT INTO VentaHistoricaHora (IdCliente, Fecha, Rango_horarios, Almacen, 
                                            Cliente, Vendedor, Descripcion, Uds, Importe)
            VALUES %s
            ON CONFLICT DO NOTHING
        """
        execute_values(cursor, query, data_to_insert)

        # Actualizar VentaHistorica para los meses afectados por la carga diaria
        years_months = df.groupby([df["fecha"].dt.year, df["fecha"].dt.month]).size().index
        current_year = datetime.now().year
        current_month = datetime.now().month

        for year, month in years_months:
            # Solo actualizar si no es un mes pasado con datos históricos ya cargados
            cursor.execute("""
                SELECT COUNT(*) 
                FROM VentaHistorica 
                WHERE IdCliente = %s AND Año = %s AND Mes = %s 
                AND Venta IS NOT NULL
            """, (id_cliente, year, month))
            has_historical_data = cursor.fetchone()[0] > 0

            # Actualizar solo si es el mes actual o no hay datos históricos
            if not has_historical_data or (year == current_year and month == current_month):
                cursor.execute("""
                    INSERT INTO VentaHistorica (IdCliente, Año, Mes, PDV, Venta)
                    SELECT 
                        %s AS IdCliente,
                        EXTRACT(YEAR FROM v.Fecha) AS Año,
                        EXTRACT(MONTH FROM v.Fecha) AS Mes,
                        p.PDV,
                        SUM(v.Importe) AS Venta
                    FROM VentaHistoricaHora v
                    JOIN PuntosDeVenta p ON v.Almacen = p.Data2 AND p.IdCliente = %s AND p.Estado = 'Activo'
                    WHERE EXTRACT(YEAR FROM v.Fecha) = %s
                    AND EXTRACT(MONTH FROM v.Fecha) = %s
                    GROUP BY p.PDV, EXTRACT(YEAR FROM v.Fecha), EXTRACT(MONTH FROM v.Fecha)
                    ON CONFLICT (IdCliente, PDV, Año, Mes) DO UPDATE
                    SET Venta = EXCLUDED.Venta
                """, (id_cliente, id_cliente, year, month))

        conn.commit()
        conn.close()

        return jsonify({"message": f"Loaded {len(data_to_insert)} rows and updated VentaHistorica"}), 200

    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return jsonify({"error": str(e)}), 500


@app.route('/upload_sales_OLD', methods=['POST'])
def upload_sales_OLD():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        if not file.filename.endswith('.xlsx'):
            return jsonify({"error": "File must be an Excel (.xlsx)"}), 400

        df = pd.read_excel(file, usecols=[
            "Fecha", "Rangos Horarios", "Almacén", "Cliente", 
            "Nombre Vendedor", "Descripción", "Uds.", "Importe"
        ])
        df.columns = ["fecha", "rango_horarios", "almacen", "cliente", 
                      "vendedor", "descripcion", "uds", "importe"]

        # Convertir tipos de datos
        df["fecha"] = pd.to_datetime(df["fecha"], errors='coerce')
        df["uds"] = pd.to_numeric(df["uds"], errors='coerce').fillna(0).astype(int)
        df["importe"] = pd.to_numeric(df["importe"], errors='coerce').fillna(0.0)

        # Filtrar filas donde 'almacen' no sea nulo (excluir totales)
        df = df.dropna(subset=["almacen"])

        # Si no quedan filas después del filtro, devolver un error
        if df.empty:
            return jsonify({"error": "No se encontraron registros válidos en el archivo"}), 400

        conn = psycopg2.connect(
            dbname=app.config['DB_NAME'], user=app.config['DB_USER'],
            password=app.config['DB_PASSWORD'], host=app.config['DB_HOST'],
            port=app.config['DB_PORT']
        )
        cursor = conn.cursor()

        # Simulación de usuario autenticado (hardcoded por ahora)
        user_id = 1  # Esto lo reemplazaremos con autenticación real después
        cursor.execute("SELECT IdCliente FROM Usuarios WHERE Id = %s", (user_id,))
        id_cliente = cursor.fetchone()
        if not id_cliente:
            conn.close()
            return jsonify({"error": "Usuario no encontrado"}), 400
        id_cliente = id_cliente[0]

        cursor.execute("SELECT Data2 FROM PuntosDeVenta WHERE IdCliente = %s", (id_cliente,))
        valid_almacenes = set(row[0] for row in cursor.fetchall())

        # Validar almacenes no nulos
        invalid_almacenes = set(df["almacen"].unique()) - valid_almacenes
        if invalid_almacenes:
            conn.close()
            return jsonify({"error": f"Almacenes no válidos: {invalid_almacenes}"}), 400

        data_to_insert = [
            (id_cliente, row["fecha"], row["rango_horarios"], row["almacen"],
             row["cliente"], row["vendedor"], row["descripcion"], row["uds"], row["importe"])
            for _, row in df.iterrows()
        ]

        query = """
            INSERT INTO VentaHistoricaHora (IdCliente, Fecha, Rango_horarios, Almacen, 
                                            Cliente, Vendedor, Descripcion, Uds, Importe)
            VALUES %s
            ON CONFLICT DO NOTHING
        """
        execute_values(cursor, query, data_to_insert)

        conn.commit()
        conn.close()

        return jsonify({"message": f"Loaded {len(data_to_insert)} rows successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/upload_arqueo', methods=['POST'])
@jwt_required()
def upload_arqueo():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        if not file.filename.endswith('.xlsx'):
            return jsonify({"error": "File must be an Excel (.xlsx)"}), 400

        df = pd.read_excel(file, header=0)  # cambiar a header = 1 si la primera linea de la plantilla debe estar vacia. Se toman encabezados dese la 2da fila
        df.columns = [col.lower().replace(' ', '_') for col in df.columns]
        df = df.rename(columns={
            "an_3": "pdv",
            "fecha": "fecha",
            "z": "z",
            "total": "total",
            "bonos": "bonos",
            "efectivo": "efectivo",
            "recibo_bancario": "recibo_bancario",
            "tarjeta_debito": "tarjeta_debito",
            "transferencia_bancaria": "transferencia_bancaria",
            "vale": "vale"  # Nueva columna
        })[["pdv", "fecha", "z", "total", "bonos", "efectivo", 
            "recibo_bancario", "tarjeta_debito", "transferencia_bancaria", "vale"]]

        df["fecha"] = pd.to_datetime(df["fecha"], errors='coerce')
        df["z"] = pd.to_numeric(df["z"], errors='coerce').fillna(0).astype(int)
        for col in ["total", "bonos", "efectivo", "recibo_bancario", "tarjeta_debito", "transferencia_bancaria", "vale"]:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)

        df = df.dropna(subset=["pdv"])
        if df.empty:
            return jsonify({"error": "No se encontraron registros válidos en el archivo"}), 400

        conn = psycopg2.connect(
            dbname=app.config['DB_NAME'], user=app.config['DB_USER'],
            password=app.config['DB_PASSWORD'], host=app.config['DB_HOST'],
            port=app.config['DB_PORT']
        )
        cursor = conn.cursor()

        # Reemplazo de user_id = 1 con autenticación
        user_id = get_jwt_identity()
        cursor.execute("SELECT IdCliente FROM Usuarios WHERE Id = %s", (user_id,))
        id_cliente_result = cursor.fetchone()
        if not id_cliente_result:
            conn.close()
            return jsonify({"error": "Usuario no encontrado"}), 404
        id_cliente = id_cliente_result[0]

        cursor.execute("SELECT PDV FROM PuntosDeVenta WHERE IdCliente = %s", (id_cliente,))
        valid_pdvs = set(row[0] for row in cursor.fetchall())
        invalid_pdvs = set(df["pdv"].unique()) - valid_pdvs
        if invalid_pdvs:
            conn.close()
            return jsonify({"error": f"PDVs no válidos: {invalid_pdvs}"}), 400

        # Agrupar por PDV y Fecha para validar el total contra VentaHistoricaHora
        df_grouped = df.groupby(["pdv", "fecha"])["total"].sum().reset_index()

        errors = []
        for _, row in df_grouped.iterrows():
            cursor.execute("""
                SELECT COALESCE(SUM(Importe), 0)
                FROM VentaHistoricaHora
                WHERE IdCliente = %s 
                AND Almacen = (SELECT Data2 FROM PuntosDeVenta WHERE PDV = %s AND IdCliente = %s)
                AND Fecha = %s
            """, (id_cliente, row["pdv"], id_cliente, row["fecha"]))
            total_ventas = cursor.fetchone()[0]
            if abs(total_ventas - row["total"]) > 0.01:  # Tolerancia de 0.01
                errors.append(f"PDV: {row['pdv']}, Fecha: {row['fecha']}, Total Arqueo: {row['total']}, Total Ventas: {total_ventas}")

        if errors:
            conn.close()
            return jsonify({"error": "Inconsistencias encontradas", "details": errors}), 400

        # Insertar datos originales (sin agrupar)
        data_to_insert = [
            (id_cliente, row["pdv"], row["fecha"], row["z"], row["total"], 
             row["bonos"], row["efectivo"], row["recibo_bancario"], row["tarjeta_debito"], 
             row["transferencia_bancaria"], row["vale"])  # Incluir Vale
            for _, row in df.iterrows()
        ]

        query = """
            INSERT INTO ArqueoCaja (IdCliente, PDV, Fecha, Z, Total, Bonos, Efectivo, 
                                    Recibo_Bancario, Tarjeta_Debito, Transferencia_Bancaria, Vale)
            VALUES %s
            ON CONFLICT (IdCliente, PDV, Fecha, Z) DO NOTHING
        """
        execute_values(cursor, query, data_to_insert)

        conn.commit()
        conn.close()

        return jsonify({"message": f"Loaded {len(data_to_insert)} rows successfully"}), 200

    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return jsonify({"error": str(e)}), 500
    

@app.route('/upload_venta_mensual', methods=['POST'])
@jwt_required()
def upload_venta_mensual():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        if not file.filename.endswith('.xlsx'):
            return jsonify({"error": "File must be an Excel (.xlsx)"}), 400

        df = pd.read_excel(file)
        df.columns = ["año", "pdv", "mes", "venta"]

        # Limpiar y convertir datos
        df["año"] = pd.to_numeric(df["año"], errors='coerce').astype(int)
        df["venta"] = df["venta"].replace({r'\$': '', r'\.': ''}, regex=True).astype(float)
        df["mes"] = df["mes"].apply(mes_a_numero)

        conn = psycopg2.connect(
            dbname=app.config['DB_NAME'], user=app.config['DB_USER'],
            password=app.config['DB_PASSWORD'], host=app.config['DB_HOST'],
            port=app.config['DB_PORT']
        )
        cursor = conn.cursor()

        # Reemplazo de user_id = 1 con autenticación
        user_id = get_jwt_identity()
        cursor.execute("SELECT IdCliente FROM Usuarios WHERE Id = %s", (user_id,))
        id_cliente_result = cursor.fetchone()
        if not id_cliente_result:
            conn.close()
            return jsonify({"error": "Usuario no encontrado"}), 404
        id_cliente = id_cliente_result[0]

        # Validar todos los PDVs (activos e inactivos) para datos históricos
        cursor.execute("SELECT PDV FROM PuntosDeVenta WHERE IdCliente = %s", (id_cliente,))
        valid_pdvs = set(row[0] for row in cursor.fetchall())
        invalid_pdvs = set(df["pdv"].unique()) - valid_pdvs
        if invalid_pdvs:
            conn.close()
            return jsonify({"error": f"PDVs no válidos: {invalid_pdvs}"}), 400

        # Agrupar datos del archivo para evitar duplicados
        df_grouped = df.groupby(["pdv", "año", "mes"], as_index=False)["venta"].sum()

        # Insertar datos históricos con prioridad
        data_to_insert = [
            (id_cliente, row["año"], row["mes"], row["pdv"], row["venta"])
            for _, row in df_grouped.iterrows()
        ]

        query = """
            INSERT INTO VentaHistorica (IdCliente, Año, Mes, PDV, Venta)
            VALUES %s
            ON CONFLICT (IdCliente, PDV, Año, Mes) DO UPDATE
            SET Venta = EXCLUDED.Venta
        """
        execute_values(cursor, query, data_to_insert)

        # Actualizar mes en curso solo si no hay datos en el archivo para ese mes
        current_year = datetime.now().year
        current_month = datetime.now().month
        has_current_month_data = any(
            row["año"] == current_year and row["mes"] == current_month 
            for _, row in df_grouped.iterrows()
        )

        if not has_current_month_data:
            cursor.execute("""
                INSERT INTO VentaHistorica (IdCliente, Año, Mes, PDV, Venta)
                SELECT 
                    %s AS IdCliente,
                    EXTRACT(YEAR FROM v.Fecha) AS Año,
                    EXTRACT(MONTH FROM v.Fecha) AS Mes,
                    p.PDV,
                    SUM(v.Importe) AS Venta
                FROM VentaHistoricaHora v
                JOIN PuntosDeVenta p ON v.Almacen = p.Data2 AND p.IdCliente = %s AND p.Estado = 'Activo'
                WHERE EXTRACT(YEAR FROM v.Fecha) = %s
                AND EXTRACT(MONTH FROM v.Fecha) = %s
                GROUP BY p.PDV, EXTRACT(YEAR FROM v.Fecha), EXTRACT(MONTH FROM v.Fecha)
                ON CONFLICT (IdCliente, PDV, Año, Mes) DO UPDATE
                SET Venta = EXCLUDED.Venta
            """, (id_cliente, id_cliente, current_year, current_month))

        conn.commit()
        conn.close()

        return jsonify({"message": f"Loaded {len(data_to_insert)} rows{' and updated current month' if not has_current_month_data else ''}"}), 200

    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return jsonify({"error": str(e)}), 500
    

@app.route('/dashboard/historical_sales', methods=['GET'])
@jwt_required()
def historical_sales():
    try:
        conn = psycopg2.connect(
            dbname=app.config['DB_NAME'], user=app.config['DB_USER'],
            password=app.config['DB_PASSWORD'], host=app.config['DB_HOST'],
            port=app.config['DB_PORT']
        )
        cursor = conn.cursor()

        user_id = get_jwt_identity()  # ID del usuario autenticado como string
        cursor.execute("SELECT IdCliente FROM Usuarios WHERE Id = %s", (user_id,))
        id_cliente = cursor.fetchone()
        if not id_cliente:
            conn.close()
            return jsonify({"error": "Usuario no encontrado"}), 404
        id_cliente = id_cliente[0]

        # Obtener parámetros de la solicitud
        year = request.args.get('year', type=int)
        month = request.args.get('month', type=int)
        status = request.args.get('status', default='Todos', type=str)
        pdv = request.args.get('pdv', type=str)  # Nuevo parámetro para filtrar por PDV

        # Construir la consulta SQL
        query = """
            SELECT vh.Año, vh.Mes, vh.PDV, SUM(vh.Venta) as Venta
            FROM VentaHistorica vh
            LEFT JOIN PuntosDeVenta pdv ON vh.PDV = pdv.PDV AND vh.IdCliente = pdv.IdCliente
            WHERE vh.IdCliente = %s
        """
        params = [id_cliente]

        if year:
            query += " AND vh.Año = %s"
            params.append(year)
        if month:
            query += " AND vh.Mes = %s"
            params.append(month)
        if status != 'Todos':
            query += " AND (pdv.Estado = %s OR pdv.Estado IS NULL)"
            params.append(status)
        if pdv and pdv != 'Todos':  # Filtrar por PDV si se especifica
            query += " AND vh.PDV = %s"
            params.append(pdv)

        query += " GROUP BY vh.Año, vh.Mes, vh.PDV ORDER BY vh.Año, vh.Mes, vh.PDV"

        cursor.execute(query, params)
        rows = cursor.fetchall()

        data = [{"year": row[0], "month": row[1], "pdv": row[2], "sales": float(row[3])} for row in rows]
        pdvs = sorted(set(row["pdv"] for row in data))
        years = sorted(set(row["year"] for row in data))
        response = {}

        if not year and not month:  # Todos los años
            pivot_data = []
            totals = {year: 0.0 for year in years}
            for pdv in pdvs:
                pdv_data = {"pdv": pdv}
                for year in years:
                    year_sales = sum(row["sales"] for row in data if row["pdv"] == pdv and row["year"] == year)
                    pdv_data[str(year)] = year_sales
                    totals[year] += year_sales
                pivot_data.append(pdv_data)
            pivot_data.append({"pdv": "Total", **{str(year): totals[year] for year in years}})
            response = {"years": years, "data": pivot_data}

        elif month:  # Mes específico (con o sin año)
            pivot_data = []
            totals = {year: 0.0 for year in years}
            for pdv in pdvs:
                pdv_data = {"pdv": pdv}
                for year in years:
                    sales = next((row["sales"] for row in data if row["pdv"] == pdv and row["year"] == year), 0.0)
                    pdv_data[str(year)] = sales
                    totals[year] += sales
                pivot_data.append(pdv_data)
            pivot_data.append({"pdv": "Total", **{str(year): totals[year] for year in years}})
            response = {"month": month, "years": years, "data": pivot_data}

        else:  # Solo año
            pivot_data = []
            totals = {year: 0.0 for year in years}
            for pdv in pdvs:
                pdv_data = {"pdv": pdv}
                for year in years:
                    year_sales = sum(row["sales"] for row in data if row["pdv"] == pdv and row["year"] == year)
                    pdv_data[str(year)] = year_sales
                    totals[year] += year_sales
                pivot_data.append(pdv_data)
            pivot_data.append({"pdv": "Total", **{str(year): totals[year] for year in years}})
            response = {"years": years, "data": pivot_data}

        conn.close()
        return jsonify(response), 200

    except Exception as e:
        logger.error(f"Error en historical_sales: {str(e)}")
        return jsonify({"error": str(e)}), 500
    

@app.route('/budget/sales', methods=['GET'])
@jwt_required()
def get_budget_sales():
    try:
        conn = psycopg2.connect(
            dbname=app.config['DB_NAME'], user=app.config['DB_USER'],
            password=app.config['DB_PASSWORD'], host=app.config['DB_HOST'],
            port=app.config['DB_PORT']
        )
        cursor = conn.cursor()

        # Reemplazo de user_id = 1 con autenticación
        user_id = get_jwt_identity()
        cursor.execute("SELECT IdCliente FROM Usuarios WHERE Id = %s", (user_id,))
        id_cliente_result = cursor.fetchone()
        if not id_cliente_result:
            conn.close()
            return jsonify({"error": "Usuario no encontrado"}), 404
        id_cliente = id_cliente_result[0]

        year = request.args.get('year', type=int, default=datetime.now().year)
        status = request.args.get('status', default='Activo', type=str)

        # Obtener PDVs según estatus
        pdv_query = """
            SELECT PDV FROM PuntosDeVenta
            WHERE IdCliente = %s
        """
        params = [id_cliente]
        if status != 'Todos':
            pdv_query += " AND Estado = %s"
            params.append(status)
        pdv_query += " ORDER BY PDV"

        cursor.execute(pdv_query, params)
        all_pdvs = [row[0] for row in cursor.fetchall()]

        # Obtener presupuestos
        budget_query = """
            SELECT pdv, mes, presupuestoventa
            FROM presupuesto
            WHERE idcliente = %s AND año = %s
        """
        budget_params = [id_cliente, year]
        if status != 'Todos':
            budget_query += " AND pdv IN (SELECT PDV FROM PuntosDeVenta WHERE IdCliente = %s AND Estado = %s)"
            budget_params.extend([id_cliente, status])

        cursor.execute(budget_query, budget_params)
        rows = cursor.fetchall()

        # Estructurar datos
        budget_data = {pdv: {str(m): 0.0 for m in range(1, 13)} for pdv in all_pdvs}
        totals = {str(m): 0.0 for m in range(1, 13)}

        for pdv, mes, presupuesto in rows:
            budget_data[pdv][str(mes)] = float(presupuesto or 0)
            totals[str(mes)] += float(presupuesto or 0)

        response = {
            "year": year,
            "pdvs": all_pdvs,
            "data": [{"pdv": pdv, **budget_data[pdv]} for pdv in all_pdvs],
            "totals": totals
        }

        conn.close()
        return jsonify(response), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

@app.route('/budget/sales', methods=['POST'])
@jwt_required()
def create_budget_sales():
    try:
        conn = psycopg2.connect(
            dbname=app.config['DB_NAME'], user=app.config['DB_USER'],
            password=app.config['DB_PASSWORD'], host=app.config['DB_HOST'],
            port=app.config['DB_PORT']
        )
        cursor = conn.cursor()

        # Reemplazo de user_id = 1 con autenticación
        user_id = get_jwt_identity()
        cursor.execute("SELECT IdCliente FROM Usuarios WHERE Id = %s", (user_id,))
        id_cliente_result = cursor.fetchone()
        if not id_cliente_result:
            conn.close()
            return jsonify({"error": "Usuario no encontrado"}), 404
        id_cliente = id_cliente_result[0]

        data = request.get_json()
        logger.debug(f"Datos recibidos: {data}")
        year = data.get('year', datetime.now().year)
        budget_entries = data.get('budget', [])

        cursor.execute("SELECT PDV FROM PuntosDeVenta WHERE IdCliente = %s", (id_cliente,))
        valid_pdvs = {row[0] for row in cursor.fetchall()}

        for entry in budget_entries:
            pdv = entry['pdv']
            if pdv not in valid_pdvs:
                logger.warning(f"PDV no válido: {pdv}")
                continue
            for month, value in entry.items():
                if month == 'pdv' or not value:
                    continue
                month_num = int(month)
                # Convertir a float asegurando precisión completa
                if isinstance(value, str):
                    cleaned_value = value.replace('$', '').replace(',', '').strip()
                    presupuesto = float(cleaned_value)  # float soporta números grandes como 154809216
                else:
                    presupuesto = float(value)
                
                logger.debug(f"Guardando: PDV={pdv}, Mes={month_num}, Presupuesto={presupuesto}")
                query = """
                    INSERT INTO presupuesto (idcliente, pdv, año, mes, presupuestoventa)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (idcliente, pdv, año, mes)
                    DO UPDATE SET presupuestoventa = EXCLUDED.presupuestoventa
                """
                cursor.execute(query, (id_cliente, pdv, year, month_num, presupuesto))

        conn.commit()
        conn.close()
        return jsonify({"message": "Presupuesto creado/actualizado exitosamente"}), 200

    except Exception as e:
        conn.rollback()
        logger.error(f"Error al guardar presupuesto: {str(e)}")
        return jsonify({"error": str(e)}), 500
    

@app.route('/budget/sales', methods=['PUT'])
@jwt_required()
def update_budget_sales():
    # Reutilizamos el mismo endpoint que POST, ya que usa ON CONFLICT
    return create_budget_sales()


@app.route('/budget/sales/delete', methods=['DELETE'])
@jwt_required()
def delete_budget_sales():
    try:
        conn = psycopg2.connect(
            dbname=app.config['DB_NAME'], user=app.config['DB_USER'],
            password=app.config['DB_PASSWORD'], host=app.config['DB_HOST'],
            port=app.config['DB_PORT']
        )
        cursor = conn.cursor()

        # Reemplazo de user_id = 1 con autenticación
        user_id = get_jwt_identity()
        cursor.execute("SELECT IdCliente FROM Usuarios WHERE Id = %s", (user_id,))
        id_cliente_result = cursor.fetchone()
        if not id_cliente_result:
            conn.close()
            return jsonify({"error": "Usuario no encontrado"}), 404
        id_cliente = id_cliente_result[0]

        data = request.get_json()
        year = data.get('year')
        pdv = data.get('pdv')
        month = data.get('month')

        if not all([year, pdv, month]):
            return jsonify({"error": "Faltan parámetros: year, pdv, month"}), 400

        query = """
            DELETE FROM presupuesto
            WHERE idcliente = %s AND año = %s AND pdv = %s AND mes = %s
        """
        cursor.execute(query, (id_cliente, year, pdv, month))

        if cursor.rowcount == 0:
            return jsonify({"message": "No se encontró el registro para eliminar"}), 404

        conn.commit()
        conn.close()
        return jsonify({"message": "Presupuesto eliminado exitosamente"}), 200

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500


# Para el Dashboard de Presupuesto mensual
@app.route('/dashboard/monthly-performance', methods=['GET'])
@jwt_required()
def get_monthly_performance():
    try:
        conn = psycopg2.connect(
            dbname=app.config['DB_NAME'], user=app.config['DB_USER'],
            password=app.config['DB_PASSWORD'], host=app.config['DB_HOST'],
            port=app.config['DB_PORT']
        )
        cursor = conn.cursor()

        # Reemplazo de user_id = 1
        user_id = get_jwt_identity()
        cursor.execute("SELECT IdCliente FROM Usuarios WHERE Id = %s", (user_id,))
        id_cliente_result = cursor.fetchone()
        if not id_cliente_result:
            conn.close()
            return jsonify({"error": "Usuario no encontrado"}), 404
        id_cliente = id_cliente_result[0]

        # Parámetros de la solicitud
        year = request.args.get('year', type=int, default=2025)
        month = request.args.get('month', type=int, default=2)  # Febrero por defecto
        status = request.args.get('status', default='Activo', type=str)

        # Obtener PDVs según estatus
        pdv_query = "SELECT PDV FROM PuntosDeVenta WHERE IdCliente = %s"
        params = [id_cliente]
        if status != 'Todos':
            pdv_query += " AND Estado = %s"
            params.append(status)
        cursor.execute(pdv_query, params)
        all_pdvs = [row[0] for row in cursor.fetchall()]

        # Obtener presupuesto
        budget_query = """
            SELECT pdv, presupuestoventa
            FROM presupuesto
            WHERE idcliente = %s AND año = %s AND mes = %s
        """
        cursor.execute(budget_query, (id_cliente, year, month))
        budget_data = dict(cursor.fetchall())

        # Obtener ventas acumuladas del mes actual desde ventahistorica
        sales_query = """
            SELECT pdv, SUM(venta) as venta_acum
            FROM ventahistorica
            WHERE idcliente = %s AND año = %s AND mes = %s
            GROUP BY pdv
        """
        cursor.execute(sales_query, (id_cliente, year, month))
        sales_data = dict(cursor.fetchall())

        # Obtener ventas del año anterior desde ventahistorica
        prev_year = year - 1
        prev_sales_query = """
            SELECT pdv, SUM(venta) as venta_prev
            FROM ventahistorica
            WHERE idcliente = %s AND año = %s AND mes = %s
            GROUP BY pdv
        """
        cursor.execute(prev_sales_query, (id_cliente, prev_year, month))
        prev_sales_data = dict(cursor.fetchall())

        # Calcular métricas
        result = []
        totals = {
            'venta_acum': 0, 'venta_proy': 0, 'presupuesto': 0, 'cump_fecha': 0,
            'saldo': 0, 'venta_prev': 0, 'crecimiento_valor': 0
        }

        # Determinar días del mes según el mes seleccionado
        days_in_month = {1: 31, 2: 28, 3: 31, 4: 30, 5: 31, 6: 30, 7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31}
        # Ajustar para años bisiestos
        if month == 2 and year % 4 == 0 and (year % 100 != 0 or year % 400 == 0):
            days_in_month[2] = 29
        days = days_in_month.get(month, 30)  # Default a 30 si no está definido
        current_day = 16  # Dado que usas 16 de marzo como referencia

        for pdv in all_pdvs:
            venta_acum = round(float(sales_data.get(pdv, 0)), 0)
            presupuesto = round(float(budget_data.get(pdv, 0)), 0)
            venta_prev = round(float(prev_sales_data.get(pdv, 0)), 0)

            # Venta proyectada (simplificamos como acumulada por ahora)
            venta_proy = venta_acum

            # Cumplimiento a la fecha
            cump_fecha = round(presupuesto * (current_day / days), 0)

            # Porcentaje de cumplimiento
            cump_percent = round((venta_proy / presupuesto * 100), 2) if presupuesto > 0 else 0

            # Indicador visual
            if cump_percent >= 90:
                cump_icon = '✅'
            elif cump_percent >= 80:
                cump_icon = '⚠️'
            else:
                cump_icon = '❌'

            # Saldo para cumplir (ajustado para coincidir con Excel)
            saldo = round(venta_proy - presupuesto, 0)

            # Crecimiento
            crecimiento_percent = round(((venta_proy - venta_prev) / venta_prev * 100), 2) if venta_prev > 0 else 0
            crecimiento_valor = round(venta_proy - venta_prev, 0)

            # Agregar fila
            result.append({
                'pdv': pdv,
                'venta_acum': venta_acum,
                'venta_proy': venta_proy,
                'presupuesto': presupuesto,
                'cump_fecha': cump_fecha,
                'cump_percent': cump_percent,
                'cump_icon': cump_icon,
                'saldo': saldo,
                'venta_prev': venta_prev,
                'crecimiento_percent': crecimiento_percent,
                'crecimiento_valor': crecimiento_valor
            })

            # Sumar totales
            totals['venta_acum'] += venta_acum
            totals['venta_proy'] += venta_proy
            totals['presupuesto'] += presupuesto
            totals['cump_fecha'] += cump_fecha
            totals['saldo'] += saldo
            totals['venta_prev'] += venta_prev
            totals['crecimiento_valor'] += crecimiento_valor

        # Calcular porcentaje de cumplimiento total
        totals['cump_percent'] = round((totals['venta_proy'] / totals['presupuesto'] * 100), 2) if totals['presupuesto'] > 0 else 0
        totals['cump_icon'] = '✅' if totals['cump_percent'] >= 90 else '⚠️' if totals['cump_percent'] >= 80 else '❌'

        # Calcular crecimiento total
        totals['crecimiento_percent'] = round(((totals['venta_proy'] - totals['venta_prev']) / totals['venta_prev'] * 100), 2) if totals['venta_prev'] > 0 else 0

        response = {
            'year': year,
            'month': month,
            'data': result,
            'totals': totals
        }

        conn.close()
        return jsonify(response), 200

    except Exception as e:
        logger.error(f"Error en monthly-performance: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/dashboard/daily-sales', methods=['GET'])
@jwt_required()
def get_daily_sales():
    try:
        conn = psycopg2.connect(
            dbname=app.config['DB_NAME'], user=app.config['DB_USER'],
            password=app.config['DB_PASSWORD'], host=app.config['DB_HOST'],
            port=app.config['DB_PORT']
        )
        cursor = conn.cursor()

        # Reemplazo de user_id = 1 con autenticación
        user_id = get_jwt_identity()
        cursor.execute("SELECT IdCliente FROM Usuarios WHERE Id = %s", (user_id,))
        id_cliente_result = cursor.fetchone()
        if not id_cliente_result:
            conn.close()
            return jsonify({"error": "Usuario no encontrado"}), 404
        id_cliente = id_cliente_result[0]

        # Obtener parámetros de la solicitud
        year = request.args.get('year', type=int, default=2025)
        month = request.args.get('month', type=int, default=1)
        status = request.args.get('status', default='Activo', type=str)
        pdv = request.args.get('pdv', type=str)  # Nuevo parámetro para filtrar por PDV
        day = request.args.get('day', type=int)  # Nuevo parámetro para filtrar por día

        # Obtener PDVs según estatus
        pdv_query = "SELECT PDV, data2 FROM PuntosDeVenta WHERE IdCliente = %s"
        params = [id_cliente]
        if status != 'Todos':
            pdv_query += " AND Estado = %s"
            params.append(status)
        cursor.execute(pdv_query, params)
        pdv_data = cursor.fetchall()
        all_pdvs = [row[0] for row in pdv_data]
        logger.info(f"PDVs obtenidos: {all_pdvs}")

        # Crear un mapeo de nombres completos a nombres en ventahistoricahora (usando data2)
        pdv_mapping = {row[0]: row[1] for row in pdv_data}
        # Ajustar manualmente las diferencias conocidas
        pdv_mapping['ACA - Caja Portal'] = 'Portal del Prado'
        pdv_mapping['AQA - Caja la Castellana'] = 'La Castellana'
        logger.info(f"Mapeo de PDVs: {pdv_mapping}")

        # Obtener ventas diarias desde ventahistoricahora
        sales_query = """
            SELECT DATE(vh.fecha) as fecha, vh.almacen as pdv, SUM(vh.importe) as venta
            FROM ventahistoricahora vh
            WHERE vh.idcliente = %s
            AND EXTRACT(YEAR FROM vh.fecha) = %s
            AND EXTRACT(MONTH FROM vh.fecha) = %s
        """
        params = [id_cliente, year, month]

        # Filtrar por PDV si se especifica
        if pdv and pdv != 'Todos':
            short_name = pdv_mapping.get(pdv, pdv)
            sales_query += " AND vh.almacen = %s"
            params.append(short_name)

        # Filtrar por día si se especifica
        if day and day != 'Todos':
            sales_query += " AND EXTRACT(DAY FROM vh.fecha) = %s"
            params.append(day)

        sales_query += " GROUP BY DATE(vh.fecha), vh.almacen ORDER BY DATE(vh.fecha), vh.almacen"
        cursor.execute(sales_query, params)
        sales_data = cursor.fetchall()
        logger.info(f"Datos de ventahistoricahora: {sales_data}")

        # Obtener los días del mes
        days_in_month = {1: 31, 2: 28, 3: 31, 4: 30, 5: 31, 6: 30, 7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31}
        if month == 2 and year % 4 == 0 and (year % 100 != 0 or year % 400 == 0):
            days_in_month[2] = 29
        num_days = days_in_month.get(month, 30)

        # Crear una lista de fechas para el mes
        start_date = datetime(year, month, 1)
        if day and day != 'Todos':
            dates = [datetime(year, month, day).strftime('%Y-%m-%d')]
        else:
            dates = [(start_date + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(num_days)]

        # Estructurar los datos
        result = []
        totals_by_pdv = {pdv: 0 for pdv in all_pdvs}
        totals_by_day = {date: 0 for date in dates}

        for date in dates:
            date_obj = datetime.strptime(date, '%Y-%m-%d')
            day_name = date_obj.strftime('%A').lower()
            day_names_es = {
                'monday': 'lunes', 'tuesday': 'martes', 'wednesday': 'miércoles', 'thursday': 'jueves',
                'friday': 'viernes', 'saturday': 'sábado', 'sunday': 'domingo'
            }
            day_name_es = day_names_es.get(day_name, day_name)
            formatted_date = f"{day_name_es}, {date_obj.strftime('%d/%m/%Y')}"

            row = {'date': formatted_date}
            daily_total = 0

            for pdv in all_pdvs:
                short_name = pdv_mapping.get(pdv, pdv)
                sale = next((s[2] for s in sales_data if s[0].strftime('%Y-%m-%d') == date and s[1] == short_name), 0)
                row[pdv] = float(sale)
                daily_total += float(sale)
                totals_by_pdv[pdv] += float(sale)

            row['total'] = daily_total
            totals_by_day[date] = daily_total
            result.append(row)

        # Agregar fila de totales por PDV
        totals_row = {'date': 'TOTALES'}
        for pdv in all_pdvs:
            totals_row[pdv] = totals_by_pdv[pdv]
        totals_row['total'] = sum(totals_by_pdv.values())

        response = {
            'year': year,
            'month': month,
            'pdvs': all_pdvs,
            'data': result,
            'totals': totals_row
        }

        conn.close()
        return jsonify(response), 200

    except Exception as e:
        logger.error(f"Error en daily-sales: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/available-years', methods=['GET'])
@jwt_required()
def get_available_years():
    try:
        conn = psycopg2.connect(
            dbname=app.config['DB_NAME'], user=app.config['DB_USER'],
            password=app.config['DB_PASSWORD'], host=app.config['DB_HOST'],
            port=app.config['DB_PORT']
        )
        cursor = conn.cursor()

        # Reemplazo de user_id = 1 con autenticación
        user_id = get_jwt_identity()
        cursor.execute("SELECT IdCliente FROM Usuarios WHERE Id = %s", (user_id,))
        id_cliente_result = cursor.fetchone()
        if not id_cliente_result:
            conn.close()
            return jsonify({"error": "Usuario no encontrado"}), 404
        id_cliente = id_cliente_result[0]

        # Obtener años de ventahistoricahora
        cursor.execute("""
            SELECT DISTINCT EXTRACT(YEAR FROM fecha) as year
            FROM ventahistoricahora
            WHERE idcliente = %s
            ORDER BY year DESC
        """, (id_cliente,))
        years = [int(row[0]) for row in cursor.fetchall()]

        conn.close()
        return jsonify({"years": years}), 200

    except Exception as e:
        logger.error(f"Error en available-years: {str(e)}")
        return jsonify({"error": str(e)}), 500



@app.route('/dashboard/sales-by-time-slot', methods=['GET'])
@jwt_required()
def get_sales_by_time_slot():
    try:
        conn = psycopg2.connect(
            dbname=app.config['DB_NAME'], user=app.config['DB_USER'],
            password=app.config['DB_PASSWORD'], host=app.config['DB_HOST'],
            port=app.config['DB_PORT']
        )
        cursor = conn.cursor()

        # Reemplazo de user_id = 1 con autenticación
        user_id = get_jwt_identity()
        cursor.execute("SELECT IdCliente FROM Usuarios WHERE Id = %s", (user_id,))
        id_cliente_result = cursor.fetchone()
        if not id_cliente_result:
            conn.close()
            return jsonify({"error": "Usuario no encontrado"}), 404
        id_cliente = id_cliente_result[0]

        # Obtener parámetros de la solicitud
        year = request.args.get('year', type=int, default=2025)
        month = request.args.get('month', type=int, default=1)
        status = request.args.get('status', default='Activo', type=str)
        pdv = request.args.get('pdv', type=str)  # Nuevo parámetro para filtrar por PDV
        day = request.args.get('day', type=int)  # Nuevo parámetro para filtrar por día

        # Obtener PDVs según estatus
        pdv_query = "SELECT PDV, data2 FROM PuntosDeVenta WHERE IdCliente = %s"
        params = [id_cliente]
        if status != 'Todos':
            pdv_query += " AND Estado = %s"
            params.append(status)
        cursor.execute(pdv_query, params)
        pdv_data = cursor.fetchall()
        all_pdvs = [row[0] for row in pdv_data]
        logger.info(f"PDVs obtenidos: {all_pdvs}")

        # Crear un mapeo de nombres completos a nombres en ventahistoricahora (usando data2)
        pdv_mapping = {row[0]: row[1] for row in pdv_data}
        # Ajustar manualmente las diferencias conocidas
        pdv_mapping['ACA - Caja Portal'] = 'Portal del Prado'
        pdv_mapping['AQA - Caja la Castellana'] = 'La Castellana'
        logger.info(f"Mapeo de PDVs: {pdv_mapping}")

        # Obtener ventas por franja horaria desde ventahistoricahora
        sales_query = """
            SELECT vh.almacen, vh.rango_horarios, SUM(vh.importe) as venta
            FROM ventahistoricahora vh
            WHERE vh.idcliente = %s
            AND EXTRACT(YEAR FROM vh.fecha) = %s
            AND EXTRACT(MONTH FROM vh.fecha) = %s
        """
        params = [id_cliente, year, month]

        # Filtrar por PDV si se especifica
        if pdv and pdv != 'Todos':
            short_name = pdv_mapping.get(pdv, pdv)
            sales_query += " AND vh.almacen = %s"
            params.append(short_name)

        # Filtrar por día si se especifica
        if day and day != 'Todos':
            sales_query += " AND EXTRACT(DAY FROM vh.fecha) = %s"
            params.append(day)

        sales_query += " GROUP BY vh.almacen, vh.rango_horarios"
        cursor.execute(sales_query, params)
        sales_data = cursor.fetchall()
        logger.info(f"Datos de ventahistoricahora: {sales_data}")

        # Estructurar los datos
        result = []
        totals = {'morning_sales': 0, 'afternoon_sales': 0, 'night_sales': 0, 'total': 0}

        # Crear un diccionario para almacenar las ventas por PDV
        pdv_sales = {pdv: {'morning_sales': 0, 'afternoon_sales': 0, 'night_sales': 0, 'total': 0} for pdv in all_pdvs}

        # Procesar los datos de ventas
        for almacen, rango, venta in sales_data:
            # Encontrar el PDV correspondiente al almacén
            pdv = next((p for p, a in pdv_mapping.items() if a == almacen), None)
            if not pdv:
                continue  # Saltar si no se encuentra el PDV

            venta = float(venta)
            if rango.lower() == 'mañana':
                pdv_sales[pdv]['morning_sales'] = venta
                totals['morning_sales'] += venta
            elif rango.lower() == 'tarde':
                pdv_sales[pdv]['afternoon_sales'] = venta
                totals['afternoon_sales'] += venta
            elif rango.lower() == 'noche':
                pdv_sales[pdv]['night_sales'] = venta
                totals['night_sales'] += venta
            pdv_sales[pdv]['total'] += venta
            totals['total'] += venta

        # Calcular porcentajes y estructurar los datos para la respuesta
        for pdv in all_pdvs:
            row = {
                'pdv': pdv,
                'morning_sales': round(pdv_sales[pdv]['morning_sales'], 0),
                'morning_part': round((pdv_sales[pdv]['morning_sales'] / pdv_sales[pdv]['total'] * 100), 0) if pdv_sales[pdv]['total'] > 0 else 0,
                'afternoon_sales': round(pdv_sales[pdv]['afternoon_sales'], 0),
                'afternoon_part': round((pdv_sales[pdv]['afternoon_sales'] / pdv_sales[pdv]['total'] * 100), 0) if pdv_sales[pdv]['total'] > 0 else 0,
                'night_sales': round(pdv_sales[pdv]['night_sales'], 0),
                'night_part': round((pdv_sales[pdv]['night_sales'] / pdv_sales[pdv]['total'] * 100), 0) if pdv_sales[pdv]['total'] > 0 else 0,
                'total': round(pdv_sales[pdv]['total'], 0)
            }
            result.append(row)

        # Calcular porcentajes para los totales
        totals['morning_part'] = round((totals['morning_sales'] / totals['total'] * 100), 0) if totals['total'] > 0 else 0
        totals['afternoon_part'] = round((totals['afternoon_sales'] / totals['total'] * 100), 0) if totals['total'] > 0 else 0
        totals['night_part'] = round((totals['night_sales'] / totals['total'] * 100), 0) if totals['total'] > 0 else 0
        totals['pdv'] = 'TOTALES'

        response = {
            'year': year,
            'month': month,
            'pdvs': all_pdvs,
            'data': result,
            'totals': totals
        }

        conn.close()
        return jsonify(response), 200

    except Exception as e:
        logger.error(f"Error en sales-by-time-slot: {str(e)}")
        return jsonify({"error": str(e)}), 500



@app.route('/pdvs', methods=['GET'])
@jwt_required()
def get_pdvs():
    try:
        conn = psycopg2.connect(
            dbname=app.config['DB_NAME'], user=app.config['DB_USER'],
            password=app.config['DB_PASSWORD'], host=app.config['DB_HOST'],
            port=app.config['DB_PORT']
        )
        cursor = conn.cursor()

        # Reemplazo de user_id = 1 con autenticación
        user_id = get_jwt_identity()
        cursor.execute("SELECT IdCliente FROM Usuarios WHERE Id = %s", (user_id,))
        id_cliente_result = cursor.fetchone()
        if not id_cliente_result:
            conn.close()
            return jsonify({"error": "Usuario no encontrado"}), 404
        id_cliente = id_cliente_result[0]

        # Obtener todos los PDVs con su estado
        cursor.execute(
            "SELECT PDV, Estado FROM PuntosDeVenta WHERE IdCliente = %s ORDER BY PDV",
            (id_cliente,)
        )
        pdvs = cursor.fetchall()

        # Estructurar los datos
        result = [{'pdv': row[0], 'estado': row[1]} for row in pdvs]

        conn.close()
        return jsonify({'pdvs': result}), 200

    except Exception as e:
        logger.error(f"Error en get_pdvs: {str(e)}")
        return jsonify({"error": str(e)}), 500
    


@app.route('/dashboard/sales-by-payment-method', methods=['GET'])
@jwt_required()
def get_sales_by_payment_method():
    try:
        conn = psycopg2.connect(
            dbname=app.config['DB_NAME'], user=app.config['DB_USER'],
            password=app.config['DB_PASSWORD'], host=app.config['DB_HOST'],
            port=app.config['DB_PORT']
        )
        cursor = conn.cursor()

        # Reemplazo de user_id = 1 con autenticación
        user_id = get_jwt_identity()
        cursor.execute("SELECT IdCliente FROM Usuarios WHERE Id = %s", (user_id,))
        id_cliente_result = cursor.fetchone()
        if not id_cliente_result:
            conn.close()
            return jsonify({"error": "Usuario no encontrado"}), 404
        id_cliente = id_cliente_result[0]

        year = request.args.get('year', type=int, default=2025)
        month = request.args.get('month', type=int, default=1)  # Enero por defecto
        day = request.args.get('day', type=int, default=None)  # Día opcional
        status = request.args.get('status', default='Activo', type=str)
        pdv = request.args.get('pdv', default=None, type=str)  # PDV seleccionado

        # Log de los parámetros
        logger.info(f"Parámetros de la consulta: year={year}, month={month}, day={day}, status={status}, pdv={pdv}")

        # Obtener PDVs según estatus
        pdv_query = "SELECT PDV FROM PuntosDeVenta WHERE IdCliente = %s"
        params = [id_cliente]
        if status != 'Todos':
            pdv_query += " AND Estado = %s"
            params.append(status)
        cursor.execute(pdv_query, params)
        all_pdvs = [row[0] for row in cursor.fetchall()]
        logger.info(f"PDVs obtenidos: {all_pdvs}")

        # Si se seleccionó un PDV específico, filtrar solo ese PDV
        if pdv is not None:
            if pdv in all_pdvs:
                all_pdvs = [pdv]
            else:
                all_pdvs = []  # Si el PDV no está en la lista filtrada por estatus, no mostrar datos

        # Obtener datos de arqueocaja, incluyendo Vale
        sales_query = """
            SELECT ac.pdv,
                   SUM(ac.bonos) as bonos,
                   SUM(ac.efectivo) as efectivo,
                   SUM(ac.recibo_bancario) as recibo_bancario,
                   SUM(ac.tarjeta_debito) as tarjeta_debito,
                   SUM(ac.transferencia_bancaria) as transferencia_bancaria,
                   SUM(ac.vale) as vale,
                   SUM(ac.total) as total
            FROM arqueocaja ac
            WHERE ac.idcliente = %s
            AND EXTRACT(YEAR FROM ac.fecha) = %s
            AND EXTRACT(MONTH FROM ac.fecha) = %s
        """
        query_params = [id_cliente, year, month]

        # Agregar filtro por día si se proporciona
        if day is not None:
            sales_query += " AND EXTRACT(DAY FROM ac.fecha) = %s"
            query_params.append(day)

        # Agregar filtro por PDV si se seleccionó uno
        if pdv is not None:
            sales_query += " AND ac.pdv = %s"
            query_params.append(pdv)
        else:
            # Si no se seleccionó un PDV, usar el filtro por estatus
            if status != 'Todos':
                sales_query += " AND ac.pdv IN (SELECT PDV FROM PuntosDeVenta WHERE IdCliente = %s AND Estado = %s)"
                query_params.extend([id_cliente, status])

        sales_query += " GROUP BY ac.pdv"
        cursor.execute(sales_query, query_params)
        sales_data = cursor.fetchall()
        logger.info(f"Datos crudos de la consulta: {sales_data}")

        # Estructurar los datos
        result = []
        totals = {
            'bonos': 0,
            'efectivo': 0,
            'recibo_bancario': 0,
            'tarjeta_debito': 0,
            'transferencia_bancaria': 0,
            'vale': 0,
            'total': 0
        }

        # Crear un diccionario para almacenar las ventas por PDV
        pdv_sales = {pdv: {
            'bonos': 0,
            'efectivo': 0,
            'recibo_bancario': 0,
            'tarjeta_debito': 0,
            'transferencia_bancaria': 0,
            'vale': 0,
            'total': 0
        } for pdv in all_pdvs}

        # Procesar los datos de ventas
        for row in sales_data:
            pdv = row[0]
            if pdv not in all_pdvs:
                continue  # Saltar si el PDV no está en la lista filtrada por estatus
            pdv_sales[pdv]['bonos'] = float(row[1])
            pdv_sales[pdv]['efectivo'] = float(row[2])
            pdv_sales[pdv]['recibo_bancario'] = float(row[3])
            pdv_sales[pdv]['tarjeta_debito'] = float(row[4])
            pdv_sales[pdv]['transferencia_bancaria'] = float(row[5])
            pdv_sales[pdv]['vale'] = float(row[6])
            pdv_sales[pdv]['total'] = float(row[7])

            # Sumar a los totales
            totals['bonos'] += float(row[1])
            totals['efectivo'] += float(row[2])
            totals['recibo_bancario'] += float(row[3])
            totals['tarjeta_debito'] += float(row[4])
            totals['transferencia_bancaria'] += float(row[5])
            totals['vale'] += float(row[6])
            totals['total'] += float(row[7])

        # Estructurar los datos para la respuesta
        for pdv in all_pdvs:
            row = {
                'pdv': pdv,
                'bonos': round(pdv_sales[pdv]['bonos'], 0),
                'efectivo': round(pdv_sales[pdv]['efectivo'], 0),
                'recibo_bancario': round(pdv_sales[pdv]['recibo_bancario'], 0),
                'tarjeta_debito': round(pdv_sales[pdv]['tarjeta_debito'], 0),
                'transferencia_bancaria': round(pdv_sales[pdv]['transferencia_bancaria'], 0),
                'vale': round(pdv_sales[pdv]['vale'], 0),
                'total': round(pdv_sales[pdv]['total'], 0)
            }
            result.append(row)

        # Redondear los totales
        totals['bonos'] = round(totals['bonos'], 0)
        totals['efectivo'] = round(totals['efectivo'], 0)
        totals['recibo_bancario'] = round(totals['recibo_bancario'], 0)
        totals['tarjeta_debito'] = round(totals['tarjeta_debito'], 0)
        totals['transferencia_bancaria'] = round(totals['transferencia_bancaria'], 0)
        totals['vale'] = round(totals['vale'], 0)
        totals['total'] = round(totals['total'], 0)
        totals['pdv'] = 'TOTALES'

        response = {
            'year': year,
            'month': month,
            'day': day,
            'pdvs': all_pdvs,
            'data': result,
            'totals': totals
        }

        conn.close()
        return jsonify(response), 200

    except Exception as e:
        logger.error(f"Error en sales-by-payment-method: {str(e)}")
        return jsonify({"error": str(e)}), 500



@app.route('/dashboard/sales-by-product', methods=['GET'])
@jwt_required()
def get_sales_by_product():
    try:
        conn = psycopg2.connect(
            dbname=app.config['DB_NAME'], user=app.config['DB_USER'],
            password=app.config['DB_PASSWORD'], host=app.config['DB_HOST'],
            port=app.config['DB_PORT']
        )
        cursor = conn.cursor()

        # Obtener el id_cliente del usuario autenticado
        user_id = get_jwt_identity()
        cursor.execute("SELECT IdCliente FROM Usuarios WHERE Id = %s", (user_id,))
        id_cliente_result = cursor.fetchone()
        if not id_cliente_result:
            conn.close()
            return jsonify({"error": "Usuario no encontrado"}), 404
        id_cliente = id_cliente_result[0]

        # Obtener parámetros de la solicitud
        year = request.args.get('year', type=int, default=2025)
        month = request.args.get('month', type=int, default=1)  # Enero por defecto
        day = request.args.get('day', type=int, default=None)  # Día opcional
        status = request.args.get('status', default='Activo', type=str)
        pdv = request.args.get('pdv', default=None, type=str)  # PDV opcional

        # Obtener PDVs según estatus
        pdv_query = "SELECT PDV, data2 FROM PuntosDeVenta WHERE IdCliente = %s"
        params = [id_cliente]
        if status != 'Todos':
            pdv_query += " AND Estado = %s"
            params.append(status)
        cursor.execute(pdv_query, params)
        pdv_data = cursor.fetchall()
        all_pdvs = [row[0] for row in pdv_data]
        logger.info(f"PDVs obtenidos: {all_pdvs}")

        # Crear un mapeo de nombres completos a nombres en ventahistoricahora (usando data2)
        pdv_mapping = {row[0]: row[1] for row in pdv_data}
        # Ajustar manualmente las diferencias conocidas
        pdv_mapping['ACA - Caja Portal'] = 'Portal del Prado'
        pdv_mapping['AQA - Caja la Castellana'] = 'La Castellana'
        logger.info(f"Mapeo de PDVs: {pdv_mapping}")

        # Obtener datos de ventahistoricahora
        sales_query = """
            SELECT vh.descripcion, vh.almacen, SUM(vh.importe) as importe
            FROM ventahistoricahora vh
            WHERE vh.idcliente = %s
            AND EXTRACT(YEAR FROM vh.fecha) = %s
            AND EXTRACT(MONTH FROM vh.fecha) = %s
        """
        query_params = [id_cliente, year, month]

        # Añadir filtro por día si está presente
        if day is not None:
            sales_query += " AND EXTRACT(DAY FROM vh.fecha) = %s"
            query_params.append(day)

        # Añadir filtro por PDV si está presente
        if pdv is not None:
            sales_query += " AND vh.almacen = (SELECT data2 FROM PuntosDeVenta WHERE IdCliente = %s AND PDV = %s)"
            query_params.extend([id_cliente, pdv])
        # Si no se especifica un PDV, pero el estatus no es 'Todos', filtrar por los PDVs activos/inactivos
        elif status != 'Todos':
            sales_query += " AND vh.almacen IN (SELECT data2 FROM PuntosDeVenta WHERE IdCliente = %s AND Estado = %s)"
            query_params.extend([id_cliente, status])

        sales_query += " GROUP BY vh.descripcion, vh.almacen"
        cursor.execute(sales_query, query_params)
        sales_data = cursor.fetchall()
        logger.info(f"Datos de ventahistoricahora: {sales_data}")

        # Obtener lista de productos únicos (considerando los filtros aplicados)
        products_query = """
            SELECT DISTINCT vh.descripcion
            FROM ventahistoricahora vh
            WHERE vh.idcliente = %s
            AND EXTRACT(YEAR FROM vh.fecha) = %s
            AND EXTRACT(MONTH FROM vh.fecha) = %s
        """
        products_params = [id_cliente, year, month]

        if day is not None:
            products_query += " AND EXTRACT(DAY FROM vh.fecha) = %s"
            products_params.append(day)

        if pdv is not None:
            products_query += " AND vh.almacen = (SELECT data2 FROM PuntosDeVenta WHERE IdCliente = %s AND PDV = %s)"
            products_params.extend([id_cliente, pdv])
        elif status != 'Todos':
            products_query += " AND vh.almacen IN (SELECT data2 FROM PuntosDeVenta WHERE IdCliente = %s AND Estado = %s)"
            products_params.extend([id_cliente, status])

        cursor.execute(products_query, products_params)
        all_products = [row[0] for row in cursor.fetchall()]
        logger.info(f"Productos obtenidos: {all_products}")

        # Estructurar los datos
        result = []
        totals = {pdv: 0 for pdv in all_pdvs}
        totals['total'] = 0
        product_totals = {product: 0 for product in all_products}

        # Crear un diccionario para almacenar las ventas por producto y PDV
        sales_by_product = {product: {pdv: 0 for pdv in all_pdvs} for product in all_products}

        # Procesar los datos de ventas
        for descripcion, almacen, importe in sales_data:
            pdv_key = next((p for p, a in pdv_mapping.items() if a == almacen), None)
            if not pdv_key or pdv_key not in all_pdvs:
                continue  # Saltar si el PDV no está en la lista filtrada
            importe = float(importe)
            sales_by_product[descripcion][pdv_key] = importe
            product_totals[descripcion] += importe
            totals[pdv_key] += importe
            totals['total'] += importe

        # Estructurar los datos para la respuesta
        for product in all_products:
            row = {'product': product}
            for pdv in all_pdvs:
                row[pdv] = round(sales_by_product[product][pdv], 0)
            row['total'] = round(product_totals[product], 0)
            result.append(row)

        # Redondear los totales
        for pdv in all_pdvs:
            totals[pdv] = round(totals[pdv], 0)
        totals['total'] = round(totals['total'], 0)
        totals['product'] = 'TOTALES'

        response = {
            'year': year,
            'month': month,
            'pdvs': all_pdvs,
            'products': all_products,
            'data': result,
            'totals': totals
        }

        conn.close()
        return jsonify(response), 200

    except Exception as e:
        logger.error(f"Error en sales-by-product: {str(e)}")
        return jsonify({"error": str(e)}), 500



@app.route('/dashboard/sales-by-seller', methods=['GET'])
@jwt_required()
def get_sales_by_seller():
    try:
        conn = psycopg2.connect(
            dbname=app.config['DB_NAME'], user=app.config['DB_USER'],
            password=app.config['DB_PASSWORD'], host=app.config['DB_HOST'],
            port=app.config['DB_PORT']
        )
        cursor = conn.cursor()

        # Obtener el id_cliente del usuario autenticado
        user_id = get_jwt_identity()
        cursor.execute("SELECT IdCliente FROM Usuarios WHERE Id = %s", (user_id,))
        id_cliente_result = cursor.fetchone()
        if not id_cliente_result:
            conn.close()
            return jsonify({"error": "Usuario no encontrado"}), 404
        id_cliente = id_cliente_result[0]

        # Obtener parámetros de la solicitud
        year = request.args.get('year', type=int, default=2025)
        month = request.args.get('month', type=int, default=1)
        day = request.args.get('day', type=int, default=None)  # Día opcional
        status = request.args.get('status', default='Activo', type=str)

        # Obtener PDVs según estatus
        pdv_query = "SELECT PDV, data2 FROM PuntosDeVenta WHERE IdCliente = %s"
        params = [id_cliente]
        if status != 'Todos':
            pdv_query += " AND Estado = %s"
            params.append(status)
        cursor.execute(pdv_query, params)
        pdv_data = cursor.fetchall()
        all_pdvs = [row[0] for row in pdv_data]
        logger.info(f"PDVs obtenidos: {all_pdvs}")

        # Crear un mapeo de nombres completos a nombres en ventahistoricahora (usando data2)
        pdv_mapping = {row[0]: row[1] for row in pdv_data}
        # Ajustar manualmente las diferencias conocidas
        pdv_mapping['ACA - Caja Portal'] = 'Portal del Prado'
        pdv_mapping['AQA - Caja la Castellana'] = 'La Castellana'
        logger.info(f"Mapeo de PDVs: {pdv_mapping}")

        # Obtener datos de ventahistoricahora
        sales_query = """
            SELECT vh.vendedor, vh.almacen, SUM(vh.importe) as importe
            FROM ventahistoricahora vh
            WHERE vh.idcliente = %s
            AND EXTRACT(YEAR FROM vh.fecha) = %s
            AND EXTRACT(MONTH FROM vh.fecha) = %s
        """
        query_params = [id_cliente, year, month]

        # Añadir filtro por día si está presente
        if day is not None:
            sales_query += " AND EXTRACT(DAY FROM vh.fecha) = %s"
            query_params.append(day)

        if status != 'Todos':
            sales_query += " AND vh.almacen IN (SELECT data2 FROM PuntosDeVenta WHERE IdCliente = %s AND Estado = %s)"
            query_params.extend([id_cliente, status])

        sales_query += " GROUP BY vh.vendedor, vh.almacen"
        cursor.execute(sales_query, query_params)
        sales_data = cursor.fetchall()
        logger.info(f"Datos de ventahistoricahora: {sales_data}")

        # Obtener lista de asesores únicos
        sellers_query = """
            SELECT DISTINCT vh.vendedor
            FROM ventahistoricahora vh
            WHERE vh.idcliente = %s
            AND EXTRACT(YEAR FROM vh.fecha) = %s
            AND EXTRACT(MONTH FROM vh.fecha) = %s
        """
        sellers_params = [id_cliente, year, month]

        if day is not None:
            sellers_query += " AND EXTRACT(DAY FROM vh.fecha) = %s"
            sellers_params.append(day)

        if status != 'Todos':
            sellers_query += " AND vh.almacen IN (SELECT data2 FROM PuntosDeVenta WHERE IdCliente = %s AND Estado = %s)"
            sellers_params.extend([id_cliente, status])

        cursor.execute(sellers_query, sellers_params)
        all_sellers = [row[0] for row in cursor.fetchall()]
        logger.info(f"Asesores obtenidos: {all_sellers}")

        # Estructurar los datos
        result = []
        totals = {pdv: 0 for pdv in all_pdvs}
        totals['total'] = 0
        seller_totals = {seller: 0 for seller in all_sellers}

        # Crear un diccionario para almacenar las ventas por asesor y PDV
        sales_by_seller = {seller: {pdv: 0 for pdv in all_pdvs} for seller in all_sellers}

        # Procesar los datos de ventas
        for vendedor, almacen, importe in sales_data:
            pdv = next((p for p, a in pdv_mapping.items() if a == almacen), None)
            if not pdv or pdv not in all_pdvs:
                continue
            importe = float(importe)
            sales_by_seller[vendedor][pdv] = importe
            seller_totals[vendedor] += importe
            totals[pdv] += importe
            totals['total'] += importe

        # Estructurar los datos para la respuesta
        for seller in all_sellers:
            row = {'seller': seller}
            for pdv in all_pdvs:
                row[pdv] = round(sales_by_seller[seller][pdv], 0)
            row['total'] = round(seller_totals[seller], 0)
            result.append(row)

        # Redondear los totales
        for pdv in all_pdvs:
            totals[pdv] = round(totals[pdv], 0)
        totals['total'] = round(totals['total'], 0)
        totals['seller'] = 'TOTALES'

        response = {
            'year': year,
            'month': month,
            'pdvs': all_pdvs,
            'sellers': all_sellers,
            'data': result,
            'totals': totals
        }

        conn.close()
        return jsonify(response), 200

    except Exception as e:
        logger.error(f"Error en sales-by-seller: {str(e)}")
        return jsonify({"error": str(e)}), 500


# Nuevo endpoint para el dashboard "Venta Acumulada por PDV"

@app.route('/dashboard/accumulated-sales-by-pdv', methods=['GET'])
@jwt_required()
def accumulated_sales_by_pdv():
    try:
        conn = psycopg2.connect(
            dbname=app.config['DB_NAME'], user=app.config['DB_USER'],
            password=app.config['DB_PASSWORD'], host=app.config['DB_HOST'],
            port=app.config['DB_PORT']
        )
        cursor = conn.cursor()

        # Reemplazo de user_id = 1 con autenticación
        user_id = get_jwt_identity()
        cursor.execute("SELECT IdCliente FROM Usuarios WHERE Id = %s", (user_id,))
        id_cliente_result = cursor.fetchone()
        if not id_cliente_result:
            conn.close()
            return jsonify({"error": "Usuario no encontrado"}), 404
        id_cliente = id_cliente_result[0]

        year = request.args.get('year', type=int)
        month = request.args.get('month', type=int)
        pdv = request.args.get('pdv')
        end_date_str = request.args.get('end_date')  # Formato: 'YYYY-MM-DD'
        status = request.args.get('status', default='Activo')  # Nuevo parámetro

        if not year or not month or not pdv or not end_date_str:
            return jsonify({'error': 'Year, month, PDV, and end_date are required'}), 400

        # Convertir la fecha de fin al formato correcto
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        if end_date.month != month or end_date.year != year:
            return jsonify({'error': 'End date must be in the selected month and year'}), 400

        # Obtener el mapeo de PDVs con filtro de estatus
        query_pdv = """
            SELECT PDV, data2, estado
            FROM PuntosDeVenta
            WHERE IdCliente = %s
        """
        cursor.execute(query_pdv, (id_cliente,))
        pdv_data = cursor.fetchall()
        
        # Filtrar PDVs según el estatus
        pdv_filtered = []
        for row in pdv_data:
            pdv_status = row[2]  # Columna 'estado' (Activo/Inactivo)
            if status == 'Todos' or pdv_status == status:
                pdv_filtered.append(row)

        pdv_mapping = {row[0]: row[1] for row in pdv_filtered}
        logger.info(f"Mapeo de PDVs: {pdv_mapping}")

        if pdv not in pdv_mapping:
            return jsonify({'error': 'Invalid PDV'}), 400
        almacen = pdv_mapping[pdv]  # Obtener el valor de data2 correspondiente al pdv

        # Calcular días del mes hasta la fecha seleccionada y totales
        last_day_of_month = calendar.monthrange(year, month)[1]
        days_until_end_date = end_date.day
        total_days_in_month = last_day_of_month

        # --- Venta Acumulada hasta la Fecha Seleccionada ---
        query_sales = """
            SELECT SUM(importe) as total
            FROM ventahistoricahora
            WHERE idcliente = %s
            AND EXTRACT(YEAR FROM fecha) = %s
            AND EXTRACT(MONTH FROM fecha) = %s
            AND fecha <= %s
            AND almacen = %s
        """
        cursor.execute(query_sales, (id_cliente, year, month, end_date, almacen))
        result = cursor.fetchone()
        venta_acumulada = round(float(result[0] or 0), 0)

        # --- Venta Proyectada para el Mes Completo ---
        venta_proyectada = venta_acumulada

        # --- Presupuesto (desde la tabla presupuesto) ---
        query_budget = """
            SELECT presupuestoventa
            FROM presupuesto
            WHERE idcliente = %s
            AND pdv = %s
            AND año = %s
            AND mes = %s
        """
        cursor.execute(query_budget, (id_cliente, pdv, year, month))
        budget_result = cursor.fetchone()
        presupuesto = round(float(budget_result[0]) if budget_result and budget_result[0] is not None else 0, 0)

        # --- Cumplimiento a la Fecha del Presupuesto ---
        cumplimiento_a_la_fecha = round((presupuesto / total_days_in_month) * days_until_end_date if total_days_in_month > 0 else 0, 0)

        # --- % Cumplimiento Proyectado vs. Presupuesto ---
        cumplimiento_porcentual = round((venta_proyectada / presupuesto) * 100, 2) if presupuesto > 0 else 0

        # --- Saldo para Cumplir ---
        saldo_para_cumplir = round(venta_proyectada - presupuesto, 0)

        # --- Venta del Año Anterior (valor bruto de ventahistorica) ---
        year_previous = year - 1

        query_previous_year = """
            SELECT venta
            FROM ventahistorica
            WHERE idcliente = %s
            AND pdv = %s
            AND año = %s
            AND mes = %s
        """
        cursor.execute(query_previous_year, (id_cliente, pdv, year_previous, month))
        previous_year_result = cursor.fetchone()
        venta_ano_anterior = round(float(previous_year_result[0]) if previous_year_result and previous_year_result[0] is not None else 0, 0)

        # --- Crecimiento (%) y ($) Año Anterior vs. Actual ---
        crecimiento_porcentual = round(((venta_acumulada - venta_ano_anterior) / venta_ano_anterior) * 100, 2) if venta_ano_anterior > 0 else 0
        crecimiento_valor = round(venta_acumulada - venta_ano_anterior, 0)

        # --- Top 5 Productos Más Vendidos ---
        query_top_products = """
            SELECT descripcion, SUM(importe) as total
            FROM ventahistoricahora
            WHERE idcliente = %s
            AND EXTRACT(YEAR FROM fecha) = %s
            AND EXTRACT(MONTH FROM fecha) = %s
            AND fecha <= %s
            AND almacen = %s
            GROUP BY descripcion
            ORDER BY total DESC
            LIMIT 5
        """
        cursor.execute(query_top_products, (id_cliente, year, month, end_date, almacen))
        top_products_data = cursor.fetchall()
        top_products = [
            {'product': row[0], 'sales': round(float(row[1]), 0)}
            for row in top_products_data
        ]

        # --- Top 5 Asesores Más Vendidos ---
        query_top_sellers = """
            SELECT vendedor, SUM(importe) as total
            FROM ventahistoricahora
            WHERE idcliente = %s
            AND EXTRACT(YEAR FROM fecha) = %s
            AND EXTRACT(MONTH FROM fecha) = %s
            AND fecha <= %s
            AND almacen = %s
            GROUP BY vendedor
            ORDER BY total DESC
            LIMIT 5
        """
        cursor.execute(query_top_sellers, (id_cliente, year, month, end_date, almacen))
        top_sellers_data = cursor.fetchall()
        top_sellers = [
            {'seller': row[0], 'sales': round(float(row[1]), 0)}
            for row in top_sellers_data
        ]

        # --- Indicador Visual para el Cumplimiento ---
        if cumplimiento_porcentual >= 90:
            cumplimiento_icono = '✅'
        elif cumplimiento_porcentual >= 80:
            cumplimiento_icono = '⚠️'
        else:
            cumplimiento_icono = '❌'

        # Estructurar la respuesta
        response = {
            'year': year,
            'month': month,
            'pdv': pdv,
            'end_date': end_date_str,
            'venta_acumulada': venta_acumulada,
            'venta_proyectada': venta_proyectada,
            'presupuesto': presupuesto,
            'cumplimiento_a_la_fecha': cumplimiento_a_la_fecha,
            'cumplimiento_porcentual': cumplimiento_porcentual,
            'cumplimiento_icono': cumplimiento_icono,
            'saldo_para_cumplir': saldo_para_cumplir,
            'venta_ano_anterior': venta_ano_anterior,
            'crecimiento_porcentual': crecimiento_porcentual,
            'crecimiento_valor': crecimiento_valor,
            'top_products': top_products,
            'top_sellers': top_sellers,
        }

        conn.close()
        return jsonify(response), 200

    except Exception as e:
        logger.error(f"Error en accumulated-sales-by-pdv: {str(e)}")
        return jsonify({"error": str(e)}), 500


# Endpoint para obtener todos los puntos de venta (Read)
@app.route('/points-of-sale', methods=['GET'])
@jwt_required()
def get_points_of_sale():
    try:
        conn = psycopg2.connect(
            dbname=app.config['DB_NAME'], user=app.config['DB_USER'],
            password=app.config['DB_PASSWORD'], host=app.config['DB_HOST'],
            port=app.config['DB_PORT']
        )
        cursor = conn.cursor()

        # Reemplazo de user_id = 1 con autenticación
        user_id = get_jwt_identity()
        cursor.execute("SELECT IdCliente FROM Usuarios WHERE Id = %s", (user_id,))
        id_cliente_result = cursor.fetchone()
        if not id_cliente_result:
            conn.close()
            return jsonify({"error": "Usuario no encontrado"}), 404
        id_cliente = id_cliente_result[0]

        status = request.args.get('status', default='Todos', type=str)

        query = """
            SELECT id, idcliente, data1, data2, pdv, estado
            FROM PuntosDeVenta
            WHERE IdCliente = %s
        """
        params = [id_cliente]

        if status != 'Todos':
            query += " AND Estado = %s"
            params.append(status)

        query += " ORDER BY pdv"

        cursor.execute(query, params)
        rows = cursor.fetchall()

        # Estructurar los datos como una lista de diccionarios
        points = [
            {
                'id': row[0],
                'idcliente': row[1],
                'data1': row[2],
                'data2': row[3],
                'pdv': row[4],
                'estado': row[5]
            }
            for row in rows
        ]

        conn.close()
        return jsonify(points), 200

    except Exception as e:
        logger.error(f"Error en get_points_of_sale: {str(e)}")
        return jsonify({"error": str(e)}), 500


# Endpoint para crear un nuevo punto de venta (Create)
@app.route('/points-of-sale', methods=['POST'])
@jwt_required()
def create_point_of_sale():
    try:
        conn = psycopg2.connect(
            dbname=app.config['DB_NAME'], user=app.config['DB_USER'],
            password=app.config['DB_PASSWORD'], host=app.config['DB_HOST'],
            port=app.config['DB_PORT']
        )
        cursor = conn.cursor()

        # Reemplazo de user_id = 1 con autenticación
        user_id = get_jwt_identity()
        cursor.execute("SELECT IdCliente FROM Usuarios WHERE Id = %s", (user_id,))
        id_cliente_result = cursor.fetchone()
        if not id_cliente_result:
            conn.close()
            return jsonify({"error": "Usuario no encontrado"}), 404
        id_cliente = id_cliente_result[0]

        data = request.get_json()
        if not data or not all(key in data for key in ['idcliente', 'data1', 'data2', 'pdv', 'estado']):
            return jsonify({"error": "Faltan datos requeridos"}), 400

        # Validar que el estado sea "Activo" o "Inactivo"
        if data['estado'] not in ['Activo', 'Inactivo']:
            return jsonify({"error": "Estado inválido. Debe ser 'Activo' o 'Inactivo'"}), 400

        query = """
            INSERT INTO PuntosDeVenta (IdCliente, Data1, Data2, PDV, Estado)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id, idcliente, data1, data2, pdv, estado
        """
        params = (
            id_cliente,
            data['data1'],
            data['data2'],
            data['pdv'],
            data['estado']
        )

        cursor.execute(query, params)
        new_point = cursor.fetchone()

        conn.commit()
        conn.close()

        # Estructurar la respuesta
        response = {
            'id': new_point[0],
            'idcliente': new_point[1],
            'data1': new_point[2],
            'data2': new_point[3],
            'pdv': new_point[4],
            'estado': new_point[5]
        }

        return jsonify(response), 201

    except psycopg2.errors.UniqueViolation as e:
        conn.rollback()
        logger.error(f"Error en create_point_of_sale: {str(e)}")
        return jsonify({"error": "El nombre del PDV ya existe"}), 409
    except Exception as e:
        conn.rollback()
        logger.error(f"Error en create_point_of_sale: {str(e)}")
        return jsonify({"error": str(e)}), 500
    

# Endpoint para actualizar un punto de venta existente (Update)
@app.route('/points-of-sale/<int:id>', methods=['PUT'])
@jwt_required()
def update_point_of_sale(id):
    try:
        conn = psycopg2.connect(
            dbname=app.config['DB_NAME'], user=app.config['DB_USER'],
            password=app.config['DB_PASSWORD'], host=app.config['DB_HOST'],
            port=app.config['DB_PORT']
        )
        cursor = conn.cursor()

        # Reemplazo de user_id = 1 con autenticación
        user_id = get_jwt_identity()
        cursor.execute("SELECT IdCliente FROM Usuarios WHERE Id = %s", (user_id,))
        id_cliente_result = cursor.fetchone()
        if not id_cliente_result:
            conn.close()
            return jsonify({"error": "Usuario no encontrado"}), 404
        id_cliente = id_cliente_result[0]

        # Verificar que el punto de venta existe
        cursor.execute("SELECT id FROM PuntosDeVenta WHERE Id = %s AND IdCliente = %s", (id, id_cliente))
        if not cursor.fetchone():
            conn.close()
            return jsonify({"error": "Punto de venta no encontrado"}), 404

        data = request.get_json()
        if not data:
            return jsonify({"error": "No se proporcionaron datos para actualizar"}), 400

        # Validar que el estado sea "Activo" o "Inactivo"
        estado = data.get('estado')
        if estado and estado not in ['Activo', 'Inactivo']:
            return jsonify({"error": "Estado inválido. Debe ser 'Activo' o 'Inactivo'"}), 400

        # Construir la consulta de actualización dinámicamente
        updates = []
        params = []
        for key in ['data1', 'data2', 'pdv', 'estado']:
            if key in data:
                updates.append(f"{key} = %s")
                params.append(data[key])
        if not updates:
            return jsonify({"error": "No se proporcionaron campos para actualizar"}), 400

        params.append(id)
        params.append(id_cliente)

        query = f"""
            UPDATE PuntosDeVenta
            SET {', '.join(updates)}
            WHERE Id = %s AND IdCliente = %s
            RETURNING id, idcliente, data1, data2, pdv, estado
        """

        cursor.execute(query, params)
        updated_point = cursor.fetchone()

        conn.commit()
        conn.close()

        # Estructurar la respuesta
        response = {
            'id': updated_point[0],
            'idcliente': updated_point[1],
            'data1': updated_point[2],
            'data2': updated_point[3],
            'pdv': updated_point[4],
            'estado': updated_point[5]
        }

        return jsonify(response), 200

    except psycopg2.errors.UniqueViolation as e:
        conn.rollback()
        logger.error(f"Error en update_point_of_sale: {str(e)}")
        return jsonify({"error": "El nombre del PDV ya existe"}), 409
    except Exception as e:
        conn.rollback()
        logger.error(f"Error en update_point_of_sale: {str(e)}")
        return jsonify({"error": str(e)}), 500
    

# Endpoint para eliminar un punto de venta (Delete)
@app.route('/points-of-sale/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_point_of_sale(id):
    try:
        conn = psycopg2.connect(
            dbname=app.config['DB_NAME'], user=app.config['DB_USER'],
            password=app.config['DB_PASSWORD'], host=app.config['DB_HOST'],
            port=app.config['DB_PORT']
        )
        cursor = conn.cursor()

        # Reemplazo de user_id = 1 con autenticación
        user_id = get_jwt_identity()
        cursor.execute("SELECT IdCliente FROM Usuarios WHERE Id = %s", (user_id,))
        id_cliente_result = cursor.fetchone()
        if not id_cliente_result:
            conn.close()
            return jsonify({"error": "Usuario no encontrado"}), 404
        id_cliente = id_cliente_result[0]

        # Verificar que el punto de venta existe
        cursor.execute("SELECT id FROM PuntosDeVenta WHERE Id = %s AND IdCliente = %s", (id, id_cliente))
        if not cursor.fetchone():
            conn.close()
            return jsonify({"error": "Punto de venta no encontrado"}), 404

        # Eliminar el punto de venta
        cursor.execute("DELETE FROM PuntosDeVenta WHERE Id = %s AND IdCliente = %s", (id, id_cliente))

        conn.commit()
        conn.close()

        return jsonify({"message": "Punto de venta eliminado exitosamente"}), 200

    except psycopg2.errors.ForeignKeyViolation as e:
        conn.rollback()
        logger.error(f"Error en delete_point_of_sale: {str(e)}")
        return jsonify({"error": "No se puede eliminar este punto de venta porque está siendo usado en otras tablas"}), 409
    except Exception as e:
        conn.rollback()
        logger.error(f"Error en delete_point_of_sale: {str(e)}")
        return jsonify({"error": str(e)}), 500

#Endpoints relativos a Inventarios
#Endpoints relativos a Gestion de Productos y materiales
@app.route('/inventory/productos', methods=['GET', 'POST'])
@jwt_required()
def gestionar_productos_materiales():
    user_id = get_jwt_identity()
    claims = get_jwt()
    idcliente = claims.get('idcliente')

    if request.method == 'POST':
        if not has_permission(claims, 'inventario', 'gestion_productos', 'editar'):
            return jsonify({"error": "No autorizado"}), 403

        data = request.get_json()
        producto_existente = Producto.query.filter(
            ((Producto.codigo == data['codigo']) | (Producto.nombre.ilike(data['nombre']))),
            Producto.idcliente == idcliente
        ).first()

        if producto_existente:
            if producto_existente.codigo == data['codigo']:
                return jsonify({'error': 'Ya existe un producto con este código.'}), 400
            if producto_existente.nombre.lower() == data['nombre'].lower():
                return jsonify({'error': 'Ya existe un producto con este nombre.'}), 400

        try:
            if data['es_producto_compuesto']:
                nuevo_producto = Producto(
                    idcliente=idcliente,
                    codigo=data['codigo'],
                    nombre=data['nombre'],
                    es_producto_compuesto=True,
                    peso_total_gr=0,
                    peso_unidad_gr=0,
                    codigo_barras=data.get('codigo_barras'),
                    stock_minimo=data.get('stock_minimo')
                )
            else:
                nuevo_producto = Producto(
                    idcliente=idcliente,
                    codigo=data['codigo'],
                    nombre=data['nombre'],
                    es_producto_compuesto=False,
                    peso_total_gr=data['peso_total_gr'],
                    peso_unidad_gr=data['peso_unidad_gr'],
                    codigo_barras=data.get('codigo_barras'),
                    stock_minimo=data.get('stock_minimo')
                )

            db.session.add(nuevo_producto)
            db.session.commit()
            return jsonify({'message': 'Producto creado correctamente', 'id': nuevo_producto.id}), 201
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error al crear producto: {str(e)}")
            return jsonify({'error': 'Error al crear el producto'}), 500

    # GET
    if not has_permission(claims, 'inventario', 'gestion_productos', 'ver'):
        return jsonify({"error": "No autorizado"}), 403

    offset = int(request.args.get('offset', 0))
    limit = int(request.args.get('limit', 20))
    search_codigo = request.args.get('search_codigo', '')
    search_nombre = request.args.get('search_nombre', '')

    query = Producto.query.filter_by(idcliente=idcliente)
    if search_codigo:
        query = query.filter(Producto.codigo.ilike(f'%{search_codigo}%'))
    if search_nombre:
        query = query.filter(Producto.nombre.ilike(f'%{search_nombre}%'))

    total = query.count()
    productos = query.order_by(Producto.codigo.asc()).offset(offset).limit(limit).all()

    return jsonify({
        'productos': [{
            'id': p.id,
            'codigo': p.codigo,
            'nombre': p.nombre,
            'peso_total_gr': float(p.peso_total_gr) if p.peso_total_gr else None,
            'peso_unidad_gr': float(p.peso_unidad_gr) if p.peso_unidad_gr else None,
            'codigo_barras': p.codigo_barras,
            'es_producto_compuesto': p.es_producto_compuesto,
            'stock_minimo': p.stock_minimo
        } for p in productos],
        'total': total
    })

@app.route('/inventory/materiales-producto', methods=['POST'])
@jwt_required()
def agregar_material_a_producto_compuesto():
    claims = get_jwt()
    idcliente = claims.get('idcliente')
    if not has_permission(claims, 'inventario', 'gestion_productos', 'editar'):
        return jsonify({"error": "No autorizado"}), 403

    data = request.get_json()
    producto_compuesto_id = data.get('producto_compuesto_id')

    producto = Producto.query.filter_by(id=producto_compuesto_id, idcliente=idcliente).first()
    if not producto or not producto.es_producto_compuesto:
        return jsonify({'error': 'Producto compuesto no encontrado'}), 404

    try:
        # Eliminar materiales existentes para el producto compuesto
        MaterialProducto.query.filter_by(producto_compuesto_id=producto_compuesto_id).delete()
        
        # Agregar nuevos materiales
        for material in data['materiales']:
            cantidad = float(material['cantidad'])
            if cantidad <= 0:
                return jsonify({'error': f'La cantidad debe ser mayor a 0 para el producto base ID {material["producto_base_id"]}'}), 400
            
            producto_base = Producto.query.filter_by(id=material['producto_base_id'], idcliente=idcliente).first()
            if not producto_base:
                return jsonify({'error': f'Producto base con ID {material["producto_base_id"]} no encontrado'}), 400

            peso_unitario = producto_base.peso_unidad_gr if not producto_base.es_producto_compuesto else producto_base.peso_total_gr
            nuevo_material = MaterialProducto(
                idcliente=idcliente,  # Agregar idcliente explícitamente
                producto_compuesto_id=producto_compuesto_id,
                producto_base_id=material['producto_base_id'],
                cantidad=cantidad,
                peso_unitario=float(peso_unitario) if peso_unitario else 0
            )
            db.session.add(nuevo_material)

        db.session.commit()
        recalcular_peso_producto_compuesto(producto_compuesto_id)
        return jsonify({'message': 'Materiales actualizados correctamente'}), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error al guardar materiales: {str(e)}")
        return jsonify({'error': 'Error al guardar materiales'}), 500



@app.route('/inventory/productos/csv', methods=['POST'])
@jwt_required()
def cargar_productos_csv():
    claims = get_jwt()
    idcliente = claims.get('idcliente')
    if not has_permission(claims, 'inventario', 'gestion_productos', 'editar'):
        return jsonify({"error": "No autorizado"}), 403

    if 'file' not in request.files:
        return jsonify({'error': 'No se ha proporcionado un archivo'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Archivo no seleccionado'}), 400

    try:
        stream = TextIOWrapper(file.stream, encoding='utf-8')
        reader = csv.DictReader(stream)
        productos_data = list(reader)

        # Cargar productos existentes
        productos_existentes = Producto.query.filter_by(idcliente=idcliente).with_entities(Producto.codigo, Producto.nombre).all()
        codigos_existentes = {p.codigo for p in productos_existentes}
        nombres_existentes = {p.nombre for p in productos_existentes}

        # Cargar productos base
        codigos_base = set()
        for row in productos_data:
            if row.get('es_producto_compuesto', '').strip().lower() == "sí":
                cantidad_productos_str = row.get('cantidad_productos', '').strip()
                if cantidad_productos_str:
                    try:
                        cantidad_productos = int(cantidad_productos_str)
                        for i in range(1, cantidad_productos + 1):
                            codigo_base = row.get(f'codigo{i}', '').strip()
                            if codigo_base:
                                codigos_base.add(codigo_base)
                    except ValueError:
                        errores.append(f"⚠️ ERROR en código {row.get('codigo', '')}: 'cantidad_productos' debe ser un número entero.")
                        continue
        productos_base = Producto.query.filter(Producto.codigo.in_(codigos_base), Producto.idcliente == idcliente).all()
        productos_base_dict = {p.codigo: (p.id, p.peso_unidad_gr) for p in productos_base}

        productos = []
        materiales = []
        productos_creados = []
        productos_duplicados = []
        errores = []
        batch_size = 100
        productos_compuestos = []

        for row in productos_data:
            codigo = row.get('codigo', '').strip()
            nombre = row.get('nombre', '').strip()
            es_producto_compuesto = row.get('es_producto_compuesto', '').strip().lower() == "sí"
            cantidad_productos = int(row.get('cantidad_productos', '0')) if row.get('cantidad_productos', '').strip() else 0
            stock_minimo = row.get('stock_minimo', '').strip()
            try:
                stock_minimo = int(float(stock_minimo)) if stock_minimo else None
            except ValueError:
                errores.append(f"⚠️ ERROR en código {codigo}: El campo 'stock_minimo' debe ser un número entero o estar vacío.")
                continue

            # Validar duplicados
            if codigo in codigos_existentes:
                productos_duplicados.append(codigo)
                continue
            if nombre in nombres_existentes:
                productos_duplicados.append(codigo)
                continue

            if not codigo or not nombre:
                errores.append(f"⚠️ ERROR en código {codigo}: Los campos 'codigo' y 'nombre' son obligatorios.")
                continue

            if es_producto_compuesto:
                if row.get('peso_total_gr', '').strip() or row.get('peso_unidad_gr', '').strip():
                    errores.append(f"⚠️ ERROR en código {codigo}: No debe incluir peso_total_gr ni peso_unidad_gr.")
                    continue
                if cantidad_productos < 1:
                    errores.append(f"⚠️ ERROR en código {codigo}: Debe incluir al menos un producto base.")
                    continue

                materiales_row = []
                for i in range(1, cantidad_productos + 1):
                    codigo_base = row.get(f'codigo{i}', '').strip()
                    cantidad_base_str = row.get(f'cantidad{i}', '0').strip()
                    try:
                        cantidad_base = float(cantidad_base_str) if cantidad_base_str else 0.0
                    except ValueError:
                        errores.append(f"⚠️ ERROR en código {codigo}: La cantidad en 'cantidad{i}' no es válida.")
                        continue

                    if not codigo_base or cantidad_base <= 0:
                        errores.append(f"⚠️ ERROR en código {codigo}: La información en 'codigo{i}' o 'cantidad{i}' es inválida.")
                        continue

                    producto_base = productos_base_dict.get(codigo_base)
                    if not producto_base:
                        errores.append(f"⚠️ ERROR en código {codigo}: El producto base '{codigo_base}' no existe.")
                        continue

                    materiales_row.append({
                        'producto_base_id': producto_base[0],
                        'cantidad': cantidad_base,
                        'peso_unitario': producto_base[1]
                    })

                if materiales_row:
                    producto = Producto(
                        idcliente=idcliente,
                        codigo=codigo,
                        nombre=nombre,
                        peso_total_gr=0,
                        peso_unidad_gr=0,
                        codigo_barras=row.get('codigo_barras', None),
                        es_producto_compuesto=True,
                        stock_minimo=stock_minimo
                    )
                    productos.append(producto)
                    productos_compuestos.append({'producto': producto, 'materiales': materiales_row})
                    productos_creados.append(codigo)
            else:
                peso_total_gr = row.get('peso_total_gr', '').strip()
                peso_unidad_gr = row.get('peso_unidad_gr', '').strip()
                if not peso_total_gr or not peso_unidad_gr:
                    errores.append(f"⚠️ ERROR en código {codigo}: Debe incluir 'peso_total_gr' y 'peso_unidad_gr'.")
                    continue

                try:
                    peso_total_gr = float(peso_total_gr)
                    peso_unidad_gr = float(peso_unidad_gr)
                except ValueError:
                    errores.append(f"⚠️ ERROR en código {codigo}: 'peso_total_gr' y 'peso_unidad_gr' deben ser números válidos.")
                    continue

                producto = Producto(
                    idcliente=idcliente,
                    codigo=codigo,
                    nombre=nombre,
                    peso_total_gr=peso_total_gr,
                    peso_unidad_gr=peso_unidad_gr,
                    codigo_barras=row.get('codigo_barras', None),
                    es_producto_compuesto=False,
                    stock_minimo=stock_minimo
                )
                productos.append(producto)
                productos_creados.append(codigo)

            if len(productos) >= batch_size:
                db.session.bulk_save_objects(productos)
                db.session.commit()

                # Asignar materiales a productos compuestos
                for comp in productos_compuestos:
                    comp['producto'].id = next(p.id for p in productos if p.codigo == comp['producto'].codigo)
                    for m in comp['materiales']:
                        materiales.append(MaterialProducto(
                            producto_compuesto_id=comp['producto'].id,
                            producto_base_id=m['producto_base_id'],
                            cantidad=m['cantidad'],
                            peso_unitario=m['peso_unitario']
                        ))

                if materiales:
                    db.session.bulk_save_objects(materiales)
                    db.session.commit()

                productos = []
                materiales = []
                productos_compuestos = []

        if productos:
            db.session.bulk_save_objects(productos)
            db.session.commit()

            # Asignar materiales a productos compuestos
            for comp in productos_compuestos:
                comp['producto'].id = next(p.id for p in productos if p.codigo == comp['producto'].codigo)
                for m in comp['materiales']:
                    materiales.append(MaterialProducto(
                        producto_compuesto_id=comp['producto'].id,
                        producto_base_id=m['producto_base_id'],
                        cantidad=m['cantidad'],
                        peso_unitario=m['peso_unitario']
                    ))

            if materiales:
                db.session.bulk_save_objects(materiales)
                db.session.commit()

        # Calcular pesos en lote
        producto_ids = [p.id for p in Producto.query.filter(
            Producto.es_producto_compuesto == True,
            Producto.idcliente == idcliente,
            Producto.codigo.in_([p.codigo for p in productos if p.es_producto_compuesto])
        ).all()]
        if producto_ids:
            result = db.session.query(
                MaterialProducto.producto_compuesto_id,
                func.sum(MaterialProducto.cantidad * MaterialProducto.peso_unitario).label('peso_total')
            ).filter(
                MaterialProducto.producto_compuesto_id.in_(producto_ids)
            ).group_by(
                MaterialProducto.producto_compuesto_id
            ).all()
            pesos = {row.producto_compuesto_id: row.peso_total for row in result}
            for producto_id, peso_total in pesos.items():
                db.session.query(Producto).filter_by(id=producto_id).update({
                    'peso_total_gr': peso_total,
                    'peso_unidad_gr': peso_total
                })
            db.session.commit()

        return jsonify({
            'message': '✅ Carga de productos completada.',
            'productos_creados': productos_creados,
            'productos_duplicados': productos_duplicados,
            'errores': errores
        }), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error al cargar productos desde CSV: {str(e)}")
        return jsonify({'error': f'Ocurrió un error al cargar productos desde CSV: {str(e)}'}), 500


@app.route('/inventory/productos/actualizar-csv', methods=['POST'])
@jwt_required()
def actualizar_productos_csv():
    claims = get_jwt()
    idcliente = claims.get('idcliente')
    if not has_permission(claims, 'inventario', 'gestion_productos', 'editar'):
        return jsonify({"error": "No autorizado"}), 403

    if 'file' not in request.files:
        return jsonify({'error': 'No se ha proporcionado un archivo'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Archivo no seleccionado'}), 400

    try:
        stream = TextIOWrapper(file.stream, encoding='utf-8')
        reader = csv.DictReader(stream)
        productos_data = list(reader)

        # Cargar productos existentes
        productos_existentes = Producto.query.filter_by(idcliente=idcliente).with_entities(Producto.id, Producto.codigo, Producto.nombre).all()
        codigos_existentes = {p.codigo: p.id for p in productos_existentes}
        nombres_existentes = {p.nombre: p.id for p in productos_existentes}

        # Cargar productos base para validar materiales
        codigos_base = set()
        for row in productos_data:
            if row.get('es_producto_compuesto', '').strip().lower() == "sí":
                cantidad_productos_str = row.get('cantidad_productos', '').strip()
                if cantidad_productos_str:
                    try:
                        cantidad_productos = int(cantidad_productos_str)
                        for i in range(1, cantidad_productos + 1):
                            codigo_base = row.get(f'codigo{i}', '').strip()
                            if codigo_base:
                                codigos_base.add(codigo_base)
                    except ValueError:
                        errores.append(f"⚠️ ERROR en código {row.get('codigo', '')}: 'cantidad_productos' debe ser un número entero.")
                        continue
        productos_base = Producto.query.filter(Producto.codigo.in_(codigos_base), Producto.idcliente == idcliente).all()
        productos_base_dict = {p.codigo: (p.id, p.peso_unidad_gr) for p in productos_base}

        productos_actualizados = []
        productos_no_encontrados = []
        errores = []
        batch_size = 100
        materiales_actualizados = []

        for row in productos_data:
            codigo = row.get('codigo', '').strip()
            if not codigo:
                errores.append("⚠️ ERROR: El campo 'codigo' es obligatorio.")
                continue

            # Verificar si el producto existe
            producto_id = codigos_existentes.get(codigo)
            if not producto_id:
                productos_no_encontrados.append(codigo)
                continue

            nombre = row.get('nombre', '').strip()
            es_producto_compuesto = row.get('es_producto_compuesto', '').strip().lower() == "sí"
            stock_minimo = row.get('stock_minimo', '').strip()
            codigo_barras = row.get('codigo_barras', '').strip() or None

            # Validar stock_minimo
            try:
                stock_minimo = int(float(stock_minimo)) if stock_minimo else None
            except ValueError:
                errores.append(f"⚠️ ERROR en código {codigo}: El campo 'stock_minimo' debe ser un número entero o estar vacío.")
                continue

            # Validar nombre único (excluyendo el producto actual)
            if nombre and nombre in nombres_existentes and nombres_existentes[nombre] != producto_id:
                errores.append(f"⚠️ ERROR en código {codigo}: El nombre '{nombre}' ya está en uso por otro producto.")
                continue

            # Validar campos según tipo de producto
            if es_producto_compuesto:
                if row.get('peso_total_gr', '').strip() or row.get('peso_unidad_gr', '').strip():
                    errores.append(f"⚠️ ERROR en código {codigo}: Productos compuestos no deben incluir 'peso_total_gr' ni 'peso_unidad_gr'.")
                    continue
                
                # Manejar cantidad_productos solo si está presente
                cantidad_productos_str = row.get('cantidad_productos', '').strip()
                materiales_row = []
                if cantidad_productos_str:
                    try:
                        cantidad_productos = int(cantidad_productos_str)
                        if cantidad_productos < 1:
                            errores.append(f"⚠️ ERROR en código {codigo}: 'cantidad_productos' debe ser mayor a 0 si se especifica.")
                            continue

                        for i in range(1, cantidad_productos + 1):
                            codigo_base = row.get(f'codigo{i}', '').strip()
                            cantidad_base_str = row.get(f'cantidad{i}', '').strip()
                            if not codigo_base or not cantidad_base_str:
                                errores.append(f"⚠️ ERROR en código {codigo}: 'codigo{i}' y 'cantidad{i}' son obligatorios si se especifica 'cantidad_productos'.")
                                continue
                            try:
                                cantidad_base = float(cantidad_base_str)
                                if cantidad_base <= 0:
                                    errores.append(f"⚠️ ERROR en código {codigo}: La cantidad en 'cantidad{i}' debe ser mayor a 0.")
                                    continue
                            except ValueError:
                                errores.append(f"⚠️ ERROR en código {codigo}: La cantidad en 'cantidad{i}' no es válida.")
                                continue

                            producto_base = productos_base_dict.get(codigo_base)
                            if not producto_base:
                                errores.append(f"⚠️ ERROR en código {codigo}: El producto base '{codigo_base}' no existe.")
                                continue

                            materiales_row.append({
                                'producto_base_id': producto_base[0],
                                'cantidad': cantidad_base,
                                'peso_unitario': producto_base[1]
                            })
                    except ValueError:
                        errores.append(f"⚠️ ERROR en código {codigo}: 'cantidad_productos' debe ser un número entero.")
                        continue

            else:
                peso_total_gr = row.get('peso_total_gr', '').strip()
                peso_unidad_gr = row.get('peso_unidad_gr', '').strip()
                try:
                    peso_total_gr = float(peso_total_gr) if peso_total_gr else None
                    peso_unidad_gr = float(peso_unidad_gr) if peso_unidad_gr else None
                except ValueError:
                    errores.append(f"⚠️ ERROR en código {codigo}: 'peso_total_gr' y 'peso_unidad_gr' deben ser números válidos.")
                    continue

                if (peso_total_gr is not None or peso_unidad_gr is not None) and (peso_total_gr is None or peso_unidad_gr is None):
                    errores.append(f"⚠️ ERROR en código {codigo}: Productos base deben incluir ambos 'peso_total_gr' y 'peso_unidad_gr' si se especifica alguno.")
                    continue

            # Preparar datos para actualización
            update_data = {}
            if nombre:
                update_data['nombre'] = nombre
            if codigo_barras is not None:
                update_data['codigo_barras'] = codigo_barras
            update_data['es_producto_compuesto'] = es_producto_compuesto
            if stock_minimo is not None:
                update_data['stock_minimo'] = stock_minimo
            if not es_producto_compuesto:
                if peso_total_gr is not None:
                    update_data['peso_total_gr'] = peso_total_gr
                if peso_unidad_gr is not None:
                    update_data['peso_unidad_gr'] = peso_unidad_gr
            else:
                update_data['peso_total_gr'] = 0
                update_data['peso_unidad_gr'] = 0

            if update_data:
                db.session.query(Producto).filter_by(id=producto_id).update(update_data)

            # Actualizar materiales solo si se proporcionaron nuevos
            if es_producto_compuesto and materiales_row:
                db.session.query(MaterialProducto).filter_by(producto_compuesto_id=producto_id).delete()
                for material in materiales_row:
                    materiales_actualizados.append(MaterialProducto(
                        producto_compuesto_id=producto_id,
                        producto_base_id=material['producto_base_id'],
                        cantidad=material['cantidad'],
                        peso_unitario=material['peso_unitario']
                    ))

            productos_actualizados.append(codigo)

            if len(productos_actualizados) % batch_size == 0:
                db.session.commit()
                if materiales_actualizados:
                    db.session.bulk_save_objects(materiales_actualizados)
                    db.session.commit()
                materiales_actualizados = []

        # Commit final
        db.session.commit()
        if materiales_actualizados:
            db.session.bulk_save_objects(materiales_actualizados)
            db.session.commit()

        # Recalcular pesos para productos compuestos
        producto_ids = [codigos_existentes[codigo] for codigo in productos_actualizados
                        if Producto.query.get(codigos_existentes[codigo]).es_producto_compuesto]
        if producto_ids:
            for producto_id in producto_ids:
                recalcular_peso_producto_compuesto(producto_id)

        return jsonify({
            'message': '✅ Actualización de productos completada.',
            'productos_actualizados': productos_actualizados,
            'productos_no_encontrados': productos_no_encontrados,
            'errores': errores
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error al actualizar productos desde CSV: {str(e)}")
        return jsonify({'error': f'Ocurrió un error al actualizar productos desde CSV: {str(e)}'}), 500


@app.route('/inventory/productos/<int:producto_id>', methods=['PUT'])
@jwt_required()
def actualizar_producto(producto_id):
    claims = get_jwt()
    idcliente = claims.get('idcliente')
    if not has_permission(claims, 'inventario', 'gestion_productos', 'editar'):
        return jsonify({"error": "No autorizado"}), 403

    producto = Producto.query.filter_by(id=producto_id, idcliente=idcliente).first()
    if not producto:
        return jsonify({'error': 'Producto no encontrado'}), 404

    data = request.get_json()
    try:
        producto.codigo = data.get('codigo', producto.codigo)
        producto.nombre = data.get('nombre', producto.nombre)
        producto.peso_total_gr = data.get('peso_total_gr', producto.peso_total_gr)
        producto.peso_unidad_gr = data.get('peso_unidad_gr', producto.peso_unidad_gr)
        producto.codigo_barras = data.get('codigo_barras', producto.codigo_barras)
        producto.es_producto_compuesto = data.get('es_producto_compuesto', producto.es_producto_compuesto)
        producto.stock_minimo = data.get('stock_minimo', producto.stock_minimo)

        db.session.commit()
        if producto.es_producto_compuesto:
            recalcular_peso_producto_compuesto(producto_id)
        return jsonify({'message': 'Producto actualizado correctamente'}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error al actualizar producto: {str(e)}")
        return jsonify({'error': 'Error al actualizar el producto'}), 500

@app.route('/inventory/productos/<int:producto_id>', methods=['DELETE'])
@jwt_required()
def eliminar_producto(producto_id):
    claims = get_jwt()
    idcliente = claims.get('idcliente')
    if not has_permission(claims, 'inventario', 'gestion_productos', 'editar'):
        return jsonify({"error": "No autorizado"}), 403

    producto = Producto.query.filter_by(id=producto_id, idcliente=idcliente).first()
    if not producto:
        return jsonify({'message': 'Producto no encontrado'}), 404

    try:
        db.session.delete(producto)
        db.session.commit()
        return jsonify({'message': 'Producto eliminado correctamente'}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error al eliminar producto: {str(e)}")
        return jsonify({'error': 'Error al eliminar el producto'}), 500


@app.route('/inventory/materiales-producto/<int:producto_id>', methods=['GET'])
@jwt_required()
def obtener_materiales_producto(producto_id):
    claims = get_jwt()
    idcliente = claims.get('idcliente')
    if not has_permission(claims, 'inventario', 'gestion_productos', 'ver'):
        return jsonify({"error": "No autorizado"}), 403

    # Verificar que el producto existe y es compuesto
    producto = Producto.query.filter_by(id=producto_id, idcliente=idcliente).first()
    if not producto:
        return jsonify({'error': 'Producto no encontrado'}), 404
    if not producto.es_producto_compuesto:
        return jsonify({'error': 'El producto no es un producto compuesto'}), 400

    try:
        # Consultar materiales con información del producto base
        materiales = db.session.query(MaterialProducto, Producto.codigo, Producto.nombre).\
            join(Producto, MaterialProducto.producto_base_id == Producto.id).\
            filter(
                MaterialProducto.producto_compuesto_id == producto_id,
                MaterialProducto.idcliente == idcliente
            ).all()

        return jsonify({
            "materiales": [{
                "id": m.MaterialProducto.id,
                "producto_base_id": m.MaterialProducto.producto_base_id,
                "producto_base_codigo": m.codigo,
                "producto_base_nombre": m.nombre,
                "cantidad": float(m.MaterialProducto.cantidad),
                "peso_unitario": float(m.MaterialProducto.peso_unitario),
                "peso_total": float(m.MaterialProducto.cantidad * m.MaterialProducto.peso_unitario)
            } for m in materiales]
        }), 200

    except Exception as e:
        logger.error(f"Error al obtener materiales: {str(e)}")
        return jsonify({'error': f'Error al obtener materiales: {str(e)}'}), 500




@app.route('/inventory/materiales-producto/<int:material_id>', methods=['DELETE'])
@jwt_required()
def eliminar_material(material_id):
    claims = get_jwt()
    idcliente = claims.get('idcliente')
    if not has_permission(claims, 'inventario', 'gestion_productos', 'editar'):
        return jsonify({"error": "No autorizado"}), 403

    material = MaterialProducto.query.filter_by(id=material_id).join(
        Producto, MaterialProducto.producto_compuesto_id == Producto.id
    ).filter(Producto.idcliente == idcliente).first()
    if not material:
        return jsonify({'message': 'Material no encontrado'}), 404

    try:
        producto_compuesto_id = material.producto_compuesto_id
        db.session.delete(material)
        db.session.commit()
        recalcular_peso_producto_compuesto(producto_compuesto_id)
        return jsonify({'message': 'Material eliminado correctamente y pesos actualizados.'}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error al eliminar material: {str(e)}")
        return jsonify({'error': 'Error al eliminar el material'}), 500


# ENDPOINTS DEL MODULO DE BODEGAS
@app.route('/inventory/bodegas', methods=['GET', 'POST'])
@jwt_required()
def gestionar_bodegas():
    claims = get_jwt()
    idcliente = claims.get('idcliente')

    if request.method == 'POST':
        if not has_permission(claims, 'inventario', 'bodegas', 'editar'):
            return jsonify({"error": "No autorizado"}), 403
        
        data = request.get_json()
        nueva_bodega = Bodega(
            nombre=data['nombre'],
            idcliente=idcliente  # Asignar el idcliente del usuario autenticado
        )
        db.session.add(nueva_bodega)
        db.session.commit()
        return jsonify({'message': 'Almacén creado correctamente', 'id': nueva_bodega.id}), 201

    if not has_permission(claims, 'inventario', 'bodegas', 'ver'):
        return jsonify({"error": "No autorizado"}), 403
    
    bodegas = Bodega.query.filter_by(idcliente=idcliente).all()
    return jsonify([{'id': b.id, 'nombre': b.nombre} for b in bodegas])



@app.route('/inventory/bodegas/<int:id>', methods=['PUT', 'DELETE'])
@jwt_required()
def modificar_bodega(id):
    claims = get_jwt()
    idcliente = claims.get('idcliente')
    bodega = Bodega.query.filter_by(id=id, idcliente=idcliente).first_or_404()  # Filtrar por idcliente

    if request.method == 'PUT':
        if not has_permission(claims, 'inventario', 'bodegas', 'editar'):
            return jsonify({"error": "No autorizado"}), 403
        
        data = request.get_json()
        bodega.nombre = data['nombre']
        db.session.commit()
        return jsonify({'message': 'Almacén actualizado correctamente'})

    if request.method == 'DELETE':
        if not has_permission(claims, 'inventario', 'bodegas', 'editar'):
            return jsonify({"error": "No autorizado"}), 403
        
        db.session.delete(bodega)
        db.session.commit()
        return jsonify({'message': 'Almacén eliminado correctamente'})


# Endpoints de la pagina de Cargar compas de Producto
@app.route('/inventory/cargar-compras', methods=['POST'])
@jwt_required()
def cargar_compras():
    claims = get_jwt()
    idcliente = claims.get('idcliente')

    if not has_permission(claims, 'inventario', 'compras', 'editar'):
        return jsonify({'error': 'No autorizado'}), 403

    if 'file' not in request.files:
        return jsonify({'message': 'No se encontró el archivo en la solicitud'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'message': 'No se seleccionó ningún archivo'}), 400

    stream = TextIOWrapper(file.stream, encoding='utf-8')
    reader = csv.DictReader(stream)
    
    expected_columns = ['factura', 'codigo', 'nombre', 'cantidad', 'bodega', 'contenedor', 'fecha_ingreso', 'costo_unitario']
    missing_columns = [col for col in expected_columns if col not in reader.fieldnames]
    if missing_columns:
        return jsonify({'message': f'Faltan las columnas: {", ".join(missing_columns)}'}), 400

    errores = []
    for index, row in enumerate(reader, start=1):
        try:
            factura = row.get('factura', '').strip()
            if not factura:
                errores.append(f"Fila {index}: El número de factura es obligatorio y no puede estar vacío.")
                continue

            codigo = row['codigo'].strip()
            cantidad = int(row['cantidad'])
            bodega = row['bodega'].strip()
            contenedor = row.get('contenedor', '').strip()
            fecha_ingreso = row.get('fecha_ingreso', None)
            costo_unitario = float(row.get('costo_unitario', 0))

            if fecha_ingreso:
                fecha_ingreso = datetime.strptime(fecha_ingreso, '%Y-%m-%d %H:%M:%S')
            else:
                fecha_ingreso = obtener_hora_colombia()

            producto = Producto.query.filter_by(codigo=codigo, idcliente=idcliente).first()
            if not producto:
                errores.append(f"Fila {index}: Producto con código {codigo} no encontrado.")
                continue

            bodega_obj = Bodega.query.filter_by(nombre=bodega, idcliente=idcliente).first()
            if not bodega_obj:
                errores.append(f"Fila {index}: Bodega con nombre {bodega} no encontrada.")
                continue

            inventario_previo = InventarioBodega.query.filter_by(producto_id=producto.id, idcliente=idcliente).first()
            descripcion = f"Ingreso de nueva mercancía con Factura de compra {factura}" if inventario_previo else f"Cargue inicial con Factura de compra {factura}"

            # Registrar en inventario_bodega
            inventario = InventarioBodega.query.filter_by(producto_id=producto.id, bodega_id=bodega_obj.id, idcliente=idcliente).first()
            if not inventario:
                inventario = InventarioBodega(
                    idcliente=idcliente,
                    producto_id=producto.id,
                    bodega_id=bodega_obj.id,
                    cantidad=cantidad,
                    factura=factura,
                    contenedor=contenedor,
                    fecha_ingreso=fecha_ingreso,
                    costo_unitario=costo_unitario,
                    costo_total=cantidad * costo_unitario
                )
                db.session.add(inventario)
            else:
                costo_total_nuevo = (float(inventario.cantidad) * float(inventario.costo_unitario)) + (cantidad * costo_unitario)
                inventario.cantidad += cantidad
                inventario.costo_unitario = costo_total_nuevo / inventario.cantidad if inventario.cantidad > 0 else costo_unitario
                inventario.costo_total = inventario.cantidad * inventario.costo_unitario
                inventario.factura = factura
                inventario.contenedor = contenedor
                inventario.fecha_ingreso = fecha_ingreso

            # Actualizar o crear en estado_inventario
            estado_inv = EstadoInventario.query.filter_by(
                idcliente=idcliente,
                producto_id=producto.id,
                bodega_id=bodega_obj.id
            ).first()
            if not estado_inv:
                estado_inv = EstadoInventario(
                    idcliente=idcliente,
                    producto_id=producto.id,
                    bodega_id=bodega_obj.id,
                    cantidad=0,
                    ultima_actualizacion=fecha_ingreso,
                    costo_unitario=costo_unitario,
                    costo_total=0
                )
                db.session.add(estado_inv)
            estado_inv.cantidad += cantidad
            estado_inv.costo_unitario = costo_unitario  # O promedio ponderado si prefieres
            estado_inv.costo_total = estado_inv.cantidad * estado_inv.costo_unitario
            estado_inv.ultima_actualizacion = fecha_ingreso

            # Verificar si el movimiento ya existe
            movimiento_existente = RegistroMovimientos.query.filter_by(
                idcliente=idcliente,
                producto_id=producto.id,
                bodega_destino_id=bodega_obj.id,
                tipo_movimiento='ENTRADA',
                descripcion=descripcion
            ).first()
            if movimiento_existente:
                errores.append(f"Fila {index}: La factura {factura} ya fue procesada para el producto {codigo} en {bodega}.")
                continue

            # Generar nuevo consecutivo
            ultimo_consecutivo = db.session.query(
                db.func.max(db.cast(RegistroMovimientos.consecutivo, db.String))
            ).filter_by(idcliente=idcliente).scalar() or "T00000"
            nuevo_consecutivo = f"T{int(ultimo_consecutivo[1:]) + 1:05d}"

            # Registrar en registro_movimientos
            nuevo_movimiento = RegistroMovimientos(
                idcliente=idcliente,
                consecutivo=nuevo_consecutivo,
                producto_id=producto.id,
                tipo_movimiento='ENTRADA',
                cantidad=cantidad,
                bodega_destino_id=bodega_obj.id,
                fecha=fecha_ingreso,
                descripcion=descripcion,
                costo_unitario=costo_unitario,
                costo_total=cantidad * costo_unitario
            )
            db.session.add(nuevo_movimiento)

            # Registrar en kardex
            kardex_entry = Kardex(
                idcliente=idcliente,
                producto_id=producto.id,
                bodega_destino_id=bodega_obj.id,
                fecha=fecha_ingreso,
                tipo_movimiento='ENTRADA',
                cantidad=cantidad,
                costo_unitario=costo_unitario,
                costo_total=cantidad * costo_unitario,
                saldo_cantidad=estado_inv.cantidad,  # Usar cantidad de estado_inventario
                saldo_costo_unitario=estado_inv.costo_unitario,
                saldo_costo_total=estado_inv.costo_total,  # Corregido
                referencia=descripcion
            )
            db.session.add(kardex_entry)

            db.session.commit()

        except Exception as e:
            db.session.rollback()
            errores.append(f"Fila {index}: Error al procesar la fila ({str(e)})")
    
    if errores:
        return jsonify({'message': 'Errores al procesar el archivo', 'errors': errores}), 400

    return jsonify({'message': 'Compras cargadas correctamente'}), 201


@app.route('/inventory/facturas', methods=['GET'])
@jwt_required()
def listar_facturas():
    claims = get_jwt()
    idcliente = claims.get('idcliente')

    if not has_permission(claims, 'inventario', 'compras', 'ver'):
        return jsonify({'error': 'No autorizado'}), 403

    try:
        facturas = db.session.query(InventarioBodega.factura).filter_by(idcliente=idcliente).distinct().all()
        facturas_lista = [factura[0] for factura in facturas if factura[0]]
        return jsonify({'facturas': facturas_lista})
    except Exception as e:
        return jsonify({'error': 'Error al listar facturas'}), 500

@app.route('/inventory/consultar-facturas', methods=['GET'])
@jwt_required()
def consultar_facturas():
    claims = get_jwt()
    idcliente = claims.get('idcliente')

    if not has_permission(claims, 'inventario', 'compras', 'ver'):
        return jsonify({'error': 'No autorizado'}), 403

    try:
        factura = request.args.get('factura')
        fecha_inicio = request.args.get('fecha_inicio')
        fecha_fin = request.args.get('fecha_fin')

        query = RegistroMovimientos.query.filter(
            RegistroMovimientos.idcliente == idcliente,
            RegistroMovimientos.tipo_movimiento == 'ENTRADA',
            RegistroMovimientos.descripcion.like('%Factura de compra%')
        )

        if factura:
            query = query.filter(RegistroMovimientos.descripcion.like(f'%{factura}%'))
        if fecha_inicio:
            query = query.filter(RegistroMovimientos.fecha >= fecha_inicio)
        if fecha_fin:
            query = query.filter(RegistroMovimientos.fecha <= fecha_fin)

        resultados = query.with_entities(
            RegistroMovimientos.descripcion,
            db.func.min(RegistroMovimientos.fecha).label('fecha')
        ).group_by(RegistroMovimientos.descripcion).order_by(db.func.min(RegistroMovimientos.fecha)).all()

        if not resultados:
            return jsonify([])

        response = []
        seen_facturas = set()
        for item in resultados:
            try:
                factura_num = item.descripcion.split("Factura de compra ")[-1].strip()
            except IndexError:
                continue

            if factura_num.startswith('NC') or factura_num in seen_facturas:
                continue

            seen_facturas.add(factura_num)
            response.append({
                'factura': factura_num,
                'fecha': item.fecha.strftime('%Y-%m-%d %H:%M:%S')
            })

        return jsonify(response)
    except Exception as e:
        return jsonify({'error': 'Error al consultar facturas'}), 500

@app.route('/inventory/detalle-factura', methods=['GET'])
@jwt_required()
def detalle_factura():
    claims = get_jwt()
    idcliente = claims.get('idcliente')

    if not has_permission(claims, 'inventario', 'compras', 'ver'):
        return jsonify({'error': 'No autorizado'}), 403

    try:
        factura = request.args.get('factura')
        if not factura:
            return jsonify({'error': 'Se requiere el número de factura'}), 400

        query = db.session.query(
            Producto.codigo,
            Producto.nombre,
            RegistroMovimientos.cantidad,
            Bodega.nombre.label('bodega'),
            RegistroMovimientos.costo_unitario,
            RegistroMovimientos.costo_total
        ).join(
            Producto, RegistroMovimientos.producto_id == Producto.id
        ).join(
            Bodega, RegistroMovimientos.bodega_destino_id == Bodega.id
        ).join(
            InventarioBodega,
            (RegistroMovimientos.producto_id == InventarioBodega.producto_id) &
            (RegistroMovimientos.bodega_destino_id == InventarioBodega.bodega_id) &
            (RegistroMovimientos.fecha == InventarioBodega.fecha_ingreso)
        ).filter(
            RegistroMovimientos.idcliente == idcliente,
            RegistroMovimientos.tipo_movimiento == 'ENTRADA',
            InventarioBodega.factura == factura
        ).order_by(
            Producto.codigo,
            Bodega.nombre,
            RegistroMovimientos.fecha.desc()
        ).distinct(Producto.codigo, Bodega.nombre)

        resultados = query.all()

        if not resultados:
            return jsonify([])

        response = [
            {
                'id': f"{item.codigo}_{item.bodega}",
                'codigo': item.codigo,
                'nombre': item.nombre,
                'cantidad': float(item.cantidad),
                'bodega': item.bodega,
                'costo_unitario': float(item.costo_unitario) if item.costo_unitario is not None else 0.0,
                'costo_total': float(item.costo_total) if item.costo_total is not None else 0.0
            }
            for item in resultados
        ]
        return jsonify(response)
    except Exception as e:
        return jsonify({'error': 'Error al obtener detalle de factura'}), 500


# Endpoints de la pagina Cargar Ventas manuel
@app.route('/inventory/ventas', methods=['POST'])
@jwt_required()
def cargar_ventas():
    claims = get_jwt()
    idcliente = claims.get('idcliente')

    if not has_permission(claims, 'inventario', 'ventas', 'editar'):
        return jsonify({'error': 'No autorizado'}), 403

    if 'file' not in request.files:
        return jsonify({'message': 'Archivo no encontrado'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'message': 'No se seleccionó ningún archivo'}), 400

    stream = TextIOWrapper(file.stream, encoding='utf-8')
    reader = csv.DictReader(stream)

    required_columns = ['factura', 'codigo', 'nombre', 'cantidad', 'fecha_venta', 'bodega']
    missing_columns = [col for col in required_columns if col not in reader.fieldnames]
    if missing_columns:
        return jsonify({'message': f'Faltan las columnas obligatorias: {", ".join(missing_columns)}'}), 400

    has_precio_unitario = 'precio_unitario' in reader.fieldnames

    errores = []
    for index, row in enumerate(reader, start=1):
        try:
            factura = row['factura'].strip()
            if not factura:
                errores.append(f"Fila {index}: El número de factura es obligatorio y no puede estar vacío.")
                continue
            if not (factura.startswith('FB') or factura.startswith('CC')):
                errores.append(f"Fila {index}: El número de factura debe comenzar con 'FB' o 'CC'.")
                continue

            codigo = row['codigo'].strip()
            nombre = row['nombre'].strip()
            cantidad = int(row['cantidad'])
            fecha_venta = datetime.strptime(row['fecha_venta'], '%Y-%m-%d %H:%M:%S')
            bodega_nombre = row['bodega'].strip()
            precio_unitario = float(row['precio_unitario']) if has_precio_unitario and row['precio_unitario'].strip() else None

            producto = Producto.query.filter_by(codigo=codigo, idcliente=idcliente).first()
            if not producto:
                errores.append(f"Fila {index}: Producto con código {codigo} no encontrado")
                continue

            bodega = Bodega.query.filter_by(nombre=bodega_nombre, idcliente=idcliente).first()
            if not bodega:
                errores.append(f"Fila {index}: Bodega con nombre {bodega_nombre} no encontrada")
                continue

            # Calcular saldo disponible desde kardex
            saldo_disponible = 0
            costo_unitario_promedio = 0
            saldo_costo_total = 0
            movimientos_previos = Kardex.query.filter(
                Kardex.producto_id == producto.id,
                Kardex.idcliente == idcliente,
                Kardex.fecha <= fecha_venta
            ).order_by(Kardex.fecha).all()

            for mov in movimientos_previos:
                if mov.tipo_movimiento == 'ENTRADA' and mov.bodega_destino_id == bodega.id:
                    saldo_disponible += mov.cantidad
                    saldo_costo_total += mov.costo_total
                elif mov.tipo_movimiento == 'SALIDA' and mov.bodega_origen_id == bodega.id:
                    saldo_disponible -= mov.cantidad
                    saldo_costo_total -= mov.costo_total
                if saldo_disponible > 0:
                    costo_unitario_promedio = saldo_costo_total / saldo_disponible
                else:
                    costo_unitario_promedio = 0

            if saldo_disponible < cantidad:
                errores.append(f"Fila {index}: Inventario insuficiente para el producto {codigo} en {bodega_nombre} a la fecha {fecha_venta}. Stock disponible: {saldo_disponible}")
                continue

            if costo_unitario_promedio == 0:
                # Intentar obtener costo de estado_inventario
                estado_inventario = EstadoInventario.query.filter_by(
                    producto_id=producto.id,
                    bodega_id=bodega.id,
                    idcliente=idcliente
                ).first()
                if not estado_inventario or not estado_inventario.costo_unitario:
                    errores.append(f"Fila {index}: No hay costo unitario inicial para el producto {codigo} en {bodega_nombre}")
                    continue
                costo_unitario_promedio = estado_inventario.costo_unitario
                saldo_disponible = estado_inventario.cantidad
                saldo_costo_total = estado_inventario.costo_total

            costo_total = cantidad * costo_unitario_promedio
            saldo_cantidad = saldo_disponible - cantidad
            saldo_costo_total -= costo_total

            estado_inventario = EstadoInventario.query.filter_by(
                producto_id=producto.id,
                bodega_id=bodega.id,
                idcliente=idcliente
            ).first()
            if estado_inventario:
                estado_inventario.cantidad -= cantidad
                estado_inventario.ultima_actualizacion = fecha_venta
                estado_inventario.costo_total = estado_inventario.cantidad * estado_inventario.costo_unitario
            else:
                estado_inventario = EstadoInventario(
                    idcliente=idcliente,
                    producto_id=producto.id,
                    bodega_id=bodega.id,
                    cantidad=saldo_cantidad,
                    ultima_actualizacion=fecha_venta,
                    costo_unitario=costo_unitario_promedio,
                    costo_total=saldo_costo_total
                )
                db.session.add(estado_inventario)

            ultimo_consecutivo = db.session.query(
                db.func.max(db.cast(RegistroMovimientos.consecutivo, db.String))
            ).filter_by(idcliente=idcliente).scalar() or "T00000"
            nuevo_consecutivo = f"T{int(ultimo_consecutivo[1:]) + 1:05d}"

            nuevo_movimiento = RegistroMovimientos(
                idcliente=idcliente,
                consecutivo=nuevo_consecutivo,
                tipo_movimiento='SALIDA',
                producto_id=producto.id,
                bodega_origen_id=bodega.id,
                bodega_destino_id=None,
                cantidad=cantidad,
                fecha=fecha_venta,
                descripcion=f"Salida de mercancía por venta con Factura {factura} desde {bodega_nombre}",
                costo_unitario=costo_unitario_promedio,
                costo_total=costo_total
            )
            db.session.add(nuevo_movimiento)

            kardex_salida = Kardex(
                idcliente=idcliente,
                producto_id=producto.id,
                tipo_movimiento='SALIDA',
                bodega_origen_id=bodega.id,
                bodega_destino_id=None,
                cantidad=cantidad,
                costo_unitario=costo_unitario_promedio,
                costo_total=costo_total,
                fecha=fecha_venta,
                referencia=f"Salida de mercancía por venta con Factura {factura} desde {bodega_nombre}",
                saldo_cantidad=saldo_cantidad,
                saldo_costo_unitario=costo_unitario_promedio if saldo_cantidad > 0 else 0.0,
                saldo_costo_total=saldo_costo_total
            )
            db.session.add(kardex_salida)

            venta = Venta(
                idcliente=idcliente,
                factura=factura,
                producto_id=producto.id,
                nombre_producto=nombre,
                cantidad=cantidad,
                fecha_venta=fecha_venta,
                bodega_id=bodega.id,
                precio_unitario=precio_unitario
            )
            db.session.add(venta)

            db.session.commit()

        except Exception as e:
            db.session.rollback()
            errores.append(f"Fila {index}: Error procesando la fila ({str(e)})")

    if errores:
        return jsonify({'message': 'Errores al procesar el archivo', 'errors': errores}), 400

    return jsonify({'message': 'Ventas cargadas correctamente'}), 201


@app.route('/inventory/ventas-facturas', methods=['GET'])
@jwt_required()
def listar_ventas_facturas():
    claims = get_jwt()
    idcliente = claims.get('idcliente')

    if not has_permission(claims, 'inventario', 'ventas', 'ver'):
        return jsonify({'error': 'No autorizado'}), 403

    try:
        facturas = db.session.query(Venta.factura).filter_by(idcliente=idcliente).distinct().all()
        facturas_lista = [factura[0] for factura in facturas if factura[0]]
        return jsonify({'facturas': facturas_lista})
    except Exception as e:
        return jsonify({'error': 'Error al listar facturas'}), 500

@app.route('/inventory/consultar-ventas', methods=['GET'])
@jwt_required()
def consultar_ventas():
    claims = get_jwt()
    idcliente = claims.get('idcliente')

    if not has_permission(claims, 'inventario', 'ventas', 'ver'):
        return jsonify({'error': 'No autorizado'}), 403

    try:
        factura = request.args.get('factura')
        fecha_inicio = request.args.get('fecha_inicio')
        fecha_fin = request.args.get('fecha_fin')
        bodega_id = request.args.get('bodega_id')

        query = db.session.query(
            Venta.factura,
            db.func.min(Venta.fecha_venta).label('fecha')
        ).filter_by(idcliente=idcliente)

        if factura:
            query = query.filter(Venta.factura == factura)
        if fecha_inicio:
            query = query.filter(Venta.fecha_venta >= fecha_inicio)
        if fecha_fin:
            query = query.filter(Venta.fecha_venta <= fecha_fin)
        if bodega_id:
            query = query.filter(Venta.bodega_id == bodega_id)

        query = query.group_by(Venta.factura)
        resultados = query.order_by(db.func.min(Venta.fecha_venta)).all()

        if not resultados:
            return jsonify([])

        response = [
            {
                'factura': item.factura,
                'fecha': item.fecha.strftime('%Y-%m-%d %H:%M:%S')
            }
            for item in resultados
        ]
        return jsonify(response)
    except Exception as e:
        return jsonify({'error': 'Error al consultar facturas'}), 500

@app.route('/inventory/detalle-venta', methods=['GET'])
@jwt_required()
def detalle_venta():
    claims = get_jwt()
    idcliente = claims.get('idcliente')

    if not has_permission(claims, 'inventario', 'ventas', 'ver'):
        return jsonify({'error': 'No autorizado'}), 403

    try:
        factura = request.args.get('factura')
        if not factura:
            return jsonify({'error': 'Se requiere el número de factura'}), 400

        query = db.session.query(
            Producto.codigo,
            Venta.nombre_producto.label('nombre'),
            Venta.cantidad,
            Bodega.nombre.label('bodega'),
            Venta.precio_unitario
        ).join(
            Producto, Venta.producto_id == Producto.id
        ).join(
            Bodega, Venta.bodega_id == Bodega.id
        ).filter(
            Venta.idcliente == idcliente,
            Venta.factura == factura
        )

        resultados = query.all()

        if not resultados:
            return jsonify([])

        response = [
            {
                'id': f"{item.codigo}_{index}",
                'codigo': item.codigo,
                'nombre': item.nombre,
                'cantidad': item.cantidad,
                'bodega': item.bodega,
                'precio_unitario': float(item.precio_unitario) if item.precio_unitario is not None else None
            }
            for index, item in enumerate(resultados)
        ]
        return jsonify(response)
    except Exception as e:
        return jsonify({'error': 'Error al obtener detalle de factura'}), 500


# ENPOINTS de la pagina de Consulta de inventario Lite
@app.route('/api/inventario/<string:codigo_producto>', methods=['GET'])
@jwt_required()
def consultar_inventario_por_producto(codigo_producto):
    try:
        claims = get_jwt()
        idcliente = claims.get('idcliente')
        if not idcliente:
            return jsonify({'error': 'No se pudo determinar el cliente asociado'}), 403

        if not has_permission(claims, 'inventario', 'consulta', 'ver'):
            return jsonify({'error': 'No tienes permiso para consultar el inventario'}), 403

        producto = Producto.query.filter_by(codigo=codigo_producto, idcliente=idcliente).first()
        if not producto:
            return jsonify({'message': f'Producto con código {codigo_producto} no encontrado'}), 404

        app.logger.debug(f"Consultando inventario para producto_id={producto.id}, idcliente={idcliente}")

        # Consultar directamente estado_inventario
        inventario = EstadoInventario.query.filter_by(
            producto_id=producto.id,
            idcliente=idcliente
        ).join(Bodega, EstadoInventario.bodega_id == Bodega.id).all()

        if not inventario:
            app.logger.debug(f"No se encontró inventario para {codigo_producto} en estado_inventario")
            return jsonify({
                'producto': {
                    'codigo': producto.codigo,
                    'nombre': producto.nombre
                },
                'inventario': []
            }), 200

        resultado = [
            {
                'bodega': inv.bodega.nombre,
                'cantidad': float(inv.cantidad)  # Convertir Decimal a float para JSON
            }
            for inv in inventario
        ]

        app.logger.debug(f"Resultado inventario: {resultado}")

        return jsonify({
            'producto': {
                'codigo': producto.codigo,
                'nombre': producto.nombre
            },
            'inventario': resultado
        }), 200

    except Exception as e:
        app.logger.error(f"Error al consultar inventario por producto: {str(e)}")
        return jsonify({'error': 'Error al consultar inventario'}), 500
    

@app.route('/api/inventario', methods=['GET'])
@jwt_required()
def consultar_inventario_general():
    try:
        claims = get_jwt()
        idcliente = claims.get('idcliente')
        if not idcliente:
            return jsonify({'error': 'No se pudo determinar el cliente asociado'}), 403

        if not has_permission(claims, 'inventario', 'consulta', 'ver'):
            return jsonify({'error': 'No tienes permiso para consultar el inventario'}), 403

        offset = int(request.args.get('offset', 0))
        limit = int(request.args.get('limit', 20))
        nombre = request.args.get('nombre', None)

        query = Producto.query.filter_by(idcliente=idcliente)
        if nombre:
            query = query.filter(Producto.nombre.ilike(f'%{nombre}%'))

        productos = query.order_by(Producto.codigo).offset(offset).limit(limit).all()
        total_productos = query.count()

        if not productos:
            return jsonify({'productos': [], 'bodegas': [], 'total': 0}), 200

        bodegas = [b.nombre for b in Bodega.query.filter_by(idcliente=idcliente).all()]
        productos_data = []
        for producto in productos:
            inventario = calcular_inventario_producto(producto.id, idcliente)
            cantidades_por_bodega = {b: 0 for b in bodegas}
            for item in inventario:
                cantidades_por_bodega[item['bodega']] = item['cantidad']
            cantidad_total = sum(item['cantidad'] for item in inventario)
            productos_data.append({
                'codigo': producto.codigo,
                'nombre': producto.nombre,
                'cantidad_total': float(cantidad_total),
                'cantidades_por_bodega': cantidades_por_bodega
            })

        return jsonify({
            'productos': productos_data,
            'bodegas': bodegas,
            'total': total_productos
        }), 200
    except Exception as e:
        print(f"Error al consultar inventario general: {str(e)}")
        return jsonify({'error': 'Error al consultar inventario general'}), 500




# Endpoints de cargue de notas credito:
@app.route('/api/cargar_notas_credito', methods=['POST'])
@jwt_required()
def cargar_notas_credito():
    claims = get_jwt()
    idcliente = claims.get('idcliente')

    # Verificar permiso para editar
    if not has_permission(claims, 'inventario', 'notas_credito', 'editar'):
        return jsonify({'error': 'No autorizado para cargar notas de crédito'}), 403

    if 'file' not in request.files:
        return jsonify({'message': 'No se encontró el archivo en la solicitud'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'message': 'No se seleccionó ningún archivo'}), 400

    stream = TextIOWrapper(file.stream, encoding='utf-8')
    reader = csv.DictReader(stream)

    # Columnas esperadas
    expected_columns = ['nota_credito', 'factura', 'codigo', 'nombre', 'cantidad', 'fecha_devolucion']
    optional_columns = ['costo_unitario']
    missing_columns = [col for col in expected_columns if col not in reader.fieldnames]
    if missing_columns:
        return jsonify({'message': f'Faltan las columnas: {", ".join(missing_columns)}'}), 400

    errores = []
    for index, row in enumerate(reader, start=1):
        try:
            nota_credito = row['nota_credito'].strip()
            factura = row['factura'].strip()
            codigo = row['codigo'].strip()
            nombre = row['nombre'].strip()
            cantidad = int(row['cantidad'])
            fecha_devolucion = row.get('fecha_devolucion', None)
            costo_unitario_csv = float(row.get('costo_unitario', 0))

            if not nota_credito or not factura:
                errores.append(f"Fila {index}: 'nota_credito' y 'factura' son obligatorios.")
                continue

            if fecha_devolucion:
                fecha_devolucion = datetime.strptime(fecha_devolucion, '%Y-%m-%d %H:%M:%S')
            else:
                fecha_devolucion = datetime.utcnow()

            producto = Producto.query.filter_by(codigo=codigo, idcliente=idcliente).first()
            if not producto:
                errores.append(f"Fila {index}: Producto con código {codigo} no encontrado.")
                continue

            # Buscar la salida asociada a la factura en el Kardex
            kardex_salida = Kardex.query.filter(
                Kardex.producto_id == producto.id,
                Kardex.idcliente == idcliente,
                Kardex.tipo_movimiento == 'SALIDA',
                Kardex.referencia.like(f"%Factura {factura}%")
            ).order_by(Kardex.fecha.desc()).first()

            if not kardex_salida:
                errores.append(f"Fila {index}: No se encontró una venta con Factura {factura} para el producto {codigo}.")
                continue

            # Usar la bodega de la salida como destino
            bodega_destino_id = kardex_salida.bodega_origen_id
            bodega_obj = Bodega.query.filter_by(id=bodega_destino_id, idcliente=idcliente).first()
            if not bodega_obj:
                errores.append(f"Fila {index}: La bodega de la venta original (ID {bodega_destino_id}) no existe.")
                continue

            # Usar el costo unitario de la salida si no se proporciona en el CSV
            costo_unitario = costo_unitario_csv if costo_unitario_csv > 0 else kardex_salida.costo_unitario
            costo_total = cantidad * costo_unitario

            # Actualizar o crear registro en inventario_bodega
            inventario = InventarioBodega.query.filter_by(
                producto_id=producto.id, 
                bodega_id=bodega_obj.id,
                idcliente=idcliente
            ).first()
            if not inventario:
                inventario = InventarioBodega(
                    idcliente=idcliente,
                    producto_id=producto.id,
                    bodega_id=bodega_obj.id,
                    cantidad=cantidad,
                    factura=nota_credito,
                    contenedor=None,
                    fecha_ingreso=fecha_devolucion,
                    costo_unitario=costo_unitario,
                    costo_total=costo_total
                )
                db.session.add(inventario)
                descripcion = f"Devolución inicial por Nota Crédito {nota_credito}"
            else:
                costo_total_nuevo = (inventario.cantidad * inventario.costo_unitario) + costo_total
                inventario.cantidad += cantidad
                inventario.costo_unitario = costo_total_nuevo / inventario.cantidad if inventario.cantidad > 0 else costo_unitario
                inventario.costo_total = inventario.cantidad * inventario.costo_unitario
                inventario.fecha_ingreso = fecha_devolucion
                inventario.factura = nota_credito
                inventario.contenedor = None
                descripcion = f"Entrada por devolución con Nota Crédito {nota_credito}"

            # Actualizar o crear registro en estado_inventario
            estado_inventario = EstadoInventario.query.filter_by(
                producto_id=producto.id, 
                bodega_id=bodega_obj.id,
                idcliente=idcliente
            ).first()
            if not estado_inventario:
                estado_inventario = EstadoInventario(
                    idcliente=idcliente,
                    producto_id=producto.id,
                    bodega_id=bodega_obj.id,
                    cantidad=cantidad,
                    ultima_actualizacion=fecha_devolucion,
                    costo_unitario=costo_unitario,
                    costo_total=costo_total
                )
                db.session.add(estado_inventario)
            else:
                costo_total_nuevo = (estado_inventario.cantidad * estado_inventario.costo_unitario) + costo_total
                estado_inventario.cantidad += cantidad
                estado_inventario.costo_unitario = costo_total_nuevo / estado_inventario.cantidad if estado_inventario.cantidad > 0 else costo_unitario
                estado_inventario.costo_total = estado_inventario.cantidad * estado_inventario.costo_unitario
                estado_inventario.ultima_actualizacion = fecha_devolucion

            # Generar nuevo consecutivo
            ultimo_consecutivo = db.session.query(
                db.func.max(db.cast(RegistroMovimientos.consecutivo, db.String))
            ).filter_by(idcliente=idcliente).scalar() or "T00000"
            nuevo_consecutivo = f"T{int(ultimo_consecutivo[1:]) + 1:05d}"

            # Registrar movimiento como ENTRADA en RegistroMovimientos
            nuevo_movimiento = RegistroMovimientos(
                idcliente=idcliente,
                consecutivo=nuevo_consecutivo,
                producto_id=producto.id,
                tipo_movimiento='ENTRADA',
                cantidad=cantidad,
                bodega_origen_id=None,
                bodega_destino_id=bodega_obj.id,
                fecha=fecha_devolucion,
                descripcion=descripcion,
                costo_unitario=costo_unitario,
                costo_total=costo_total
            )
            db.session.add(nuevo_movimiento)

            # Registrar en Kardex
            kardex_entry = Kardex(
                idcliente=idcliente,
                producto_id=producto.id,
                bodega_origen_id=None,
                bodega_destino_id=bodega_obj.id,
                fecha=fecha_devolucion,
                tipo_movimiento='ENTRADA',
                cantidad=cantidad,
                costo_unitario=costo_unitario,
                costo_total=costo_total,
                saldo_cantidad=estado_inventario.cantidad,
                saldo_costo_unitario=estado_inventario.costo_unitario,
                saldo_costo_total=estado_inventario.costo_total,
                referencia=f"Entrada por devolución con Nota Crédito {nota_credito} (Factura {factura})"
            )
            db.session.add(kardex_entry)

            db.session.commit()

        except Exception as e:
            db.session.rollback()
            errores.append(f"Fila {index}: Error al procesar la fila ({str(e)})")

    if errores:
        return jsonify({'message': 'Errores al procesar el archivo', 'errors': errores}), 400

    return jsonify({'message': 'Notas crédito cargadas correctamente'}), 201

@app.route('/api/notas_credito', methods=['GET'])
@jwt_required()
def listar_notas_credito():
    claims = get_jwt()
    idcliente = claims.get('idcliente')

    # Verificar permiso para ver
    if not has_permission(claims, 'inventario', 'notas_credito', 'ver'):
        return jsonify({'error': 'No autorizado para listar notas de crédito'}), 403

    try:
        notas_credito = db.session.query(InventarioBodega.factura).join(
            RegistroMovimientos,
            (RegistroMovimientos.producto_id == InventarioBodega.producto_id) &
            (RegistroMovimientos.bodega_destino_id == InventarioBodega.bodega_id)
        ).filter(
            RegistroMovimientos.tipo_movimiento == 'ENTRADA',
            RegistroMovimientos.descripcion.like('%Nota Crédito%'),
            InventarioBodega.idcliente == idcliente
        ).distinct().all()

        notas_credito_lista = [nota[0] for nota in notas_credito if nota[0]]
        return jsonify({'notas_credito': notas_credito_lista})
    except Exception as e:
        print(f"Error al listar notas crédito: {str(e)}")
        return jsonify({'error': 'Error al listar notas crédito'}), 500

@app.route('/api/consultar_notas_credito', methods=['GET'])
@jwt_required()
def consultar_notas_credito():
    claims = get_jwt()
    idcliente = claims.get('idcliente')

    # Verificar permiso para ver
    if not has_permission(claims, 'inventario', 'notas_credito', 'ver'):
        return jsonify({'error': 'No autorizado para consultar notas de crédito'}), 403

    try:
        nota_credito = request.args.get('nota_credito')
        fecha_inicio = request.args.get('fecha_inicio')
        fecha_fin = request.args.get('fecha_fin')

        query = db.session.query(
            InventarioBodega.factura.label('nota_credito'),
            db.func.min(RegistroMovimientos.fecha).label('fecha')
        ).join(
            RegistroMovimientos,
            (RegistroMovimientos.producto_id == InventarioBodega.producto_id) &
            (RegistroMovimientos.bodega_destino_id == InventarioBodega.bodega_id)
        ).filter(
            RegistroMovimientos.tipo_movimiento == 'ENTRADA',
            RegistroMovimientos.descripcion.like('%Nota Crédito%'),
            InventarioBodega.idcliente == idcliente
        )

        if nota_credito:
            query = query.filter(InventarioBodega.factura == nota_credito)
        if fecha_inicio:
            query = query.filter(RegistroMovimientos.fecha >= fecha_inicio)
        if fecha_fin:
            query = query.filter(RegistroMovimientos.fecha <= fecha_fin)

        query = query.group_by(InventarioBodega.factura)
        resultados = query.order_by(db.func.min(RegistroMovimientos.fecha)).all()

        if not resultados:
            return jsonify([])

        response = [
            {
                'nota_credito': item.nota_credito,
                'fecha': item.fecha.strftime('%Y-%m-%d %H:%M:%S')
            }
            for item in resultados
        ]
        return jsonify(response)
    except Exception as e:
        print(f"Error al consultar notas crédito: {str(e)}")
        return jsonify({'error': 'Error al consultar notas crédito'}), 500

@app.route('/api/detalle_nota_credito', methods=['GET'])
@jwt_required()
def detalle_nota_credito():
    claims = get_jwt()
    idcliente = claims.get('idcliente')

    # Verificar permiso para ver
    if not has_permission(claims, 'inventario', 'notas_credito', 'ver'):
        return jsonify({'error': 'No autorizado para ver detalles de notas de crédito'}), 403

    try:
        nota_credito = request.args.get('nota_credito')
        if not nota_credito:
            return jsonify({'error': 'Se requiere el número de nota crédito'}), 400

        query = db.session.query(
            Producto.codigo,
            Producto.nombre,
            RegistroMovimientos.cantidad,
            Bodega.nombre.label('bodega'),
            RegistroMovimientos.costo_unitario,
            RegistroMovimientos.costo_total
        ).join(
            Producto, RegistroMovimientos.producto_id == Producto.id
        ).join(
            Bodega, RegistroMovimientos.bodega_destino_id == Bodega.id
        ).join(
            InventarioBodega,
            (RegistroMovimientos.producto_id == InventarioBodega.producto_id) &
            (RegistroMovimientos.bodega_destino_id == InventarioBodega.bodega_id)
        ).filter(
            RegistroMovimientos.tipo_movimiento == 'ENTRADA',
            RegistroMovimientos.descripcion.like('%Nota Crédito%'),
            InventarioBodega.factura == nota_credito,
            InventarioBodega.idcliente == idcliente
        )

        resultados = query.all()

        if not resultados:
            return jsonify([])

        response = [
            {
                'codigo': item.codigo,
                'nombre': item.nombre,
                'cantidad': float(item.cantidad),
                'bodega': item.bodega,
                'costo_unitario': float(item.costo_unitario) if item.costo_unitario is not None else 0.0,
                'costo_total': float(item.costo_total) if item.costo_total is not None else 0.0
            }
            for item in resultados
        ]
        return jsonify(response)
    except Exception as e:
        print(f"Error al obtener detalle de nota crédito: {str(e)}")
        return jsonify({'error': 'Error al obtener detalle de nota crédito'}), 500


# ENDPOINTS PARA PAGINA DE CONSULTA DE INVENTARIO
@app.route('/api/inventario-con-costos/<string:codigo_producto>', methods=['GET'])
@jwt_required()
def consultar_inventario_por_producto_con_costos(codigo_producto):
    try:
        claims = get_jwt()
        idcliente = claims.get('idcliente')
        print(f"[DEBUG] Consultando inventario para codigo={codigo_producto}, idcliente={idcliente}")
        if not idcliente:
            return jsonify({'error': 'No se pudo determinar el cliente asociado'}), 403

        producto = Producto.query.filter_by(codigo=codigo_producto, idcliente=idcliente).first()
        if not producto:
            return jsonify({'message': f'Producto con código {codigo_producto} no encontrado'}), 404

        inventario = calcular_inventario_producto(producto.id, idcliente)
        print(f"[DEBUG] Inventario para {codigo_producto}: {inventario}")
        if not inventario:
            return jsonify({
                'producto': {
                    'codigo': producto.codigo,
                    'nombre': producto.nombre,
                    'stock_minimo': producto.stock_minimo
                },
                'inventario': []
            }), 200

        inventario_con_costos = []
        for item in inventario:
            bodega = Bodega.query.filter_by(nombre=item['bodega'], idcliente=idcliente).first()
            if not bodega:
                print(f"[DEBUG] No se encontró bodega: {item['bodega']}")
                continue
            ultimo_kardex = db.session.query(Kardex).filter(
                Kardex.producto_id == producto.id,
                Kardex.bodega_destino_id == bodega.id,
                Kardex.idcliente == idcliente
            ).order_by(Kardex.fecha.desc()).first()
            costo_unitario = float(ultimo_kardex.saldo_costo_unitario) if ultimo_kardex else 0.0
            costo_total = costo_unitario * float(item['cantidad'])
            inventario_con_costos.append({
                'bodega': item['bodega'],
                'cantidad': float(item['cantidad']),
                'costo_unitario': costo_unitario,
                'costo_total': costo_total
            })
            print(f"[DEBUG] Item para {codigo_producto}: {inventario_con_costos[-1]}")

        return jsonify({
            'producto': {
                'codigo': producto.codigo,
                'nombre': producto.nombre,
                'stock_minimo': producto.stock_minimo
            },
            'inventario': inventario_con_costos
        }), 200
    except Exception as e:
        print(f"Error al consultar inventario por producto con costos: {str(e)}")
        return jsonify({'error': 'Error al consultar inventario'}), 500
        

@app.route('/api/inventario-con-costos', methods=['GET'])
@jwt_required()
def consultar_inventario_general_con_costos():
    try:
        claims = get_jwt()
        idcliente = claims.get('idcliente')
        print(f"[DEBUG] idcliente: {idcliente}")
        if not idcliente:
            return jsonify({'error': 'No se pudo determinar el cliente asociado'}), 403

        offset = request.args.get('offset', default=0, type=int)
        limit = min(request.args.get('limit', default=20, type=int), 1000)
        nombre = request.args.get('nombre', default=None, type=str)

        bodegas = Bodega.query.filter_by(idcliente=idcliente).all()
        lista_bodegas = {bodega.id: bodega.nombre for bodega in bodegas}
        print(f"[DEBUG] Bodegas encontradas: {[b.nombre for b in bodegas]}")
        if not bodegas:
            return jsonify({'productos': [], 'bodegas': []}), 200

        query = Producto.query.filter_by(idcliente=idcliente)
        if nombre:
            query = query.filter(Producto.nombre.ilike(f'%{nombre}%'))

        productos = query.order_by(Producto.codigo).offset(offset).limit(limit).all()
        print(f"[DEBUG] Productos encontrados: {len(productos)}")
        if not productos:
            return jsonify({'productos': [], 'bodegas': [b.nombre for b in bodegas]}), 200

        resultado = []
        for producto in productos:
            inventario = calcular_inventario_producto(producto.id, idcliente)
            cantidades_por_bodega = {bodega.nombre: 0.0 for bodega in bodegas}
            costos_por_bodega = {bodega.nombre: 0.0 for bodega in bodegas}
            
            for item in inventario:
                bodega_nombre = item['bodega']
                print(f"[DEBUG] Procesando bodega {bodega_nombre} para producto {producto.codigo}")
                cantidades_por_bodega[bodega_nombre] = float(item['cantidad'])
                # Obtener el último costo unitario
                bodega = next((b for b in bodegas if b.nombre == bodega_nombre), None)
                if bodega:
                    ultimo_kardex = db.session.query(Kardex).filter(
                        Kardex.producto_id == producto.id,
                        Kardex.bodega_destino_id == bodega.id,
                        Kardex.idcliente == idcliente
                    ).order_by(Kardex.fecha.desc()).first()
                    costo_unitario = float(ultimo_kardex.saldo_costo_unitario) if ultimo_kardex else 0.0
                    costos_por_bodega[bodega_nombre] = costo_unitario * float(item['cantidad'])
                    print(f"[DEBUG] Costo para {producto.codigo} en {bodega_nombre}: {costos_por_bodega[bodega_nombre]}")
                else:
                    print(f"[DEBUG] Bodega no encontrada: {bodega_nombre}")

            total_cantidad = sum(cantidades_por_bodega.values())
            resultado.append({
                'codigo': producto.codigo,
                'nombre': producto.nombre,
                'cantidad_total': total_cantidad,
                'cantidades_por_bodega': cantidades_por_bodega,
                'costos_por_bodega': costos_por_bodega,
                'stock_minimo': producto.stock_minimo
            })
            print(f"[DEBUG] Producto {producto.codigo}: cantidad_total={total_cantidad}, cantidades_por_bodega={cantidades_por_bodega}")

        print(f"[DEBUG] Respuesta generada con {len(resultado)} productos")
        return jsonify({
            'productos': resultado,
            'bodegas': [b.nombre for b in bodegas]
        }), 200
    except Exception as e:
        print(f"Error en consultar_inventario_general_con_costos: {str(e)}")
        return jsonify({'error': 'Error al consultar el inventario general'}), 500


@app.route('/api/productos/completos', methods=['GET'])
@jwt_required()
def obtener_todos_los_productos():
    try:
        claims = get_jwt()
        idcliente = claims.get('idcliente')
        print(f"[DEBUG] idcliente: {idcliente}")
        if not idcliente:
            return jsonify({'error': 'No se pudo determinar el cliente asociado'}), 403

        print("[DEBUG] Consultando productos...")
        productos = db.session.query(
            Producto.id,
            Producto.codigo,
            Producto.nombre,
            Producto.peso_unidad_gr,
            Producto.es_producto_compuesto,
            Producto.stock_minimo
        ).filter_by(idcliente=idcliente).order_by(Producto.codigo).all()
        print(f"[DEBUG] Productos encontrados: {len(productos)}")

        if not productos:
            return jsonify([]), 200

        resultado = [
            {
                'id': p.id,
                'codigo': p.codigo,
                'nombre': p.nombre,
                'peso_unidad_gr': float(p.peso_unidad_gr) if p.peso_unidad_gr else None,
                'es_producto_compuesto': p.es_producto_compuesto,
                'stock_minimo': p.stock_minimo
            } for p in productos
        ]
        print("[DEBUG] Respuesta generada")
        return jsonify(resultado), 200
    except Exception as e:
        print(f"[DEBUG] Error al obtener productos completos: {str(e)}")
        return jsonify({'error': 'Error al obtener productos completos'}), 500




@app.route('/inventory/kardex', methods=['GET'])
@jwt_required()
def consultar_kardex():
    try:
        claims = get_jwt()
        idcliente = claims.get('idcliente')
        if not idcliente:
            return jsonify({'error': 'No se pudo determinar el cliente asociado'}), 403

        codigo_producto = request.args.get('codigo')
        fecha_inicio = request.args.get('fecha_inicio')
        fecha_fin = request.args.get('fecha_fin')
        bodegas = request.args.get('bodegas')

        if not codigo_producto or not fecha_inicio or not fecha_fin:
            return jsonify({'message': 'Debe proporcionar el código del producto y el rango de fechas'}), 400

        # Convertir fechas a datetime en hora local de Colombia (naive, como en la base de datos)
        try:
            fecha_inicio_dt = datetime.strptime(fecha_inicio, '%Y-%m-%d')
            fecha_fin_dt = datetime.strptime(fecha_fin, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
        except ValueError:
            return jsonify({'error': 'Formato de fecha inválido. Use YYYY-MM-DD.'}), 400

        producto = Producto.query.filter_by(codigo=codigo_producto, idcliente=idcliente).first()
        if not producto:
            return jsonify({'message': f'Producto con código {codigo_producto} no encontrado'}), 404

        bodegas_ids = None
        if bodegas:
            bodegas_list = bodegas.split(',')
            bodegas_query = Bodega.query.filter(Bodega.nombre.in_(bodegas_list), Bodega.idcliente == idcliente).all()
            bodegas_ids = [b.id for b in bodegas_query]
            if not bodegas_ids:
                return jsonify({'message': 'Ninguna de las bodegas especificadas fue encontrada'}), 404

        # Calcular saldo inicial
        saldo_bodegas = {}
        saldo_costo_total_bodegas = {}
        kardex_interno_query = Kardex.query.filter(
            Kardex.producto_id == producto.id,
            Kardex.idcliente == idcliente,
            Kardex.fecha < fecha_inicio_dt
        )
        if bodegas_ids:
            kardex_interno_query = kardex_interno_query.filter(
                (Kardex.bodega_origen_id.in_(bodegas_ids)) | (Kardex.bodega_destino_id.in_(bodegas_ids))
            )
        kardex_interno = kardex_interno_query.order_by(Kardex.fecha).all()

        for movimiento in kardex_interno:
            if movimiento.tipo_movimiento == 'SALIDA' and movimiento.bodega_origen_id:
                saldo_bodegas[movimiento.bodega_origen_id] = saldo_bodegas.get(movimiento.bodega_origen_id, 0) - movimiento.cantidad
                saldo_costo_total_bodegas[movimiento.bodega_origen_id] = saldo_costo_total_bodegas.get(movimiento.bodega_origen_id, 0) - (movimiento.costo_total or 0)
            elif movimiento.tipo_movimiento == 'ENTRADA' and movimiento.bodega_destino_id:
                saldo_bodegas[movimiento.bodega_destino_id] = saldo_bodegas.get(movimiento.bodega_destino_id, 0) + movimiento.cantidad
                saldo_costo_total_bodegas[movimiento.bodega_destino_id] = saldo_costo_total_bodegas.get(movimiento.bodega_destino_id, 0) + (movimiento.costo_total or 0)
            elif movimiento.tipo_movimiento == 'TRASLADO':
                if movimiento.bodega_origen_id:
                    saldo_bodegas[movimiento.bodega_origen_id] = saldo_bodegas.get(movimiento.bodega_origen_id, 0) - movimiento.cantidad
                    saldo_costo_total_bodegas[movimiento.bodega_origen_id] = saldo_costo_total_bodegas.get(movimiento.bodega_origen_id, 0) - (movimiento.costo_total or 0)
                if movimiento.bodega_destino_id:
                    saldo_bodegas[movimiento.bodega_destino_id] = saldo_bodegas.get(movimiento.bodega_destino_id, 0) + movimiento.cantidad
                    saldo_costo_total_bodegas[movimiento.bodega_destino_id] = saldo_costo_total_bodegas.get(movimiento.bodega_destino_id, 0) + (movimiento.costo_total or 0)

        # Preparar saldos iniciales por bodega
        saldo_bodegas_nombres = {}
        total_saldo_global = 0
        total_costo_global = 0
        for bodega_id, saldo in saldo_bodegas.items():
            bodega = db.session.query(Bodega).filter_by(id=bodega_id, idcliente=idcliente).first()
            if bodega and saldo > 0:
                costo_total = saldo_costo_total_bodegas.get(bodega_id, 0)
                costo_unitario = costo_total / saldo if saldo > 0 else 0.0
                saldo_bodegas_nombres[bodega.nombre] = {
                    'cantidad': float(saldo),
                    'costo_total': float(costo_total),
                    'costo_unitario': float(costo_unitario)
                }
                total_saldo_global += saldo
                total_costo_global += costo_total

        saldo_costo_unitario_global = total_costo_global / total_saldo_global if total_saldo_global > 0 else 0.0

        # Consultar movimientos en el rango
        movimientos_query = Kardex.query.filter(
            Kardex.producto_id == producto.id,
            Kardex.idcliente == idcliente,
            Kardex.fecha >= fecha_inicio_dt,
            Kardex.fecha <= fecha_fin_dt
        )
        if bodegas_ids:
            movimientos_query = movimientos_query.filter(
                (Kardex.bodega_origen_id.in_(bodegas_ids)) | (Kardex.bodega_destino_id.in_(bodegas_ids))
            )
        movimientos = movimientos_query.order_by(Kardex.fecha).all()

        kardex = []
        saldo_actual = saldo_bodegas.copy()
        saldo_costo_total_actual = saldo_costo_total_bodegas.copy()
        total_saldo_global_actual = total_saldo_global
        total_costo_global_actual = total_costo_global

        # Registrar saldos iniciales
        for bodega_nombre, saldos in saldo_bodegas_nombres.items():
            kardex.append({
                'fecha': fecha_inicio_dt.strftime('%Y-%m-%d 00:00:00'),
                'tipo': 'SALDO INICIAL',
                'cantidad': saldos['cantidad'],
                'bodega': bodega_nombre,
                'saldo': saldos['cantidad'],
                'costo_unitario': saldos['costo_unitario'],
                'costo_total': saldos['costo_total'],
                'saldo_costo_unitario': saldos['costo_unitario'],
                'saldo_costo_total': saldos['costo_total'],
                'saldo_costo_unitario_global': saldo_costo_unitario_global,
                'descripcion': 'Saldo inicial antes del rango de consulta'
            })

        # Procesar movimientos
        for movimiento in movimientos:
            if movimiento.tipo_movimiento == 'ENTRADA' and movimiento.bodega_destino_id:
                bodega_destino = movimiento.bodega_destino.nombre if movimiento.bodega_destino else None
                saldo_antes = saldo_actual.get(movimiento.bodega_destino_id, 0)
                costo_total_antes = saldo_costo_total_actual.get(movimiento.bodega_destino_id, 0)

                saldo_actual[movimiento.bodega_destino_id] = saldo_antes + movimiento.cantidad
                costo_total_movimiento = movimiento.costo_total or (movimiento.cantidad * movimiento.costo_unitario)
                saldo_costo_total_actual[movimiento.bodega_destino_id] = costo_total_antes + costo_total_movimiento
                total_saldo_global_actual += movimiento.cantidad
                total_costo_global_actual += costo_total_movimiento

                saldo_costo_unitario_bodega = (
                    saldo_costo_total_actual[movimiento.bodega_destino_id] /
                    saldo_actual[movimiento.bodega_destino_id] if saldo_actual[movimiento.bodega_destino_id] > 0 else 0.0
                )
                saldo_costo_unitario_global = total_costo_global_actual / total_saldo_global_actual if total_saldo_global_actual > 0 else 0.0

                kardex.append({
                    'fecha': movimiento.fecha.strftime('%Y-%m-%d %H:%M:%S'),
                    'tipo': 'ENTRADA',
                    'cantidad': float(movimiento.cantidad),
                    'bodega': bodega_destino,
                    'saldo': float(saldo_actual[movimiento.bodega_destino_id]),
                    'costo_unitario': float(movimiento.costo_unitario or 0.0),
                    'costo_total': float(costo_total_movimiento),
                    'saldo_costo_unitario': float(saldo_costo_unitario_bodega),
                    'saldo_costo_total': float(saldo_costo_total_actual[movimiento.bodega_destino_id]),
                    'saldo_costo_unitario_global': float(saldo_costo_unitario_global),
                    'descripcion': movimiento.referencia or 'Entrada registrada'
                })

            elif movimiento.tipo_movimiento == 'SALIDA' and movimiento.bodega_origen_id:
                bodega_origen = movimiento.bodega_origen.nombre if movimiento.bodega_origen else None
                saldo_antes = saldo_actual.get(movimiento.bodega_origen_id, 0)
                costo_total_antes = saldo_costo_total_actual.get(movimiento.bodega_origen_id, 0)
                costo_unitario_antes = costo_total_antes / saldo_antes if saldo_antes > 0 else 0.0

                saldo_actual[movimiento.bodega_origen_id] = saldo_antes - movimiento.cantidad
                costo_total_movimiento = movimiento.costo_total or (movimiento.cantidad * (movimiento.costo_unitario or costo_unitario_antes))
                saldo_costo_total_actual[movimiento.bodega_origen_id] = costo_total_antes - costo_total_movimiento
                total_saldo_global_actual -= movimiento.cantidad
                total_costo_global_actual -= costo_total_movimiento

                saldo_costo_unitario_bodega = (
                    saldo_costo_total_actual[movimiento.bodega_origen_id] /
                    saldo_actual[movimiento.bodega_origen_id] if saldo_actual[movimiento.bodega_origen_id] > 0 else costo_unitario_antes
                )
                saldo_costo_unitario_global = total_costo_global_actual / total_saldo_global_actual if total_saldo_global_actual > 0 else 0.0

                saldo_costo_total = float(saldo_costo_total_actual[movimiento.bodega_origen_id]) if saldo_actual[movimiento.bodega_origen_id] > 0 else 0.0

                kardex.append({
                    'fecha': movimiento.fecha.strftime('%Y-%m-%d %H:%M:%S'),
                    'tipo': 'SALIDA',
                    'cantidad': float(movimiento.cantidad),
                    'bodega': bodega_origen,
                    'saldo': float(saldo_actual[movimiento.bodega_origen_id]),
                    'costo_unitario': float(movimiento.costo_unitario or costo_unitario_antes),
                    'costo_total': float(costo_total_movimiento),
                    'saldo_costo_unitario': float(saldo_costo_unitario_bodega),
                    'saldo_costo_total': saldo_costo_total,
                    'saldo_costo_unitario_global': float(saldo_costo_unitario_global),
                    'descripcion': movimiento.referencia or 'Salida registrada'
                })

            elif movimiento.tipo_movimiento == 'TRASLADO' and movimiento.bodega_origen_id and movimiento.bodega_destino_id:
                bodega_origen = movimiento.bodega_origen.nombre if movimiento.bodega_origen else None
                saldo_origen_antes = saldo_actual.get(movimiento.bodega_origen_id, 0)
                costo_total_origen_antes = saldo_costo_total_actual.get(movimiento.bodega_origen_id, 0)
                costo_unitario_origen = costo_total_origen_antes / saldo_origen_antes if saldo_origen_antes > 0 else 0.0
                costo_total_traslado = movimiento.cantidad * costo_unitario_origen

                saldo_actual[movimiento.bodega_origen_id] = saldo_origen_antes - movimiento.cantidad
                saldo_costo_total_actual[movimiento.bodega_origen_id] = costo_total_origen_antes - costo_total_traslado
                saldo_costo_unitario_origen = (
                    saldo_costo_total_actual[movimiento.bodega_origen_id] /
                    saldo_actual[movimiento.bodega_origen_id] if saldo_actual[movimiento.bodega_origen_id] > 0 else costo_unitario_origen
                )

                kardex.append({
                    'fecha': movimiento.fecha.strftime('%Y-%m-%d %H:%M:%S'),
                    'tipo': 'SALIDA',
                    'cantidad': float(movimiento.cantidad),
                    'bodega': bodega_origen,
                    'saldo': float(saldo_actual[movimiento.bodega_origen_id]),
                    'costo_unitario': float(costo_unitario_origen),
                    'costo_total': float(costo_total_traslado),
                    'saldo_costo_unitario': float(saldo_costo_unitario_origen),
                    'saldo_costo_total': float(saldo_costo_total_actual[movimiento.bodega_origen_id]),
                    'saldo_costo_unitario_global': float(saldo_costo_unitario_global),
                    'descripcion': f'Traslado con referencia {movimiento.referencia}. Salida de Mercancía de {bodega_origen}'
                })

                bodega_destino = movimiento.bodega_destino.nombre if movimiento.bodega_destino else None
                saldo_destino_antes = saldo_actual.get(movimiento.bodega_destino_id, 0)
                costo_total_destino_antes = saldo_costo_total_actual.get(movimiento.bodega_destino_id, 0)

                saldo_actual[movimiento.bodega_destino_id] = saldo_destino_antes + movimiento.cantidad
                saldo_costo_total_actual[movimiento.bodega_destino_id] = costo_total_destino_antes + costo_total_traslado

                saldo_costo_unitario_destino = (
                    saldo_costo_total_actual[movimiento.bodega_destino_id] /
                    saldo_actual[movimiento.bodega_destino_id] if saldo_actual[movimiento.bodega_destino_id] > 0 else costo_unitario_origen
                )

                kardex.append({
                    'fecha': movimiento.fecha.strftime('%Y-%m-%d %H:%M:%S'),
                    'tipo': 'ENTRADA',
                    'cantidad': float(movimiento.cantidad),
                    'bodega': bodega_destino,
                    'saldo': float(saldo_actual[movimiento.bodega_destino_id]),
                    'costo_unitario': float(costo_unitario_origen),
                    'costo_total': float(costo_total_traslado),
                    'saldo_costo_unitario': float(saldo_costo_unitario_destino),
                    'saldo_costo_total': float(saldo_costo_total_actual[movimiento.bodega_destino_id]),
                    'saldo_costo_unitario_global': float(saldo_costo_unitario_global),
                    'descripcion': f'Traslado con referencia {movimiento.referencia}. Entrada de Mercancía a {bodega_destino}'
                })

        return jsonify({'producto': {'codigo': producto.codigo, 'nombre': producto.nombre}, 'kardex': kardex})

    except Exception as e:
        print(f"Error al consultar Kardex: {str(e)}")
        return jsonify({'error': f'Error al consultar Kardex: {str(e)}'}), 500



@app.route('/api/kardex/pdf', methods=['GET'])
@jwt_required()
def generar_kardex_pdf():
    try:
        # Verificar permisos
        claims = get_jwt()
        if not has_permission(claims, 'inventario', 'kardex', 'ver'):
            return jsonify({'error': 'No tienes permiso para generar el PDF del Kardex'}), 403

        # Obtener parámetros
        codigo_producto = request.args.get('codigo')
        fecha_inicio = request.args.get('fecha_inicio')
        fecha_fin = request.args.get('fecha_fin')
        bodegas = request.args.get('bodegas')
        idcliente = claims.get('idcliente')

        if not all([codigo_producto, fecha_inicio, fecha_fin, idcliente]):
            return jsonify({'error': 'Faltan parámetros (código, fecha_inicio, fecha_fin, idcliente).'}), 400

        # Convertir fechas a datetime en hora local de Colombia (naive)
        try:
            fecha_inicio_dt = datetime.strptime(fecha_inicio, '%Y-%m-%d')
            fecha_fin_dt = datetime.strptime(fecha_fin, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
        except ValueError:
            return jsonify({'error': 'Formato de fecha inválido. Use YYYY-MM-DD.'}), 400

        # Verificar cliente
        cliente = Clientes.query.filter_by(idcliente=idcliente).first()
        if not cliente:
            return jsonify({'error': f'Cliente con ID {idcliente} no encontrado.'}), 404

        # Verificar producto
        producto = Producto.query.filter_by(codigo=codigo_producto, idcliente=idcliente).first()
        if not producto:
            return jsonify({'error': f'Producto con código {codigo_producto} no encontrado.'}), 404

        # Obtener IDs de bodegas si se especifican
        bodegas_ids = None
        if bodegas:
            bodegas_list = bodegas.split(',')
            bodegas_ids = [b.id for b in Bodega.query.filter(Bodega.nombre.in_(bodegas_list), Bodega.idcliente == idcliente).all()]
            if not bodegas_ids:
                return jsonify({'error': 'Ninguna de las bodegas especificadas fue encontrada.'}), 404

        # Calcular saldo inicial antes del rango
        saldo_bodegas = {}
        saldo_costo_total_bodegas = {}
        kardex_interno_query = Kardex.query.filter(
            Kardex.producto_id == producto.id,
            Kardex.idcliente == idcliente,
            Kardex.fecha < fecha_inicio_dt
        )
        if bodegas_ids:
            kardex_interno_query = kardex_interno_query.filter(
                (Kardex.bodega_origen_id.in_(bodegas_ids)) | (Kardex.bodega_destino_id.in_(bodegas_ids))
            )
        kardex_interno = kardex_interno_query.order_by(Kardex.fecha).all()

        for movimiento in kardex_interno:
            if movimiento.tipo_movimiento == 'SALIDA' and movimiento.bodega_origen_id:
                saldo_bodegas[movimiento.bodega_origen_id] = saldo_bodegas.get(movimiento.bodega_origen_id, 0) - movimiento.cantidad
                saldo_costo_total_bodegas[movimiento.bodega_origen_id] = saldo_costo_total_bodegas.get(movimiento.bodega_origen_id, 0) - (movimiento.costo_total or 0)
            elif movimiento.tipo_movimiento == 'ENTRADA' and movimiento.bodega_destino_id:
                saldo_bodegas[movimiento.bodega_destino_id] = saldo_bodegas.get(movimiento.bodega_destino_id, 0) + movimiento.cantidad
                saldo_costo_total_bodegas[movimiento.bodega_destino_id] = saldo_costo_total_bodegas.get(movimiento.bodega_destino_id, 0) + (movimiento.costo_total or 0)
            elif movimiento.tipo_movimiento == 'TRASLADO':
                if movimiento.bodega_origen_id:
                    saldo_bodegas[movimiento.bodega_origen_id] = saldo_bodegas.get(movimiento.bodega_origen_id, 0) - movimiento.cantidad
                    saldo_costo_total_bodegas[movimiento.bodega_origen_id] = saldo_costo_total_bodegas.get(movimiento.bodega_origen_id, 0) - (movimiento.costo_total or 0)
                if movimiento.bodega_destino_id:
                    saldo_bodegas[movimiento.bodega_destino_id] = saldo_bodegas.get(movimiento.bodega_destino_id, 0) + movimiento.cantidad
                    saldo_costo_total_bodegas[movimiento.bodega_destino_id] = saldo_costo_total_bodegas.get(movimiento.bodega_destino_id, 0) + (movimiento.costo_total or 0)

        # Preparar saldos iniciales por bodega
        saldo_bodegas_nombres = {}
        total_saldo_global = 0
        total_costo_global = 0
        for bodega_id, saldo in saldo_bodegas.items():
            if saldo <= 0:
                continue
            bodega = Bodega.query.filter_by(id=bodega_id).first()
            if bodega:
                costo_total = saldo_costo_total_bodegas.get(bodega_id, 0)
                costo_unitario = costo_total / saldo if saldo > 0 else 0.0
                saldo_bodegas_nombres[bodega.nombre] = {
                    'cantidad': float(saldo),
                    'costo_total': float(costo_total),
                    'costo_unitario': float(costo_unitario)
                }
                total_saldo_global += saldo
                total_costo_global += costo_total

        saldo_costo_unitario_global = total_costo_global / total_saldo_global if total_saldo_global > 0 else 0.0

        # Consultar movimientos en el rango
        movimientos_query = Kardex.query.filter(
            Kardex.producto_id == producto.id,
            Kardex.idcliente == idcliente,
            Kardex.fecha >= fecha_inicio_dt,
            Kardex.fecha <= fecha_fin_dt
        )
        if bodegas_ids:
            movimientos_query = movimientos_query.filter(
                (Kardex.bodega_origen_id.in_(bodegas_ids)) | (Kardex.bodega_destino_id.in_(bodegas_ids))
            )
        movimientos = movimientos_query.order_by(Kardex.fecha).all()

        kardex = []
        saldo_actual = saldo_bodegas.copy()
        saldo_costo_total_actual = saldo_costo_total_bodegas.copy()
        total_saldo_global_actual = total_saldo_global
        total_costo_global_actual = total_costo_global

        # Registrar saldos iniciales
        for bodega_nombre, saldos in saldo_bodegas_nombres.items():
            kardex.append({
                'fecha': fecha_inicio_dt.strftime('%Y-%m-%d 00:00:00'),
                'tipo': 'SALDO INICIAL',
                'cantidad': saldos['cantidad'],
                'bodega': bodega_nombre,
                'saldo': saldos['cantidad'],
                'costo_unitario': saldos['costo_unitario'],
                'costo_total': saldos['costo_total'],
                'saldo_costo_unitario': saldos['costo_unitario'],
                'saldo_costo_total': saldos['costo_total'],
                'saldo_costo_unitario_global': saldo_costo_unitario_global,
                'descripcion': 'Saldo inicial antes del rango de consulta'
            })

        # Procesar movimientos
        for movimiento in movimientos:
            if movimiento.tipo_movimiento == 'ENTRADA' and movimiento.bodega_destino_id:
                bodega = movimiento.bodega_destino.nombre if movimiento.bodega_destino else 'N/A'
                saldo_antes = saldo_actual.get(movimiento.bodega_destino_id, 0)
                costo_total_antes = saldo_costo_total_actual.get(movimiento.bodega_destino_id, 0)

                saldo_actual[movimiento.bodega_destino_id] = saldo_antes + movimiento.cantidad
                costo_total_movimiento = movimiento.costo_total or (movimiento.cantidad * movimiento.costo_unitario)
                saldo_costo_total_actual[movimiento.bodega_destino_id] = costo_total_antes + costo_total_movimiento
                total_saldo_global_actual += movimiento.cantidad
                total_costo_global_actual += costo_total_movimiento

                saldo_costo_unitario_bodega = (
                    saldo_costo_total_actual[movimiento.bodega_destino_id] / saldo_actual[movimiento.bodega_destino_id]
                    if saldo_actual[movimiento.bodega_destino_id] > 0 else 0.0
                )
                saldo_costo_unitario_global = (
                    total_costo_global_actual / total_saldo_global_actual if total_saldo_global_actual > 0 else 0.0
                )

                kardex.append({
                    'fecha': movimiento.fecha.strftime('%Y-%m-%d %H:%M:%S'),
                    'tipo': 'ENTRADA',
                    'cantidad': float(movimiento.cantidad),
                    'bodega': bodega,
                    'saldo': float(saldo_actual[movimiento.bodega_destino_id]),
                    'costo_unitario': float(movimiento.costo_unitario or 0.0),
                    'costo_total': float(costo_total_movimiento),
                    'saldo_costo_unitario': float(saldo_costo_unitario_bodega),
                    'saldo_costo_total': float(saldo_costo_total_actual[movimiento.bodega_destino_id]),
                    'saldo_costo_unitario_global': float(saldo_costo_unitario_global),
                    'descripcion': movimiento.referencia or 'Entrada registrada'
                })

            elif movimiento.tipo_movimiento == 'SALIDA' and movimiento.bodega_origen_id:
                bodega = movimiento.bodega_origen.nombre if movimiento.bodega_origen else 'N/A'
                saldo_antes = saldo_actual.get(movimiento.bodega_origen_id, 0)
                costo_total_antes = saldo_costo_total_actual.get(movimiento.bodega_origen_id, 0)
                costo_unitario_antes = costo_total_antes / saldo_antes if saldo_antes > 0 else 0.0

                saldo_actual[movimiento.bodega_origen_id] = saldo_antes - movimiento.cantidad
                costo_total_movimiento = movimiento.costo_total or (movimiento.cantidad * (movimiento.costo_unitario or costo_unitario_antes))
                saldo_costo_total_actual[movimiento.bodega_origen_id] = costo_total_antes - costo_total_movimiento
                total_saldo_global_actual -= movimiento.cantidad
                total_costo_global_actual -= costo_total_movimiento

                saldo_costo_unitario_bodega = (
                    saldo_costo_total_actual[movimiento.bodega_origen_id] / saldo_actual[movimiento.bodega_origen_id]
                    if saldo_actual[movimiento.bodega_origen_id] > 0 else 0.0
                )
                saldo_costo_unitario_global = (
                    total_costo_global_actual / total_saldo_global_actual if total_saldo_global_actual > 0 else 0.0
                )

                kardex.append({
                    'fecha': movimiento.fecha.strftime('%Y-%m-%d %H:%M:%S'),
                    'tipo': 'SALIDA',
                    'cantidad': float(movimiento.cantidad),
                    'bodega': bodega,
                    'saldo': float(saldo_actual[movimiento.bodega_origen_id]),
                    'costo_unitario': float(movimiento.costo_unitario or costo_unitario_antes),
                    'costo_total': float(costo_total_movimiento),
                    'saldo_costo_unitario': float(saldo_costo_unitario_bodega),
                    'saldo_costo_total': float(saldo_costo_total_actual[movimiento.bodega_origen_id]),
                    'saldo_costo_unitario_global': float(saldo_costo_unitario_global),
                    'descripcion': movimiento.referencia or 'Salida registrada'
                })

            elif movimiento.tipo_movimiento == 'TRASLADO' and movimiento.bodega_origen_id and movimiento.bodega_destino_id:
                # Salida desde origen
                bodega_origen = movimiento.bodega_origen.nombre
                saldo_origen_antes = saldo_actual.get(movimiento.bodega_origen_id, 0)
                costo_total_origen_antes = saldo_costo_total_actual.get(movimiento.bodega_origen_id, 0)
                costo_unitario_origen = costo_total_origen_antes / saldo_origen_antes if saldo_origen_antes > 0 else 0.0
                costo_total_traslado = movimiento.cantidad * costo_unitario_origen

                saldo_actual[movimiento.bodega_origen_id] = saldo_origen_antes - movimiento.cantidad
                saldo_costo_total_actual[movimiento.bodega_origen_id] = costo_total_origen_antes - costo_total_traslado
                saldo_costo_unitario_origen = (
                    saldo_costo_total_actual[movimiento.bodega_origen_id] / saldo_actual[movimiento.bodega_origen_id]
                    if saldo_actual[movimiento.bodega_origen_id] > 0 else 0.0
                )

                kardex.append({
                    'fecha': movimiento.fecha.strftime('%Y-%m-%d %H:%M:%S'),
                    'tipo': 'SALIDA',
                    'cantidad': float(movimiento.cantidad),
                    'bodega': bodega_origen,
                    'saldo': float(saldo_actual[movimiento.bodega_origen_id]),
                    'costo_unitario': float(costo_unitario_origen),
                    'costo_total': float(costo_total_traslado),
                    'saldo_costo_unitario': float(saldo_costo_unitario_origen),
                    'saldo_costo_total': float(saldo_costo_total_actual[movimiento.bodega_origen_id]),
                    'saldo_costo_unitario_global': float(saldo_costo_unitario_global),
                    'descripcion': f'Traslado a {movimiento.bodega_destino.nombre}. Ref: {movimiento.referencia or "N/A"}'
                })

                # Entrada en destino
                bodega_destino = movimiento.bodega_destino.nombre
                saldo_destino_antes = saldo_actual.get(movimiento.bodega_destino_id, 0)
                costo_total_destino_antes = saldo_costo_total_actual.get(movimiento.bodega_destino_id, 0)

                saldo_actual[movimiento.bodega_destino_id] = saldo_destino_antes + movimiento.cantidad
                saldo_costo_total_actual[movimiento.bodega_destino_id] = costo_total_destino_antes + costo_total_traslado
                saldo_costo_unitario_destino = (
                    saldo_costo_total_actual[movimiento.bodega_destino_id] / saldo_actual[movimiento.bodega_destino_id]
                    if saldo_actual[movimiento.bodega_destino_id] > 0 else 0.0
                )

                kardex.append({
                    'fecha': movimiento.fecha.strftime('%Y-%m-%d %H:%M:%S'),
                    'tipo': 'ENTRADA',
                    'cantidad': float(movimiento.cantidad),
                    'bodega': bodega_destino,
                    'saldo': float(saldo_actual[movimiento.bodega_destino_id]),
                    'costo_unitario': float(costo_unitario_origen),
                    'costo_total': float(costo_total_traslado),
                    'saldo_costo_unitario': float(saldo_costo_unitario_destino),
                    'saldo_costo_total': float(saldo_costo_total_actual[movimiento.bodega_destino_id]),
                    'saldo_costo_unitario_global': float(saldo_costo_unitario_global),
                    'descripcion': f'Traslado desde {bodega_origen}. Ref: {movimiento.referencia or "N/A"}'
                })

        if not kardex:
            bodegas_str = bodegas if bodegas else "todas las bodegas"
            return jsonify({
                'error': f'No hay movimientos para el producto {codigo_producto} en {bodegas_str} en el rango de fechas seleccionado.'
            }), 404

        # Generar PDF
        buffer = BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=landscape(letter))
        pdf.setTitle(f"Kardex_{codigo_producto}_{fecha_inicio}_{fecha_fin}")

        # Encabezado
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawCentredString(400, 550, "Kardex de Inventario")
        pdf.setFont("Helvetica", 10)
        pdf.drawString(30, 530, f"Cliente: {cliente.nombre}")
        pdf.drawString(30, 510, f"Producto: {producto.nombre} (Código: {producto.codigo})")
        pdf.drawString(30, 490, f"Rango de Fechas: {fecha_inicio} a {fecha_fin}")
        bodegas_str = ", ".join(bodegas.split(',')) if bodegas else "Todos los almacenes"
        pdf.drawString(30, 470, f"Almacenes: {bodegas_str}")
        y = 450

        # Resumen por almacén
        almacenes = sorted(set(mov['bodega'] for mov in kardex if mov['bodega'] and mov['bodega'] != 'N/A'))
        resumen = []
        for almacen in almacenes:
            movimientos_almacen = [m for m in kardex if m['bodega'] == almacen]
            ultimo_mov = max(movimientos_almacen, key=lambda x: datetime.strptime(x['fecha'], '%Y-%m-%d %H:%M:%S'))
            resumen.append({
                'almacen': almacen,
                'stock_final': ultimo_mov['saldo'],
                'valor_acumulado': ultimo_mov['saldo_costo_total'],
                'cpp': ultimo_mov['saldo_costo_unitario'],
            })
        total_stock = sum(r['stock_final'] for r in resumen)
        total_valor = sum(r['valor_acumulado'] for r in resumen)
        cpp_global = total_valor / total_stock if total_stock > 0 else 0.0

        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(30, y, "Resumen por Almacén")
        pdf.line(30, y - 5, 750, y - 5)
        y -= 20
        pdf.setFont("Helvetica", 10)
        pdf.drawString(30, y, f"CPP Global: ${cpp_global:.2f}")
        y -= 20

        pdf.setFont("Helvetica-Bold", 9)
        pdf.drawString(30, y, "Almacén")
        pdf.drawString(150, y, "Stock Final")
        pdf.drawString(250, y, "Valor Acumulado")
        pdf.drawString(350, y, "CPP")
        pdf.line(30, y - 5, 450, y - 5)
        y -= 15

        pdf.setFont("Helvetica", 9)
        for r in resumen:
            pdf.drawString(30, y, r['almacen'])
            pdf.drawString(150, y, f"{r['stock_final']:.3f}")
            pdf.drawString(250, y, f"${r['valor_acumulado']:.2f}")
            pdf.drawString(350, y, f"${r['cpp']:.2f}")
            y -= 15

        pdf.setFont("Helvetica-Bold", 9)
        pdf.drawString(30, y, "Total")
        pdf.drawString(150, y, f"{total_stock:.3f}")
        pdf.drawString(250, y, f"${total_valor:.2f}")
        y -= 25

        # Tabla de movimientos
        if y < 100:
            pdf.showPage()
            y = 550

        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(30, y, "Movimientos del Producto")
        pdf.line(30, y - 5, 750, y - 5)
        y -= 20

        # Definir anchos de columnas
        ancho_fecha = 90
        ancho_documento = 60
        ancho_almacen = 80
        ancho_cantidad = 50
        ancho_costo = 50
        ancho_costo_total = 60
        ancho_cantidad_acumulada = 60
        ancho_valor_acumulado = 70
        ancho_cpp = 50
        ancho_cpp_global = 60
        ancho_descripcion = 750 - (
            ancho_fecha + ancho_documento + ancho_almacen + ancho_cantidad + ancho_costo +
            ancho_costo_total + ancho_cantidad_acumulada + ancho_valor_acumulado + ancho_cpp + ancho_cpp_global + 30
        )

        # Encabezados de tabla
        pdf.setFont("Helvetica-Bold", 8)
        pdf.drawString(30, y, "Fecha")
        pdf.drawString(30 + ancho_fecha, y, "Tipo")
        pdf.drawString(30 + ancho_fecha + ancho_documento, y, "Almacén")
        pdf.drawString(30 + ancho_fecha + ancho_documento + ancho_almacen, y, "Cantidad")
        pdf.drawString(30 + ancho_fecha + ancho_documento + ancho_almacen + ancho_cantidad, y, "Costo Unit.")
        pdf.drawString(30 + ancho_fecha + ancho_documento + ancho_almacen + ancho_cantidad + ancho_costo, y, "Costo Total")
        pdf.drawString(30 + ancho_fecha + ancho_documento + ancho_almacen + ancho_cantidad + ancho_costo + ancho_costo_total, y, "Cant. Acum.")
        pdf.drawString(30 + ancho_fecha + ancho_documento + ancho_almacen + ancho_cantidad + ancho_costo + ancho_costo_total + ancho_cantidad_acumulada, y, "Valor Acum.")
        pdf.drawString(30 + ancho_fecha + ancho_documento + ancho_almacen + ancho_cantidad + ancho_costo + ancho_costo_total + ancho_cantidad_acumulada + ancho_valor_acumulado, y, "CPP")
        pdf.drawString(30 + ancho_fecha + ancho_documento + ancho_almacen + ancho_cantidad + ancho_costo + ancho_costo_total + ancho_cantidad_acumulada + ancho_valor_acumulado + ancho_cpp, y, "CPP Global")
        pdf.drawString(30 + ancho_fecha + ancho_documento + ancho_almacen + ancho_cantidad + ancho_costo + ancho_costo_total + ancho_cantidad_acumulada + ancho_valor_acumulado + ancho_cpp + ancho_cpp_global, y, "Descripción")
        pdf.line(30, y - 5, 750, y - 5)
        y -= 15

        # Filas de movimientos
        pdf.setFont("Helvetica", 7)
        for movimiento in kardex:
            if y < 50:
                pdf.showPage()
                pdf.setFont("Helvetica", 7)
                y = 550

            cantidad = f"-{movimiento['cantidad']:.3f}" if movimiento['tipo'] == "SALIDA" else f"{movimiento['cantidad']:.3f}"
            costo_total = f"-${movimiento['costo_total']:.2f}" if movimiento['tipo'] == "SALIDA" else f"${movimiento['costo_total']:.2f}"
            descripcion = movimiento['descripcion'] or "N/A"
            descripcion_lines = simpleSplit(descripcion, "Helvetica", 7, ancho_descripcion)

            pdf.drawString(30, y, movimiento['fecha'])
            pdf.drawString(30 + ancho_fecha, y, movimiento['tipo'])
            pdf.drawString(30 + ancho_fecha + ancho_documento, y, movimiento['bodega'] or "N/A")
            pdf.drawString(30 + ancho_fecha + ancho_documento + ancho_almacen, y, cantidad)
            pdf.drawString(30 + ancho_fecha + ancho_documento + ancho_almacen + ancho_cantidad, y, f"${movimiento['costo_unitario']:.2f}")
            pdf.drawString(30 + ancho_fecha + ancho_documento + ancho_almacen + ancho_cantidad + ancho_costo, y, costo_total)
            pdf.drawString(30 + ancho_fecha + ancho_documento + ancho_almacen + ancho_cantidad + ancho_costo + ancho_costo_total, y, f"{movimiento['saldo']:.3f}")
            pdf.drawString(30 + ancho_fecha + ancho_documento + ancho_almacen + ancho_cantidad + ancho_costo + ancho_costo_total + ancho_cantidad_acumulada, y, f"${movimiento['saldo_costo_total']:.2f}")
            pdf.drawString(30 + ancho_fecha + ancho_documento + ancho_almacen + ancho_cantidad + ancho_costo + ancho_costo_total + ancho_cantidad_acumulada + ancho_valor_acumulado, y, f"${movimiento['saldo_costo_unitario']:.2f}")
            pdf.drawString(30 + ancho_fecha + ancho_documento + ancho_almacen + ancho_cantidad + ancho_costo + ancho_costo_total + ancho_cantidad_acumulada + ancho_valor_acumulado + ancho_cpp, y, f"${movimiento['saldo_costo_unitario_global']:.2f}")

            # Manejar descripción multilínea
            for i, line in enumerate(descripcion_lines):
                if i == 0:
                    pdf.drawString(
                        30 + ancho_fecha + ancho_documento + ancho_almacen + ancho_cantidad + ancho_costo +
                        ancho_costo_total + ancho_cantidad_acumulada + ancho_valor_acumulado + ancho_cpp + ancho_cpp_global,
                        y, line
                    )
                else:
                    y -= 12
                    if y < 50:
                        pdf.showPage()
                        pdf.setFont("Helvetica", 7)
                        y = 550
                    pdf.drawString(
                        30 + ancho_fecha + ancho_documento + ancho_almacen + ancho_cantidad + ancho_costo +
                        ancho_costo_total + ancho_cantidad_acumulada + ancho_valor_acumulado + ancho_cpp + ancho_cpp_global,
                        y, line
                    )
            y -= 12

        pdf.save()
        buffer.seek(0)

        # Generar nombre del archivo
        bodegas_str = bodegas.replace(',', '_') if bodegas else 'todas'
        filename = f"kardex_{idcliente}_{codigo_producto}_{fecha_inicio}_{fecha_fin}_{bodegas_str}.pdf"

        return send_file(
            buffer,
            as_attachment=True,
            download_name=filename,
            mimetype="application/pdf"
        )

    except Exception as e:
        print(f"Error al generar PDF del Kardex: {str(e)}")
        return jsonify({'error': f'Error al generar el PDF: {str(e)}'}), 500


# ENDPOINTS PAGINA DE TRANSLADOS CANTIDADES:
@app.route('/api/trasladar_varios', methods=['POST'])
@jwt_required()
def trasladar_varios():
    try:
        claims = get_jwt()
        idcliente = claims.get('idcliente')
        if not idcliente:
            return jsonify({'error': 'No se pudo determinar el cliente asociado'}), 403

        if not has_permission(claims, 'inventario', 'traslados', 'editar'):
            return jsonify({'error': 'No tienes permiso para realizar traslados'}), 403

        data = request.get_json()
        productos = data.get('productos', [])
        if not productos:
            return jsonify({'error': 'No se proporcionaron productos para trasladar.'}), 400

        app.logger.debug(f"Datos recibidos: {productos}")

        ultimo_consecutivo = db.session.query(
            func.max(RegistroMovimientos.consecutivo)
        ).filter(RegistroMovimientos.consecutivo.like('T%')).scalar() or "T00000"
        nuevo_consecutivo = f"T{int(ultimo_consecutivo[1:]) + 1:05d}"

        with db.session.no_autoflush:
            for producto in productos:
                codigo = producto.get('codigo')
                bodega_origen = producto.get('bodega_origen')
                bodega_destino = producto.get('bodega_destino')
                cantidad = producto.get('cantidad')

                app.logger.debug(f"Procesando producto: {codigo}, origen: {bodega_origen}, destino: {bodega_destino}, cantidad: {cantidad}")

                if not all([codigo, bodega_origen, bodega_destino, cantidad]):
                    return jsonify({'error': f'Datos incompletos para el producto {codigo}.'}), 400
                if cantidad <= 0:
                    return jsonify({'error': f'La cantidad para el producto {codigo} debe ser mayor a 0.'}), 400
                if bodega_origen == bodega_destino:
                    return jsonify({'error': f'Las bodegas origen y destino no pueden ser iguales para el producto {codigo}.'}), 400

                producto_obj = Producto.query.filter_by(codigo=codigo, idcliente=idcliente).first()
                if not producto_obj:
                    return jsonify({'error': f'Producto con código {codigo} no encontrado.'}), 404

                app.logger.debug(f"Producto encontrado: id={producto_obj.id}, nombre={producto_obj.nombre}")

                bodega_origen_obj = Bodega.query.filter_by(nombre=bodega_origen, idcliente=idcliente).first()
                bodega_destino_obj = Bodega.query.filter_by(nombre=bodega_destino, idcliente=idcliente).first()
                if not bodega_origen_obj or not bodega_destino_obj:
                    return jsonify({'error': f'Bodegas no encontradas: Origen={bodega_origen}, Destino={bodega_destino}.'}), 404

                app.logger.debug(f"Bodegas: origen_id={bodega_origen_obj.id}, destino_id={bodega_destino_obj.id}")

                # Verificar inventario en estado_inventario
                inventario_origen = EstadoInventario.query.filter_by(
                    bodega_id=bodega_origen_obj.id,
                    producto_id=producto_obj.id,
                    idcliente=idcliente
                ).first()

                # Si no existe, intentar inicializar desde inventario_bodega
                if not inventario_origen:
                    inv_bodega = InventarioBodega.query.filter_by(
                        bodega_id=bodega_origen_obj.id,
                        producto_id=producto_obj.id,
                        idcliente=idcliente
                    ).first()
                    if inv_bodega and inv_bodega.cantidad >= cantidad:
                        inventario_origen = EstadoInventario(
                            idcliente=idcliente,
                            bodega_id=bodega_origen_obj.id,
                            producto_id=producto_obj.id,
                            cantidad=inv_bodega.cantidad,
                            ultima_actualizacion=obtener_hora_colombia(),
                            costo_unitario=inv_bodega.costo_unitario,
                            costo_total=inv_bodega.costo_total
                        )
                        db.session.add(inventario_origen)
                        app.logger.debug(f"Inicializado estado_inventario para {codigo} desde inventario_bodega: {inv_bodega.cantidad}")
                    else:
                        return jsonify({
                            'error': f'Inventario insuficiente en {bodega_origen} para el producto {codigo}. '
                                     f'Disponible: 0, Requerido: {cantidad}.'
                        }), 400

                if inventario_origen.cantidad < cantidad:
                    return jsonify({
                        'error': f'Inventario insuficiente en {bodega_origen} para el producto {codigo}. '
                                 f'Disponible: {inventario_origen.cantidad}, Requerido: {cantidad}.'
                    }), 400

                app.logger.debug(f"Inventario origen para {codigo}: {inventario_origen.cantidad}")

                # Calcular costo unitario promedio desde Kardex (como en el original)
                movimientos_previos = Kardex.query.filter(
                    Kardex.producto_id == producto_obj.id,
                    Kardex.bodega_destino_id == bodega_origen_obj.id,
                    Kardex.idcliente == idcliente,
                    Kardex.fecha <= obtener_hora_colombia()
                ).order_by(Kardex.fecha.desc()).first()
                costo_unitario = movimientos_previos.saldo_costo_unitario if movimientos_previos else inventario_origen.costo_unitario
                costo_total = cantidad * costo_unitario

                # Calcular saldos actuales
                saldo_origen_previo = inventario_origen.cantidad
                inventario_destino = EstadoInventario.query.filter_by(
                    bodega_id=bodega_destino_obj.id,
                    producto_id=producto_obj.id,
                    idcliente=idcliente
                ).first()
                saldo_destino_previo = inventario_destino.cantidad if inventario_destino else 0

                # Actualizar inventario
                inventario_origen.cantidad -= cantidad
                if inventario_origen.cantidad == 0:
                    db.session.delete(inventario_origen)
                    app.logger.debug(f"Eliminado registro de estado_inventario para {codigo} en {bodega_origen}")

                if not inventario_destino:
                    inventario_destino = EstadoInventario(
                        idcliente=idcliente,
                        bodega_id=bodega_destino_obj.id,
                        producto_id=producto_obj.id,
                        cantidad=0,
                        ultima_actualizacion=obtener_hora_colombia(),
                        costo_unitario=costo_unitario,
                        costo_total=0
                    )
                    db.session.add(inventario_destino)
                inventario_destino.cantidad += cantidad
                inventario_destino.costo_total = inventario_destino.cantidad * costo_unitario
                inventario_destino.ultima_actualizacion = obtener_hora_colombia()

                # Registrar movimientos en Kardex
                kardex_salida = Kardex(
                    idcliente=idcliente,
                    producto_id=producto_obj.id,
                    tipo_movimiento='SALIDA',
                    cantidad=cantidad,
                    bodega_origen_id=bodega_origen_obj.id,
                    costo_unitario=costo_unitario,
                    costo_total=costo_total,
                    saldo_cantidad=saldo_origen_previo - cantidad,
                    saldo_costo_unitario=costo_unitario,
                    saldo_costo_total=(saldo_origen_previo - cantidad) * costo_unitario,
                    fecha=obtener_hora_colombia(),
                    referencia=f"Traslado {nuevo_consecutivo} de {bodega_origen} a {bodega_destino}"
                )
                kardex_entrada = Kardex(
                    idcliente=idcliente,
                    producto_id=producto_obj.id,
                    tipo_movimiento='ENTRADA',
                    cantidad=cantidad,
                    bodega_destino_id=bodega_destino_obj.id,
                    costo_unitario=costo_unitario,
                    costo_total=costo_total,
                    saldo_cantidad=saldo_destino_previo + cantidad,
                    saldo_costo_unitario=costo_unitario,
                    saldo_costo_total=(saldo_destino_previo + cantidad) * costo_unitario,
                    fecha=obtener_hora_colombia(),
                    referencia=f"Traslado {nuevo_consecutivo} de {bodega_origen} a {bodega_destino}"
                )
                db.session.add(kardex_salida)
                db.session.add(kardex_entrada)

                # Registrar en registro_movimientos
                nuevo_movimiento = RegistroMovimientos(
                    idcliente=idcliente,
                    consecutivo=nuevo_consecutivo,
                    tipo_movimiento='TRASLADO',
                    producto_id=producto_obj.id,
                    bodega_origen_id=bodega_origen_obj.id,
                    bodega_destino_id=bodega_destino_obj.id,
                    cantidad=cantidad,
                    fecha=obtener_hora_colombia(),
                    descripcion=f"Traslado de {cantidad} unidades de {codigo} de {bodega_origen} a {bodega_destino}",
                    costo_unitario=costo_unitario,
                    costo_total=costo_total
                )
                db.session.add(nuevo_movimiento)

            db.session.commit()
            app.logger.debug(f"Traslado {nuevo_consecutivo} completado exitosamente")
            return jsonify({'message': 'Traslado realizado correctamente.', 'consecutivo': nuevo_consecutivo}), 200

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error al registrar traslados múltiples: {str(e)}")
        return jsonify({'error': f'Error al registrar los traslados: {str(e)}'}), 500
    

@app.route('/api/traslados-por-bodega', methods=['GET'])
@jwt_required()
def consultar_traslados_por_bodega():
    try:
        claims = get_jwt()
        idcliente = claims.get('idcliente')
        if not idcliente:
            return jsonify({'error': 'No se pudo determinar el cliente asociado'}), 403

        if not has_permission(claims, 'inventario', 'traslados', 'ver'):
            return jsonify({'error': 'No tienes permiso para consultar traslados'}), 403

        from sqlalchemy.orm import aliased
        BodegaOrigen = aliased(Bodega)
        BodegaDestino = aliased(Bodega)

        consecutivo = request.args.get('consecutivo')
        codigo_producto = request.args.get('codigo')
        fecha_inicio = request.args.get('fecha_inicio')
        fecha_fin = request.args.get('fecha_fin')
        bodega_origen = request.args.get('bodega_origen')
        bodega_destino = request.args.get('bodega_destino')

        query = db.session.query(
            RegistroMovimientos.consecutivo,
            RegistroMovimientos.fecha,
            Producto.nombre.label('producto_nombre'),
            RegistroMovimientos.cantidad,
            BodegaOrigen.nombre.label('bodega_origen'),
            BodegaDestino.nombre.label('bodega_destino'),
        ).join(
            Producto, RegistroMovimientos.producto_id == Producto.id
        ).join(
            BodegaOrigen, RegistroMovimientos.bodega_origen_id == BodegaOrigen.id
        ).join(
            BodegaDestino, RegistroMovimientos.bodega_destino_id == BodegaDestino.id
        ).filter(
            RegistroMovimientos.tipo_movimiento == 'TRASLADO',
            RegistroMovimientos.idcliente == idcliente
        )

        if consecutivo:
            query = query.filter(RegistroMovimientos.consecutivo == consecutivo)
        if codigo_producto:
            producto = Producto.query.filter_by(codigo=codigo_producto, idcliente=idcliente).first()
            if not producto:
                return jsonify({'error': f'Producto con código {codigo_producto} no encontrado.'}), 404
            query = query.filter(RegistroMovimientos.producto_id == producto.id)
        if fecha_inicio:
            try:
                datetime.strptime(fecha_inicio, '%Y-%m-%d')
                query = query.filter(RegistroMovimientos.fecha >= fecha_inicio)
            except ValueError:
                return jsonify({'error': 'Formato de fecha_inicio inválido. Use YYYY-MM-DD.'}), 400
        if fecha_fin:
            try:
                datetime.strptime(fecha_fin, '%Y-%m-%d')
                query = query.filter(RegistroMovimientos.fecha <= fecha_fin)
            except ValueError:
                return jsonify({'error': 'Formato de fecha_fin inválido. Use YYYY-MM-DD.'}), 400
        if bodega_origen:
            bodega = Bodega.query.filter_by(nombre=bodega_origen, idcliente=idcliente).first()
            if not bodega:
                return jsonify({'error': f'Bodega de origen {bodega_origen} no encontrada.'}), 404
            query = query.filter(RegistroMovimientos.bodega_origen_id == bodega.id)
        if bodega_destino:
            bodega = Bodega.query.filter_by(nombre=bodega_destino, idcliente=idcliente).first()
            if not bodega:
                return jsonify({'error': f'Bodega de destino {bodega_destino} no encontrada.'}), 404
            query = query.filter(RegistroMovimientos.bodega_destino_id == bodega.id)

        traslados = query.order_by(RegistroMovimientos.fecha).all()
        resultado = [
            {
                'consecutivo': traslado.consecutivo,
                'fecha': traslado.fecha.strftime('%Y-%m-%d %H:%M:%S'),
                'producto': traslado.producto_nombre,
                'cantidad': traslado.cantidad,
                'bodega_origen': traslado.bodega_origen,
                'bodega_destino': traslado.bodega_destino,
            }
            for traslado in traslados
        ]
        return jsonify(resultado)

    except Exception as e:
        print(f"Error al consultar traslados por bodega: {e}")
        return jsonify({'error': 'Error al consultar traslados por bodega'}), 500

@app.route('/api/traslados', methods=['GET'])
@jwt_required()
def consultar_traslados():
    try:
        claims = get_jwt()
        idcliente = claims.get('idcliente')
        if not idcliente:
            return jsonify({'error': 'No se pudo determinar el cliente asociado'}), 403

        if not has_permission(claims, 'inventario', 'traslados', 'ver'):
            return jsonify({'error': 'No tienes permiso para consultar traslados'}), 403

        from sqlalchemy.orm import aliased
        BodegaOrigen = aliased(Bodega)
        BodegaDestino = aliased(Bodega)

        consecutivo = request.args.get('consecutivo')
        codigo_producto = request.args.get('codigo')
        fecha_inicio = request.args.get('fecha_inicio')
        fecha_fin = request.args.get('fecha_fin')

        query = db.session.query(
            RegistroMovimientos.consecutivo,
            RegistroMovimientos.fecha,
            Producto.nombre.label('producto_nombre'),
            RegistroMovimientos.cantidad,
            BodegaOrigen.nombre.label('bodega_origen'),
            BodegaDestino.nombre.label('bodega_destino'),
        ).join(
            Producto, RegistroMovimientos.producto_id == Producto.id
        ).join(
            BodegaOrigen, RegistroMovimientos.bodega_origen_id == BodegaOrigen.id
        ).join(
            BodegaDestino, RegistroMovimientos.bodega_destino_id == BodegaDestino.id
        ).filter(
            RegistroMovimientos.tipo_movimiento == 'TRASLADO',
            RegistroMovimientos.idcliente == idcliente
        )

        if consecutivo:
            query = query.filter(RegistroMovimientos.consecutivo == consecutivo)
        if codigo_producto:
            producto = Producto.query.filter_by(codigo=codigo_producto, idcliente=idcliente).first()
            if not producto:
                return jsonify({'error': f'Producto con código {codigo_producto} no encontrado.'}), 404
            query = query.filter(RegistroMovimientos.producto_id == producto.id)
        if fecha_inicio:
            try:
                datetime.strptime(fecha_inicio, '%Y-%m-%d')
                query = query.filter(RegistroMovimientos.fecha >= fecha_inicio)
            except ValueError:
                return jsonify({'error': 'Formato de fecha_inicio inválido. Use YYYY-MM-DD.'}), 400
        if fecha_fin:
            try:
                datetime.strptime(fecha_fin, '%Y-%m-%d')
                query = query.filter(RegistroMovimientos.fecha <= fecha_fin)
            except ValueError:
                return jsonify({'error': 'Formato de fecha_fin inválido. Use YYYY-MM-DD.'}), 400

        traslados = query.order_by(RegistroMovimientos.fecha).all()
        resultado = [
            {
                'consecutivo': traslado.consecutivo,
                'fecha': traslado.fecha.strftime('%Y-%m-%d %H:%M:%S'),
                'producto': traslado.producto_nombre,
                'cantidad': traslado.cantidad,
                'bodega_origen': traslado.bodega_origen,
                'bodega_destino': traslado.bodega_destino,
            }
            for traslado in traslados
        ]
        return jsonify(resultado)

    except Exception as e:
        print(f"Error al consultar traslados: {e}")
        return jsonify({'error': 'Error al consultar traslados'}), 500

@app.route('/api/traslados-pdf', methods=['GET'])
@jwt_required()
def generar_traslados_pdf():
    try:
        claims = get_jwt()
        idcliente = claims.get('idcliente')
        if not idcliente:
            return jsonify({'error': 'No se pudo determinar el cliente asociado'}), 403

        if not has_permission(claims, 'inventario', 'traslados', 'ver'):
            return jsonify({'error': 'No tienes permiso para generar PDFs de traslados'}), 403

        consecutivo = request.args.get('consecutivo')
        codigo = request.args.get('codigo')
        fecha_inicio = request.args.get('fecha_inicio')
        fecha_fin = request.args.get('fecha_fin')
        bodega_origen = request.args.get('bodega_origen')
        bodega_destino = request.args.get('bodega_destino')

        query = RegistroMovimientos.query.filter_by(tipo_movimiento='TRASLADO', idcliente=idcliente)

        if consecutivo:
            query = query.filter(RegistroMovimientos.consecutivo == consecutivo)
        if codigo:
            producto = Producto.query.filter_by(codigo=codigo, idcliente=idcliente).first()
            if producto:
                query = query.filter(RegistroMovimientos.producto_id == producto.id)
        if fecha_inicio and fecha_fin:
            query = query.filter(RegistroMovimientos.fecha.between(fecha_inicio, fecha_fin))
        if bodega_origen:
            bodega = Bodega.query.filter_by(nombre=bodega_origen, idcliente=idcliente).first()
            if not bodega:
                return jsonify({'error': f'Bodega de origen {bodega_origen} no encontrada.'}), 404
            query = query.filter(RegistroMovimientos.bodega_origen_id == bodega.id)
        if bodega_destino:
            bodega = Bodega.query.filter_by(nombre=bodega_destino, idcliente=idcliente).first()
            if not bodega:
                return jsonify({'error': f'Bodega de destino {bodega_destino} no encontrada.'}), 404
            query = query.filter(RegistroMovimientos.bodega_destino_id == bodega.id)

        traslados = query.with_entities(
            RegistroMovimientos.consecutivo,
            func.min(RegistroMovimientos.fecha).label("fecha")
        ).group_by(RegistroMovimientos.consecutivo).all()

        if not traslados:
            return jsonify({'error': 'No se encontraron traslados'}), 404

        buffer = BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=letter)
        pdf.setTitle(f"Traslados_{fecha_inicio or 'todos'}_al_{fecha_fin or 'todos'}")

        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(30, 750, "Traslados Realizados")
        pdf.setFont("Helvetica", 12)
        pdf.drawString(30, 730, f"Rango de fecha: {fecha_inicio or 'Todos'} - {fecha_fin or 'Todos'}")
        pdf.drawString(30, 710, f"Bodega de Origen: {bodega_origen or 'Cualquiera'}")
        pdf.drawString(30, 690, f"Bodega de Destino: {bodega_destino or 'Cualquiera'}")
        pdf.line(30, 670, 570, 670)

        pdf.setFont("Helvetica-Bold", 10)
        y = 650
        pdf.drawString(30, y, "Consecutivo")
        pdf.drawString(200, y, "Fecha")
        pdf.line(30, y - 5, 570, y - 5)

        pdf.setFont("Helvetica", 10)
        y -= 20
        for traslado in traslados:
            if y < 50:
                pdf.showPage()
                pdf.setFont("Helvetica", 10)
                y = 750
                pdf.setFont("Helvetica-Bold", 10)
                pdf.drawString(30, y, "Consecutivo")
                pdf.drawString(200, y, "Fecha")
                pdf.line(30, y - 5, 570, y - 5)
                pdf.setFont("Helvetica", 10)
                y -= 20
            pdf.drawString(30, y, traslado.consecutivo)
            pdf.drawString(200, y, traslado.fecha.strftime('%Y-%m-%d %H:%M:%S'))
            y -= 15

        pdf.save()
        buffer.seek(0)
        return send_file(
            buffer,
            as_attachment=True,
            download_name=f"traslados_{fecha_inicio or 'todos'}_al_{fecha_fin or 'todos'}.pdf",
            mimetype="application/pdf"
        )
    except Exception as e:
        print(f"Error al generar PDF de traslados: {e}")
        return jsonify({'error': 'Ocurrió un error al generar el PDF.'}), 500

@app.route('/api/traslado-detalle-pdf/<consecutivo>', methods=['GET'])
@jwt_required()
def generar_traslado_detalle_pdf(consecutivo):
    try:
        claims = get_jwt()
        idcliente = claims.get('idcliente')
        if not idcliente:
            return jsonify({'error': 'No se pudo determinar el cliente asociado'}), 403

        if not has_permission(claims, 'inventario', 'traslados', 'ver'):
            return jsonify({'error': 'No tienes permiso para generar PDFs de traslados'}), 403

        traslados = RegistroMovimientos.query.filter_by(
            tipo_movimiento='TRASLADO', consecutivo=consecutivo, idcliente=idcliente
        ).all()

        if not traslados:
            return jsonify({'error': 'Traslado no encontrado'}), 404

        buffer = BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=letter)
        pdf.setTitle(f"Traslado_{consecutivo}")

        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(30, 750, "Traslado entre Bodegas")
        pdf.setFont("Helvetica", 12)
        pdf.drawString(30, 730, f"Número Traslado: {consecutivo}")
        pdf.drawString(30, 710, f"Fecha del Traslado: {traslados[0].fecha.strftime('%Y-%m-%d %H:%M:%S')}")
        pdf.line(30, 700, 570, 700)

        pdf.setFont("Helvetica-Bold", 10)
        y = 680
        pdf.drawString(30, y, "Producto")
        pdf.drawString(230, y, "Cantidad")
        pdf.drawString(310, y, "Bodega Origen")
        pdf.drawString(420, y, "Bodega Destino")
        pdf.line(30, y - 5, 570, y - 5)

        pdf.setFont("Helvetica", 10)
        y -= 20
        for traslado in traslados:
            if y < 100:
                pdf.showPage()
                pdf.setFont("Helvetica", 10)
                y = 750
                pdf.setFont("Helvetica-Bold", 10)
                pdf.drawString(30, y, "Producto")
                pdf.drawString(230, y, "Cantidad")
                pdf.drawString(310, y, "Bodega Origen")
                pdf.drawString(420, y, "Bodega Destino")
                pdf.line(30, y - 5, 570, y - 5)
                pdf.setFont("Helvetica", 10)
                y -= 20

            producto = Producto.query.get(traslado.producto_id)
            bodega_origen = Bodega.query.get(traslado.bodega_origen_id) if traslado.bodega_origen_id else None
            bodega_destino = Bodega.query.get(traslado.bodega_destino_id) if traslado.bodega_destino_id else None

            def draw_wrapped_text(pdf, x, y, text, max_width):
                words = text.split()
                line = ""
                y_current = y
                for word in words:
                    test_line = f"{line} {word}".strip()
                    if pdf.stringWidth(test_line, "Helvetica", 10) <= max_width:
                        line = test_line
                    else:
                        pdf.drawString(x, y_current, line)
                        line = word
                        y_current -= 12
                if line:
                    pdf.drawString(x, y_current, line)
                return y_current - 12

            y_inicial = y
            y_nueva = draw_wrapped_text(pdf, 30, y_inicial, producto.nombre if producto else "Desconocido", 200)
            y_nueva = min(y_nueva, draw_wrapped_text(pdf, 310, y_inicial, bodega_origen.nombre if bodega_origen else "N/A", 110))
            y_nueva = min(y_nueva, draw_wrapped_text(pdf, 420, y_inicial, bodega_destino.nombre if bodega_destino else "N/A", 150))
            pdf.drawString(230, y_inicial, str(traslado.cantidad))
            y = y_nueva - 15

        if y < 100:
            pdf.showPage()
            y = 750
        pdf.setFont("Helvetica", 12)
        y -= 40
        pdf.line(30, y, 210, y)
        pdf.drawString(30, y - 15, "Despachado por")
        pdf.line(230, y, 410, y)
        pdf.drawString(230, y - 15, "Entregado por")
        pdf.line(430, y, 610, y)
        pdf.drawString(430, y - 15, "Recibido")

        pdf.save()
        buffer.seek(0)
        return send_file(
            buffer,
            as_attachment=True,
            download_name=f"traslado_{consecutivo}.pdf",
            mimetype="application/pdf"
        )
    except Exception as e:
        print(f"Error al generar PDF del detalle del traslado: {e}")
        return jsonify({'error': 'Ocurrió un error al generar el PDF.'}), 500

# endpoints para Paginas de ajustes de inventario:
# Endpoint POST /api/ajuste-inventario
@app.route('/api/ajuste-inventario', methods=['POST'])
@jwt_required()
def ajuste_inventario():
    try:
        data = request.get_json()
        logger.info(f"Datos recibidos en ajuste-inventario: {data}")

        # Validar datos de entrada
        if not all(key in data for key in ['bodega', 'productos']):
            logger.error(f"Faltan datos en la solicitud: {data}")
            return jsonify({'error': 'Faltan datos: bodega o productos'}), 400

        bodega_nombre = data['bodega']
        productos = data['productos']
        logger.debug(f"Bodega: {bodega_nombre}, Productos: {productos}")

        # Obtener claims del JWT
        claims = get_jwt()
        idcliente = claims.get('idcliente')
        user_id = int(get_jwt_identity())  # Usar el 'sub' del token como usuario_id
        logger.debug(f"Claims obtenidos: idcliente={idcliente}, user_id={user_id}")

        if not idcliente:
            logger.error("No se encontró idcliente en el token")
            return jsonify({'error': 'No se encontró idcliente en el token'}), 403

        # Verificar permisos
        if not has_permission(claims, 'inventario', 'ajustes', 'editar'):
            logger.error(f"Usuario {user_id} no autorizado para realizar ajustes")
            return jsonify({'error': 'Usuario no autorizado para realizar ajustes'}), 403

        # Verificar usuario
        logger.debug(f"Buscando usuario con id={user_id}")
        usuario = db.session.get(Usuarios, user_id)
        if not usuario:
            logger.error(f"Usuario no encontrado: user_id={user_id}")
            return jsonify({'error': 'Usuario no encontrado o no pertenece al cliente'}), 404
        if usuario.idcliente != idcliente:
            logger.error(f"Usuario no pertenece al cliente: user_id={user_id}, usuario.idcliente={usuario.idcliente}, idcliente={idcliente}")
            return jsonify({'error': 'Usuario no encontrado o no pertenece al cliente'}), 404
        logger.debug(f"Usuario encontrado: usuario={usuario.usuario}, idcliente={usuario.idcliente}")

        # Verificar bodega
        logger.debug(f"Buscando bodega: nombre={bodega_nombre}, idcliente={idcliente}")
        bodega = Bodega.query.filter_by(nombre=bodega_nombre, idcliente=idcliente).first()
        if not bodega:
            logger.error(f"Bodega no encontrada: {bodega_nombre}, idcliente={idcliente}")
            return jsonify({'error': f'Bodega {bodega_nombre} no encontrada'}), 404
        logger.debug(f"Bodega encontrada: id={bodega.id}, nombre={bodega.nombre}")

        # Generar consecutivo y fecha
        consecutivo = generar_consecutivo()
        fecha_actual = obtener_hora_colombia()
        logger.debug(f"Consecutivo generado: {consecutivo}, Fecha: {fecha_actual}")

        for producto_data in productos:
            if not all(key in producto_data for key in ['codigoProducto', 'nuevaCantidad', 'tipoMovimiento']):
                logger.error(f"Faltan datos en producto: {producto_data}")
                return jsonify({'error': 'Faltan datos en producto: codigoProducto, nuevaCantidad o tipoMovimiento'}), 400

            codigo_producto = producto_data['codigoProducto']
            cantidad_ajuste = int(producto_data['nuevaCantidad'])
            tipo_movimiento = producto_data['tipoMovimiento']
            logger.debug(f"Procesando producto: codigo={codigo_producto}, cantidad={cantidad_ajuste}, tipo={tipo_movimiento}")

            if tipo_movimiento not in ['Incrementar', 'Disminuir']:
                logger.error(f"Tipo de movimiento inválido: {tipo_movimiento}, producto: {codigo_producto}")
                return jsonify({'error': f'Tipo de movimiento inválido para {codigo_producto}'}), 400

            # Verificar producto
            logger.debug(f"Buscando producto: codigo={codigo_producto}, idcliente={idcliente}")
            producto = Producto.query.filter_by(codigo=codigo_producto, idcliente=idcliente).first()
            if not producto:
                logger.error(f"Producto no encontrado: {codigo_producto}, idcliente={idcliente}")
                return jsonify({'error': f'Producto {codigo_producto} no encontrado'}), 404
            logger.debug(f"Producto encontrado: id={producto.id}, nombre={producto.nombre}")

            # Verificar inventario
            logger.debug(f"Buscando inventario: producto_id={producto.id}, bodega_id={bodega.id}")
            estado_inventario = EstadoInventario.query.filter_by(producto_id=producto.id, bodega_id=bodega.id).first()

            if not estado_inventario:
                if tipo_movimiento == 'Disminuir':
                    logger.error(f"No hay inventario para {codigo_producto} en {bodega_nombre}")
                    return jsonify({'error': f'No hay inventario de {codigo_producto} en {bodega_nombre}'}), 404
                estado_inventario = EstadoInventario(
                    idcliente=idcliente,
                    producto_id=producto.id,
                    bodega_id=bodega.id,
                    cantidad=0,
                    costo_unitario=Decimal('0.00'),
                    costo_total=Decimal('0.00'),
                    ultima_actualizacion=fecha_actual
                )
                db.session.add(estado_inventario)
                logger.debug(f"Creado nuevo estado_inventario para producto_id={producto.id}, bodega_id={bodega.id}")

            cantidad_anterior = estado_inventario.cantidad
            logger.debug(f"Cantidad anterior: {cantidad_anterior}")

            # Obtener último registro del Kardex
            logger.debug(f"Buscando último kardex: producto_id={producto.id}, idcliente={idcliente}")
            ultimo_kardex = Kardex.query.filter(
                Kardex.producto_id == producto.id,
                Kardex.idcliente == idcliente,
                (Kardex.bodega_origen_id == bodega.id) | (Kardex.bodega_destino_id == bodega.id)
            ).order_by(Kardex.fecha.desc()).first()

            # Determinar costo unitario
            costo_unitario = (
                ultimo_kardex.saldo_costo_unitario if ultimo_kardex and tipo_movimiento == 'Disminuir'
                else estado_inventario.costo_unitario or Decimal('0.00')
            )
            costo_total = Decimal(str(cantidad_ajuste)) * costo_unitario
            logger.debug(f"Costo calculado: unitario={costo_unitario}, total={costo_total}")

            # Saldos anteriores
            saldo_cantidad_anterior = ultimo_kardex.saldo_cantidad if ultimo_kardex else Decimal('0')
            saldo_costo_total_anterior = ultimo_kardex.saldo_costo_total if ultimo_kardex else Decimal('0.00')
            saldo_costo_unitario_anterior = ultimo_kardex.saldo_costo_unitario if ultimo_kardex else Decimal('0.00')
            logger.debug(f"Saldos anteriores: cantidad={saldo_cantidad_anterior}, costo_total={saldo_costo_total_anterior}")

            # Actualizar inventario
            if tipo_movimiento == 'Incrementar':
                valor_total_anterior = Decimal(str(cantidad_anterior)) * estado_inventario.costo_unitario
                valor_total_nuevo = valor_total_anterior + costo_total
                estado_inventario.cantidad += cantidad_ajuste
                estado_inventario.costo_unitario = (
                    valor_total_nuevo / Decimal(str(estado_inventario.cantidad))
                    if estado_inventario.cantidad > 0 else Decimal('0.00')
                )
                estado_inventario.costo_total = valor_total_nuevo

                saldo_cantidad = saldo_cantidad_anterior + Decimal(str(cantidad_ajuste))
                saldo_costo_total = saldo_costo_total_anterior + costo_total
                saldo_costo_unitario = (
                    saldo_costo_total / saldo_cantidad if saldo_cantidad > 0 else Decimal('0.00')
                )
            else:  # Disminuir
                if estado_inventario.cantidad < cantidad_ajuste:
                    logger.error(f"Stock insuficiente: {codigo_producto}, cantidad disponible={estado_inventario.cantidad}, solicitada={cantidad_ajuste}")
                    return jsonify({'error': f'Stock insuficiente de {codigo_producto} en {bodega_nombre}'}), 400
                estado_inventario.cantidad -= cantidad_ajuste
                estado_inventario.costo_unitario = costo_unitario
                estado_inventario.costo_total = Decimal(str(estado_inventario.cantidad)) * costo_unitario

                saldo_cantidad = saldo_cantidad_anterior - Decimal(str(cantidad_ajuste))
                saldo_costo_total = saldo_costo_total_anterior - costo_total
                saldo_costo_unitario = (
                    saldo_costo_total / saldo_cantidad if saldo_cantidad > 0 else Decimal('0.00')
                )

            estado_inventario.ultima_actualizacion = fecha_actual
            logger.debug(f"Inventario actualizado: producto_id={producto.id}, cantidad={estado_inventario.cantidad}")

            # RegistroMovimientos
            mensaje = (
                f"Entrada por ajuste manual {consecutivo}" if tipo_movimiento == 'Incrementar'
                else f"Salida por ajuste manual {consecutivo}"
            )
            nuevo_movimiento = RegistroMovimientos(
                idcliente=idcliente,
                consecutivo=consecutivo,
                tipo_movimiento='ENTRADA' if tipo_movimiento == 'Incrementar' else 'SALIDA',
                producto_id=producto.id,
                bodega_origen_id=bodega.id if tipo_movimiento == 'Disminuir' else None,
                bodega_destino_id=bodega.id if tipo_movimiento == 'Incrementar' else None,
                cantidad=cantidad_ajuste,
                fecha=fecha_actual,
                descripcion=mensaje,
                costo_unitario=costo_unitario,
                costo_total=costo_total
            )
            db.session.add(nuevo_movimiento)
            logger.debug(f"RegistroMovimientos creado: {mensaje}")

            # Kardex
            nuevo_kardex = Kardex(
                idcliente=idcliente,
                producto_id=producto.id,
                bodega_origen_id=bodega.id if tipo_movimiento == 'Disminuir' else None,
                bodega_destino_id=bodega.id if tipo_movimiento == 'Incrementar' else None,
                fecha=fecha_actual,
                tipo_movimiento='ENTRADA' if tipo_movimiento == 'Incrementar' else 'SALIDA',
                cantidad=Decimal(str(cantidad_ajuste)),
                costo_unitario=costo_unitario,
                costo_total=costo_total,
                saldo_cantidad=saldo_cantidad,
                saldo_costo_unitario=saldo_costo_unitario,
                saldo_costo_total=saldo_costo_total,
                referencia=f"Ajuste manual {consecutivo}"
            )
            db.session.add(nuevo_kardex)
            logger.debug(f"Kardex creado: tipo={tipo_movimiento}, cantidad={cantidad_ajuste}")

            # AjusteInventarioDetalle
            nuevo_ajuste = AjusteInventarioDetalle(
                idcliente=idcliente,
                consecutivo=consecutivo,
                producto_id=producto.id,
                producto_nombre=producto.nombre,
                bodega_id=bodega.id,
                bodega_nombre=bodega.nombre,
                cantidad_anterior=cantidad_anterior,
                tipo_movimiento=tipo_movimiento,
                cantidad_ajustada=cantidad_ajuste,
                cantidad_final=estado_inventario.cantidad,
                fecha=fecha_actual,
                usuario_id=user_id,
                costo_unitario=costo_unitario,
                costo_total=costo_total
            )
            db.session.add(nuevo_ajuste)
            logger.debug(f"AjusteInventarioDetalle creado para producto_id={producto.id}")

        db.session.commit()
        logger.info(f"Ajuste exitoso. Consecutivo: {consecutivo}, usuario_id={user_id}")
        return jsonify({'message': 'Ajuste realizado con éxito', 'consecutivo': consecutivo}), 200

    except Exception as e:
        logger.error(f"Error en ajuste de inventario: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Error al realizar el ajuste'}), 500
    

@app.route('/api/consulta-ajustes', methods=['GET'])
@jwt_required()
def consulta_ajustes():
    try:
        consecutivo = request.args.get('consecutivo')
        fecha_inicio = request.args.get('fechaInicio')
        fecha_fin = request.args.get('fechaFin')

        # Obtener claims del JWT
        claims = get_jwt()
        idcliente = claims.get('idcliente')
        if not idcliente:
            return jsonify({'error': 'No se encontró idcliente en el token'}), 403

        # Verificar permisos
        if not has_permission(claims, 'inventario', 'ajustes', 'ver'):
            return jsonify({'error': 'Usuario no autorizado para consultar ajustes'}), 403

        query = AjusteInventarioDetalle.query.filter_by(idcliente=idcliente)

        if consecutivo:
            query = query.filter(AjusteInventarioDetalle.consecutivo == consecutivo)
        elif fecha_inicio and fecha_fin:
            query = query.filter(AjusteInventarioDetalle.fecha.between(fecha_inicio, fecha_fin))
        else:
            return jsonify({'error': 'Se requiere consecutivo o rango de fechas'}), 400

        ajustes = query.with_entities(
            AjusteInventarioDetalle.consecutivo,
            db.func.min(AjusteInventarioDetalle.fecha).label('fecha')
        ).group_by(AjusteInventarioDetalle.consecutivo).all()

        return jsonify([
            {
                'consecutivo': ajuste.consecutivo,
                'fecha': ajuste.fecha.strftime('%Y-%m-%d %H:%M:%S')
            } for ajuste in ajustes
        ])

    except Exception as e:
        logger.error(f"Error en consulta de ajustes: {str(e)}")
        return jsonify({'error': 'No se pudo recuperar la información'}), 500

@app.route('/api/ajuste-detalle/<consecutivo>', methods=['GET'])
@jwt_required()
def ajuste_detalle(consecutivo):
    try:
        # Obtener claims del JWT
        claims = get_jwt()
        idcliente = claims.get('idcliente')
        if not idcliente:
            return jsonify({'error': 'No se encontró idcliente en el token'}), 403

        # Verificar permisos
        if not has_permission(claims, 'inventario', 'ajustes', 'ver'):
            return jsonify({'error': 'Usuario no autorizado para consultar detalles'}), 403

        detalles = (
            db.session.query(AjusteInventarioDetalle, Producto.codigo)
            .join(Producto, AjusteInventarioDetalle.producto_id == Producto.id)
            .filter(
                AjusteInventarioDetalle.consecutivo == consecutivo,
                AjusteInventarioDetalle.idcliente == idcliente
            )
            .all()
        )

        if not detalles:
            return jsonify({'error': f'No se encontraron detalles para el ajuste {consecutivo}'}), 404

        return jsonify([
            {
                'codigo_producto': producto_codigo,
                'nombre_producto': d.producto_nombre,
                'bodega_nombre': d.bodega_nombre,
                'cantidad_anterior': d.cantidad_anterior,
                'tipo_movimiento': d.tipo_movimiento,
                'cantidad_ajustada': d.cantidad_ajustada,
                'cantidad_final': d.cantidad_final,
                'costo_unitario': float(d.costo_unitario) if d.costo_unitario is not None else 0.0,
                'costo_total': float(d.costo_total) if d.costo_total is not None else 0.0
            } for d, producto_codigo in detalles
        ])

    except Exception as e:
        logger.error(f"Error en consulta de detalle de ajuste: {str(e)}")
        return jsonify({'error': 'No se pudo recuperar el detalle'}), 500

@app.route('/api/ajuste-detalle-pdf/<consecutivo>', methods=['GET'])
@jwt_required()
def generar_ajuste_pdf(consecutivo):
    try:
        # Obtener claims del JWT
        claims = get_jwt()
        idcliente = claims.get('idcliente')
        if not idcliente:
            return jsonify({'error': 'No se encontró idcliente en el token'}), 403

        # Verificar permisos
        if not has_permission(claims, 'inventario', 'ajustes', 'ver'):
            return jsonify({'error': 'Usuario no autorizado para generar PDF'}), 403

        detalles = (
            db.session.query(AjusteInventarioDetalle, Producto.codigo, Usuarios.nombres, Usuarios.apellidos)
            .join(Producto, AjusteInventarioDetalle.producto_id == Producto.id)
            .outerjoin(Usuarios, AjusteInventarioDetalle.usuario_id == Usuarios.id)
            .filter(
                AjusteInventarioDetalle.consecutivo == consecutivo,
                AjusteInventarioDetalle.idcliente == idcliente
            )
            .all()
        )

        if not detalles:
            return jsonify({'error': f'Ajuste {consecutivo} no encontrado'}), 404

        primer_detalle = detalles[0][0]
        fecha = primer_detalle.fecha.strftime('%Y-%m-%d %H:%M:%S')
        usuario_nombre = f"{detalles[0][2] or ''} {detalles[0][3] or ''}".strip() or 'Desconocido'

        detalles_json = [
            {
                'codigo_producto': producto_codigo,
                'nombre_producto': d.producto_nombre,
                'bodega_nombre': d.bodega_nombre,
                'cantidad_anterior': d.cantidad_anterior,
                'tipo_movimiento': d.tipo_movimiento,
                'cantidad_ajustada': d.cantidad_ajustada,
                'cantidad_final': d.cantidad_final,
                'costo_unitario': float(d.costo_unitario or 0),
                'costo_total': float(d.costo_total or 0)
            } for d, producto_codigo, nombres, apellidos in detalles
        ]

        # Generar PDF
        buffer = BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=landscape(letter))
        pdf.setTitle(f"Ajuste_{consecutivo}")

        # Encabezado
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(30, 570, "Ajuste de Inventario")
        pdf.setFont("Helvetica", 10)
        pdf.drawString(30, 550, f"Detalle del Ajuste {consecutivo}")
        pdf.drawString(30, 530, f"Fecha Realización: {fecha}")
        pdf.drawString(30, 510, f"Realizado por: {usuario_nombre}")
        pdf.line(30, 500, 780, 500)

        # Tabla
        pdf.setFont("Helvetica-Bold", 8)
        y = 480
        headers = [
            ("Código", 30),
            ("Nombre Producto", 100),
            ("Bodega", 300),
            ("Cant. Anterior", 360),
            ("Acción", 430),
            ("Cant. Ajustada", 500),
            ("Cant. Final", 570),
            ("Costo Unit.", 640),
            ("Costo Total", 710)
        ]
        for text, x in headers:
            pdf.drawString(x, y, text)
        pdf.line(30, y - 5, 780, y - 5)

        pdf.setFont("Helvetica", 8)
        y -= 15
        for detalle in detalles_json:
            if y < 80:
                pdf.showPage()
                pdf.setFont("Helvetica-Bold", 8)
                for text, x in headers:
                    pdf.drawString(x, y, text)
                pdf.line(30, y - 5, 780, y - 5)
                pdf.setFont("Helvetica", 8)
                y = 570
                y -= 15

            y_inicial = y
            max_width = 190
            y_nueva = draw_wrapped_text_ajuste(pdf, 100, y_inicial, detalle['nombre_producto'], max_width)
            pdf.drawString(30, y_inicial, detalle['codigo_producto'])
            pdf.drawString(300, y_inicial, detalle['bodega_nombre'])
            pdf.drawString(360, y_inicial, str(detalle['cantidad_anterior']))
            pdf.drawString(430, y_inicial, detalle['tipo_movimiento'])
            pdf.drawString(500, y_inicial, str(detalle['cantidad_ajustada']))
            pdf.drawString(570, y_inicial, str(detalle['cantidad_final']))
            pdf.drawString(640, y_inicial, f"${detalle['costo_unitario']:.2f}")
            pdf.drawString(710, y_inicial, f"${detalle['costo_total']:.2f}")
            y = min(y_inicial, y_nueva) - 15

        # Firmas
        pdf.setFont("Helvetica", 10)
        y_firmas = 60
        pdf.drawString(30, y_firmas, "Elaborado Por:")
        pdf.line(100, y_firmas + 5, 300, y_firmas + 5)
        pdf.drawString(400, y_firmas, "Aprobado Por:")
        pdf.line(470, y_firmas + 5, 670, y_firmas + 5)

        pdf.save()
        buffer.seek(0)
        return send_file(
            buffer,
            as_attachment=True,
            download_name=f"ajuste_{consecutivo}.pdf",
            mimetype="application/pdf"
        )

    except Exception as e:
        logger.error(f"Error al generar PDF del ajuste: {str(e)}")
        return jsonify({'error': 'Error al generar el PDF'}), 500

@app.route('/api/consultaListado-ajustes-pdf', methods=['GET'])
@jwt_required()
def generar_ajustes_pdf():
    try:
        fecha_inicio = request.args.get('fechaInicio')
        fecha_fin = request.args.get('fechaFin')

        # Obtener claims del JWT
        claims = get_jwt()
        idcliente = claims.get('idcliente')
        if not idcliente:
            return jsonify({'error': 'No se encontró idcliente en el token'}), 403

        # Verificar permisos
        if not has_permission(claims, 'inventario', 'ajustes', 'ver'):
            return jsonify({'error': 'Usuario no autorizado para generar PDF'}), 403

        if not fecha_inicio or not fecha_fin:
            return jsonify({'error': 'Faltan parámetros: fechaInicio o fechaFin'}), 400

        query = AjusteInventarioDetalle.query.filter(
            AjusteInventarioDetalle.fecha.between(fecha_inicio, fecha_fin),
            AjusteInventarioDetalle.idcliente == idcliente
        )
        ajustes = query.with_entities(
            AjusteInventarioDetalle.consecutivo,
            db.func.min(AjusteInventarioDetalle.fecha).label('fecha')
        ).group_by(AjusteInventarioDetalle.consecutivo).all()

        if not ajustes:
            return jsonify({'error': 'No se encontraron ajustes en el rango de fechas'}), 404

        # Generar PDF
        buffer = BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=letter)
        pdf.setTitle(f"Ajustes_{fecha_inicio}_al_{fecha_fin}")

        # Encabezado
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(30, 750, "Ajustes de Inventario Realizados")
        pdf.setFont("Helvetica", 12)
        pdf.drawString(30, 730, f"Rango de fecha: {fecha_inicio} - {fecha_fin}")
        pdf.line(30, 720, 570, 720)

        # Tabla
        pdf.setFont("Helvetica-Bold", 10)
        y = 700
        pdf.drawString(30, y, "Consecutivo")
        pdf.drawString(200, y, "Fecha")
        pdf.line(30, y - 5, 570, y - 5)

        pdf.setFont("Helvetica", 10)
        y -= 20
        for ajuste in ajustes:
            if y < 50:
                pdf.showPage()
                pdf.setFont("Helvetica-Bold", 10)
                pdf.drawString(30, y, "Consecutivo")
                pdf.drawString(200, y, "Fecha")
                pdf.line(30, y - 5, 570, y - 5)
                pdf.setFont("Helvetica", 10)
                y = 750
                y -= 20

            pdf.drawString(30, y, ajuste.consecutivo)
            pdf.drawString(200, y, ajuste.fecha.strftime('%Y-%m-%d %H:%M:%S'))
            y -= 15

        pdf.save()
        buffer.seek(0)
        return send_file(
            buffer,
            as_attachment=True,
            download_name=f"Listado_ajustes_{fecha_inicio}_al_{fecha_fin}.pdf",
            mimetype="application/pdf"
        )

    except Exception as e:
        logger.error(f"Error al generar PDF de ajustes: {str(e)}")
        return jsonify({'error': 'Error al generar el PDF'}), 500


# Endpoints relativos a las paginas de Produccion:
@app.route('/api/ordenes-produccion', methods=['POST'])
@jwt_required()
def crear_orden_produccion():
    try:
        claims = get_jwt()
        idcliente = claims.get('idcliente')
        if not idcliente:
            return jsonify({'error': 'No se encontró idcliente en el token.'}), 401

        if not has_permission(claims, 'production', 'admin', 'editar'):
            return jsonify({'error': 'No autorizado para crear órdenes de producción.'}), 403

        # Obtener datos
        try:
            data = request.get_json()
            logger.info(f"Datos recibidos: {data}")
        except Exception as e:
            logger.error(f"Error al parsear JSON: {str(e)}")
            return jsonify({'error': 'Cuerpo de la solicitud inválido.'}), 400

        if not data:
            logger.error("No se proporcionaron datos en la solicitud.")
            return jsonify({'error': 'No se proporcionaron datos.'}), 400

        # Validar campos requeridos
        required_fields = ['producto_compuesto_id', 'cantidad_paquetes', 'creado_por', 'bodega_produccion']
        missing_fields = [field for field in required_fields if field not in data or data[field] is None]
        if missing_fields:
            error_msg = f'Faltan campos requeridos: {", ".join(missing_fields)}.'
            logger.error(error_msg)
            return jsonify({'error': error_msg}), 400

        # Validar tipos y valores
        try:
            producto_compuesto_id = int(str(data['producto_compuesto_id']).strip())
            cantidad_paquetes = int(str(data['cantidad_paquetes']).strip())
            creado_por = int(str(data['creado_por']).strip())
            bodega_produccion_id = int(str(data['bodega_produccion']).strip())
        except (ValueError, TypeError) as e:
            error_msg = 'Los campos producto_compuesto_id, cantidad_paquetes, creado_por y bodega_produccion deben ser números válidos.'
            logger.error(f"Error de conversión: {str(e)}, datos: {data}")
            return jsonify({'error': error_msg}), 400

        if cantidad_paquetes <= 0:
            logger.error(f"cantidad_paquetes inválida: {cantidad_paquetes}")
            return jsonify({'error': 'La cantidad de paquetes debe ser mayor a cero.'}), 400

        # Verificar producto compuesto
        producto_compuesto = Producto.query.filter(
            and_(
                Producto.id == producto_compuesto_id,
                Producto.es_producto_compuesto == True,
                Producto.idcliente == idcliente
            )
        ).first()
        if not producto_compuesto:
            logger.error(f"Producto compuesto no encontrado: id={producto_compuesto_id}, idcliente={idcliente}")
            return jsonify({'error': 'El producto compuesto especificado no existe o no pertenece al cliente.'}), 404

        # Verificar bodega
        bodega_produccion = Bodega.query.filter(
            and_(
                Bodega.id == bodega_produccion_id,
                Bodega.idcliente == idcliente
            )
        ).first()
        if not bodega_produccion:
            logger.error(f"Bodega no encontrada: id={bodega_produccion_id}, idcliente={idcliente}")
            return jsonify({'error': 'La bodega de producción especificada no existe o no pertenece al cliente.'}), 404

        # Verificar usuario
        usuario = Usuarios.query.filter_by(id=creado_por).first()
        if not usuario:
            logger.error(f"Usuario no encontrado: id={creado_por}")
            return jsonify({'error': 'El usuario especificado no existe.'}), 404

        # Calcular costos
        materiales = MaterialProducto.query.filter_by(producto_compuesto_id=producto_compuesto.id).all()
        costo_total_materiales = 0.0
        for material in materiales:
            ultimo_kardex = Kardex.query.filter(
                and_(
                    Kardex.producto_id == material.producto_base_id,
                    Kardex.idcliente == idcliente,
                    Kardex.bodega_destino_id == bodega_produccion.id
                )
            ).order_by(Kardex.fecha.desc()).first()
            costo_unitario = float(ultimo_kardex.saldo_costo_unitario) if ultimo_kardex else 0.0

            cantidad_requerida = float(material.cantidad) * cantidad_paquetes
            costo_material = costo_unitario * cantidad_requerida
            costo_total_materiales += costo_material

        costo_unitario_compuesto = costo_total_materiales / cantidad_paquetes if cantidad_paquetes > 0 else 0.0

        # Generar numero_orden
        ultimo_orden = db.session.query(OrdenProduccion.numero_orden).filter_by(idcliente=idcliente).order_by(OrdenProduccion.id.desc()).first()
        if ultimo_orden and ultimo_orden.numero_orden.startswith(f"OP-{idcliente}-"):
            ultimo_numero = int(ultimo_orden.numero_orden.split('-')[-1])
            nuevo_numero = ultimo_numero + 1
        else:
            nuevo_numero = 1
        numero_orden = f"OP-{idcliente}-{nuevo_numero:08d}"

        # Crear orden
        nueva_orden = OrdenProduccion(
            idcliente=idcliente,
            producto_compuesto_id=producto_compuesto_id,
            cantidad_paquetes=cantidad_paquetes,
            bodega_produccion_id=bodega_produccion_id,
            creado_por=creado_por,
            numero_orden=numero_orden,
            fecha_creacion=obtener_hora_colombia(),
            costo_unitario=costo_unitario_compuesto,
            costo_total=costo_total_materiales,
            estado='Pendiente'
        )
        db.session.add(nueva_orden)
        db.session.commit()

        logger.info(f"Orden creada: id={nueva_orden.id}, numero_orden={numero_orden}")
        return jsonify({
            'message': 'Orden de producción creada exitosamente.',
            'orden_id': nueva_orden.id,
            'numero_orden': nueva_orden.numero_orden
        }), 201

    except Exception as e:
        logger.error(f"Error al crear orden de producción: {str(e)}, datos: {data}")
        db.session.rollback()
        return jsonify({'error': 'Ocurrió un error al crear la orden de producción.'}), 500


@app.route('/api/ordenes-produccion', methods=['GET'])
@jwt_required()
def obtener_ordenes_produccion():
    claims = get_jwt()
    idcliente = claims.get('idcliente')
    if not idcliente:
        return jsonify({'error': 'No se encontró idcliente en el token.'}), 401

    try:
        numero_orden = request.args.get('numero_orden')
        estado = request.args.get('estado')

        query = OrdenProduccion.query.filter_by(idcliente=idcliente)

        if numero_orden:
            query = query.filter_by(numero_orden=numero_orden)
        if estado:
            query = query.filter_by(estado=estado)

        ordenes = query.all()

        resultado = []
        for orden in ordenes:
            producto = Producto.query.filter_by(id=orden.producto_compuesto_id).first()
            producto_nombre = f"{producto.codigo} - {producto.nombre}" if producto else "Producto no encontrado"

            resultado.append({
                "id": orden.id,
                "numero_orden": orden.numero_orden,
                "producto_compuesto_id": orden.producto_compuesto_id,
                "producto_compuesto_nombre": producto_nombre,
                "cantidad_paquetes": orden.cantidad_paquetes,
                "estado": orden.estado,
                "bodega_produccion_id": orden.bodega_produccion_id,
                "bodega_produccion_nombre": orden.bodega_produccion.nombre if orden.bodega_produccion else "No especificada",
                "fecha_creacion": orden.fecha_creacion.isoformat() if orden.fecha_creacion else None,
                "fecha_lista_para_produccion": orden.fecha_lista_para_produccion.isoformat() if orden.fecha_lista_para_produccion else None,
                "fecha_inicio": orden.fecha_inicio.isoformat() if orden.fecha_inicio else None,
                "fecha_finalizacion": orden.fecha_finalizacion.isoformat() if orden.fecha_finalizacion else None,
                "creado_por": orden.creado_por_usuario.nombres if orden.creado_por_usuario else None,
                "en_produccion_por": orden.en_produccion_por,
            })

        return jsonify(resultado), 200
    except Exception as e:
        print(f"Error al obtener órdenes de producción: {str(e)}")
        return jsonify({'error': 'Ocurrió un error al obtener las órdenes de producción.'}), 500


@app.route('/api/ordenes-produccion/<int:orden_id>', methods=['GET'])
@jwt_required()
def obtener_detalle_orden_produccion(orden_id):
    try:
        # Obtener claims del JWT
        claims = get_jwt()
        idcliente = claims.get('idcliente')
        if not idcliente:
            logger.error("No se encontró idcliente en el token")
            return jsonify({'error': 'No se encontró idcliente en el token.'}), 401

        # Verificar permisos
        if not has_permission(claims, 'production', 'admin', 'ver'):
            logger.error("Usuario no autorizado para ver detalles de órdenes de producción")
            return jsonify({'error': 'No autorizado para ver detalles de órdenes de producción.'}), 403

        # Obtener la orden
        orden = db.session.query(OrdenProduccion).filter(
            and_(
                OrdenProduccion.id == orden_id,
                OrdenProduccion.idcliente == idcliente
            )
        ).first()
        if not orden:
            logger.error(f"Orden de producción con ID {orden_id} no encontrada para idcliente {idcliente}")
            return jsonify({'error': f'Orden de producción con ID {orden_id} no encontrada o no pertenece al cliente.'}), 404

        # Obtener materiales
        materiales = MaterialProducto.query.filter_by(producto_compuesto_id=orden.producto_compuesto_id).all()
        materiales_response = []
        for material in materiales:
            # Obtener el producto base manualmente
            producto_base = db.session.get(Producto, material.producto_base_id)
            if not producto_base:
                logger.warning(f"Producto base con ID {material.producto_base_id} no encontrado")
                continue  # Ignorar materiales con producto base no encontrado

            ultimo_kardex = Kardex.query.filter(
                and_(
                    Kardex.producto_id == material.producto_base_id,
                    Kardex.bodega_destino_id == orden.bodega_produccion_id,
                    Kardex.idcliente == idcliente
                )
            ).order_by(Kardex.fecha.desc()).first()
            costo_unitario = float(ultimo_kardex.saldo_costo_unitario) if ultimo_kardex else 0.0

            # Convertir valores a float explícitamente
            cantidad = float(material.cantidad)
            peso_unidad_gr = float(producto_base.peso_unidad_gr or 0.0)
            cantidad_paquetes = float(orden.cantidad_paquetes)

            materiales_response.append({
                'producto_base_id': material.producto_base_id,
                'producto_base_nombre': f"{producto_base.codigo} - {producto_base.nombre}",
                'cant_x_paquete': cantidad,
                'peso_x_paquete': cantidad * peso_unidad_gr,
                'cantidad_total': cantidad * cantidad_paquetes,
                'peso_total': peso_unidad_gr * cantidad * cantidad_paquetes,
                'costo_unitario': costo_unitario,
                'costo_total': costo_unitario * (cantidad * cantidad_paquetes)
            })

        # Obtener información del usuario que creó la orden
        creado_por_usuario = db.session.query(Usuarios).get(orden.creado_por)
        creado_por_nombre = f"{creado_por_usuario.nombres} {creado_por_usuario.apellidos}" if creado_por_usuario else "Usuario no encontrado"

        # Obtener información del usuario en producción (si existe)
        producido_por = None
        if orden.en_produccion_por:
            usuario = db.session.query(Usuarios).get(orden.en_produccion_por)
            producido_por = f"{usuario.nombres} {usuario.apellidos}" if usuario else "Usuario no encontrado"

        # Preparar respuesta
        response = {
            'id': orden.id,
            'numero_orden': orden.numero_orden,
            'producto_compuesto_id': orden.producto_compuesto_id,
            'producto_compuesto_nombre': f"{orden.producto_compuesto.codigo} - {orden.producto_compuesto.nombre}",
            'cantidad_paquetes': orden.cantidad_paquetes,
            'peso_total': float(orden.peso_total) if orden.peso_total else 0.0,
            'estado': orden.estado,
            'bodega_produccion_id': orden.bodega_produccion_id,
            'bodega_produccion_nombre': orden.bodega_produccion.nombre if orden.bodega_produccion else "No especificada",
            'fecha_creacion': orden.fecha_creacion.isoformat() if orden.fecha_creacion else None,
            'fecha_lista_para_produccion': orden.fecha_lista_para_produccion.isoformat() if orden.fecha_lista_para_produccion else None,
            'fecha_inicio': orden.fecha_inicio.isoformat() if orden.fecha_inicio else None,
            'fecha_finalizacion': orden.fecha_finalizacion.isoformat() if orden.fecha_finalizacion else None,
            'creado_por': creado_por_nombre,
            'producido_por': producido_por,
            'costo_unitario': float(orden.costo_unitario or 0),
            'costo_total': float(orden.costo_total or 0),
            'comentario_cierre_forzado': orden.comentario_cierre_forzado or "",
            'materiales': materiales_response
        }

        logger.info(f"Detalles de la orden {orden_id} obtenidos exitosamente")
        return jsonify(response), 200

    except Exception as e:
        logger.error(f"Error al obtener detalles de la orden {orden_id}: {str(e)}")
        return jsonify({'error': 'Ocurrió un error al obtener los detalles.'}), 500
    

@app.route('/api/ordenes-produccion/<int:orden_id>/historial-entregas', methods=['GET'])
@jwt_required()
def obtener_historial_entregas(orden_id):
    try:
        # Obtener claims del JWT
        claims = get_jwt()
        idcliente = claims.get('idcliente')
        if not idcliente:
            logger.error("No se encontró idcliente en el token")
            return jsonify({'error': 'No se encontró idcliente en el token.'}), 401

        # Verificar permisos
        if not has_permission(claims, 'production', 'admin', 'ver'):
            logger.error("Usuario no autorizado para ver historial de entregas")
            return jsonify({'error': 'No autorizado para ver historial de entregas.'}), 403

        # Verificar si la orden existe
        orden = db.session.query(OrdenProduccion).filter(
            and_(
                OrdenProduccion.id == orden_id,
                OrdenProduccion.idcliente == idcliente
            )
        ).first()
        if not orden:
            logger.error(f"Orden de producción con ID {orden_id} no encontrada para idcliente {idcliente}")
            return jsonify({'error': f'Orden de producción con ID {orden_id} no encontrada o no pertenece al cliente.'}), 404

        # Consultar las entregas parciales
        entregas = db.session.query(EntregaParcial).filter_by(
            orden_produccion_id=orden_id,
            idcliente=idcliente
        ).all()

        historial_response = [
            {
                'id': entrega.id,  # Añadido para clave única en Vue.js
                'cantidad': float(entrega.cantidad_entregada),
                'fecha_hora': entrega.fecha_entrega.strftime('%Y-%m-%d %I:%M %p'),
                'comentario': entrega.comentario or 'N/A'
            }
            for entrega in entregas
        ]

        # Calcular la cantidad total entregada y pendiente
        total_entregado = float(db.session.query(func.sum(EntregaParcial.cantidad_entregada))
                               .filter_by(orden_produccion_id=orden_id, idcliente=idcliente)
                               .scalar() or 0)
        cantidad_pendiente = max(float(orden.cantidad_paquetes) - total_entregado, 0)

        logger.info(f"Historial de entregas para la orden {orden_id} obtenido exitosamente")
        return jsonify({
            'historial': historial_response,
            'total_entregado': total_entregado,
            'cantidad_pendiente': cantidad_pendiente
        }), 200

    except Exception as e:
        logger.error(f"Error al obtener historial de entregas para la orden {orden_id}: {str(e)}")
        return jsonify({'error': 'Ocurrió un error al obtener el historial de entregas.'}), 500
    

@app.route('/api/ordenes-produccion/<int:orden_id>/entrega-parcial', methods=['POST'])
@jwt_required()
def registrar_entrega_parcial(orden_id):
    claims = get_jwt()
    idcliente = claims.get('idcliente')
    if not idcliente:
        logger.error("No se encontró idcliente en el token")
        return jsonify({'error': 'No se encontró idcliente en el token.'}), 401

    try:
        data = request.get_json()
        cantidad_entregada = float(data.get('cantidad_entregada', 0))
        comentario = data.get('comentario', '')
        usuario_id = data.get('usuario_id')
        if not usuario_id:
            logger.error("Se requiere el ID del usuario")
            return jsonify({'error': 'Se requiere el ID del usuario.'}), 400

        if cantidad_entregada <= 0:
            logger.error("Cantidad entregada no válida: debe ser mayor a 0")
            return jsonify({'error': 'La cantidad entregada debe ser mayor a 0.'}), 400

        orden = db.session.get(OrdenProduccion, orden_id)
        if not orden or orden.estado == "Finalizada" or orden.idcliente != idcliente:
            logger.error(f"Orden no válida o no pertenece al cliente: orden_id={orden_id}, idcliente={idcliente}")
            return jsonify({'error': 'Orden no válida o no pertenece al cliente.'}), 400

        # Calcular cantidad pendiente antes de registrar la entrega
        entregas_totales = float(db.session.query(func.sum(EntregaParcial.cantidad_entregada))
                                .filter_by(orden_produccion_id=orden.id, idcliente=idcliente)
                                .scalar() or 0)
        cantidad_pendiente = float(orden.cantidad_paquetes) - entregas_totales
        if cantidad_entregada > cantidad_pendiente:
            logger.error(f"Cantidad entregada ({cantidad_entregada}) excede cantidad pendiente ({cantidad_pendiente})")
            return jsonify({'error': f'La cantidad entregada ({cantidad_entregada}) excede la cantidad pendiente ({cantidad_pendiente}).'}), 400

        with no_autoflush(db.session):
            # Procesar materiales y registrar salidas en Kardex
            materiales = MaterialProducto.query.filter_by(producto_compuesto_id=orden.producto_compuesto_id).all()
            for material in materiales:
                cantidad_consumida = abs(float(material.cantidad)) * float(cantidad_entregada)
                ultimo_kardex = Kardex.query.filter(
                    Kardex.producto_id == material.producto_base_id,
                    (Kardex.bodega_origen_id == orden.bodega_produccion_id) | (Kardex.bodega_destino_id == orden.bodega_produccion_id)
                ).order_by(Kardex.fecha.desc()).first()

                saldo_cantidad = float(ultimo_kardex.saldo_cantidad) if ultimo_kardex else 0.0
                costo_unitario = float(ultimo_kardex.saldo_costo_unitario) if ultimo_kardex else 0.0
                saldo_costo_total = float(ultimo_kardex.saldo_costo_total) if ultimo_kardex else 0.0

                if saldo_cantidad < cantidad_consumida:
                    logger.error(f"No hay suficiente inventario para producto {material.producto_base_id} en bodega {orden.bodega_produccion_id}")
                    raise ValueError(f"No hay suficiente inventario para el producto {material.producto_base_id} en la bodega {orden.bodega_produccion_id}")

                kardex_salida = Kardex(
                    idcliente=idcliente,
                    producto_id=material.producto_base_id,
                    bodega_origen_id=orden.bodega_produccion_id,
                    fecha=obtener_hora_colombia(),
                    tipo_movimiento='SALIDA',
                    cantidad=cantidad_consumida,
                    costo_unitario=costo_unitario,
                    costo_total=costo_unitario * cantidad_consumida,
                    saldo_cantidad=saldo_cantidad - cantidad_consumida,
                    saldo_costo_unitario=costo_unitario,
                    saldo_costo_total=saldo_costo_total - (costo_unitario * cantidad_consumida),
                    referencia=f"Consumo para orden {orden.numero_orden}"
                )
                db.session.add(kardex_salida)
                actualizar_estado_inventario(
                    material.producto_base_id,
                    orden.bodega_produccion_id,
                    cantidad_consumida,
                    es_entrada=False,
                    orden_id=orden_id
                )

                detalle = DetalleProduccion(
                    idcliente=idcliente,
                    orden_produccion_id=orden.id,
                    producto_base_id=material.producto_base_id,
                    cantidad_consumida=cantidad_consumida,
                    cantidad_producida=cantidad_entregada,
                    bodega_destino_id=orden.bodega_produccion_id,
                    fecha_registro=obtener_hora_colombia()
                )
                db.session.add(detalle)

            # Registrar entrada del producto compuesto en Kardex
            ultimo_kardex_compuesto = Kardex.query.filter(
                Kardex.producto_id == orden.producto_compuesto_id,
                Kardex.bodega_destino_id == orden.bodega_produccion_id
            ).order_by(Kardex.fecha.desc()).first()
            saldo_cantidad_compuesto = float(ultimo_kardex_compuesto.saldo_cantidad) if ultimo_kardex_compuesto else 0.0
            costo_unitario_compuesto = float(orden.costo_unitario or 0)

            kardex_entrada = Kardex(
                idcliente=idcliente,
                producto_id=orden.producto_compuesto_id,
                bodega_destino_id=orden.bodega_produccion_id,
                fecha=obtener_hora_colombia(),
                tipo_movimiento='ENTRADA',
                cantidad=cantidad_entregada,
                costo_unitario=costo_unitario_compuesto,
                costo_total=costo_unitario_compuesto * cantidad_entregada,
                saldo_cantidad=saldo_cantidad_compuesto + cantidad_entregada,
                saldo_costo_unitario=costo_unitario_compuesto,
                saldo_costo_total=(saldo_cantidad_compuesto + cantidad_entregada) * costo_unitario_compuesto,
                referencia=f"Producción parcial de orden {orden.numero_orden}"
            )
            db.session.add(kardex_entrada)
            actualizar_estado_inventario(
                orden.producto_compuesto_id,
                orden.bodega_produccion_id,
                cantidad_entregada,
                es_entrada=True,
                orden_id=orden_id
            )

            # Registrar entrega parcial
            entrega = EntregaParcial(
                orden_produccion_id=orden_id,
                cantidad_entregada=cantidad_entregada,
                fecha_entrega=obtener_hora_colombia(),
                comentario=comentario,
                idcliente=idcliente,
                usuario_id=usuario_id
            )
            db.session.add(entrega)

            # Actualizar estado de la orden
            entregas_totales = float(db.session.query(func.sum(EntregaParcial.cantidad_entregada))
                                    .filter_by(orden_produccion_id=orden.id, idcliente=idcliente)
                                    .scalar() or 0) + cantidad_entregada
            cantidad_pendiente = float(orden.cantidad_paquetes) - entregas_totales

            if cantidad_pendiente <= 0:
                orden.estado = "Finalizada"
                orden.fecha_finalizacion = obtener_hora_colombia()
                logger.info(f"Orden {orden_id} finalizada: total entregado ({entregas_totales}) >= cantidad paquetes ({orden.cantidad_paquetes})")
            else:
                orden.estado = "En Producción-Parcial"
                logger.info(f"Orden {orden_id} en producción parcial: cantidad pendiente ({cantidad_pendiente})")

        db.session.commit()
        logger.info(f"Entrega parcial de {cantidad_entregada} registrada para orden {orden_id}")
        return jsonify({
            'message': 'Entrega parcial registrada con éxito.',
            'cantidad_pendiente': cantidad_pendiente
        }), 200

    except ValueError as ve:
        db.session.rollback()
        logger.error(f"Error de validación al registrar entrega parcial para orden {orden_id}: {str(ve)}")
        return jsonify({'error': str(ve)}), 400
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error al registrar entrega parcial para orden {orden_id}: {str(e)}")
        return jsonify({'error': 'Ocurrió un error al registrar la entrega parcial.'}), 500



@app.route('/api/ordenes-produccion/<int:orden_id>/registrar-entrega-total', methods=['POST'])
@jwt_required()
def registrar_entrega_total(orden_id):
    claims = get_jwt()
    idcliente = claims.get('idcliente')
    usuario_id = claims.get('sub')  # Obtener usuario_id desde el token JWT
    if not idcliente:
        return jsonify({'error': 'No se encontró idcliente en el token.'}), 401
    if not usuario_id:
        return jsonify({'error': 'No se encontró usuario_id en el token.'}), 401

    try:
        # Convertir usuario_id a entero
        usuario_id = int(usuario_id)

        # Validar que el usuario exista (opcional, comentar si no es necesario)
        usuario = db.session.get(Usuarios, usuario_id)
        if not usuario:
            return jsonify({'error': 'Usuario no encontrado.'}), 400

        orden = db.session.get(OrdenProduccion, orden_id)
        if not orden or orden.estado not in ["En Producción", "En Producción-Parcial"] or orden.idcliente != idcliente:
            return jsonify({'error': 'La orden no está en estado válido o no pertenece al cliente.'}), 400

        cantidad_entregada = orden.cantidad_paquetes - (
            db.session.query(func.sum(EntregaParcial.cantidad_entregada))
            .filter_by(orden_produccion_id=orden.id)
            .scalar() or 0
        )

        if cantidad_entregada <= 0:
            return jsonify({'error': 'No hay cantidad pendiente para registrar entrega total.'}), 400

        with no_autoflush(db.session):
            materiales = MaterialProducto.query.filter_by(producto_compuesto_id=orden.producto_compuesto_id).all()
            for material in materiales:
                cantidad_consumida = abs(float(material.cantidad)) * float(cantidad_entregada)
                ultimo_kardex = Kardex.query.filter(
                    Kardex.producto_id == material.producto_base_id,
                    (Kardex.bodega_origen_id == orden.bodega_produccion_id) | (Kardex.bodega_destino_id == orden.bodega_produccion_id)
                ).order_by(Kardex.fecha.desc()).first()
                costo_unitario = float(ultimo_kardex.saldo_costo_unitario) if ultimo_kardex else 0.0
                saldo_cantidad_actual = float(ultimo_kardex.saldo_cantidad) if ultimo_kardex else 0.0
                saldo_costo_total_actual = float(ultimo_kardex.saldo_costo_total) if ultimo_kardex else 0.0

                if saldo_cantidad_actual < cantidad_consumida:
                    raise ValueError(f"No hay suficiente inventario para el producto {material.producto_base_id} en la bodega {orden.bodega_produccion_id}")

                kardex_salida = Kardex(
                    idcliente=idcliente,
                    producto_id=material.producto_base_id,
                    bodega_origen_id=orden.bodega_produccion_id,
                    fecha=obtener_hora_colombia(),
                    tipo_movimiento='SALIDA',
                    cantidad=cantidad_consumida,
                    costo_unitario=costo_unitario,
                    costo_total=costo_unitario * cantidad_consumida,
                    saldo_cantidad=saldo_cantidad_actual - cantidad_consumida,
                    saldo_costo_unitario=costo_unitario,
                    saldo_costo_total=saldo_costo_total_actual - (costo_unitario * cantidad_consumida),
                    referencia=f"Consumo para orden {orden.numero_orden}"
                )
                db.session.add(kardex_salida)
                actualizar_estado_inventario(
                    material.producto_base_id,
                    orden.bodega_produccion_id,
                    cantidad_consumida,
                    es_entrada=False,
                    orden_id=orden_id
                )

                detalle = DetalleProduccion(
                    idcliente=idcliente,
                    orden_produccion_id=orden.id,
                    producto_base_id=material.producto_base_id,
                    cantidad_consumida=cantidad_consumida,
                    cantidad_producida=cantidad_entregada,
                    bodega_destino_id=orden.bodega_produccion_id,
                    fecha_registro=obtener_hora_colombia()
                )
                db.session.add(detalle)

            ultimo_kardex_compuesto = Kardex.query.filter(
                Kardex.producto_id == orden.producto_compuesto_id,
                Kardex.bodega_destino_id == orden.bodega_produccion_id
            ).order_by(Kardex.fecha.desc()).first()
            saldo_cantidad_compuesto = float(ultimo_kardex_compuesto.saldo_cantidad) if ultimo_kardex_compuesto else 0.0
            costo_unitario_compuesto = float(orden.costo_unitario or 0)

            kardex_entrada = Kardex(
                idcliente=idcliente,
                producto_id=orden.producto_compuesto_id,
                bodega_destino_id=orden.bodega_produccion_id,
                fecha=obtener_hora_colombia(),
                tipo_movimiento='ENTRADA',
                cantidad=float(cantidad_entregada),
                costo_unitario=costo_unitario_compuesto,
                costo_total=costo_unitario_compuesto * float(cantidad_entregada),
                saldo_cantidad=saldo_cantidad_compuesto + float(cantidad_entregada),
                saldo_costo_unitario=costo_unitario_compuesto,
                saldo_costo_total=(saldo_cantidad_compuesto + float(cantidad_entregada)) * costo_unitario_compuesto,
                referencia=f"Producción total de orden {orden.numero_orden}"
            )
            db.session.add(kardex_entrada)
            actualizar_estado_inventario(
                orden.producto_compuesto_id,
                orden.bodega_produccion_id,
                float(cantidad_entregada),
                es_entrada=True,
                orden_id=orden_id
            )

            entrega = EntregaParcial(
                orden_produccion_id=orden_id,
                cantidad_entregada=float(cantidad_entregada),
                fecha_entrega=obtener_hora_colombia(),
                comentario="Entrega total en bodega registrada automáticamente",
                idcliente=idcliente,
                usuario_id=usuario_id
            )
            db.session.add(entrega)

            orden.estado = "Finalizada"
            orden.fecha_finalizacion = obtener_hora_colombia()

        db.session.commit()
        return jsonify({'message': 'Entrega total registrada y orden finalizada con éxito.'}), 200

    except ValueError as ve:
        db.session.rollback()
        return jsonify({'error': str(ve)}), 400
    except Exception as e:
        db.session.rollback()
        print(f"Error al registrar entrega total: {str(e)}")
        return jsonify({'error': str(e)}), 500



@app.route('/api/ordenes-produccion/<int:orden_id>/cierre-forzado', methods=['POST'])
@jwt_required()
def cierre_forzado(orden_id):
    claims = get_jwt()
    idcliente = claims.get('idcliente')
    if not idcliente:
        logger.error("No se encontró idcliente en el token")
        return jsonify({'error': 'No se encontró idcliente en el token.'}), 401

    try:
        data = request.get_json()
        comentario_usuario = data.get("comentario", "").strip()

        orden = db.session.get(OrdenProduccion, orden_id)
        if not orden or orden.idcliente != idcliente:
            logger.error(f"Orden no encontrada o no pertenece al cliente: orden_id={orden_id}, idcliente={idcliente}")
            return jsonify({'error': 'Orden no encontrada o no pertenece al cliente.'}), 404

        if orden.estado != "En Producción-Parcial":
            logger.error(f"Estado inválido para cierre forzado: orden_id={orden_id}, estado={orden.estado}")
            return jsonify({'error': 'Solo se pueden cerrar órdenes en estado "En Producción-Parcial".'}), 400

        comentario_final = comentario_usuario if comentario_usuario else "Cierre forzado sin comentario adicional"

        # Obtener el último saldo del producto compuesto en Kardex
        ultimo_kardex = Kardex.query.filter(
            Kardex.producto_id == orden.producto_compuesto_id,
            Kardex.bodega_destino_id == orden.bodega_produccion_id
        ).order_by(Kardex.fecha.desc()).first()

        saldo_cantidad = float(ultimo_kardex.saldo_cantidad) if ultimo_kardex else 0.0
        costo_unitario = float(ultimo_kardex.saldo_costo_unitario) if ultimo_kardex else float(orden.costo_unitario or 0)
        saldo_costo_total = saldo_cantidad * costo_unitario

        # Obtener la cantidad total producida
        entregas = db.session.query(func.sum(EntregaParcial.cantidad_entregada))\
            .filter_by(orden_produccion_id=orden_id).scalar() or 0
        costo_total_real = float(entregas) * costo_unitario

        # Registrar movimiento en Kardex
        kardex_cierre = Kardex(
            idcliente=idcliente,  # Asignar idcliente desde claims
            producto_id=orden.producto_compuesto_id,
            bodega_destino_id=orden.bodega_produccion_id,
            fecha=obtener_hora_colombia(),
            tipo_movimiento='ENTRADA',
            cantidad=0,
            costo_unitario=costo_unitario,
            costo_total=0,
            saldo_cantidad=saldo_cantidad,
            saldo_costo_unitario=costo_unitario,
            saldo_costo_total=saldo_costo_total,
            referencia=f"Cierre forzado de orden {orden.numero_orden}"
        )
        db.session.add(kardex_cierre)

        # Usar un bloque no_autoflush para evitar flush prematuro
        with db.session.no_autoflush:
            # Actualizar estado_inventario usando la función
            actualizar_estado_inventario(
                orden.producto_compuesto_id,
                orden.bodega_produccion_id,
                0,  # Cantidad 0 para mantener el saldo actual
                es_entrada=True,
                orden_id=orden_id
            )

        # Ajustar el costo_total de la orden
        orden.costo_total = costo_total_real
        orden.estado = "Finalizada"
        orden.fecha_finalizacion = obtener_hora_colombia()
        orden.comentario_cierre_forzado = comentario_final

        db.session.commit()
        logger.info(f"Cierre forzado realizado con éxito para orden_id={orden_id}")

        return jsonify({
            'message': 'Cierre forzado realizado con éxito.',
            'comentario': comentario_final,
            'costo_total_real': costo_total_real
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error al realizar el cierre forzado para orden_id={orden_id}: {str(e)}")
        return jsonify({'error': 'No se pudo completar el cierre forzado.'}), 500
    


@app.route('/api/ordenes-produccion/<int:orden_id>/estado', methods=['PUT'])
@jwt_required()
def actualizar_estado_orden(orden_id):
    claims = get_jwt()
    idcliente = claims.get('idcliente')
    if not idcliente:
        return jsonify({'error': 'No se encontró idcliente en el token.'}), 401

    try:
        data = request.get_json()
        nuevo_estado = data.get("nuevo_estado")
        usuario_id = data.get("usuario_id")

        estados_validos = ["Pendiente", "Lista para Producción", "En Producción", "En Producción-Parcial", "Finalizada"]
        if not nuevo_estado or nuevo_estado not in estados_validos:
            return jsonify({"error": "El estado proporcionado no es válido."}), 400

        orden = db.session.get(OrdenProduccion, orden_id)
        if not orden or orden.idcliente != idcliente:
            return jsonify({"error": "Orden de producción no encontrada o no pertenece al cliente."}), 404

        if nuevo_estado == "Lista para Producción":
            materiales_necesarios = db.session.query(
                MaterialProducto.producto_base_id, MaterialProducto.cantidad
            ).filter(MaterialProducto.producto_compuesto_id == orden.producto_compuesto_id).all()

            for producto_base_id, cantidad_por_paquete in materiales_necesarios:
                cantidad_total_requerida = cantidad_por_paquete * orden.cantidad_paquetes
                inventario_disponible = db.session.query(
                    EstadoInventario.cantidad
                ).filter(
                    EstadoInventario.producto_id == producto_base_id,
                    EstadoInventario.bodega_id == orden.bodega_produccion_id
                ).scalar() or 0

                if inventario_disponible < cantidad_total_requerida:
                    codigo_producto = db.session.query(Producto.codigo).filter(Producto.id == producto_base_id).scalar()
                    return jsonify({
                        "error": f"El producto con código '{codigo_producto}' no tiene suficiente inventario en la bodega de producción. Se requieren {cantidad_total_requerida}, pero solo hay {inventario_disponible}."
                    }), 400

        if nuevo_estado == "Lista para Producción" and not orden.fecha_lista_para_produccion:
            orden.fecha_lista_para_produccion = obtener_hora_colombia()

        if nuevo_estado == "En Producción":
            if not orden.fecha_inicio:
                orden.fecha_inicio = obtener_hora_colombia()
            if usuario_id:
                orden.en_produccion_por = usuario_id

        if nuevo_estado == "Finalizada" and not orden.fecha_finalizacion:
            orden.fecha_finalizacion = obtener_hora_colombia()

        orden.estado = nuevo_estado
        db.session.commit()

        return jsonify({"message": f"Estado actualizado a {nuevo_estado} correctamente."}), 200

    except Exception as e:
        print(f"Error al actualizar estado: {str(e)}")
        return jsonify({"error": "Ocurrió un error al actualizar el estado."}), 500


# Generar PDF detallado de una orden de producción
@app.route('/api/ordenes-produccion/<int:orden_id>/pdf', methods=['GET'])
@jwt_required()
def generar_pdf_orden(orden_id):
    claims = get_jwt()
    idcliente = claims.get('idcliente')
    if not idcliente:
        return jsonify({'error': 'No se encontró idcliente en el token.'}), 401

    try:
        # Consultar la orden de producción
        orden = db.session.get(OrdenProduccion, orden_id)
        if not orden or orden.idcliente != idcliente:
            return jsonify({'error': 'Orden de producción no encontrada o no pertenece al cliente.'}), 404

        # Verificar permisos
        permisos = claims.get('permisos', [])
        if not any(p['seccion'] == 'production' and p['subseccion'] == 'admin' and p['permiso'] == 'ver' for p in permisos):
            return jsonify({'error': 'No tienes permiso para generar este PDF.'}), 403

        # Consultar el usuario creador
        usuario_creador = db.session.get(Usuarios, orden.creado_por)
        nombre_creador = f"{usuario_creador.nombres} {usuario_creador.apellidos}" if usuario_creador else "Desconocido"

        # Consultar el usuario que produjo la orden
        usuario_productor = db.session.get(Usuarios, orden.en_produccion_por)
        nombre_productor = f"{usuario_productor.nombres} {usuario_productor.apellidos}" if usuario_productor else "N/A"

        # Verificar si la orden tuvo un cierre forzado
        tiene_cierre_forzado = bool(orden.comentario_cierre_forzado)
        comentario_cierre_forzado = orden.comentario_cierre_forzado or "Orden finalizada sin novedad."

        # Consultar los materiales del producto compuesto
        materiales_producto = MaterialProducto.query.filter_by(
            producto_compuesto_id=orden.producto_compuesto_id
        ).all()

        # Consultar el historial de entregas y calcular cantidad pendiente
        entregas_parciales = EntregaParcial.query.filter_by(
            orden_produccion_id=orden_id
        ).all()
        entregas_totales = sum(entrega.cantidad_entregada for entrega in entregas_parciales)
        cantidad_pendiente = orden.cantidad_paquetes - entregas_totales

        # Configuración del PDF con orientación horizontal
        buffer = BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=landscape(letter))
        styles = getSampleStyleSheet()

        # Encabezados del PDF
        pdf.setFont("Helvetica-Bold", 9)
        y = 570
        pdf.drawString(50, y, f"Orden de Producción: {orden.numero_orden}")
        y -= 15
        pdf.drawString(50, y, f"Producto: {orden.producto_compuesto.codigo} - {orden.producto_compuesto.nombre}")
        y -= 15
        pdf.drawString(50, y, f"Cantidad de Paquetes: {orden.cantidad_paquetes}")
        y -= 15
        pdf.drawString(50, y, f"Bodega de Producción: {orden.bodega_produccion.nombre if orden.bodega_produccion else 'No especificada'}")
        y -= 15
        pdf.drawString(50, y, f"Estado: {orden.estado}")
        y -= 15
        pdf.drawString(50, y, f"Costo Unitario: ${orden.costo_unitario:.2f}  |  Costo Total: ${orden.costo_total:.2f}")
        y -= 15
        pdf.setFont("Helvetica", 8)
        pdf.drawString(50, y, f"Creado por: {nombre_creador}")
        y -= 15
        pdf.drawString(50, y, f"Producido por: {nombre_productor}")

        # Tabla de fechas
        y -= 15
        pdf.setFont("Helvetica-Bold", 8)
        pdf.drawString(50, y, "Fecha de Creación")
        pdf.drawString(200, y, "Fecha Lista para Producción")
        pdf.drawString(350, y, "Fecha Inicio Producción")
        pdf.drawString(500, y, "Fecha Finalización")
        y -= 12
        pdf.setFont("Helvetica", 7)
        pdf.drawString(50, y, orden.fecha_creacion.strftime('%Y-%m-%d %H:%M'))
        pdf.drawString(200, y, orden.fecha_lista_para_produccion.strftime('%Y-%m-%d %H:%M') if orden.fecha_lista_para_produccion else 'N/A')
        pdf.drawString(350, y, orden.fecha_inicio.strftime('%Y-%m-%d %H:%M') if orden.fecha_inicio else 'N/A')
        pdf.drawString(500, y, orden.fecha_finalizacion.strftime('%Y-%m-%d %H:%M') if orden.fecha_finalizacion else 'N/A')
        y -= 10
        pdf.line(50, y, 742, y)

        # Tabla de materiales
        y -= 15
        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawString(50, y, "Detalle de la Orden")
        y -= 15
        pdf.setFont("Helvetica-Bold", 8)
        pdf.drawString(50, y, "Componente")
        pdf.drawString(250, y, "Cant. x Paquete")
        pdf.drawString(320, y, "Cant. Total")
        pdf.drawString(380, y, "Peso x Paquete")
        pdf.drawString(450, y, "Peso Total")
        pdf.drawString(520, y, "Costo Unitario")
        pdf.drawString(590, y, "Costo Total")
        y -= 15

        pdf.setFont("Helvetica", 7)

        def draw_wrapped_text(pdf, x, y, text, max_width):
            """Dibuja texto justificado que salta de línea si excede el ancho máximo."""
            words = text.split(" ")
            line = ""
            for word in words:
                test_line = f"{line} {word}".strip()
                if pdf.stringWidth(test_line, "Helvetica", 7) <= max_width:
                    line = test_line
                else:
                    pdf.drawString(x, y, line)
                    y -= 8
                    line = word
            if line:
                pdf.drawString(x, y, line)
                y -= 8
            return y

        for material in materiales_producto:
            producto_base = db.session.get(Producto, material.producto_base_id)

            # Obtener costo unitario desde el último registro en kardex para la bodega de producción
            ultimo_kardex = Kardex.query.filter(
                Kardex.producto_id == material.producto_base_id,
                Kardex.bodega_destino_id == orden.bodega_produccion_id
            ).order_by(Kardex.fecha.desc()).first()
            costo_unitario = Decimal(str(ultimo_kardex.saldo_costo_unitario)) if ultimo_kardex else Decimal('0.0')

            peso_x_paquete = (
                Decimal(str(material.peso_unitario)) if material.peso_unitario is not None else (
                    Decimal(str(producto_base.peso_unitario)) if producto_base and producto_base.peso_unitario is not None else Decimal('0.0')
                )
            )
            # Convertir cantidades a Decimal para evitar problemas con float
            cantidad_material = Decimal(str(material.cantidad))
            cantidad_paquetes = Decimal(str(orden.cantidad_paquetes))

            cantidad_total = cantidad_material * cantidad_paquetes
            peso_total = cantidad_total * peso_x_paquete
            costo_total = cantidad_total * costo_unitario

            y = draw_wrapped_text(pdf, 50, y, f"{producto_base.codigo} - {producto_base.nombre}", 200)
            pdf.drawString(250, y + 8, f"{cantidad_material:.2f}")
            pdf.drawString(320, y + 8, f"{cantidad_total:.2f}")
            pdf.drawString(380, y + 8, f"{peso_x_paquete:.2f}")
            pdf.drawString(450, y + 8, f"{peso_total:.2f}")
            pdf.drawString(520, y + 8, f"${costo_unitario:.2f}")
            pdf.drawString(590, y + 8, f"${costo_total:.2f}")
            y -= 8

            if y < 80:
                pdf.showPage()
                y = 550

        # Línea divisoria después de Detalle de la Orden
        y -= 10
        pdf.line(50, y, 742, y)

        # Tabla de historial de entregas
        y -= 15
        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawString(50, y, "Historial de Entregas")
        y -= 15
        pdf.setFont("Helvetica-Bold", 8)
        pdf.drawString(50, y, "Fecha")
        pdf.drawString(200, y, "Cantidad Entregada")
        pdf.drawString(350, y, "Comentario")
        y -= 15

        pdf.setFont("Helvetica", 7)
        for entrega in entregas_parciales:
            pdf.drawString(50, y, entrega.fecha_entrega.strftime('%Y-%m-%d %H:%M'))
            pdf.drawString(200, y, f"{entrega.cantidad_entregada:.2f}")
            pdf.drawString(350, y, entrega.comentario or "N/A")
            y -= 10

            if y < 80:
                pdf.showPage()
                y = 550

        # Cantidad pendiente
        y -= 15
        pdf.setFont("Helvetica-Bold", 8)
        pdf.drawString(50, y, f"Cantidad Pendiente: {cantidad_pendiente:.2f}")

        # Línea divisoria después de Historial de Entregas
        y -= 10
        pdf.line(50, y, 742, y)

        # Mostrar "Cierre Forzado" o "Orden Finalizada sin Novedad" con título en negrita
        y -= 15
        pdf.setFont("Helvetica-Bold", 10)
        if tiene_cierre_forzado:
            pdf.drawString(50, y, "Cierre Forzado")
        elif orden.estado == "Finalizada":
            pdf.drawString(50, y, "Orden Finalizada sin Novedad")
        else:
            pdf.drawString(50, y, "Orden en Proceso de Producción")
        y -= 15

        # Mostrar el comentario (si lo hay) en texto normal
        if tiene_cierre_forzado:
            pdf.setFont("Helvetica", 8)
            y = draw_wrapped_text(pdf, 50, y, comentario_cierre_forzado, 700)

        # Agregar firmas al final en una fila horizontal
        if y < 80:
            pdf.showPage()
            y = 550

        pdf.setFont("Helvetica", 10)
        y -= 50

        # Despachado por (izquierda)
        pdf.line(50, y, 280, y)
        pdf.drawString(50, y - 12, "Despachado por")

        # Entregado por (centro)
        pdf.line(300, y, 530, y)
        pdf.drawString(300, y - 12, "Entregado por")

        # Recibido (derecha)
        pdf.line(550, y, 780, y)
        pdf.drawString(550, y - 12, "Recibido")

        # Finalizar y guardar el PDF
        pdf.save()
        buffer.seek(0)

        # Configurar la respuesta del PDF
        nombre_archivo = f"Orden_{orden.numero_orden}.pdf"
        response = make_response(buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename="{nombre_archivo}"'
        return response

    except Exception as e:
        print(f"Error al generar PDF: {str(e)}")
        return jsonify({'error': 'Ocurrió un error al generar el PDF'}), 500


# Generar PDF simplificado para operadores
@app.route('/api/ordenes-produccion/<int:orden_id>/pdf-operador', methods=['GET'])
@jwt_required()
def generar_pdf_orden_operador(orden_id):
    claims = get_jwt()
    idcliente = claims.get('idcliente')
    if not idcliente:
        return jsonify({'error': 'No se encontró idcliente en el token.'}), 401

    try:
        # Consultar la orden de producción
        orden = db.session.get(OrdenProduccion, orden_id)
        if not orden or orden.idcliente != idcliente:
            return jsonify({'error': 'Orden de producción no encontrada o no pertenece al cliente.'}), 404

        # Verificar permisos
        permisos = claims.get('permisos', [])
        if not any(p['seccion'] == 'production' and p['subseccion'] == 'admin' and p['permiso'] == 'ver' for p in permisos):
            return jsonify({'error': 'No tienes permiso para generar este PDF.'}), 403

        # Consultar el usuario creador
        usuario_creador = db.session.get(Usuarios, orden.creado_por)
        nombre_creador = f"{usuario_creador.nombres} {usuario_creador.apellidos}" if usuario_creador else "Desconocido"

        # Consultar el usuario que produjo la orden
        usuario_productor = db.session.get(Usuarios, orden.en_produccion_por)
        nombre_productor = f"{usuario_productor.nombres} {usuario_productor.apellidos}" if usuario_productor else "N/A"

        # Verificar si la orden tuvo un cierre forzado
        tiene_cierre_forzado = bool(orden.comentario_cierre_forzado)
        comentario_cierre_forzado = orden.comentario_cierre_forzado or "Orden finalizada sin novedad."

        # Consultar los materiales del producto compuesto
        materiales_producto = MaterialProducto.query.filter_by(
            producto_compuesto_id=orden.producto_compuesto_id
        ).all()

        # Consultar el historial de entregas y calcular cantidad pendiente
        entregas_parciales = EntregaParcial.query.filter_by(
            orden_produccion_id=orden_id
        ).all()
        entregas_totales = sum(entrega.cantidad_entregada for entrega in entregas_parciales)
        cantidad_pendiente = orden.cantidad_paquetes - entregas_totales

        # Configuración del PDF con orientación horizontal
        buffer = BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=landscape(letter))

        # Encabezados del PDF
        pdf.setFont("Helvetica-Bold", 9)
        y = 570
        pdf.drawString(50, y, f"Orden de Producción: {orden.numero_orden}")
        y -= 15
        pdf.drawString(50, y, f"Producto: {orden.producto_compuesto.codigo} - {orden.producto_compuesto.nombre}")
        y -= 15
        pdf.drawString(50, y, f"Cantidad de Paquetes: {orden.cantidad_paquetes}")
        y -= 15
        pdf.drawString(50, y, f"Bodega de Producción: {orden.bodega_produccion.nombre if orden.bodega_produccion else 'No especificada'}")
        y -= 15
        pdf.drawString(50, y, f"Estado: {orden.estado}")
        y -= 15
        pdf.setFont("Helvetica", 8)
        pdf.drawString(50, y, f"Creado por: {nombre_creador}")
        y -= 15
        pdf.drawString(50, y, f"Producido por: {nombre_productor}")

        # Tabla de fechas
        y -= 15
        pdf.setFont("Helvetica-Bold", 8)
        pdf.drawString(50, y, "Fecha de Creación")
        pdf.drawString(200, y, "Fecha Lista para Producción")
        pdf.drawString(350, y, "Fecha Inicio Producción")
        pdf.drawString(500, y, "Fecha Finalización")
        y -= 12
        pdf.setFont("Helvetica", 7)
        pdf.drawString(50, y, orden.fecha_creacion.strftime('%Y-%m-%d %H:%M'))
        pdf.drawString(200, y, orden.fecha_lista_para_produccion.strftime('%Y-%m-%d %H:%M') if orden.fecha_lista_para_produccion else 'N/A')
        pdf.drawString(350, y, orden.fecha_inicio.strftime('%Y-%m-%d %H:%M') if orden.fecha_inicio else 'N/A')
        pdf.drawString(500, y, orden.fecha_finalizacion.strftime('%Y-%m-%d %H:%M') if orden.fecha_finalizacion else 'N/A')
        y -= 10
        pdf.line(50, y, 742, y)

        # Tabla de materiales (sin costos)
        y -= 15
        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawString(50, y, "Detalle de la Orden")
        y -= 15
        pdf.setFont("Helvetica-Bold", 8)
        pdf.drawString(50, y, "Componente")
        pdf.drawString(400, y, "Cant. x Paquete")
        pdf.drawString(500, y, "Cant. Total")
        pdf.drawString(600, y, "Peso Total")
        y -= 15

        pdf.setFont("Helvetica", 7)

        def draw_wrapped_text(pdf, x, y, text, max_width):
            words = text.split(" ")
            line = ""
            for word in words:
                test_line = f"{line} {word}".strip()
                if pdf.stringWidth(test_line, "Helvetica", 7) <= max_width:
                    line = test_line
                else:
                    pdf.drawString(x, y, line)
                    y -= 8
                    line = word
            if line:
                pdf.drawString(x, y, line)
                y -= 8
            return y

        for material in materiales_producto:
            producto_base = db.session.get(Producto, material.producto_base_id)
            peso_x_paquete = (
                Decimal(str(material.peso_unitario)) if material.peso_unitario is not None else (
                    Decimal(str(producto_base.peso_unitario)) if producto_base and producto_base.peso_unitario is not None else Decimal('0.0')
                )
            )
            # Convertir cantidades a Decimal
            cantidad_material = Decimal(str(material.cantidad))
            cantidad_paquetes = Decimal(str(orden.cantidad_paquetes))

            cantidad_total = cantidad_material * cantidad_paquetes
            peso_total = cantidad_total * peso_x_paquete

            y = draw_wrapped_text(pdf, 50, y, f"{producto_base.codigo} - {producto_base.nombre}", 350)
            pdf.drawString(400, y + 8, f"{cantidad_material:.2f}")
            pdf.drawString(500, y + 8, f"{cantidad_total:.2f}")
            pdf.drawString(600, y + 8, f"{peso_total:.2f}")
            y -= 8

            if y < 80:
                pdf.showPage()
                y = 550

        # Línea divisoria después de Detalle de la Orden
        y -= 10
        pdf.line(50, y, 742, y)

        # Tabla de historial de entregas
        y -= 15
        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawString(50, y, "Historial de Entregas")
        y -= 15
        pdf.setFont("Helvetica-Bold", 8)
        pdf.drawString(50, y, "Fecha")
        pdf.drawString(200, y, "Cantidad Entregada")
        pdf.drawString(350, y, "Comentario")
        y -= 15

        pdf.setFont("Helvetica", 7)
        for entrega in entregas_parciales:
            pdf.drawString(50, y, entrega.fecha_entrega.strftime('%Y-%m-%d %H:%M'))
            pdf.drawString(200, y, f"{entrega.cantidad_entregada:.2f}")
            pdf.drawString(350, y, entrega.comentario or "N/A")
            y -= 10

            if y < 80:
                pdf.showPage()
                y = 550

        # Cantidad pendiente
        y -= 15
        pdf.setFont("Helvetica-Bold", 8)
        pdf.drawString(50, y, f"Cantidad Pendiente: {cantidad_pendiente:.2f}")

        # Línea divisoria después de Historial de Entregas
        y -= 10
        pdf.line(50, y, 742, y)

        # Mostrar "Cierre Forzado" o "Orden Finalizada sin Novedad" con título en negrita
        y -= 15
        pdf.setFont("Helvetica-Bold", 10)
        if tiene_cierre_forzado:
            pdf.drawString(50, y, "Cierre Forzado")
        elif orden.estado == "Finalizada":
            pdf.drawString(50, y, "Orden Finalizada sin Novedad")
        else:
            pdf.drawString(50, y, "Orden en Proceso de Producción")
        y -= 15

        if tiene_cierre_forzado:
            pdf.setFont("Helvetica", 8)
            y = draw_wrapped_text(pdf, 50, y, comentario_cierre_forzado, 700)

        # Agregar firmas al final
        if y < 80:
            pdf.showPage()
            y = 550

        pdf.setFont("Helvetica", 10)
        y -= 50
        pdf.line(50, y, 280, y)
        pdf.drawString(50, y - 12, "Despachado por")
        pdf.line(300, y, 530, y)
        pdf.drawString(300, y - 12, "Entregado por")
        pdf.line(550, y, 780, y)
        pdf.drawString(550, y - 12, "Recibido")

        # Finalizar y guardar el PDF
        pdf.save()
        buffer.seek(0)

        # Configurar la respuesta del PDF
        nombre_archivo = f"Orden_{orden.numero_orden}_Operador.pdf"
        response = make_response(buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename="{nombre_archivo}"'
        return response

    except Exception as e:
        print(f"Error al generar PDF para operador: {str(e)}")
        return jsonify({'error': 'Ocurrió un error al generar el PDF'}), 500

# Generar PDF del listado de órdenes de producción
@app.route('/api/ordenes-produccion/listado-pdf', methods=['POST'])
@jwt_required()
def generar_listado_pdf():
    claims = get_jwt()
    idcliente = claims.get('idcliente')
    if not idcliente:
        return jsonify({'error': 'No se encontró idcliente en el token.'}), 401

    try:
        # Verificar permisos
        permisos = claims.get('permisos', [])
        if not any(p['seccion'] == 'production' and p['subseccion'] == 'admin' and p['permiso'] == 'ver' for p in permisos):
            return jsonify({'error': 'No tienes permiso para generar este PDF.'}), 403

        data = request.get_json()
        estado = data.get('estado')
        fecha_inicio = data.get('fecha_inicio')
        fecha_fin = data.get('fecha_fin')

        # Consultar las órdenes con los filtros aplicados
        query = OrdenProduccion.query.filter_by(idcliente=idcliente)

        if estado:
            query = query.filter_by(estado=estado)
        if fecha_inicio and fecha_fin:
            query = query.filter(
                OrdenProduccion.fecha_finalizacion.between(fecha_inicio, fecha_fin)
            )

        ordenes = query.all()

        # Crear el PDF
        buffer = BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=landscape(letter))
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(30, 550, "Listado de Órdenes de Producción")

        # Encabezados
        pdf.setFont("Helvetica-Bold", 10)
        headers = ["# Orden", "Producto", "Cantidad", "Estado", "Fecha Estado", "Tiempo Producción"]
        x_positions = [30, 110, 380, 460, 550, 680]

        for i, header in enumerate(headers):
            pdf.drawString(x_positions[i], 520, header)

        # Función para ajustar texto
        def draw_wrapped_text(canvas, text, x, y, max_width, line_height):
            words = text.split(" ")
            line = ""
            for word in words:
                test_line = f"{line} {word}".strip()
                if canvas.stringWidth(test_line, "Helvetica", 10) <= max_width:
                    line = test_line
                else:
                    canvas.drawString(x, y, line)
                    y -= line_height
                    line = word
            if line:
                canvas.drawString(x, y, line)
                y -= line_height
            return y

        def calcular_tiempo_produccion(orden):
            """Calcula el tiempo en producción en horas o días."""
            if not orden.fecha_creacion:
                return "-"

            # Determinar la fecha de referencia según el estado de la orden
            fecha_referencia = (
                orden.fecha_finalizacion if orden.estado == "Finalizada" else
                orden.fecha_inicio if orden.estado in ["En Producción", "En Producción-Parcial"] else
                orden.fecha_lista_para_produccion if orden.estado == "Lista para Producción" else
                orden.fecha_creacion
            )

            if not fecha_referencia:
                return "-"

            # Calcular la diferencia en horas
            diferencia_horas = (fecha_referencia - orden.fecha_creacion).total_seconds() / 3600

            # Si el tiempo es mayor a 24 horas, mostrar en días
            if diferencia_horas >= 24:
                return f"{int(diferencia_horas // 24)} día(s)"
            else:
                return f"{int(diferencia_horas)} hora(s)"

        # Cuerpo del PDF
        pdf.setFont("Helvetica", 10)
        y = 500
        line_height = 15

        for orden in ordenes:
            producto_nombre = f"{orden.producto_compuesto.codigo} - {orden.producto_compuesto.nombre}"
            fecha_estado = (
                orden.fecha_finalizacion or
                orden.fecha_inicio or
                orden.fecha_lista_para_produccion or
                orden.fecha_creacion or None
            )

            # Datos a mostrar
            data = [
                orden.numero_orden,
                producto_nombre,
                str(orden.cantidad_paquetes),
                orden.estado,
                fecha_estado.strftime('%Y-%m-%d %H:%M') if fecha_estado else "-",
                calcular_tiempo_produccion(orden)
            ]

            y_position = y
            for i, value in enumerate(data):
                if i == 1:  # Ajustar texto en la columna de Producto
                    y_position = draw_wrapped_text(
                        pdf, value, x_positions[i], y, max_width=250, line_height=line_height
                    )
                else:
                    pdf.drawString(x_positions[i], y, value)

            y = y_position - line_height  # Ajustar espacio entre filas
            if y < 50:  # Salto de página si el contenido excede
                pdf.showPage()
                pdf.setFont("Helvetica", 10)
                y = 550

        pdf.save()
        buffer.seek(0)

        response = make_response(buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'attachment; filename="Listado_Ordenes_Produccion.pdf"'
        return response

    except Exception as e:
        print(f"Error al generar listado PDF: {str(e)}")
        return jsonify({'error': 'Ocurrió un error al generar el listado PDF.'}), 500

# Generar PDF del listado de órdenes de producción para operadores
@app.route('/api/ordenes-produccion/listado-operador-pdf', methods=['POST'])
@jwt_required()
def generar_listado_operador_pdf():
    claims = get_jwt()
    idcliente = claims.get('idcliente')
    if not idcliente:
        return jsonify({'error': 'No se encontró idcliente en el token.'}), 401

    try:
        # Verificar permisos
        permisos = claims.get('permisos', [])
        if not any(p['seccion'] == 'production' and p['subseccion'] == 'admin' and p['permiso'] == 'ver' for p in permisos):
            return jsonify({'error': 'No tienes permiso para generar este PDF.'}), 403

        data = request.get_json()
        estado = data.get('estado')
        fecha_inicio = data.get('fecha_inicio')
        fecha_fin = data.get('fecha_fin')

        # Consultar las órdenes con los filtros aplicados
        query = OrdenProduccion.query.filter_by(idcliente=idcliente)

        if estado:
            query = query.filter_by(estado=estado)
        if fecha_inicio and fecha_fin:
            query = query.filter(
                OrdenProduccion.fecha_finalizacion.between(fecha_inicio, fecha_fin)
            )

        ordenes = query.all()

        # Crear el PDF
        buffer = BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=landscape(letter))
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(30, 550, "Listado de Órdenes de Producción")

        # Encabezados
        pdf.setFont("Helvetica-Bold", 10)
        headers = ["# Orden", "Producto", "Cantidad", "Estado", "Fecha Estado"]
        x_positions = [30, 110, 440, 540, 650]

        for i, header in enumerate(headers):
            pdf.drawString(x_positions[i], 520, header)

        # Función para ajustar texto
        def draw_wrapped_text(canvas, text, x, y, max_width, line_height):
            words = text.split(" ")
            line = ""
            for word in words:
                test_line = f"{line} {word}".strip()
                if canvas.stringWidth(test_line, "Helvetica", 10) <= max_width:
                    line = test_line
                else:
                    canvas.drawString(x, y, line)
                    y -= line_height
                    line = word
            if line:
                canvas.drawString(x, y, line)
                y -= line_height
            return y

        # Cuerpo del PDF
        pdf.setFont("Helvetica", 10)
        y = 500
        line_height = 15
        for orden in ordenes:
            producto_nombre = f"{orden.producto_compuesto.codigo} - {orden.producto_compuesto.nombre}"
            fecha_estado = (
                orden.fecha_finalizacion if orden.estado == "Finalizada" else
                orden.fecha_inicio if orden.estado in ["En Producción", "En Producción-Parcial"] else
                orden.fecha_lista_para_produccion if orden.estado == "Lista para Producción" else
                orden.fecha_creacion
            )

            # Datos a mostrar
            data = [
                orden.numero_orden,
                producto_nombre,
                str(orden.cantidad_paquetes),
                orden.estado,
                fecha_estado.strftime('%Y-%m-%d %H:%M') if fecha_estado else "-"
            ]

            y_position = y
            for i, value in enumerate(data):
                if i == 1:  # Ajustar texto en la columna de Producto
                    y_position = draw_wrapped_text(
                        pdf, value, x_positions[i], y, max_width=300, line_height=line_height
                    )
                else:
                    pdf.drawString(x_positions[i], y, value)

            y = y_position - line_height  # Ajustar espacio entre filas
            if y < 50:  # Salto de página si el contenido excede
                pdf.showPage()
                pdf.setFont("Helvetica", 10)
                y = 550

        pdf.save()
        buffer.seek(0)

        response = make_response(buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'attachment; filename="Listado_Ordenes_Produccion_Operador.pdf"'
        return response

    except Exception as e:
        print(f"Error al generar listado PDF: {str(e)}")
        return jsonify({'error': 'Ocurrió un error al generar el listado PDF.'}), 500

#Filtro para pagina de reportes de producción
@app.route('/api/ordenes-produccion/filtrar', methods=['GET'])
@jwt_required()
def filtrar_ordenes_produccion():
    try:
        claims = get_jwt()
        idcliente = claims.get('idcliente')
        if not idcliente:
            return jsonify({'error': 'No se encontró idcliente en el token.'}), 401

        # Verificar permisos
        permisos = claims.get('permisos', [])
        if not any(p['seccion'] == 'production' and p['subseccion'] == 'reportes' and p['permiso'] == 'ver' for p in permisos):
            return jsonify({'error': 'No tienes permiso para consultar órdenes de producción.'}), 403

        numero_orden = request.args.get('numero_orden')
        estado = request.args.get('estado')
        fecha_inicio = request.args.get('fecha_inicio')
        fecha_fin = request.args.get('fecha_fin')

        query = OrdenProduccion.query.filter_by(idcliente=idcliente)

        # Filtrar por número de orden
        if numero_orden:
            query = query.filter_by(numero_orden=numero_orden)

        # Filtrar por estado
        if estado:
            query = query.filter_by(estado=estado)

        # Filtrar por rango de fechas
        if fecha_inicio and fecha_fin:
            query = query.filter(
                (OrdenProduccion.fecha_creacion.between(fecha_inicio, fecha_fin)) |
                (OrdenProduccion.fecha_inicio.between(fecha_inicio, fecha_fin)) |
                (OrdenProduccion.fecha_finalizacion.between(fecha_inicio, fecha_fin))
            )

        ordenes = query.order_by(OrdenProduccion.id.desc()).all()

        resultado = [
            {
                'id': orden.id,
                'numero_orden': orden.numero_orden,
                'producto_compuesto_id': orden.producto_compuesto_id,
                'producto_compuesto_nombre': f'{orden.producto_compuesto.codigo} - {orden.producto_compuesto.nombre}' if orden.producto_compuesto else 'N/A',
                'cantidad_paquetes': float(orden.cantidad_paquetes) if orden.cantidad_paquetes else 0.0,
                'estado': orden.estado,
                'bodega_produccion_id': orden.bodega_produccion_id,
                'bodega_produccion_nombre': orden.bodega_produccion.nombre if orden.bodega_produccion else 'No especificada',
                'fecha_creacion': orden.fecha_creacion.isoformat() if orden.fecha_creacion else None,
                'fecha_inicio': orden.fecha_inicio.isoformat() if orden.fecha_inicio else None,
                'fecha_finalizacion': orden.fecha_finalizacion.isoformat() if orden.fecha_finalizacion else None,
                'creado_por': f'{orden.creado_por_usuario.nombres} {orden.creado_por_usuario.apellidos}' if orden.creado_por_usuario else 'N/A'
            }
            for orden in ordenes
        ]

        return jsonify(resultado), 200
    except Exception as e:
        print(f'Error al filtrar órdenes de producción: {str(e)}')
        return jsonify({'error': 'Ocurrió un error al filtrar las órdenes de producción.'}), 500



@app.route('/inventory/productos-compuestos', methods=['GET'])
@jwt_required()
def obtener_productos_compuestos():
    try:
        claims = get_jwt()
        idcliente = claims.get('idcliente')
        if not idcliente:
            return jsonify({'error': 'Cliente no identificado'}), 401

        if not has_permission(claims, 'inventario', 'gestion_productos', 'ver'):
            return jsonify({'error': 'No autorizado'}), 403

        productos_compuestos = Producto.query.filter(
            and_(
                Producto.es_producto_compuesto == True,
                Producto.idcliente == idcliente
            )
        ).all()

        resultado = [
            {
                'id': producto.id,
                'codigo': producto.codigo,
                'nombre': producto.nombre
            }
            for producto in productos_compuestos
        ]

        return jsonify(resultado), 200
    except Exception as e:
        logger.error(f"Error al obtener productos compuestos: {str(e)}")
        return jsonify({'error': 'Ocurrió un error al obtener los productos compuestos.'}), 500


@app.route('/inventory/productos-compuestos/detalle', methods=['GET'])
@jwt_required()
def buscar_producto_compuesto():
    try:
        claims = get_jwt()
        idcliente = claims.get('idcliente')
        if not idcliente:
            return jsonify({'error': 'Cliente no identificado'}), 401

        if not has_permission(claims, 'inventario', 'gestion_productos', 'ver'):
            return jsonify({'error': 'No autorizado'}), 403

        producto_id = request.args.get('id', None)
        if not producto_id:
            return jsonify({'error': 'Debe proporcionar un ID de producto'}), 400

        producto = Producto.query.filter(
            and_(
                Producto.id == producto_id,
                Producto.es_producto_compuesto == True,
                Producto.idcliente == idcliente
            )
        ).first()

        if not producto:
            return jsonify({'error': 'Producto compuesto no encontrado'}), 404

        materiales = MaterialProducto.query.filter_by(producto_compuesto_id=producto.id).all()
        materiales_response = []
        for material in materiales:
            producto_base = db.session.get(Producto, material.producto_base_id)
            if not producto_base:
                continue  # Ignorar materiales con producto base no encontrado

            ultimo_kardex = Kardex.query.filter_by(
                producto_id=material.producto_base_id,
                idcliente=idcliente
            ).order_by(Kardex.fecha.desc()).first()
            costo_unitario = float(ultimo_kardex.saldo_costo_unitario) if ultimo_kardex else 0.0

            cantidad = float(material.cantidad) if isinstance(material.cantidad, Decimal) else material.cantidad
            peso_unitario = float(producto_base.peso_unidad_gr) if producto_base.peso_unidad_gr else 0.0

            materiales_response.append({
                'producto_base_nombre': producto_base.nombre,
                'cantidad': cantidad,
                'peso_unitario': peso_unitario,
                'costo_unitario': costo_unitario,
                'producto_base_id': material.producto_base_id,
                'producto_base_codigo': producto_base.codigo
            })

        return jsonify({
            'producto': {
                'id': producto.id,
                'codigo': producto.codigo,
                'nombre': producto.nombre
            },
            'materiales': materiales_response
        }), 200
    except Exception as e:
        logger.error(f"Error al buscar producto compuesto: {str(e)}")
        return jsonify({'error': 'Error al buscar producto compuesto'}), 500



#if __name__ == '__main__':
#    app.run(debug=True, host='0.0.0.0', port=5000)

if __name__ == '__main__':
        
    with app.app_context():
        db.create_all()  # Crea las tablas si no existen
    port = int(os.getenv('PORT', 5000))  # Usa $PORT si existe (Railway), o 5000 por defecto
    app.run(debug=True, host='0.0.0.0', port=port)
