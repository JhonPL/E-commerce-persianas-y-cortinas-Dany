from decimal import Decimal

from django.core.management.base import BaseCommand

from catalogo.models import Categoria, ImagenProducto, Producto


class Command(BaseCommand):
    help = "Create a small demo catalog when the catalog database is empty."

    def handle(self, *args, **options):
        if Producto.objects.exists():
            self.stdout.write(
                self.style.WARNING("Catalog already has products; no demo data added.")
            )
            return

        categoria, _ = Categoria.objects.get_or_create(
            nombre="Persianas",
            defaults={"descripcion": "Categoria demo", "activo": True},
        )
        for index in range(1, 6):
            producto = Producto.objects.create(
                nombre=f"Persiana Demo {index}",
                descripcion="Producto de prueba",
                precio_m2=Decimal("25000.00") + index * 1000,
                categoria=categoria,
                activo=True,
            )
            ImagenProducto.objects.create(
                producto=producto,
                url="https://via.placeholder.com/300x200.png?text=Producto",
                es_principal=True,
                orden=0,
            )

        self.stdout.write(self.style.SUCCESS("Created 5 demo catalog products."))
