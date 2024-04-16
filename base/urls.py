from django.urls import path
from . import views

from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [

    path('', views.home, name='home'),
    path('process_attendance/', views.process_attendance2, name='process_attendance'),
    

    path('login/', views.custom_login, name='login'),
    path('register/', views.register_page, name='register'),
    path('logout/', views.custom_logout, name='logout'),


    path('dashboard/', views.dashboard, name='dashboard'),
    path('attendance/', views.attendance, name='attendance'),
    path('path/to/render_attendance_list/', views.render_attendance_list, name='render_attendance_list'),

    path('subjects/', views.subjects, name='subjects'),
    path('subject/details/<str:subject_name>/', views.subject_details, name='subject_details'),

    path('subject/add-subject', views.add_subject, name="add_subject"),
    path('subject/edit-subject/<int:subject_id>/', views.edit_subject, name="edit_subject"),
    path('subject/delete-subject/<int:subject_id>/', views.delete_subject, name="edit_subject"),

    path('subject/set-schedule/', views.set_schedule, name='set_schedule'),
    path('get-schedule-data/<int:schedule_id>/', views.get_subject_schedule_info, name="get_subject_schedule_info"),
    path('subjects/edit-schedule/<int:schedule_id>/', views.set_schedule, name='edit_schedule'),
    path('delete-schedule/<int:schedule_id>/', views.delete_schedule, name='delete_schedule'),
    
    path('path/to/render_subject_list/', views.render_subject_list_template, name='render_subject_list'),

    path('students/', views.students, name='students'),
    path('student-profile/<slug:student_id>/', views.student_profile, name='student_profile'),
    path('student/edit-information/<slug:student_id>/', views.edit_student_info, name="edit-student-info"),
    path('add-student/', views.add_student, name="add_student")

]

urlpatterns += static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)
