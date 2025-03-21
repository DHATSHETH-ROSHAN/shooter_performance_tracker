from django import forms
from .models import DayPlanner, UserProfiles, Event

class DayPlannerForm(forms.ModelForm):
    class Meta:
        model = DayPlanner
        fields = ['shooter', 'date', 'time', 'activity', 'shared_with_shooter']
        widgets = {
            'shooter': forms.Select(attrs={'id': 'id_shooter', 'class': 'form-control'}),
            'date': forms.DateInput(attrs={'id': 'id_date', 'type': 'date', 'class': 'form-control'}),
            'time': forms.TimeInput(attrs={'id': 'id_time', 'type': 'time', 'class': 'form-control'}),
            'activity': forms.TextInput(attrs={'id': 'id_activity', 'class': 'form-control'}),
            'shared_with_shooter': forms.CheckboxInput(attrs={'id': 'id_shared_with_shooter', 'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        self.coach = kwargs.pop('coach', None)  # Extract 'coach' before calling super()
        super(DayPlannerForm, self).__init__(*args, **kwargs)

        # If a coach is provided, filter the shooter queryset
        if self.coach:
            self.fields['shooter'].queryset = UserProfiles.objects.filter(coach=self.coach)


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['title', 'date', 'location', 'description', 'visibility', 'assigned_shooters']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'visibility': forms.Select(attrs={'class': 'form-control'}),
            'assigned_shooters': forms.SelectMultiple(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super(EventForm, self).__init__(*args, **kwargs)
        self.fields['assigned_shooters'].queryset = UserProfiles.objects.all()
        for field_name, field in self.fields.items():
            field.widget.attrs['style'] = "background-color: #050505; color: #00DDFF; border: 1px solid #00DDFF; padding: 8px; border-radius: 5px;"

