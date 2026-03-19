# infrastructure/adapters/secondary/mongodb/usuario_repository.py
# Adaptador secundario: implementa el puerto UsuarioRepository usando MongoDB

from datetime import datetime
from typing import Optional

from domain.entities.usuario import Usuario, PerfilUsuario
from domain.ports.repositories.usuario_repository import UsuarioRepository
from infrastructure.adapters.secondary.mongodb.connection import usuarios_col


class MongoUsuarioRepository(UsuarioRepository):
    """
    Implementación concreta del puerto UsuarioRepository sobre MongoDB.
    Solo este archivo conoce el esquema de documentos Mongo.
    """

    # ── Mapeo dominio → documento ──────────────────────────────────────

    @staticmethod
    def _a_documento(usuario: Usuario) -> dict:
        return {
            'numeroTelefono': usuario.numero_telefono,
            'nombre': usuario.nombre,
            'email': usuario.email,
            'passwordHash': usuario.password_hash,
            'saldo': usuario.saldo,
            'fechaRegistro': usuario.fecha_registro,
            'activo': usuario.activo,
            'perfil': {
                'foto': usuario.perfil.foto,
                'biografia': usuario.perfil.biografia,
            },
        }

    # ── Mapeo documento → dominio ──────────────────────────────────────

    @staticmethod
    def _a_entidad(doc: dict) -> Usuario:
        perfil_doc = doc.get('perfil', {})
        return Usuario(
            numero_telefono=doc['numeroTelefono'],
            nombre=doc['nombre'],
            email=doc['email'],
            password_hash=doc['passwordHash'],
            saldo=doc['saldo'],
            fecha_registro=doc.get('fechaRegistro', datetime.utcnow()),
            activo=doc.get('activo', True),
            perfil=PerfilUsuario(
                foto=perfil_doc.get('foto'),
                biografia=perfil_doc.get('biografia', ''),
            ),
        )

    # ── Implementación del puerto ──────────────────────────────────────

    def guardar(self, usuario: Usuario) -> None:
        usuarios_col.insert_one(self._a_documento(usuario))

    def actualizar(self, usuario: Usuario) -> None:
        doc = self._a_documento(usuario)
        doc.pop('numeroTelefono', None)  # No actualizar la clave primaria
        usuarios_col.update_one(
            {'numeroTelefono': usuario.numero_telefono},
            {'$set': doc},
        )

    def buscar_por_telefono(self, numero_telefono: str) -> Optional[Usuario]:
        doc = usuarios_col.find_one({'numeroTelefono': numero_telefono})
        return self._a_entidad(doc) if doc else None

    def buscar_por_email(self, email: str) -> Optional[Usuario]:
        doc = usuarios_col.find_one({'email': email})
        return self._a_entidad(doc) if doc else None

    def existe_telefono(self, numero_telefono: str) -> bool:
        return usuarios_col.find_one(
            {'numeroTelefono': numero_telefono}, {'_id': 1}
        ) is not None

    def existe_email(self, email: str) -> bool:
        return usuarios_col.find_one({'email': email}, {'_id': 1}) is not None
