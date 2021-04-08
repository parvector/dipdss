from django.urls import path
from . import views



urlpatterns = [
    path("", views.HomePageView.as_view(), name="home"),
    path("create-list/", views.create_list, name="create_list"),
    path("accounts/profile/", views.ProfileView.as_view(), name="profile"),
    path("accounts/signup/", views.SignUpView.as_view(), name="signup"),
    path("create-nsga3/", views.CreateNSGA3View.as_view(), name="create_nsga3"),
    path("update-nsga3/<int:pk>/", views.UpdateNSGA3View.as_view(), name="update_nsga3"),
    path("create-unsga3/", views.CreateUNSGA3View.as_view(), name="create_unsga3"),
    path("update-unsga3/<int:pk>/", views.UpdateUNSGA3View.as_view(), name="update_unsga3"),
    path("create-problem/", views.CreateProblemView.as_view(), name="create_problem"),
    path("update-problem/<int:pk>/", views.UpdateProblemView.as_view(), name="update_problem"),
    path("create-fg/", views.CreateFGView.as_view(), name="create_fg"),
    path("update-fg/<int:pk>/", views.UpdateFGView.as_view(), name="update_fg"),
    path("task-create/", views.TaskCreateView.as_view(), name="task_create"),
    path("task-detail/<int:pk>/", views.TaskDetailView.as_view(), name="task_detail")
]