from decimal import Decimal
import random

from django.core.management.base import BaseCommand
from django.utils import timezone

from usuarios.models import Usuario, Cliente, Rol
from pedidos.models import (
    Departamento,
    Ciudad,
    Direccion,
    EstadoPedido,
    Pedido,
    DetallePedido,
    HistorialEstadoPedido,
)
from catalogo.models import Categoria, Producto, ImagenProducto


class Command(BaseCommand):
    help = 'Seed demo data for usuarios and pedidos without external dependencies.'

    def add_arguments(self, parser):
        parser.add_argument('--users', type=int, default=10, help='Number of users to create')
        parser.add_argument('--orders', type=int, default=30, help='Number of orders to create')
        parser.add_argument('--seed', type=int, default=42, help='Random seed')

    def handle(self, *args, **options):
        random.seed(options['seed'])
        num_users = options['users']
        num_orders = options['orders']

        admin_role, _ = Rol.objects.get_or_create(nombre=Rol.ADMIN)
        client_role, _ = Rol.objects.get_or_create(nombre=Rol.CLIENTE)

        estados = [
            EstadoPedido.PENDIENTE,
            EstadoPedido.PREPARADO,
            EstadoPedido.ENVIADO,
        ]
        for nombre in estados:
            EstadoPedido.objects.get_or_create(nombre=nombre)

        categoria, _ = Categoria.objects.get_or_create(
            nombre='Persianas',
            defaults={'descripcion': 'Categoria demo', 'activo': True},
        )

        productos = []
        if Producto.objects.count() == 0:
            for i in range(1, 6):
                prod = Producto.objects.create(
                    nombre=f'Persiana Demo {i}',
                    descripcion='Producto de prueba',
                    precio_m2=Decimal('25000.00') + (i * 1000),
                    categoria=categoria,
                    activo=True,
                )
                ImagenProducto.objects.create(
                    producto=prod,
                    url='https://via.placeholder.com/300x200.png?text=Producto',
                    es_principal=True,
                    orden=0,
                )
                productos.append(prod)
        else:
            productos = list(Producto.objects.all()[:5])

        departamentos = ['Cundinamarca', 'Antioquia', 'Valle']
        ciudades_map = {
            'Cundinamarca': ['Bogota', 'Soacha'],
            'Antioquia': ['Medellin', 'Bello'],
            'Valle': ['Cali', 'Palmira'],
        }
        dept_objs = {}
        city_objs = []
        for dep in departamentos:
            d, _ = Departamento.objects.get_or_create(nombre=dep)
            dept_objs[dep] = d
            for c in ciudades_map[dep]:
                city, _ = Ciudad.objects.get_or_create(nombre=c, departamento=d)
                city_objs.append(city)

        nombres = [
            'Carlos Rojas',
            'Daniela Pardo',
            'Miguel Torres',
            'Laura Cardenas',
            'Sofia Medina',
            'Andres Vega',
            'Paula Ortiz',
            'Jorge Salazar',
            'Valeria Castro',
            'Juan Lozano',
        ]

        usuarios = []
        clientes = []
        for i in range(num_users):
            nombre = nombres[i % len(nombres)]
            email = f'user{i+1}@demo.com'
            is_admin = i == 0
            rol = admin_role if is_admin else client_role

            user, created = Usuario.objects.get_or_create(
                email=email,
                defaults={
                    'nombre': nombre,
                    'rol': rol,
                    'activo': True,
                    'is_staff': is_admin,
                    'proveedor_auth': 'local',
                },
            )
            if created:
                user.set_password('Demo12345')
                user.save(update_fields=['password'])
            usuarios.append(user)

            if not is_admin:
                cliente, _ = Cliente.objects.get_or_create(usuario=user)
                clientes.append(cliente)

        if not clientes:
            self.stdout.write(self.style.WARNING('No client users available for orders.'))
            return

        direcciones = []
        for c in clientes:
            city = random.choice(city_objs)
            direccion, _ = Direccion.objects.get_or_create(
                cliente=c,
                ciudad=city,
                calle='Calle 10',
                numero=str(random.randint(1, 200)),
                defaults={
                    'barrio': 'Centro',
                    'complemento': '',
                    'es_principal': True,
                },
            )
            direcciones.append(direccion)

        estado_objs = list(EstadoPedido.objects.all())
        admin_user = usuarios[0]

        created_orders = 0
        for _ in range(num_orders):
            cliente = random.choice(clientes)
            direccion = random.choice([d for d in direcciones if d.cliente_id == cliente.cliente_id] or direcciones)
            estado = random.choice(estado_objs)

            pedido = Pedido.objects.create(
                cliente=cliente,
                direccion=direccion,
                estado=estado,
                total=Decimal('0.00'),
                referencia_pago='',
                notas='Pedido demo',
            )

            num_items = random.randint(1, 3)
            total = Decimal('0.00')
            for _ in range(num_items):
                prod = random.choice(productos)
                ancho = Decimal(random.choice([80, 100, 120, 140]))
                alto = Decimal(random.choice([120, 150, 180, 200]))
                area = (ancho * alto) / Decimal('10000')
                precio_m2 = Decimal(prod.precio_m2)
                precio_total = (area * precio_m2).quantize(Decimal('0.01'))
                total += precio_total
                DetallePedido.objects.create(
                    pedido=pedido,
                    producto=prod,
                    cantidad=1,
                    ancho_cm=ancho,
                    alto_cm=alto,
                    area_m2=area,
                    precio_m2=precio_m2,
                    precio_total=precio_total,
                )

            pedido.total = total
            pedido.save(update_fields=['total'])

            HistorialEstadoPedido.objects.create(
                pedido=pedido,
                estado=estado,
                cambiado_por=admin_user,
                notas_cambio='Creado por seed',
            )

            created_orders += 1

        self.stdout.write(self.style.SUCCESS(
            f'Seed complete: usuarios={len(usuarios)}, clientes={len(clientes)}, pedidos={created_orders}'
        ))
