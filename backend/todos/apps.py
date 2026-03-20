from django.apps import AppConfig


class TodosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'todos'

    def ready(self):
        """
        Import signals when Django starts
        This ensures our post_save signal for automatic reminder_time calculation is registered
        """
        import todos.signals  # noqa
