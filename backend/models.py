from database import db

# No creamos una nueva instancia de SQLAlchemy aquí
# En su lugar, usaremos la instancia 'db' que se pasa desde app.py

# Modelos de SQLAlchemy
class Usuarios(db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    idcliente = db.Column(db.Integer, db.ForeignKey('clientes.idcliente'))
    perfilid = db.Column(db.Integer, db.ForeignKey('perfiles.perfil_id'))
    usuario = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    nombres = db.Column(db.String(50))
    apellidos = db.Column(db.String(50))
    fechacreacion = db.Column(db.DateTime, default=db.func.current_timestamp())
    fechamodificacion = db.Column(db.DateTime)
    estado = db.Column(db.Boolean, default=True)

class Clientes(db.Model):
    __tablename__ = 'clientes'
    idcliente = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    nit_cc = db.Column(db.String(20))
    pais = db.Column(db.String(50))
    ciudad = db.Column(db.String(50))
    direccion_ppal = db.Column(db.String(100))
    tel1 = db.Column(db.String(20))
    tel2 = db.Column(db.String(20))
    correo = db.Column(db.String(100))
    nombre_contacto = db.Column(db.String(100))
    tel_contacto = db.Column(db.String(20))
    correo_contacto = db.Column(db.String(100))
    estado = db.Column(db.Boolean, default=True)
    logo = db.Column(db.String(255))

class Perfiles(db.Model):
    __tablename__ = 'perfiles'
    perfil_id = db.Column(db.Integer, primary_key=True)
    idcliente = db.Column(db.Integer, db.ForeignKey('clientes.idcliente'))
    perfil_nombre = db.Column(db.String(50), nullable=False)
    estado = db.Column(db.Boolean, default=True)

class Permisos(db.Model):
    __tablename__ = 'permisos'
    idPermiso = db.Column(db.Integer, primary_key=True)
    idPerfil = db.Column(db.Integer, db.ForeignKey('perfiles.perfil_id'), nullable=False)
    seccion = db.Column(db.String(50), nullable=False)
    subseccion = db.Column(db.String(50))
    permiso = db.Column(db.String(20), nullable=False)

class Producto(db.Model):
    __tablename__ = 'productos'
    id = db.Column(db.Integer, primary_key=True)
    idcliente = db.Column(db.Integer, db.ForeignKey('clientes.idcliente'), nullable=False)
    codigo = db.Column(db.String(20), nullable=False)
    nombre = db.Column(db.String(255), nullable=False)
    peso_total_gr = db.Column(db.Numeric(10, 2))
    peso_unidad_gr = db.Column(db.Numeric(10, 2))
    codigo_barras = db.Column(db.String(50))
    es_producto_compuesto = db.Column(db.Boolean, default=False)
    stock_minimo = db.Column(db.Integer, nullable=True)

    __table_args__ = (
        db.UniqueConstraint('idcliente', 'codigo', name='uix_idcliente_codigo'),
        db.UniqueConstraint('idcliente', 'nombre', name='uix_idcliente_nombre'),
    )

class MaterialProducto(db.Model):
    __tablename__ = 'materiales_producto'
    id = db.Column(db.Integer, primary_key=True)
    idcliente = db.Column(db.Integer, db.ForeignKey('clientes.idcliente'), nullable=False)
    producto_compuesto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    producto_base_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    cantidad = db.Column(db.Float, nullable=False)
    peso_unitario = db.Column(db.Float, nullable=False)

class Bodega(db.Model):
    __tablename__ = 'bodegas'
    id = db.Column(db.Integer, primary_key=True)
    idcliente = db.Column(db.Integer, nullable=False)
    nombre = db.Column(db.String(255), nullable=False)

class InventarioBodega(db.Model):
    __tablename__ = 'inventario_bodega'
    id = db.Column(db.Integer, primary_key=True)
    idcliente = db.Column(db.Integer, nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    bodega_id = db.Column(db.Integer, db.ForeignKey('bodegas.id'), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False, default=0)
    factura = db.Column(db.String(50))
    contenedor = db.Column(db.String(50))
    fecha_ingreso = db.Column(db.DateTime, nullable=False)
    costo_unitario = db.Column(db.Numeric(15, 2), default=0.00)
    costo_total = db.Column(db.Numeric(15, 2), default=0.00)

    producto = db.relationship('Producto', backref='inventario_bodega')
    bodega = db.relationship('Bodega', backref='inventario_bodega')

class RegistroMovimientos(db.Model):
    __tablename__ = 'registro_movimientos'
    id = db.Column(db.Integer, primary_key=True)
    idcliente = db.Column(db.Integer, nullable=False)
    consecutivo = db.Column(db.String(20), nullable=False)
    tipo_movimiento = db.Column(db.String(50), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'))
    bodega_origen_id = db.Column(db.Integer, db.ForeignKey('bodegas.id'))
    bodega_destino_id = db.Column(db.Integer, db.ForeignKey('bodegas.id'))
    cantidad = db.Column(db.Integer, nullable=False)
    fecha = db.Column(db.DateTime, nullable=False)
    descripcion = db.Column(db.Text)
    costo_unitario = db.Column(db.Numeric(15, 2), default=0.00)
    costo_total = db.Column(db.Numeric(15, 2), default=0.00)

    producto = db.relationship('Producto', backref='movimientos')
    bodega_origen = db.relationship('Bodega', foreign_keys=[bodega_origen_id])
    bodega_destino = db.relationship('Bodega', foreign_keys=[bodega_destino_id])

class Kardex(db.Model):
    __tablename__ = 'kardex'
    id = db.Column(db.Integer, primary_key=True)
    idcliente = db.Column(db.Integer, db.ForeignKey('clientes.idcliente'), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    bodega_origen_id = db.Column(db.Integer, db.ForeignKey('bodegas.id'), nullable=True)
    bodega_destino_id = db.Column(db.Integer, db.ForeignKey('bodegas.id'), nullable=True)
    fecha = db.Column(db.DateTime, nullable=False)
    tipo_movimiento = db.Column(db.String(50), nullable=False)
    cantidad = db.Column(db.Numeric(15, 3), nullable=False)
    costo_unitario = db.Column(db.Numeric(15, 2), default=0.00)
    costo_total = db.Column(db.Numeric(15, 2), default=0.00)
    saldo_cantidad = db.Column(db.Numeric(15, 3), nullable=False)
    saldo_costo_unitario = db.Column(db.Numeric(15, 2), default=0.00)
    saldo_costo_total = db.Column(db.Numeric(15, 2), default=0.00)
    referencia = db.Column(db.String(100))

    producto = db.relationship('Producto', backref=db.backref('kardex_entries', lazy='dynamic'))
    bodega_origen = db.relationship('Bodega', foreign_keys=[bodega_origen_id], backref='kardex_origen_entries')
    bodega_destino = db.relationship('Bodega', foreign_keys=[bodega_destino_id], backref='kardex_destino_entries')
    cliente = db.relationship('Clientes', backref='kardex_entries')

class Venta(db.Model):
    __tablename__ = 'ventas'
    id = db.Column(db.Integer, primary_key=True)
    idcliente = db.Column(db.Integer, nullable=False)
    factura = db.Column(db.String(50), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'))
    nombre_producto = db.Column(db.String(100))
    cantidad = db.Column(db.Integer, nullable=False)
    fecha_venta = db.Column(db.DateTime, nullable=False)
    bodega_id = db.Column(db.Integer, db.ForeignKey('bodegas.id'), nullable=False)
    precio_unitario = db.Column(db.Float, nullable=True)

    producto = db.relationship('Producto', backref='ventas')
    bodega = db.relationship('Bodega', backref='ventas')

class EstadoInventario(db.Model):
    __tablename__ = 'estado_inventario'
    id = db.Column(db.Integer, primary_key=True)
    idcliente = db.Column(db.Integer, nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    bodega_id = db.Column(db.Integer, db.ForeignKey('bodegas.id'), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False, default=0)
    ultima_actualizacion = db.Column(db.DateTime, nullable=False)
    costo_unitario = db.Column(db.Numeric(15, 2), default=0.00)
    costo_total = db.Column(db.Numeric(15, 2), default=0.00)

    producto = db.relationship('Producto', backref='estado_inventario')
    bodega = db.relationship('Bodega', backref='estado_inventario')

class AjusteInventarioDetalle(db.Model):
    __tablename__ = 'ajuste_inventario_detalle'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    idcliente = db.Column(db.Integer, db.ForeignKey('clientes.idcliente'), nullable=False)
    consecutivo = db.Column(db.String(20), nullable=False, index=True)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    producto_nombre = db.Column(db.String(255), nullable=False)
    bodega_id = db.Column(db.Integer, db.ForeignKey('bodegas.id'), nullable=False)
    bodega_nombre = db.Column(db.String(255), nullable=False)
    cantidad_anterior = db.Column(db.Integer, nullable=False)
    tipo_movimiento = db.Column(db.String(20), nullable=False)
    cantidad_ajustada = db.Column(db.Integer, nullable=False)
    cantidad_final = db.Column(db.Integer, nullable=False)
    fecha = db.Column(db.DateTime, nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    costo_unitario = db.Column(db.Numeric(15, 2), default=0.00)
    costo_total = db.Column(db.Numeric(15, 2), default=0.00)

    producto = db.relationship('Producto', backref='ajustes')
    bodega = db.relationship('Bodega', backref='ajustes')
    usuario = db.relationship('Usuarios', backref='ajustes')
    cliente = db.relationship('Clientes', backref='ajustes')

    def __repr__(self):
        return f"<AjusteInventarioDetalle {self.consecutivo} - {self.producto_nombre}>"

class OrdenProduccion(db.Model):
    __tablename__ = 'ordenes_produccion'
    id = db.Column(db.Integer, primary_key=True)
    idcliente = db.Column(db.Integer, db.ForeignKey('clientes.idcliente'), nullable=False)
    producto_compuesto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    cantidad_paquetes = db.Column(db.Integer, nullable=False)
    peso_total = db.Column(db.Numeric(10, 2))
    estado = db.Column(db.String(50), nullable=False, default='Pendiente')
    bodega_produccion_id = db.Column(db.Integer, db.ForeignKey('bodegas.id'), nullable=False)
    fecha_creacion = db.Column(db.DateTime, nullable=False, default=db.func.now())
    fecha_inicio = db.Column(db.DateTime)
    fecha_finalizacion = db.Column(db.DateTime)
    fecha_lista_para_produccion = db.Column(db.DateTime)
    creado_por = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    numero_orden = db.Column(db.String(20), unique=True, nullable=False)
    en_produccion_por = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    comentario_cierre_forzado = db.Column(db.Text)
    costo_unitario = db.Column(db.Double, nullable=True)
    costo_total = db.Column(db.Double, nullable=True)

    producto_compuesto = db.relationship('Producto', backref='ordenes_produccion')
    bodega_produccion = db.relationship('Bodega', backref='ordenes_produccion')
    creado_por_usuario = db.relationship('Usuarios', foreign_keys=[creado_por], backref='ordenes_creadas')
    en_produccion_usuario = db.relationship('Usuarios', foreign_keys=[en_produccion_por], backref='ordenes_en_produccion')
    cliente = db.relationship('Clientes', backref='ordenes_produccion')

    def __repr__(self):
        return f"<OrdenProduccion(id={self.id}, estado='{self.estado}', numero_orden='{self.numero_orden}')>"

class DetalleProduccion(db.Model):
    __tablename__ = 'detalle_produccion'
    id = db.Column(db.Integer, primary_key=True)
    idcliente = db.Column(db.Integer, db.ForeignKey('clientes.idcliente'), nullable=False)
    orden_produccion_id = db.Column(db.Integer, db.ForeignKey('ordenes_produccion.id'), nullable=False)
    producto_base_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    cantidad_consumida = db.Column(db.Integer, nullable=False)
    cantidad_producida = db.Column(db.Integer, nullable=False)
    bodega_destino_id = db.Column(db.Integer, db.ForeignKey('bodegas.id'), nullable=False)
    fecha_registro = db.Column(db.DateTime, nullable=False, default=db.func.now())

    orden_produccion = db.relationship('OrdenProduccion', backref='detalle_produccion')
    producto_base = db.relationship('Producto', backref='detalle_produccion')
    bodega_destino = db.relationship('Bodega', backref='detalle_produccion')
    cliente = db.relationship('Clientes', backref='detalle_produccion')

    def __repr__(self):
        return f"<DetalleProduccion(id={self.id}, orden_produccion_id={self.orden_produccion_id})>"
    

# En models.py
class EntregaParcial(db.Model):
    __tablename__ = 'entregas_parciales'
    id = db.Column(db.Integer, primary_key=True)
    idcliente = db.Column(db.Integer, db.ForeignKey('clientes.idcliente'), nullable=False)
    orden_produccion_id = db.Column(db.Integer, db.ForeignKey('ordenes_produccion.id'), nullable=False)
    cantidad_entregada = db.Column(db.Numeric(15, 3), nullable=False)
    fecha_entrega = db.Column(db.DateTime, nullable=False, default=db.func.now())
    comentario = db.Column(db.Text, nullable=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)  # Nuevo campo

    orden = db.relationship('OrdenProduccion', backref=db.backref('entregas_parciales', lazy='dynamic'))
    cliente = db.relationship('Clientes', backref='entregas_parciales')
    usuario = db.relationship('Usuarios', backref='entregas_parciales')  # Relación con la tabla usuarios

    def __repr__(self):
        return (
            f"<EntregaParcial(id={self.id}, orden_produccion_id={self.orden_produccion_id}, "
            f"cantidad_entregada={self.cantidad_entregada}, fecha_entrega={self.fecha_entrega})>"
        )