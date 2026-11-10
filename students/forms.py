from django import forms

from .models import Student


class StudentSearchForm(forms.Form):
    year = forms.ChoiceField(
        label='Admission year',
        required=True,
        choices=(),
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    department = forms.ChoiceField(
        label='Department',
        required=True,
        choices=(),
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    roll_number = forms.CharField(
        label='Roll number',
        required=True,
        max_length=20,
        strip=True,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'autocomplete': 'off',
                'placeholder': 'Enter roll number',
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        years = Student.objects.values_list('batch_year', flat=True).distinct().order_by('-batch_year')
        departments = Student.objects.values_list('department', flat=True).distinct().order_by('department')
        self.fields['year'].choices = [('', 'Select admission year')] + [
            (str(year), str(year)) for year in years
        ]
        self.fields['department'].choices = [('', 'Select department')] + [
            (department, department) for department in departments
        ]