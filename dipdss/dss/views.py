from threading import Thread  
from django.shortcuts import render
from django.views.generic.base import *
from django.views.generic.edit import *
from django.views.generic.detail import DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy
from django.shortcuts import redirect
from dss.forms import *
from django.http import HttpResponse, HttpResponseForbidden
from .task_api import *
from django.contrib.auth.decorators import login_required
import plotly.express as pe
import plotly.graph_objects as go
import plotly
import copy



# Create your views here.

class HomePageView(TemplateView):
    template_name = "dss/home.html"


class ProfileView(LoginRequiredMixin, FormView):
    template_name = "dss/profile.html"
    form_class = ProfileUpdateForm
    success_url = reverse_lazy("profile")

    def form_valid(self, form):
        user = self.request.user
        if self.request.POST.get("email", False):
            user.email = self.request.POST["email"]
        if self.request.POST.get("first_name", False):
            user.first_name = self.request.POST["first_name"]
        if self.request.POST.get("last_name", False):
            user.last_name = self.request.POST["last_name"]
        if self.request.POST.get("password_new", False) and self.request.POST.get("password_old", False):
            if user.check_password(self.request.POST["password_old"]):
                user.set_password( self.request.POST["password_new"] )
                user.save()
        user.save()
        return super().form_valid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs


@login_required(login_url='/accounts/login/')
def create_list(request):
    context = dict()
    if request.method == "POST":
        if request.POST.get("Ready", False) == "Launch" and \
           TaskModel.objects.get(id=int(request.POST["task"])).status == StatusEnum.READY.value:
            task_id = int(request.POST["task"])
            thr = Thread(target=moo_tasks, args=(task_id,))
            thr.start()
        if request.POST.get("change_ready", False) == "Change to Ready":
            task = TaskModel.objects.get(id=int(request.POST["task"]))
            task.status = StatusEnum.READY.value
            task.save()
        if request.POST.get("Delete", False) == "Delete":
            task = TaskModel.objects.get(pk=int(request.POST["task"]))
            for fg in task.fgs_fk.all():
                fg.delete()
            for nsga3 in task.nsga3_fk.all():
                nsga3.delete()
            for unsga3 in task.unsga3_fk.all():
                unsga3.delete()
            task.problem_fk.delete()
            task.delete()
    context["nsga3s"] = NSGA3Model.objects.filter(user_fk=request.user, isused=False)
    context["unsga3s"] = UNSGA3Model.objects.filter(user_fk=request.user, isused=False)
    context["problems"] = ProblemModel.objects.filter(user_fk=request.user, isused=False)
    context["fgs"] = FGModel.objects.filter(user_fk=request.user, isused=False)
    context["tasks"] = TaskModel.objects.filter(user_fk=request.user)
    return render(request, "dss/create_list.html", context)


class SignUpView(CreateView):
    form_class = UserCreationForm
    success_url = reverse_lazy("login")
    template_name = "registration/signup.html"


class CreateNSGA3View(LoginRequiredMixin,CreateView):
    model = NSGA3Model
    fields = ["alg_name", "ref_dirs", "auto_ref_dirs_method", "auto_ref_dirs_dimensions", 
            "auto_ref_dirs_npartitions", "pop_size", "eliminate_duplicates", "n_offsprings", "n_gen"]   
    template_name = "dss/create_nsga3.html"
    success_url = reverse_lazy("create_list")

    def form_valid(self, form):
        nsga3 = form.save(commit=False)
        nsga3.user_fk = self.request.user
        nsga3.save()
        return super(CreateNSGA3View, self).form_valid(form)


class UpdateNSGA3View(LoginRequiredMixin, ModelFormMixin, DetailView):
    model = NSGA3Model
    fields = ["alg_name", "ref_dirs", "auto_ref_dirs_method", "auto_ref_dirs_dimensions", 
            "auto_ref_dirs_npartitions", "pop_size", "eliminate_duplicates", "n_offsprings", "n_gen"] 
    template_name = "dss/update_nsga3.html"
    success_url = reverse_lazy("create_list")

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponseForbidden()
        self.object = self.get_object()
        if self.request.POST.get("Delete",False):
            self.object.delete()
            return redirect("create_list")
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        return super().form_valid(form)


class CreateUNSGA3View(LoginRequiredMixin,CreateView):
    model = UNSGA3Model
    fields = ["alg_name", "ref_dirs", "auto_ref_dirs_method", "auto_ref_dirs_dimensions", 
            "auto_ref_dirs_npartitions", "pop_size", "eliminate_duplicates", "n_offsprings", "n_gen"]   
    template_name = "dss/create_unsga3.html"
    success_url = reverse_lazy("create_list")

    def form_valid(self, form):
        unsga3 = form.save(commit=False)
        unsga3.user_fk = self.request.user
        unsga3.save()
        return super(CreateUNSGA3View, self).form_valid(form)


class UpdateUNSGA3View(LoginRequiredMixin, ModelFormMixin, DetailView):
    model = UNSGA3Model
    fields = ["alg_name", "ref_dirs", "auto_ref_dirs_method", "auto_ref_dirs_dimensions", 
            "auto_ref_dirs_npartitions", "pop_size", "eliminate_duplicates", "n_offsprings", "n_gen"] 
    template_name = "dss/update_unsga3.html"
    success_url = reverse_lazy("create_list")

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponseForbidden()
        self.object = self.get_object()
        if self.request.POST.get("Delete",False):
            self.object.delete()
            return redirect("create_list")
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        return super().form_valid(form)

class CreateProblemView(LoginRequiredMixin,CreateView):
    model = ProblemModel
    fields = ["problem_name", "nvar", "nobj", "ncostr", "xl", "xu"]   
    template_name = "dss/create_problem.html"
    success_url = reverse_lazy("create_list")

    def form_valid(self, form):
        problem = form.save(commit=False)
        problem.user_fk = self.request.user
        problem.save()
        return super(CreateProblemView, self).form_valid(form)


class UpdateProblemView(LoginRequiredMixin, ModelFormMixin, DetailView):
    model = ProblemModel
    fields = ["problem_name", "nvar", "nobj", "ncostr", "xl", "xu"]   
    template_name = "dss/update_problem.html"
    success_url = reverse_lazy("create_list")

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponseForbidden()
        self.object = self.get_object()
        if self.request.POST.get("Delete",False):
            self.object.delete()
            return redirect("create_list")
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        return super().form_valid(form)

class CreateFGView(LoginRequiredMixin, CreateView):
    model = FGModel
    fields = ["fg_name", "f", "g"]   
    template_name = "dss/create_fg.html"
    success_url = reverse_lazy("create_list")

    def form_valid(self, form):
        fg = form.save(commit=False)
        fg.user_fk = self.request.user
        fg.save()
        return super(CreateFGView, self).form_valid(form)


class UpdateFGView(LoginRequiredMixin, ModelFormMixin, DetailView):
    model = FGModel
    fields = ["fg_name", "f", "g"]   
    template_name = "dss/update_fg.html"
    success_url = reverse_lazy("create_list")

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponseForbidden()
        self.object = self.get_object()
        if self.request.POST.get("Delete",False):
            self.object.delete()
            return redirect("create_list")
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        return super().form_valid(form)

class TaskCreateView(LoginRequiredMixin,CreateView):
    form_class = CreateTaskForm
    template_name = "dss/create_task.html"
    success_url = reverse_lazy("create_list")

    def form_valid(self, form):
        task = form.save(commit=False)
        task.user_fk = self.request.user
        task.save()
        return super(TaskCreateView, self).form_valid(form)

    def get_form_kwargs(self):
        kwargs = super(TaskCreateView, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

class TaskDetailView(LoginRequiredMixin, DetailView):
    model = TaskModel
    template_name = "dss/detail_task.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        obj = context["object"]
        context["ress_hsts_hvs"] = []
        all_res_hvs = []
        for res in obj.resultmodel_set.all():
            context["ress_hsts_hvs"].append({ "res":res, "hstry_x_f_g":list( zip( eval(res.hstry_x),eval(res.hstry_f),eval(res.hstry_g), eval(res.hvs) ) ) })

            if res.nsga3_fk:
                alg_name = res.nsga3_fk.alg_name
            elif res.unsga3_fk:
                alg_name = res.unsga3_fk.alg_name
            if res.nsga3_fk:
                gens = res.nsga3_fk.n_gen
            elif res.unsga3_fk:
                gens = res.unsga3_fk.n_gen
            all_res_hvs.append( { "alg_name":alg_name, "res_max":[ max(hvs) for hvs in eval(res.hvs)], "gens":list(range(1,gens+1)) } )

        all_res_hvs_fig = go.Figure()
        for res_hvs in all_res_hvs:
            all_res_hvs_fig.add_trace( go.Scatter(x=res_hvs["gens"], y=res_hvs["res_max"], name=res_hvs["alg_name"], mode='lines+markers') )
        all_res_hvs_fig.update_layout(xaxis_title="GEN", yaxis_title="BEST HV IN GEN")
        context["all_res_hvs_fig"] = plotly.io.to_html(all_res_hvs_fig, full_html=False)
        
        return context  