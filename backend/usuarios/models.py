from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class Rol(models.Model):
    ADMIN   = 'admin'
    CLIENTE = 'cliente'
    CHOICES = [(ADMIN, 'Admin'), (CLIENTE, 'Cliente')]

    rol_id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=50, choices=CHOICES, unique=True)

    class Meta:
        db_table = 'roles'

    def __str__(self):
        return self.nombre


class UsuarioManager(BaseUserManager):
    def create_user(self, email, nombre, password=None, **extra):
        if not email:
            raise ValueError('El email es obligatorio')
        user = self.model(email=self.normalize_email(email), nombre=nombre, **extra)
        if password:
            user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, nombre, password, **extra):
        rol, _ = Rol.objects.get_or_create(nombre=Rol.ADMIN)
        extra.setdefault('rol', rol)
        extra.setdefault('is_staff', True)
        extra.setdefault('is_superuser', True)
        return self.create_user(email, nombre, password, **extra)


class Usuario(AbstractBaseUser, PermissionsMixin):
    PROVEEDOR_CHOICES = [
        ('local',     'Local'),
        ('google',    'Google'),
        ('microsoft', 'Microsoft'),
    ]

    usuario_id     = models.AutoField(primary_key=True)
    nombre         = models.CharField(max_length=100)
    email          = models.EmailField(max_length=150, unique=True)
    proveedor_auth = models.CharField(max_length=20, choices=PROVEEDOR_CHOICES, default='local')
    proveedor_id   = models.CharField(max_length=255, null=True, blank=True)
    rol            = models.ForeignKey(Rol, on_delete=models.PROTECT, default=2)
    activo         = models.BooleanField(default=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    is_staff       = models.BooleanField(default=False)

    objects = UsuarioManager()

    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = ['nombre']

    class Meta:
        db_table = 'usuarios'

    def __str__(self):
        return self.email


class Cliente(models.Model):
    DOC_CHOICES = [('CC','CC'),('NIT','NIT'),('CE','CE'),('pasaporte','Pasaporte')]

    cliente_id       = models.AutoField(primary_key=True)
    usuario          = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name='cliente')
    telefono         = models.CharField(max_length=20, null=True, blank=True)
    documento_tipo   = models.CharField(max_length=20, choices=DOC_CHOICES, null=True, blank=True)
    documento_numero = models.CharField(max_length=30, null=True, blank=True)

    class Meta:
        db_table = 'clientes'

    def __str__(self):
        return f"Cliente: {self.usuario.email}"