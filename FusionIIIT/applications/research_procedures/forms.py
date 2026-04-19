from django import forms
from .models import ResearchGroup
from django.contrib.auth.models import User
from applications.research_procedures.api.services import ResearchGroupService


class ResearchGroupForm(forms.ModelForm):
    """
    Form for creating and updating research groups.
    Uses service layer for M2M operations.
    """
    students = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'ui fluid search dropdown'})
    )
    faculty = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'ui fluid search dropdown'})
    )

    def __init__(self, *args, **kwargs):
        if kwargs.get('instance'):
            initial = kwargs.setdefault('initial', {})
            initial['students'] = [
                t.pk for t in kwargs['instance'].students_under_group.all()
            ]
            initial['faculty'] = [
                t.pk for t in kwargs['instance'].faculty_under_group.all()
            ]

        forms.ModelForm.__init__(self, *args, **kwargs)

    def save(self, commit=True):
        """
        Save the form using the service layer for M2M operations.
        """
        instance = forms.ModelForm.save(self, False)

        if commit:
            instance.save()
            # Use service to handle M2M relationships
            ResearchGroupService.update_research_group_members(
                instance,
                self.cleaned_data['faculty'],
                self.cleaned_data['students']
            )
        else:
            # If not committing, prepare for later M2M save
            old_save_m2m = self.save_m2m

            def save_m2m():
                old_save_m2m()
                ResearchGroupService.update_research_group_members(
                    instance,
                    self.cleaned_data['faculty'],
                    self.cleaned_data['students']
                )

            self.save_m2m = save_m2m

        return instance

    class Meta:
        model = ResearchGroup
        fields = ('name', 'students', 'faculty', 'description',)
