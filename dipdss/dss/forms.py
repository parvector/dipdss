from django.forms import ModelForm
from dss.models import *
from django import forms
from django.contrib.auth.models import User



class CreateTaskForm(forms.ModelForm):
    class Meta:
       model = TaskModel
       fields = ["task_name","problem_fk", "fgs_fk", "nsga3_fk", "unsga3_fk", "is_hv", ]

    def __init__(self, *args, **kwargs):
       user = kwargs.pop('user')
       super(CreateTaskForm, self).__init__(*args, **kwargs)
       self.fields['problem_fk'].queryset = ProblemModel.objects.filter(user_fk=user, isused=False)

       self.fields['fgs_fk'].widget = forms.CheckboxSelectMultiple()
       self.fields['fgs_fk'].queryset = FGModel.objects.filter(user_fk=user, isused=False)

       self.fields['nsga3_fk'].widget = forms.CheckboxSelectMultiple()
       self.fields['nsga3_fk'].queryset = NSGA3Model.objects.filter(user_fk=user, isused=False)

       self.fields['unsga3_fk'].widget = forms.CheckboxSelectMultiple()
       self.fields['unsga3_fk'].queryset = UNSGA3Model.objects.filter(user_fk=user, isused=False)



class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["email", "first_name", "last_name"]

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user")
        super(ProfileUpdateForm, self).__init__(*args, **kwargs)
        self.fields["email"] = forms.EmailField(initial=user.email, required=False)
        self.fields["first_name"] = forms.CharField(max_length=150, initial=user.first_name, required=False)
        self.fields["last_name"] = forms.CharField(max_length=150, initial=user.last_name, required=False)
        self.fields["password_old"] = forms.CharField(max_length=32, widget=forms.PasswordInput, required=False, label="Old password") 
        self.fields["password_new"] = forms.CharField(max_length=32, widget=forms.PasswordInput, required=False, label="New password") 