from django.apps import AppConfig

class KnowledgeGraphConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.knowledge_graph'
    verbose_name = '知识图谱'

    def ready(self):
        import apps.knowledge_graph.signals
