from django.shortcuts import render, redirect, get_object_or_404

from django.http import JsonResponse, HttpResponse

from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

from django.contrib.auth.decorators import login_required

from .models import *

from django.utils import timezone
from django.core import serializers
from datetime import datetime, time, timedelta

from django.utils import timezone
import pytz

from django.db.models import Count
from django.db.models.functions import ExtractMonth
from django.db.models import Q

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from datetime import date


#from django_celery_beat.models import PeriodicTask, IntervalSchedule

def custom_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('dashboard')

        else:
            messages.error(request, 'Invalid login credentials.')

    return render(request, 'base/sign_in.html')

def custom_logout(request):
    logout(request)
    return redirect('login')

def home(request):
    # Get the current day and time in your project's timezone
    now = timezone.now()

    # Convert the datetime to your desired timezone (e.g., 'Asia/Manila')
    local_timezone = pytz.timezone('Asia/Manila')
    now = now.astimezone(local_timezone)
    day = now.strftime('%A')

    # Format the current time as a string in 24-hour format
    formatted_time = now.strftime("%H:%M:%S")

    # Filter subjects that match the current day, time, and classification
    current_subjects = SubjectSchedule.objects.filter(
        day__contains=day,
        start_time__lte=formatted_time,
        end_time__gte=formatted_time,
    ).select_related('subject', 'classification')

    # Prepare a list of dictionaries containing subject and classification information
    current_subjects_info = [
        {
            'subject_name': subject_schedule.subject.name,
            'classification_name': subject_schedule.classification,
        }
        for subject_schedule in current_subjects
    ]

    context = {
        'current_time': formatted_time,
        'current_day': day,
        'current_subjects_info': current_subjects_info,
    }
    return render(request, 'base/home.html', context)


def process_attendance(request):
    # Get the current day and time in your project's timezone
    now = timezone.now()
                    
    # Convert the datetime to your desired timezone (e.g., 'Asia/Manila')
    local_timezone = pytz.timezone('Asia/Manila')
    now = now.astimezone(local_timezone)
    day = now.strftime('%A')
    # Format the current time as a string in 24-hour format
    formatted_time = now.strftime("%H:%M:%S")
    
    if request.method == 'POST':
        rfid_number = request.POST.get('rfid_number', '')
        print(f"Received RFID number: {rfid_number}")  # Debugging output

        try:
            rfid_card = RFIDCard.objects.get(card_number=rfid_number)
            print(f"RFID card found: {rfid_card}")  # Debugging output

            if rfid_card.student:
                student = rfid_card.student
                active_attendance = Attendance.objects.filter(student=student, time_out=None).first()

                if active_attendance:
                    active_attendance.time_out = timezone.now()
                    active_attendance.save()
                    return JsonResponse({'message': f'Time-out for {student}', 'icon':'success'})
                else:
                    # Filter subjects that match the current day and time
                    current_subjects = Subject.objects.filter(subjectschedule__day__contains=day, subjectschedule__start_time__lte=formatted_time, subjectschedule__end_time__gte=formatted_time)
                    
                    print(day)
                    print(formatted_time)
                    print(current_subjects)

                    # Check if the student is enrolled in any of the scheduled subjects
                    for schedule in current_subjects:
                        if student.student_subject_schedules.filter(subject=schedule).exists():
                            new_attendance = Attendance(student=student, rfid_card=rfid_card, subject=schedule, time_in=timezone.now())
                            new_attendance.save()
                            return JsonResponse({'message': f'Time-in for {student} for subject {schedule.name}', 'icon':'success'})
                    
                    return JsonResponse({'message': 'No subject schedule found for the current time.', 'icon': 'info'})

            else:
                return JsonResponse({'message': 'RFID card is not assigned to any student.', 'icon':'info'})
        except RFIDCard.DoesNotExist:
            return JsonResponse({'message': 'RFID card not found.', 'icon':'info'})

    return JsonResponse({'message': 'Invalid request method.', 'icon':'info'})


def process_attendance3(request):


    # Get the current day and time in your project's timezone
    now = timezone.localtime(timezone.now())
    day = now.strftime('%A')

    if request.method == 'POST':
        rfid_number = request.POST.get('rfid_number', '')
        print(f"Received RFID number: {rfid_number}")  # Debugging output

        try:
            rfid_card = RFIDCard.objects.get(card_number=rfid_number)
            print(f"RFID card found: {rfid_card}")  # Debugging output

            if rfid_card.student:
                student = rfid_card.student
                active_attendance = Attendance.objects.filter(student=student, time_out=None).first()

                if active_attendance:
                    # Check if the student is tapping out on the same day
                    if active_attendance.time_in is None and active_attendance.time_out.date() == now.date():
                        return JsonResponse({'message': 'You have already tapped in today.', 'icon': 'info'})
                    else:
                        # Check for time-in grace period
                        grace_period_difference = now - active_attendance.time_in

                        # Fetch the related SubjectSchedule
                        subject_schedule = SubjectSchedule.objects.get(subject=active_attendance.subject)

                        if grace_period_difference.total_seconds() / 60 <= active_attendance.subject.time_in_grace_period_minutes and now.time() <= subject_schedule.start_time:
                            active_attendance.status = 'present'
                        else:
                            if active_attendance.status is None:
                                active_attendance.status = 'late'

                        active_attendance.time_out = now

                        # Check for time-out grace period
                        #time_out_grace_period_difference = now - active_attendance.time_in
                        subject = active_attendance.subject

                        time_out_grace_period_difference = now - active_attendance.time_out

                        if time_out_grace_period_difference.total_seconds() / 60 >= subject.time_out_grace_period_minutes:
                            active_attendance.status = 'absent'
                        #else:
                        #    active_attendance.status = 'present'

                        active_attendance.time_out = now
                        active_attendance.save()

                        return JsonResponse({'message': f'Time-out for {student}', 'icon': 'success'})
                else:
                    # Filter subjects that match the current day and time
                    current_subjects = Subject.objects.filter(subjectschedule__day__contains=day, subjectschedule__start_time__lte=now.time(), subjectschedule__end_time__gte=now.time())


                    # Check if the student is enrolled in any of the scheduled subjects
                    enrolled_subjects = student.student_subject_schedules.filter(subject__in=current_subjects)

                    if enrolled_subjects.exists():
                        # Student is enrolled in at least one scheduled subject
                        schedule = enrolled_subjects.first().subject

                        # Check if the student already has an attendance for this subject schedule
                        existing_attendance = Attendance.objects.filter(student=student, subject=schedule, time_out__isnull=False).first()
                        if existing_attendance:
                            return JsonResponse({'message': 'You have already timed in and out for this subject schedule.', 'icon': 'info'})

                        subject_schedule = SubjectSchedule.objects.get(subject=schedule)
                        start_datetime = timezone.make_aware(datetime.combine(now.date(), subject_schedule.start_time))
                        grace_period_difference = now - start_datetime

                        if grace_period_difference.total_seconds() / 60 <= schedule.time_in_grace_period_minutes:
                            status = 'present'
                        else:
                            status = 'late'

                        new_attendance = Attendance(
                            student=student,
                            subject=schedule,
                            time_in=now,
                            status=status
                        )
                        new_attendance.save()

                        return JsonResponse({'message': f'Time-in for {student} for subject {schedule.name}', 'icon': 'success'})
                    else:
                        return JsonResponse({'message': 'No subject schedule found for the current time.', 'icon': 'info'})

            else:
                return JsonResponse({'message': 'RFID card is not assigned to any student.', 'icon': 'info'})
        except RFIDCard.DoesNotExist as e:
            return JsonResponse({'message': f'RFID card not found. Error: {str(e)}', 'icon': 'info'})
        except Exception as e:
            return JsonResponse({'message': f'An error occurred: {str(e)}', 'icon': 'info'})

    return JsonResponse({'message': 'Invalid request method.', 'icon': 'info'})

def process_attendance2(request):
    # Get the current day and time in your project's timezone
    now = timezone.localtime(timezone.now())
    day = now.strftime('%A')

    if request.method == 'POST':
        rfid_number = request.POST.get('rfid_number', '')
        print(f"Received RFID number: {rfid_number}")  # Debugging output

        try:
            rfid_card = RFIDCard.objects.get(card_number=rfid_number)
            print(f"RFID card found: {rfid_card}")  # Debugging output

            if rfid_card.student:
                student = rfid_card.student
                active_attendance = Attendance.objects.filter(student=student, time_out=None).first()

                if active_attendance:
                    
                    if active_attendance.time_in is None and active_attendance.time_out.date() == now.date():
                        return JsonResponse({'message': 'You have already tapped in today.', 'icon': 'info'})
                    else:
                        grace_period_difference = now - active_attendance.time_in

                        subject_schedule = active_attendance.subject_schedule

                        if grace_period_difference.total_seconds() / 60 <= subject_schedule.subject.time_in_grace_period_minutes and now.time() <= subject_schedule.start_time:
                            active_attendance.status = 'present'
                        else:
                            if active_attendance.status is None:
                                active_attendance.status = 'late'

                        active_attendance.time_out = now

                        time_out_grace_period_difference = now - active_attendance.time_out
                        subject = subject_schedule.subject

                        if time_out_grace_period_difference.total_seconds() / 60 >= subject.time_out_grace_period_minutes:
                            active_attendance.status = 'absent'

                        active_attendance.save()
                        

                        return JsonResponse({'message': f'Time-out for {student}', 'icon': 'success'})
                else:
                    # Filter subject schedules that match the current day and time
                    current_subject_schedules = SubjectSchedule.objects.filter(
                        day__contains=day,
                        start_time__lte=now.time(),
                        end_time__gte=now.time()
                    )

                    # Check if the student is enrolled in any of the scheduled subjects
                    enrolled_subject_schedules = student.subject_schedules.filter(
                        id__in=current_subject_schedules.values('id')
                    )

                    if enrolled_subject_schedules.exists():
                        # Student is enrolled in at least one scheduled subject
                        schedule = enrolled_subject_schedules.first()

                        # Check if the student already has an attendance for this subject schedule
                        existing_attendance = Attendance.objects.filter(
                            student=student,
                            subject_schedule=schedule,
                            time_out__isnull=False
                        ).first()

                        if existing_attendance:
                            return JsonResponse({'message': 'You have already timed in and out for this subject schedule.', 'icon': 'info'})

                        start_datetime = timezone.make_aware(datetime.combine(now.date(), schedule.start_time))
                        grace_period_difference = now - start_datetime

                        if grace_period_difference.total_seconds() / 60 <= schedule.subject.time_in_grace_period_minutes:
                            status = 'present'
                        else:
                            status = 'late'

                        new_attendance = Attendance(
                            student=student,
                            subject_schedule=schedule,
                            time_in=now,
                            status=status
                        )
                        new_attendance.save()

                        return JsonResponse({'message': f'Time-in for {student} for subject {schedule.subject.name}', 'icon': 'success'})
                    
                    else:
                        return JsonResponse({'message': 'No subject schedule found for the current time.', 'icon': 'info'})

            else:
                return JsonResponse({'message': 'RFID card is not assigned to any student.', 'icon': 'info'})
        except RFIDCard.DoesNotExist as e:
            return JsonResponse({'message': f'RFID card not found. Error: {str(e)}', 'icon': 'info'})
        except Exception as e:
            return JsonResponse({'message': f'An error occurred: {str(e)}', 'icon': 'info'})


    return JsonResponse({'message': 'Invalid request method.', 'icon': 'info'})

def record_auto_attendance(request):
    # Get the current day and time in your project's timezone
    now = timezone.localtime(timezone.now())
    day = now.strftime('%A')

    # Filter subjects that match the current day and time
    current_subjects = Subject.objects.filter(
        subjectschedule__day__contains=day,
        subjectschedule__start_time__lte=now.time(),
        subjectschedule__end_time__gte=now.time()
    )

    for subject in current_subjects:
        # Filter students who are enrolled in the current subject
        enrolled_students = Student.objects.filter(
            student_subject_schedules__subject=subject,
            student_subject_schedules__is_enrolled=True
        )

        for student in enrolled_students:
            # Check if the student already has an attendance for this subject schedule
            existing_attendance = Attendance.objects.filter(
                student=student,
                subject=subject,
                time_out__isnull=False
            ).first()

            if not existing_attendance:
                # If the student hasn't tapped in for the subject, record an absent attendance
                new_attendance = Attendance(
                    student=student,
                    subject=subject,
                    time_in=None,
                    time_out=None,
                    status='absent'
                )
                new_attendance.save()

    return JsonResponse({'message': 'Auto attendance recorded successfully.', 'icon': 'success'})


def login_page(request):
    page = 'login'

    #if request.user.is_authenticated:
    #    return redirect('home')
    
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')

        try:
            user = User.objects.get(username = username)
        except:
            messages.error(request, 'User does not exist!')

        user = authenticate(request, username = username, password = password) #authenticate if credentials are correct

        if user is not None:
            login(request, user) #add the session to database
            return redirect('dashboard')
        else:
            messages.error(request, 'Username OR Password does not exist!')

    context = {
        'page': page,
    }

    return render(request, 'base/sign_in.html', context)


def register_page(request):

    return render(request, 'base/sign_up.html')



def dashboard(request):
    current_year = timezone.now().year

    # Query to get the counts for each status for each month
    data = (
        Attendance.objects
        .filter(time_in__year=current_year)
        .annotate(month=ExtractMonth('time_in'))
        .values('month', 'status')
        .annotate(count=Count('id'))
    )

    # Initialize empty lists for each status
    present_data = [0] * 12
    late_data = [0] * 12
    absent_data = [0] * 12
    excused_data = [0] * 12

    # Populate the lists based on the query results
    for entry in data:
        month = entry['month'] - 1  # Adjusting month to be zero-indexed
        status = entry['status']
        count = entry['count']

        if status == 'present':
            present_data[month] = count
        elif status == 'late':
            late_data[month] = count
        elif status == 'absent':
            absent_data[month] = count
        elif status == 'excused':
            excused_data[month] = count
            
    user_profile = request.user.userprofile

    if user_profile.role == 'secretary':

        now = timezone.now().date()

        attendance = Attendance.objects.filter(status='present')

        adviser = Adviser.objects.all()
        subject = Subject.objects.all()

        students = Student.objects.all()
            # Query to get the count of students for each year classification
        year_counts = Student.objects.values('classification__year').annotate(count=Count('id'))

        # Extracting labels and data for the chart
        student_labels = [f"{item['classification__year']} Year" for item in year_counts]
        student_data = [item['count'] for item in year_counts]

        context = {
            'present_data': present_data,
            'late_data': late_data,
            'absent_data': absent_data,
            'excused_data': excused_data,

            'labels': student_labels,
            'data': student_data,

            'attendance': attendance,
            'adviser': adviser,
            'subject': subject,
            'students': students,
        }
        return render(request, 'base/dashboard.html', context)
    
    if user_profile.role == 'adviser':
        return HttpResponse('Under maintenance')
    
    if request.user.is_authenticated:
        return HttpResponse(' You dont have access to this page')
    


def attendance(request):
    today = timezone.now()
    # Get the adviser related to the logged-in user

    attendance_data = Attendance.objects.all()
    subjects = SubjectSchedule.objects.all()

    today_attendance = []
    for subject_schedule in subjects:
        today_attendance += subject_schedule.attendance_set.filter(time_in__date=today)

    overall_attendance_summary_today = []

    for subject_schedule in subjects:
        enrolled_students_today = subject_schedule.students.count()
        attended_students_today = subject_schedule.attendance_set.filter(time_in__date = today).count()

        if enrolled_students_today > 0:
            attendance_percentage_today = (attended_students_today / enrolled_students_today) * 100
        else:
            attendance_percentage_today = 0

        overall_attendance_summary_today.append({
            'subject_schedule': subject_schedule,
            'enrolled_students_today': enrolled_students_today,
            'attended_students_today': attended_students_today,
            'attendance_percentage_today': attendance_percentage_today,
        })


    context = {
        'attendance_data': attendance_data,
        'subject_attendance': overall_attendance_summary_today
    }

    return render(request, 'base/attendance.html', context)

def render_attendance_list(request):

    attendance_data = Attendance.objects.all()

    context = {
        'attendance_data': attendance_data
        }
    return render(request, 'base/updated_attendance_list.html', context)


def subjects(request):
    students = Student.objects.all()

    # Query to get the count of students for each year classification
    year_counts = Student.objects.values('classification__year').annotate(count=Count('id'))

    # Extracting labels and data for the chart
    labels = [f"{item['classification__year']} Year" for item in year_counts]
    data = [item['count'] for item in year_counts]

    subjects = Subject.objects.annotate(student_count=Count('subjectschedule__students'))

    classification = StudentClassification.objects.all()

    advisers = Adviser.objects.all()

    subjects = Subject.objects.annotate(student_count=Count('subjectschedule__students'))
    # Filter subjects based on search query
    search_query = request.GET.get('search') if request.GET.get('search') != None else ""
    year_level = request.GET.get('year_level') if request.GET.get('year_level') != None else ""
    semester = request.GET.get('semester') if request.GET.get('semester') != None else ""


    if search_query:
        subjects = subjects.filter(Q(name__icontains=search_query) | Q(adviser__user__first_name__icontains=search_query) | Q(adviser__user__last_name__icontains=search_query))

    if year_level:
        subjects = subjects.filter(year_level=year_level)

    if semester:
        subjects = subjects.filter(semester=semester)

    # Additional filter for both semester and year level
    if semester and year_level:
        subjects = subjects.filter(semester=semester, year_level=year_level)

    # Adding pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(subjects, 5)  # Show 5 subjects per page

    try:
        paginated_subjects = paginator.page(page)
    except PageNotAnInteger:
        paginated_subjects = paginator.page(1)
    except EmptyPage:
        paginated_subjects = paginator.page(paginator.num_pages)

        
    context = {
        'advisers': advisers,
        'subjects': subjects,
        'classification': classification,
        'labels': labels,
        'data': data,
        'students': students,
        'paginated_subjects': paginated_subjects,
        'search_query': search_query,
        'selected_year_level': year_level,
        'selected_semester': semester,
    
    }
    return render(request, 'base/subjects2.html', context)


def subject_details(request, subject_name):
    subject = get_object_or_404(Subject, name=subject_name)
    subject_schedules = subject.subjectschedule_set.all()

    # Fetch all attendance for each SubjectSchedule
    all_attendance = []
    for subject_schedule in subject_schedules:
        all_attendance += subject_schedule.attendance_set.all()

    # Fetch today's attendance for each SubjectSchedule
    today = date.today()
    today_attendance = []
    for subject_schedule in subject_schedules:
        today_attendance += subject_schedule.attendance_set.filter(time_in__date=today)

    # Calculate overall attendance summary for today
    overall_attendance_summary_today = []
    for subject_schedule in subject_schedules:
        enrolled_students_today = subject_schedule.students.count()
        attended_students_today = subject_schedule.attendance_set.filter(time_in__date=today).count()

        # Calculate percentage of attended students for today
        if enrolled_students_today > 0:
            attendance_percentage_today = (attended_students_today / enrolled_students_today) * 100
        else:
            attendance_percentage_today = 0

        overall_attendance_summary_today.append({
            'subject_schedule': subject_schedule,
            'enrolled_students_today': enrolled_students_today,
            'attended_students_today': attended_students_today,
            'attendance_percentage_today': attendance_percentage_today,
        })


    # Get the list of students in the subject
    students_in_subject = Student.objects.filter(subject_schedules__subject=subject).distinct()

    classifications = StudentClassification.objects.all()


    context = {
        'subject': subject,
        'subject_schedules': subject_schedules,
        'all_attendance': all_attendance,
        'today_attendance': today_attendance,
        'overall_attendance_summary_today': overall_attendance_summary_today,
        'today': today,
        'students_in_subject': students_in_subject,

        'classifications': classifications
    }
    return render(request, 'base/subject_details.html', context)

def subject_attendance(request, subject_name):

    subject = Subject.objects.get(name=subject_name)
    attendances = Attendance.objects.filter(subject = subject)

   # attendances = Attendance.objects.filter(subject=subject)
    context = {
        'subject': subject,
        'attendances': attendances,
     #   'attendances': attendances,
    }
    
    return render(request, 'base/subject_attendance.html', context)


def add_subject(request):
    if request.method == 'POST':
        # Get data from the POST request
        name = request.POST.get('subject_name')
        adviser_id = request.POST.get('adviser')
        semester = request.POST.get('semester')
        year_level = request.POST.get('year_level')
        time_in_grace_period = request.POST.get('time_in_grace_period')
        time_out_grace_period = request.POST.get('time_out_grace_period')

        # Validate the data (you should add more validation based on your requirements)
        if not name or not adviser_id or not time_in_grace_period or not time_out_grace_period:
            return JsonResponse({'success': False, 'message': 'All fields are required'})

        try:
            adviser = Adviser.objects.get(pk=adviser_id)
        except Adviser.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Invalid adviser'})

        # Create the Subject instance
        subject = Subject(
            name=name,
            adviser=adviser,
            semester=semester,
            year_level=year_level,
            time_in_grace_period_minutes=time_in_grace_period,
            time_out_grace_period_minutes=time_out_grace_period
        )
        subject.save()


        return JsonResponse({'success': True, 'message': 'Subject added successfully'})

    # If the request is not a POST request, handle it accordingly
    return JsonResponse({'success': False, 'message': 'Invalid request method'})


def edit_subject(request, subject_id):
    subject = get_object_or_404(Subject, pk=subject_id)

    subject.name = request.POST.get('subject_name')
    subject.adviser_id = request.POST.get('adviser')
    subject.time_in_grace_period_minutes = request.POST.get('time_in_grace_period_minutes')
    subject.time_out_grace_period_minutes = request.POST.get('time_out_grace_period_minutes')
    subject.semester = request.POST.get('semester')
    subject.year_level = request.POST.get('year_level')

    try:
        adviser = Adviser.objects.get(pk=subject.adviser_id)
    except Adviser.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Invalid adviser'})

    subject.save()

    return JsonResponse({'success': True, 'message': 'Subject updated successfully'})


def delete_subject(request, subject_id):
    try:
        subject = get_object_or_404(Subject, pk=subject_id)

        # Delete the subject
        subject.delete()

        return JsonResponse({'success': True, 'message': 'Subject deleted successfully'})
    except Exception as e:
        print(f"Error deleting subject: {e}")
        return JsonResponse({'success': False, 'message': 'Failed to delete subject'})
    
def render_subject_list_template(request):

    subjects = Subject.objects.all()
    page = request.GET.get('page', 1)
    paginator = Paginator(subjects, 5)  # Show 5 subjects per page

    try:
        paginated_subjects = paginator.page(page)
    except PageNotAnInteger:
        paginated_subjects = paginator.page(1)
    except EmptyPage:
        paginated_subjects = paginator.page(paginator.num_pages)
    context = {
        'paginated_subjects': paginated_subjects
        }
    return render(request, 'base/updated_subject_list.html', context)


def set_schedule(request, schedule_id=None):
    if request.method == 'POST':
        subject_name = request.POST.get('subject_name')
        classification_id = request.POST.get('classification')
        day = request.POST.get('day')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')

        subject = get_object_or_404(Subject, name=subject_name)
        classification = get_object_or_404(StudentClassification, id=classification_id)

        if schedule_id:  # Editing existing schedule
            schedule = get_object_or_404(SubjectSchedule, id=schedule_id)
            schedule.subject = subject
            schedule.classification = classification
            schedule.day = day
            schedule.start_time = start_time
            schedule.end_time = end_time
            schedule.save()

            # Update associated students
            schedule.students.set(classification.student_set.all())
            return redirect('subject_details', subject_name)
        else:  # Creating a new schedule
            schedule = SubjectSchedule(
                subject=subject,
                classification=classification,
                day=day,
                start_time=start_time,
                end_time=end_time,
            )
            schedule.save()

            # Get all students with the selected classification
            students_with_classification = Student.objects.filter(classification=classification)

            # Associate each student with the new schedule
            for student in students_with_classification:
                schedule.students.add(student)

            return redirect('subject_details', subject_name)

def delete_schedule(request, schedule_id):
    try:
        schedule = get_object_or_404(SubjectSchedule, id=schedule_id)
        subject = schedule.subject
        schedule.delete()
        return redirect('subject_details', subject)
    except SubjectSchedule.DoesNotExist:
        return JsonResponse({'error': 'Subject Schedule not found!'})
         

def get_subject_schedule_info(request, schedule_id):
    try:
        schedule = SubjectSchedule.objects.get(id=schedule_id)
        print(schedule.classification)
        data = {
            'day': schedule.day,
            'classification': str(schedule.classification.id),
            'start_time': schedule.start_time.strftime('%H:%M'),
            'end_time': schedule.end_time.strftime('%H:%M'),
            'classification_id': str(schedule.classification.id),
        }

        return JsonResponse(data)
    except SubjectSchedule.DoesNotExist:
        return JsonResponse({'error': 'Subject Schedule not found!'})
    

def students(request):
    students = Student.objects.all()
    classification = StudentClassification.objects.all()

    # Query to get the count of students for each year classification
    year_counts = Student.objects.values('classification__year').annotate(count=Count('id'))

    # Extracting labels and data for the chart
    labels = [f"{item['classification__year']} Year" for item in year_counts]
    data = [item['count'] for item in year_counts]

    context = {
        'labels': labels,
        'data': data,
        'students': students,
        'classification': classification,
    }
    return render(request, 'base/students.html',context)

def student_profile(request, student_id):

    student = Student.objects.get(student_id = student_id)
    subject_schedules = SubjectSchedule.objects.filter(students=student)
    attendance = Attendance.objects.filter(student=student)
    rfid = RFIDCard.objects.get(student = student)
    student_subject_schedule_attendance_counts = {}


    for subject_schedule in subject_schedules:
        attendance_counts = Attendance.objects.filter(student=student, subject_schedule=subject_schedule) \
            .values('status') \
            .annotate(count=Count('status'))

        status_counts = {entry['status']: entry['count'] for entry in attendance_counts}

        student_subject_schedule_attendance_counts[subject_schedule] = {
            'subject_name': subject_schedule.subject.name,
            'status_counts': status_counts,
        }

    context = {
        'student': student,
        'subject_schedules': subject_schedules,
        'attendance_data': attendance,
        'rfid': rfid,
        'student_subject_schedule_attendance_counts': student_subject_schedule_attendance_counts,

    }
    return render(request, 'base/student_profile2.html', context)

def edit_student_info(request, student_id):
    # Retrieve the student instance or return a 404 response if not found
    student = get_object_or_404(Student, student_id=student_id)
    rfid = RFIDCard.objects.get(student = student)

    rfid.card_number = request.POST.get('card_number', rfid.card_number)
    # Update student information based on the data sent in the request
    student.first_name = request.POST.get('first_name', student.first_name)
    student.last_name = request.POST.get('last_name', student.last_name)
    student.email = request.POST.get('email', student.email)
    student.address = request.POST.get('address', student.address)
    student.contact_number = request.POST.get('contact_number', student.contact_number)
    student.avatar = request.FILES.get('avatar', student.avatar)

    # Save the changes to the database
    student.save()
    rfid.save()

    # Return a JSON response indicating success
    return JsonResponse({'message': 'Student information updated successfully'})

def add_student(request):
    if request.method == 'POST':
        print(request.POST)
        # Retrieve form data
        classification_id = request.POST.get('classification')
        student_id = request.POST.get('student_id')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        address = request.POST.get('address')
        contact_number = request.POST.get('contact_number')
        avatar = request.FILES.get('avatar')
        rfid_card_number = request.POST.get('rfid_card_number')

        # Create or get the StudentClassification instance
        classification = StudentClassification.objects.get(id=classification_id)

        # Create the student
        student = Student.objects.create(
            classification=classification,
            student_id=student_id,
            first_name=first_name,
            last_name=last_name,
            email=email,
            address=address,
            contact_number=contact_number,
            avatar=avatar
        )

        # Create or get the RFIDCard instance
        rfid_card, created = RFIDCard.objects.get_or_create(
            card_number=rfid_card_number,
            defaults={'student': student}
        )

        # Add the student to the schedule based on classification
        schedule = SubjectSchedule.objects.filter(classification=classification).first()
        if schedule:
            schedule.students.add(student)

        return JsonResponse({'message': 'Student added successfully'})

    # Retrieve classifications to pass to the template
    return redirect('students')
