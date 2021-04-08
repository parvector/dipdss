from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from dipdss import settings
from enum import Enum
import django

# Create your models here.

def vals_have_same_dim(value):
    values = value.split("],[")
    if len(values) == 1 and values[0][0] != "[" and values[0][-1:] != "]":
        raise ValidationError(message="The string %(value)s does not contain closing parentheses.", params={"value":value})
    elif len(values) == 1:
        values[0] = values[0][1:-1]
    elif len(values) > 1:
        values[0] = values[0][1:]
        values[-1] = values[-1][0:-1]
        first_val_dim = len(values[0].split(","))
        for value in values[1:]:
            if len(value.split(",")) != first_val_dim:
                raise ValidationError(message="The dimension %(error_value)s differs from the dimension of the first value [%(first_val)s].", params={"first_val":values[0], "error_value":value})

def is_positive_int_or_None(value):
    if not value.isdigit() and value != "None":
        raise ValidationError(message="The value must be a positive number or None. %(value)s is not a positive number or None.", params={"value":value})

class NSGA3Model(models.Model):
    user_fk = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    alg_name = models.CharField(max_length=64, default="", blank=False)
    ref_dirs = models.TextField(validators=[vals_have_same_dim], help_text="input format:[x,y,...,z],[x,y,...,z],...,[x,y,...,z]. Float format:1.2", null=True, blank=True)
    auto_ref_dirs_method = models.CharField(max_length=11,choices=[("None","None"),("das-dennis","das-dennis"),("energy","energy")], default="None", blank=True)
    auto_ref_dirs_dimensions = models.PositiveIntegerField(null=True, blank=True)
    auto_ref_dirs_npartitions = models.PositiveIntegerField(null=True, blank=True)
    pop_size = models.PositiveIntegerField(default=10)
    eliminate_duplicates = models.BooleanField(default=True)
    n_offsprings = models.CharField(max_length=16, null=10, validators=[is_positive_int_or_None], default="None", blank=True)
    n_gen = models.PositiveIntegerField(default=10)
    isused = models.BooleanField(default=False)

    def __str__(self):
        return self.alg_name

class UNSGA3Model(models.Model):
    user_fk = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    alg_name = models.CharField(max_length=64, default="", blank=False)
    ref_dirs = models.TextField(validators=[vals_have_same_dim], help_text="input format:[x,y,...,z],[x,y,...,z],...,[x,y,...,z]. Float format:1.2", null=True, blank=True)
    auto_ref_dirs_method = models.CharField(max_length=11,choices=[("None","None"),("das-dennis","das-dennis"),("energy","energy")], default="None", blank=True)
    auto_ref_dirs_dimensions = models.PositiveIntegerField(null=True, blank=True)
    auto_ref_dirs_npartitions = models.PositiveIntegerField(null=True, blank=True)
    pop_size = models.PositiveIntegerField(default=10)
    eliminate_duplicates = models.BooleanField(default=True)
    n_offsprings = models.CharField(max_length=16, null=10, validators=[is_positive_int_or_None], blank=True)
    n_gen = models.PositiveIntegerField(default=10)
    isused = models.BooleanField(default=False)

    def __str__(self):
        return self.alg_name

class ProblemModel(models.Model):
    user_fk = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    problem_name = models.CharField(max_length=64)
    nvar = models.PositiveIntegerField()
    nobj = models.PositiveIntegerField()
    ncostr = models.PositiveIntegerField()
    xl = models.TextField(validators=[vals_have_same_dim], help_text="input format:[x,y,...,z],[x,y,...,z],...,[x,y,...,z]. Float format:1.2", null=True)
    xu = models.TextField(validators=[vals_have_same_dim], help_text="input format:[x,y,...,z],[x,y,...,z],...,[x,y,...,z]. Float format:1.2", null=True)
    nsga3_fk = models.ForeignKey(NSGA3Model, on_delete=models.CASCADE, null=True, blank=True)
    unsga3_fk = models.ForeignKey(UNSGA3Model, on_delete=models.CASCADE, null=True, blank=True)
    isused = models.BooleanField(default=False)


    def __str__(self):
        return self.problem_name

class FGModel(models.Model):
    user_fk = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    problem_fk = models.ManyToManyField(ProblemModel, blank=True)
    fg_name = models.CharField(max_length=64, default="")
    f = models.TextField()
    g = models.TextField()
    isused = models.BooleanField(default=False)

    def __str__(self):
        return self.fg_name

class StatusEnum(Enum):
    READY = "Ready"
    LAUNCHED = "Launched"
    ERROR = "Error"
    SUCCES = "Succes"

class TaskModel(models.Model):
    user_fk = models.ForeignKey(User, on_delete=models.CASCADE)
    task_name = models.CharField(max_length=64, default="")
    problem_fk = models.ForeignKey(ProblemModel, on_delete=models.SET_NULL, null=True)
    fgs_fk = models.ManyToManyField(FGModel)
    nsga3_fk = models.ManyToManyField(NSGA3Model, blank=True)
    unsga3_fk = models.ManyToManyField(UNSGA3Model, blank=True)
    error_result = models.TextField(blank=True)
    status = models.CharField(max_length=11, 
                            choices = [(StatusEnum.READY.value,StatusEnum.READY.value),
                                        (StatusEnum.LAUNCHED.value,StatusEnum.LAUNCHED.value),
                                        (StatusEnum.ERROR.value,StatusEnum.ERROR.value),
                                        (StatusEnum.SUCCES.value,StatusEnum.SUCCES.value)],
                            default=StatusEnum.READY.value)
    start_time = models.DateTimeField(default=django.utils.timezone.now)
    end_time = models.DateTimeField(default=django.utils.timezone.now, blank=True)
    is_hv = models.BooleanField(default=False)


    def __str__(self):
        return self.task_name



class ResultModel(models.Model):
    task_fk = models.ForeignKey(TaskModel, on_delete=models.CASCADE)
    problem_fk = models.ForeignKey(ProblemModel, on_delete=models.CASCADE)
    nsga3_fk = models.ForeignKey(NSGA3Model, on_delete=models.CASCADE, blank=True, null=True)
    unsga3_fk = models.ForeignKey(UNSGA3Model, on_delete=models.CASCADE, blank=True, null=True)
    result_x = models.TextField(blank=True)
    result_f = models.TextField(blank=True)
    result_g = models.TextField(blank=True)
    hv = models.FloatField(blank=True, null=True)

    class Meta:
        unique_together = ["task_fk", "nsga3_fk", "unsga3_fk", "problem_fk"]