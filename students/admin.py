
from django.contrib import admin
from .models import Student


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):

    list_display = (
        'student_name',
        'roll_number',
        'batch_year',
        'department',
        'status',
    )

    list_filter = (
        'batch_year',
        'department',
        'status',
    )

    search_fields = (
        'student_name',
        'roll_number',
    )

    ordering = ('batch_year', 'roll_number')

    def has_module_permission(self, request):
        return request.user.is_staff

    def has_view_permission(self, request, obj=None):
        return request.user.is_staff

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
