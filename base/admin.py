from django.contrib import admin
from .models import *

# Register your models here.

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role')

@admin.register(StudentClassification)
class StudentClassificationAdmin(admin.ModelAdmin):
    list_display = ('year', 'block')


@admin.register(RFIDCard)
class RFIDCardAdmin(admin.ModelAdmin):
    list_display = ('card_number', 'student')

@admin.register(Adviser)
class AdviserAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'contact_number', 'address')

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'adviser', 'semester', 'year_level', 'time_in_grace_period_minutes', 'time_out_grace_period_minutes')

@admin.register(SubjectSchedule)
class SubjectScheduleAdmin(admin.ModelAdmin):
    list_display = ('subject', 'class_code', 'classification', 'day', 'start_time', 'end_time')

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'student_id', 'classification')

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'subject_schedule', 'time_in', 'time_out', 'status')
