from django.db import models
from django.contrib.auth.models import User
from datetime import timedelta
import random
import string

class UserProfile(models.Model):
    USER_ROLES = (
        ('adviser', 'Adviser'),
        ('secretary', 'Secretary'),
        ('dean', 'Dean'),
        ('admin', 'Admin'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=USER_ROLES)

    def __str__(self):
        return f"{self.user.username} - {self.role}"

class StudentClassification(models.Model):
    YEAR_CHOICES = (
        ('1st', '1st Year'),
        ('2nd', '2nd Year'),
        ('3rd', '3rd Year'),
        ('4th', '4th Year'),
    )
    BLOCK_CHOICES = (
        ('A', 'Block A'),
        ('B', 'Block B'),
        ('C', 'Block C'),
        # Add more as needed
    )
    year = models.CharField(max_length=3, choices=YEAR_CHOICES)
    block = models.CharField(max_length=1, choices=BLOCK_CHOICES, default='A')

    def __str__(self):
        return f"{self.year} Year - Block {self.block}"



class RFIDCard(models.Model):
    card_number = models.CharField(max_length=255, unique=True)
    student = models.OneToOneField('Student', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"{self.card_number} - {self.student}"

class Adviser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to='adviser_avatars/', null=True, blank=True, default='default_avatar.png')
    contact_number = models.CharField(max_length=15, null=True, blank=True)
    address = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.user.username

class Student(models.Model):
    first_name = models.CharField(max_length=30, null=True, blank=True)
    last_name = models.CharField(max_length=30, null=True, blank=True)
    email = models.EmailField(max_length=255, null=True, blank=True)
    address = models.CharField(max_length=255, null=True, blank=True)
    contact_number = models.CharField(max_length=15, null=True, blank=True)
    avatar = models.ImageField(upload_to='student_avatars/', blank=True, null=True, default='/default_avatar.png')
    student_id = models.CharField(max_length=12, unique=True)
    classification = models.ForeignKey(StudentClassification, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.classification} - {self.first_name} {self.last_name} - {self.student_id} - "


class Subject(models.Model):
    SEM_CHOICES = (
        ('1st', '1st Semester'),
        ('2nd', '2nd Semester'),
    )

    YEAR_CHOICES = (
        ('1st', '1st Year'),
        ('2nd', '2nd Year'),
        ('3rd', '3rd Year'),
        ('4th', '4th Year'),
    )
    name = models.CharField(max_length=255)
    adviser = models.ForeignKey(Adviser, on_delete=models.CASCADE, related_name='subjects')
    #classifications = models.ManyToManyField(StudentClassification, related_name='subjects')
    time_in_grace_period_minutes = models.PositiveIntegerField(default=0, help_text="Time in grace period for attendance in minutes")
    time_out_grace_period_minutes = models.PositiveIntegerField(default=0, help_text="Time out grace period for attendance in minutes")

    semester = models.CharField(max_length=3, choices=SEM_CHOICES, null=True, blank=True)
    year_level = models.CharField(max_length=3, choices=YEAR_CHOICES, null = True, blank = True)
    
    def __str__(self):
        return self.name



class SubjectSchedule(models.Model):
    class_code = models.CharField(max_length=6, unique=True, editable=False, null = True)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    classification = models.ForeignKey(StudentClassification, on_delete=models.CASCADE)
    day = models.CharField(max_length=100, null=True)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    students = models.ManyToManyField(Student, related_name='subject_schedules', blank=True)

    def __str__(self):
        return f"{self.class_code} - {self.subject.name} - {self.classification}"

    def is_on_day(self, day_name):
        return day_name in self.day.split(' - ')

    def is_at_time(self, start_time, end_time):
        return self.start_time <= start_time <= self.end_time and self.start_time <= end_time <= self.end_time
    
    def save(self, *args, **kwargs):
        # Generate a random 6-letter code
        if not self.class_code:
            self.class_code = self.generate_class_code()
        super().save(*args, **kwargs)

    def generate_class_code(self):
        letters = string.ascii_uppercase
        return ''.join(random.choice(letters) for _ in range(6))



class Attendance(models.Model):
    STATUS_CHOICES = (
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('present', 'Present'),
        ('excused', 'Excused')
    )
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    subject_schedule = models.ForeignKey(SubjectSchedule, on_delete=models.CASCADE, null=True, blank=True)
    time_in = models.DateTimeField()
    time_out = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, null=True, blank=True)
    updated = models.DateTimeField(auto_now=True, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def is_on_time(self):
        if self.subject_schedule and self.subject_schedule.subject.time_in_grace_period_minutes:
            grace_period = timedelta(minutes=self.subject_schedule.subject.time_in_grace_period_minutes)
            return self.time_in <= (self.subject_schedule.start_time + grace_period)
        return True

    def __str__(self):
        return f"{self.student} - {self.time_in} - {self.time_out}"
