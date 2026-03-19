# tests/test_fase4.py
import unittest
from unittest.mock import MagicMock
import sys

# ¡MOCK de MongoDB! Parcheamos pymongo ANTES de importar los adaptadores 
# para que no intente conectarse a localhost:27017 y lance TimeoutError.
class DummyClient:
    class Admin:
        def command(self, cmd): return True
    admin = Admin()
    def __getitem__(self, item):
        class DummyCollection:
            def create_index(self, *args, **kwargs): pass
        class DummyDB:
            def __getattr__(self, name): return DummyCollection()
            def __getitem__(self, name): return DummyCollection()
        return DummyDB()

import pymongo
pymongo.MongoClient = lambda *args, **kwargs: DummyClient()

# Importar adaptadores 
from infrastructure.adapters.mongodb_repository import MongoUsuarioRepository, MongoTransaccionRepository

# Importar entrypoints para asegurar que no hay errores de sintaxis o importación
from infrastructure.entrypoints.api_rest import bp as api_rest_bp
from infrastructure.entrypoints.graphql_resolvers import Query as GraphQLQuery

# Nota: Para probar el CLI de Click se requeriría el 'CliRunner', 
# pero probaremos las importaciones arquitectónicas aquí.
import infrastructure.entrypoints.cli as cli

class TestFase4(unittest.TestCase):
    def test_repositorios_instanciables(self):
        """
        Verifica que los repositorios de MongoDB de la Fase 4
        se instancien correctamente sin acoplamiento a la conexión global.
        """
        mock_collection = MagicMock()
        repo_usuarios = MongoUsuarioRepository(collection=mock_collection)
        repo_transacciones = MongoTransaccionRepository(collection=mock_collection)
        
        self.assertIsNotNone(repo_usuarios)
        self.assertIsNotNone(repo_transacciones)

    def test_api_rest_blueprint(self):
        """
        Verifica que el entrypoint REST se configuró como Blueprint
        y tiene un prefijo de /api. Validamos estructuralmente.
        """
        self.assertIsNotNone(api_rest_bp)
        self.assertEqual(api_rest_bp.name, 'api_rest')
        self.assertEqual(api_rest_bp.url_prefix, '/api')

    def test_graphql_query_class(self):
        """
        Verifica que GraphQL expone los resolvers re-escritos 
        donde instancian repositorios localmente.
        """
        self.assertTrue(hasattr(GraphQLQuery, 'resolve_mi_perfil'))
        self.assertTrue(hasattr(GraphQLQuery, 'resolve_buscar_usuario'))
        self.assertTrue(hasattr(GraphQLQuery, 'resolve_mis_movimientos'))
        self.assertTrue(hasattr(GraphQLQuery, 'resolve_mis_estadisticas'))
        self.assertTrue(hasattr(GraphQLQuery, 'resolve_ultimas_transacciones'))

    def test_cli_commands(self):
        """
        Verifica que la CLI configurada con Click carga el grupo 
        y expone los dos comandos solicitados en la Fase 4.
        """
        comandos_registrados = cli.nequiz.commands.keys()
        self.assertIn('transferir', comandos_registrados)
        self.assertIn('historial', comandos_registrados)


if __name__ == '__main__':
    unittest.main()
