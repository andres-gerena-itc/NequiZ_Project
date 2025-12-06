# graphql/schema.py - Schema Principal de GraphQL

import graphene
from graphql_schema.queries import Query

# Crear schema con las queries
schema = graphene.Schema(query=Query)

# Exportar
__all__ = ['schema']