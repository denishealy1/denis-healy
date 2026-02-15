from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('login/', views.UserLoginView.as_view(), name='login'),
    path('logout/', views.UserLogoutView.as_view(), name='logout'),
    path('set-language/', views.set_language_preference, name='set_language'),

    path('projects/new/', views.project_create, name='project_create'),
    path('projects/<int:project_id>/', views.partner_project_detail, name='partner_project_detail'),
    path('projects/<int:project_id>/invite/', views.invite_students, name='invite_students'),
    path('projects/<int:project_id>/invite-csv/', views.invite_csv_upload, name='invite_csv_upload'),

    path('invite/<uuid:token>/', views.invite_signup, name='invite_signup'),
    path('student/onboarding/', views.student_onboarding, name='student_onboarding'),
    path('student/logistics/', views.student_logistics, name='student_logistics'),

    path('admin/companies/', views.companies, name='companies'),
    path('admin/students/<int:profile_id>/', views.student_detail, name='student_detail'),
    path('admin/students/<int:profile_id>/certificate/', views.generate_certificate, name='generate_certificate'),
]
