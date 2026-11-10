
from django.contrib import admin
from django import forms
from .models import Student


class StudentAdminForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.fields['card_expiry_date'].required = True


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):

    form = StudentAdminForm

    list_display = (
        'student_name',
        'roll_number',
        'batch_year',
        'department',
        'status',
        'current_verification_status',
        'card_expiry_date',
    )

    list_filter = (
        'batch_year',
        'department',
        'status',
        'card_expiry_date',
    )

    search_fields = (
        'student_name',
        'roll_number',
        'department',
    )

    ordering = ('batch_year', 'roll_number')

    @admin.display(description='Current status', ordering='status')
    def current_verification_status(self, obj):
        return obj.effective_status()

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
