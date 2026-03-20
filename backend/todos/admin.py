from django.contrib import admin
from .models import Todo


@admin.register(Todo)
class TodoAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'scheduled_date', 'priority', 'status', 'source', 'is_overdue']
    search_fields = ['user__email', 'title']
    list_filter = ['status', 'priority', 'source', 'scheduled_date']
    readonly_fields = ['created_at', 'updated_at', 'is_overdue', 'days_overdue']
    date_hierarchy = 'scheduled_date'
