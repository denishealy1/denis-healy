from django.urls import path

from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('partner/', views.partner_dashboard, name='partner_dashboard'),
    path('partner/projects/new/', views.project_create, name='project_create'),
    path('partner/projects/<int:project_id>/invite/', views.invite_students, name='invite_students'),
    path('invite/<str:token>/', views.invite_accept, name='invite_accept'),
    path('student/', views.student_dashboard, name='student_dashboard'),
    path('student/profile/', views.student_profile, name='student_profile'),
    path('student/logistics/', views.student_logistics, name='student_logistics'),
    path('admin-portal/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-portal/projects/<int:project_id>/', views.project_detail, name='project_detail'),
    path('admin-portal/companies/', views.company_list, name='company_list'),
    path('admin-portal/companies/new/', views.company_edit, name='company_create'),
    path('admin-portal/companies/<int:pk>/', views.company_edit, name='company_edit'),
    path('admin-portal/students/<int:pk>/', views.student_admin_detail, name='student_admin_detail'),
    path('admin-portal/students/<int:pk>/certificate/', views.generate_certificate, name='generate_certificate'),
]
