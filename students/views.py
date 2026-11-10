
from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
from django.shortcuts import render

from .forms import StudentSearchForm
from .models import Student


@login_required
def student_search(request):
    student = None
    searched = any(field in request.GET for field in ('year', 'department', 'roll_number'))
    form = StudentSearchForm(request.GET or None)

    if searched and form.is_valid():
        student = Student.objects.filter(
            batch_year=form.cleaned_data['year'],
            department=form.cleaned_data['department'],
            roll_number=form.cleaned_data['roll_number'],
            status='Active',
        ).first()

    student_card_url = None
    if student and student.student_card and default_storage.exists(student.student_card.name):
        student_card_url = student.student_card.url

    context = {
        'student': student,
        'searched': searched,
        'form': form,
        'student_card_url': student_card_url,
    }

    return render(request, 'students/search.html', context)
