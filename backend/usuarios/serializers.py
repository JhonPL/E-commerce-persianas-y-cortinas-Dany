from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .models import Usuario, Cliente


class RegistroSerializer(serializers.ModelSerializer):
    password          = serializers.CharField(write_only=True, min_length=8)
    password_confirmar = serializers.CharField(write_only=True)

    class Meta:
        model  = Usuario
        fields = ['nombre', 'email', 'password', 'password_confirmar']

    def validate_email(self, value):
        if Usuario.objects.filter(email=value.lower()).exists():
            raise serializers.ValidationError("Ya existe una cuenta con este email.")
        return value.lower()

    def validate(self, data):
        if data['password'] != data['password_confirmar']:
            raise serializers.ValidationError({"password_confirmar": "Las contraseñas no coinciden."})
        return data

    def create(self, validated_data):
        validated_data.pop('password_confirmar')
        user = Usuario.objects.create_user(**validated_data)
        Cliente.objects.create(usuario=user)
        return user


class LoginSerializer(serializers.Serializer):
    email    = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(
            request  = self.context.get('request'),
            username = data['email'],
            password = data['password'],
        )
        if not user:
            raise serializers.ValidationError("Email o contraseña incorrectos.")
        if not user.activo:
            raise serializers.ValidationError("Esta cuenta está desactivada.")
        refresh = RefreshToken.for_user(user)
        return {
            'usuario': UsuarioSerializer(user).data,
            'access':  str(refresh.access_token),
            'refresh': str(refresh),
        }


class UsuarioSerializer(serializers.ModelSerializer):
    rol_nombre = serializers.CharField(source='rol.nombre', read_only=True)

    class Meta:
        model  = Usuario
        fields = ['usuario_id', 'nombre', 'email', 'rol_nombre',
                  'activo', 'fecha_registro', 'proveedor_auth']
        read_only_fields = fields


class ClienteSerializer(serializers.ModelSerializer):
    usuario = UsuarioSerializer(read_only=True)

    class Meta:
        model  = Cliente
        fields = ['cliente_id', 'usuario', 'telefono',
                  'documento_tipo', 'documento_numero']


class ActualizarClienteSerializer(serializers.ModelSerializer):
    nombre = serializers.CharField(source='usuario.nombre', required=False)

    class Meta:
        model  = Cliente
        fields = ['nombre', 'telefono', 'documento_tipo', 'documento_numero']

    def update(self, instance, validated_data):
        usuario_data = validated_data.pop('usuario', {})
        if 'nombre' in usuario_data:
            instance.usuario.nombre = usuario_data['nombre']
            instance.usuario.save()
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance