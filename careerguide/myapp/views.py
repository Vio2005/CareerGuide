from turtle import position
from urllib import request

from django.shortcuts import render,redirect
from .models import *
from django.contrib import messages
from django.core.paginator import Paginator

from django.contrib.auth import logout,login,authenticate
from django.contrib.auth.models import User
from django.views.generic import View
from django.db.models import Count






def homeview(request):
    jobs = Job.objects.all().order_by('-posted_date')

    cities = City.objects.all()
    positions = Position.objects.all()

    position = request.GET.get('position')
    city = request.GET.get('city')
    job_type = request.GET.get('job_type')

    if position:
        jobs = jobs.filter(position__position_name__icontains=position)

    if city:
        jobs = jobs.filter(city__city_name__icontains=city)

    if job_type:
        jobs = jobs.filter(job_type=job_type)

    employee = None

    employee_id = request.session.get('employee_id')

    if employee_id:
        employee = Employee.objects.get(id=employee_id)
    paginator = Paginator(jobs, 5)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    jobcount=Job.objects.count()
    companycount=Job.objects.count()
    fillcount=JobApplication.objects.filter(status='Accepted').count()
    employeecount= JobApplication.objects.values('employee').distinct().count()

    context = {
        'job': jobs,
        'cities': cities,
        'positions': positions,
        'position': position,
        'city': city,
        'job_type': job_type,
        'employee': employee,
        'page_obj':page_obj,
        'jobcount':jobcount,
        'companycount':companycount,
        'fillcount':fillcount,
        'employeecount':employeecount
    }

    return render(request, 'index.html', context)
def jobdetail(request, id):
    job = Job.objects.get(id=id)

    employee_id = request.session.get('employee_id')
    employee = None
    save = False
    apply = False   # add this

    if employee_id:
        employee = Employee.objects.get(id=employee_id)

        save = SaveJob.objects.filter(
            employee=employee,
            job=job
        ).exists()

        apply = JobApplication.objects.filter(
            employee=employee,
            job=job
        ).exists()

    apply_modal = request.session.pop("open_apply_modal", False)

    context = {
        "data": job,
        "employee": employee,
        "save": save,
        "apply": apply,
        "apply_modal": apply_modal
    }

    return render(request, 'jobdetail.html', context)


# Employee Register
def employee_register(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")

        if Employee.objects.filter(email=email).exists():
            return render(request, "employee_register.html", {
                "error": "Email already exists."
            })

        Employee.objects.create(
            username=username,
            email=email,
            password=password      # For a real application, hash the password.
        )

        return redirect("employeelogin")

    return render(request, "employee_register.html")


# Employee Login
def employee_login(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        try:
            employee = Employee.objects.get(
                email=email,
                password=password
            )

            request.session["employee_id"] = employee.id
            request.session["employee_name"] = employee.username

            return redirect("homeview")

        except Employee.DoesNotExist:
            return render(request, "employee_login.html", {
                "error": "Invalid email or password."
            })

    return render(request, "employee_login.html")


# Employee Logout
def employee_logout(request):
    request.session.flush()
    return redirect("employeelogin")

def employee_profile(request):

    employee_id = request.session.get('employee_id')

    if not employee_id:
        return redirect('employeelogin')

    employee = Employee.objects.get(id=employee_id)


    if request.method == "POST":

        full_name = request.POST.get('full_name')
        phone = request.POST.get('phone')
        gender = request.POST.get('gender')
        date_of_birth = request.POST.get('date_of_birth')
        address = request.POST.get('address')
        summary = request.POST.get('summary')
        profile_image = request.FILES.get('profile_image')


        # Employee Profile
        profile, created = EmployeeProfile.objects.update_or_create(
            employee=employee,
            defaults={
                'full_name': full_name,
                'phone': phone,
                'gender': gender,
                'date_of_birth': date_of_birth,
                'address': address,
                'summary': summary,
            }
        )

        if profile_image:
            profile.profile_image = profile_image
            profile.save()



        # Education (Update instead of creating duplicate)
        Education.objects.update_or_create(
            employee=employee,
            defaults={
                'institution': request.POST.get('institution'),
                'degree': request.POST.get('degree'),
                'field_of_study': request.POST.get('field_of_study'),
                'start_year': request.POST.get('start_year'),
                'end_year': request.POST.get('end_year'),
            }
        )


        # Experience (Update instead of creating duplicate)
        Experience.objects.update_or_create(
            employee=employee,
            defaults={
                'company_name': request.POST.get('company_name'),
                'position': request.POST.get('position'),
                'start_date': request.POST.get('start_date'),
                'end_date': request.POST.get('end_date'),
                'description': request.POST.get('description'),
            }
        )


        # Skill (Update instead of creating duplicate)
        Skill.objects.update_or_create(
            employee=employee,
            defaults={
                'skill_name': request.POST.get('skill_name'),
                'proficiency': request.POST.get('skill_level'),
            }
        )


        job_id = request.session.pop("apply_job_id", None)

        if job_id:
            request.session["open_apply_modal"] = True
            return redirect("jobdetail", id=job_id)

        return redirect('employeeprofile')



    try:
        profile = EmployeeProfile.objects.get(employee=employee)

        return render(
            request,
            'employee_profile_detail.html',
            {
                'profile': profile,
                'employee': employee,
            }
        )


    except EmployeeProfile.DoesNotExist:

        return render(
            request,
            'employee_profile.html'
        )

def applyjob(request, id):

    employee_id = request.session.get('employee_id')

    if not employee_id:
        return redirect('employeelogin')

    employee = Employee.objects.get(id=employee_id)

    if not EmployeeProfile.objects.filter(employee=employee).exists():
        return redirect('employeeprofile')

    job = Job.objects.get(id=id)

    if request.method == "POST":

        if JobApplication.objects.filter(
            employee=employee,
            job=job
        ).exists():

            
            return redirect('jobdetail', id=id)

        cover_letter = request.POST.get("cover_letter")

        

        JobApplication.objects.create(
            employee=employee,
            job=job,
            cover_letter=cover_letter,
            status="Pending"
        )

        
    return redirect('jobdetail', id=id)

def check_apply(request, id):

    employee_id = request.session.get("employee_id")

    if not employee_id:
        return redirect("employeelogin")

    employee = Employee.objects.get(id=employee_id)

    if not EmployeeProfile.objects.filter(employee=employee).exists():

        # remember which job the user wanted to apply
        request.session["apply_job_id"] = id

        return redirect("employeeprofile")


    # profile exists, open modal
    request.session["open_apply_modal"] = True

    return redirect("jobdetail", id=id)

def company_register(request):
    if request.method == "POST":

        company_name = request.POST.get("company_name")
        email = request.POST.get("email")
        password = request.POST.get("password")

        # Required fields
        phone = request.POST.get("phone")
        description = request.POST.get("description")
        website = request.POST.get("website")
        address = request.POST.get("address")

        # Optional fields
        tagline = request.POST.get("tagline") or None
        facebook = request.POST.get("facebook") or None
        twitter = request.POST.get("twitter") or None
        linkedin = request.POST.get("linkedin") or None

        profile_image = request.FILES.get("profile_image")


        if Company.objects.filter(email=email).exists():

            return render(request, "company_register.html", {
                "error": "Email already exists."
            })


        Company.objects.create(

            company_name=company_name,
            email=email,
            password=password,

            phone=phone,
            description=description,
            website=website,
            address=address,

            tagline=tagline,
            facebook=facebook,
            twitter=twitter,
            linkedin=linkedin,

            profile_image=profile_image
        )


        return redirect("companylogin")


    return render(request, "company_register.html")

# Company Login
def company_login(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        try:
            company = Company.objects.get(
                email=email,
                password=password
            )

            request.session["company_id"] = company.id
            request.session["company_name"] = company.company_name

            return redirect("company_index")

        except Company.DoesNotExist:
            return render(request, "company_login.html", {
                "error": "Invalid email or password."
            })

    return render(request, "company_login.html")


# Company Logout
def company_logout(request):
    request.session.flush()
    return redirect("companylogin")

def companyview(request):
    company_id = request.session.get('company_id')

    if not company_id:
        return redirect('companylogin')

    company = Company.objects.get(id=company_id)

    job = Job.objects.filter(company=company)
    job_applications = JobApplication.objects.filter(job__company=company).order_by('-id')[:5]
    job_posted=Job.objects.filter(company=company).count()
    applicant = JobApplication.objects.filter(
    job__company=company
).values('employee').distinct().count()

    context = {
        'company': company,
        'job': job,
        'job_applications': job_applications,
        'job_posted' : job_posted,
        'applicant' : applicant
    }

    return render(request, 'company_index.html', context)


def edit_employee_profile(request, id):

    employee = Employee.objects.get(id=id)

    profile = EmployeeProfile.objects.get(employee=employee)

    if request.method == "POST":

        # Update Employee Profile
        profile.full_name = request.POST.get('full_name')
        profile.phone = request.POST.get('phone')
        profile.gender = request.POST.get('gender')
        profile.date_of_birth = request.POST.get('date_of_birth')
        profile.address = request.POST.get('address')
        profile.summary = request.POST.get('summary')

        if request.FILES.get('profile_image'):
            profile.profile_image = request.FILES.get('profile_image')

        profile.save()


        # Update Education
        Education.objects.filter(employee=employee).delete()

        Education.objects.create(
            employee=employee,
            institution=request.POST.get('institution'),
            degree=request.POST.get('degree'),
            field_of_study=request.POST.get('field_of_study'),
            start_year=request.POST.get('start_year'),
            end_year=request.POST.get('end_year'),
        )


        # Update Experience
        Experience.objects.filter(employee=employee).delete()

        Experience.objects.create(
            employee=employee,
            company_name=request.POST.get('company_name'),
            position=request.POST.get('position'),
            start_date=request.POST.get('start_date'),
            end_date=request.POST.get('end_date'),
            description=request.POST.get('description'),
        )


        # Update Skill
        Skill.objects.filter(employee=employee).delete()

        Skill.objects.create(
            employee=employee,
            skill_name=request.POST.get('skill_name'),
            proficiency=request.POST.get('skill_level'),
        )


        return redirect('employeeprofile')


    education = Education.objects.filter(employee=employee).first()
    experience = Experience.objects.filter(employee=employee).first()
    skill = Skill.objects.filter(employee=employee).first()


    return render(
        request,
        'edit_employee_profile.html',
        {
            'employee': employee,
            'profile': profile,
            'education': education,
            'experience': experience,
            'skill': skill,
        }
    )
def post(request):
    company_id = request.session.get('company_id')

    if not company_id:
        return redirect('companylogin')

    company = Company.objects.get(id=company_id)

    if request.method == "POST":
        city_obj, _ = City.objects.get_or_create(
            city_name=request.POST.get("city")
        )

        position_obj, _ = Position.objects.get_or_create(
            position_name=request.POST.get("position")
        )

        Job.objects.create(
            company=company,
            job_type=request.POST.get("job_type"),
            description=request.POST.get("description"),
            vacancy=request.POST.get("vacancy"),
            salary=request.POST.get("salary"),
            requirements=request.POST.get("requirements"),
            location=request.POST.get("location"),
            city=city_obj,
            position=position_obj,
        )

        messages.success(request, "Job posted successfully!")
        return redirect("company_index")

    return render(request, "company_post.html", {"company": company})
def company_profile(request,id):
    

    company = Company.objects.get(id=id)

    context = {
        'company': company,
    }

    return render(request, 'company_profile.html', context)

def edit_company_profile(request, id):
    company = Company.objects.get(id=id)

    if request.method == "POST":

        # Update Company Profile
        company.company_name = request.POST.get('company_name')
        company.email = request.POST.get('email') or company.email
        company.phone = request.POST.get('phone')
        company.description = request.POST.get('description')
        company.website = request.POST.get('website')
        company.address = request.POST.get('address')
        company.tagline = request.POST.get('tagline')
        company.facebook = request.POST.get('facebook')
        company.twitter = request.POST.get('twitter')
        company.linkedin = request.POST.get('linkedin')

        if request.FILES.get('profile_image'):
            company.profile_image = request.FILES.get('profile_image')

        company.save()

        return redirect('companyprofile', id=company.id)

    return render(
        request,
        'edit_company_profile.html',
        {
            'company': company,
        }
    )




def company_post_view(request, id):

    company = Company.objects.get(id=id)

    jobs = Job.objects.filter(company=company)

    paginator = Paginator(jobs, 5)  # show 5 jobs per page

    page_number = request.GET.get('page')

    page_obj = paginator.get_page(page_number)

    return render(request, 'company_post_view.html', {
        'company': company,
        'jobs': page_obj,
        'page_obj': page_obj,
    })

def edit_post(request, id):
    job = Job.objects.get(id=id)

    if request.method == "POST":

        # Update Job Post
        job.job_type = request.POST.get('job_type')
        job.description = request.POST.get('description')
        job.vacancy = request.POST.get('vacancy')
        job.salary = request.POST.get('salary')
        job.requirements = request.POST.get('requirements')
        job.location = request.POST.get('location')

        city_name = request.POST.get('city')
        position_name = request.POST.get('position')

        city_obj, created = City.objects.get_or_create(city_name=city_name)
        position_obj, created = Position.objects.get_or_create(position_name=position_name)

        job.city = city_obj
        job.position = position_obj

        job.save()

        return redirect('companypostview', id=job.company.id)

    return render(
        request,
        'edit_post.html',
        {
            'job': job,
            'city':job.city,
            'position':job.position,
        }
    )

def view_apply(request, id):
    app = JobApplication.objects.get(id=id)
    if request.method == "POST":

      
        app.status = request.POST.get('status')
        app.save()
        return redirect('companyview')
    context = {
        'app': app,
    }
    return render(request, 'view_apply.html', context)

def deletepost(request,id):
    job=Job.objects.filter(id=id).delete()
    return redirect('companypostview', id=job.company.id)

def career_quiz(request):

    if request.method == "POST":

        answers = request.POST.dict()

        # Save temporarily in session
        request.session['quiz_answers'] = answers


        # Calculate recommendation
        result = calculate_career(answers)


        return render(
            request,
            "career_result.html",
            {
                "best_match": result[0],
                "similar": result[1:]
            }
        )


    return render(
        request,
        "career_quiz.html"
    )


from .quiz_questions import QUESTIONS
from .career_data import CAREERS


def career_quiz(request):
    employee_id = request.session.get(
            "employee_id"
        )

    employee=Employee.objects.get(id=employee_id)
    if request.method == "POST":

        answers=[]

        for i in range(1,26):

            answer=request.POST.get(
                f"q{i}"
            )

            answers.append(answer)


        result = calculate_match(
            answers
        )


        employee_id = request.session.get(
            "employee_id"
        )



        # Only save after employee login

        if employee_id:

            EmployeeCareerResult.objects.create(

                employee_id=employee_id,

                best_match=result["best"],

                similar_matches=
                ", ".join(result["similar"])

            )
        context = {
    **result,
    "employee": employee
}

        return render(
            request,
            "career_result.html",
            context
        )


    return render(
        request,
        "career_quiz.html",
        {
            "questions":QUESTIONS,
            'employee':employee
        }
    )




def calculate_match(answers):

    career_scores={}


    for career, data in CAREERS.items():

        score=0


        for answer in answers:

            if answer in data["keywords"]:

                score += 1


        career_scores[career]=score



    result=sorted(
        career_scores.items(),
        key=lambda x:x[1],
        reverse=True
    )


    return {

        "best":result[0][0],

        "similar":[

            result[1][0],
            result[2][0],
            result[3][0]

        ]

    }

def last_result(request):

    employee_id = request.session.get('employee_id')

    employee = Employee.objects.get(id=employee_id)

    latest_result = EmployeeCareerResult.objects.filter(
        employee=employee
    ).order_by('-created_at').first()


    context = {
        'best': latest_result.best_match if latest_result else None,
        'similar': latest_result.similar_matches if latest_result else [],
    }

    return render(request, 'last_result.html', context)

def result_history(request):
    employee_id=request.session.get('employee_id')
    if not employee_id:
        return redirect('employeelogin')
    employee=Employee.objects.get(id=employee_id)
    history = EmployeeCareerResult.objects.filter(employee=employee).order_by('-created_at')

    return render(request, 'result_history.html', {
    'history': history,
    'employee':employee
})



def employeelist(request):
    employee=Employee.objects.all()
    paginator = Paginator(employee, 5) 

    page_number = request.GET.get("page")
    obj = paginator.get_page(page_number)
    ecount=Employee.objects.count()
    pending=JobApplication.objects.filter(
        status='Pending'
    ).count()
    accept=JobApplication.objects.filter(
        status='Accepted'
    ).count()
    reject=JobApplication.objects.filter(
        status='Reject'
    ).count()
    short=JobApplication.objects.filter(
        status='Shortlisted'
    ).count()
    app = JobApplication.objects.values('employee').distinct().count()

    context={'employee':employee,'obj':obj , 'ecount' : ecount,
             'pending':pending, 'accept':accept, 'reject':reject,
             'app':app, 'short':short}
    return render(request,'employee_list.html',context)

def companylist(request):
    company=Company.objects.all()
    paginator = Paginator(company, 5) 

    page_number = request.GET.get("page")
    obj = paginator.get_page(page_number)
    count=Company.objects.count()
    
    context={'count':count,'company':company, 'obj':obj }
    return render(request,'company_list.html',context)

def profile(request):
    user = request.user
    
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')

        # Basic validation (optional)
        if not username or not email:
            messages.error(request, 'Username and email are required.')
            return render(request, 'profile.html', {'user_obj': user})

        # Update user object
        user.username = username
        user.email = email
        user.first_name = first_name
        user.last_name = last_name
        user.save()

        messages.success(request, 'Profile updated successfully.')
        return redirect('profile')
    context={'user':user, 'user_obj': user}
    
    return render(request,'profile.html',context)


def application(request):
    app = JobApplication.objects.select_related(
        'employee',
        'employee__employeeprofile',
        'job',
        'job__company',
        'job__position'
    ).all()

    paginator = Paginator(app, 5)

    page_number = request.GET.get("page")
    obj = paginator.get_page(page_number)

    count = JobApplication.objects.count()

    context = {
        'count': count,
        'obj': obj
    }

    return render(request, 'application.html', context)

import json

from django.db.models.functions import TruncMonth
from datetime import timedelta
from django.utils import timezone
from django.db.models.functions import TruncDate



def chart(request):

    # Popular Job Positions
    popular_positions = (
        Position.objects
        .annotate(
            application_count=Count('job__jobapplication')
        )
        .order_by('-application_count')[:5]
    )


    position_labels = list(
        popular_positions.values_list(
            'position_name',
            flat=True
        )
    )


    position_data = list(
        popular_positions.values_list(
            'application_count',
            flat=True
        )
    )



    # Monthly Applications
    monthly_applications = (
        JobApplication.objects
        .annotate(
            month=TruncMonth('applied_date')
        )
        .values('month')
        .annotate(
            total=Count('id')
        )
        .order_by('month')
    )


    month_labels = [
        item['month'].strftime('%b')
        for item in monthly_applications
    ]


    month_data = [
        item['total']
        for item in monthly_applications
    ]




    # Last 30 Days Applications
    today = timezone.now().date()

    start_date = today - timedelta(days=29)


    daily_applications = (
        JobApplication.objects
        .filter(
            applied_date__date__gte=start_date
        )
        .annotate(
            day=TruncDate('applied_date')
        )
        .values('day')
        .annotate(
            total=Count('id')
        )
        .order_by('day')
    )


    daily_counts = {
        item['day']: item['total']
        for item in daily_applications
    }


    daily_labels = []

    daily_data = []


    for i in range(30):

        day = start_date + timedelta(days=i)

        daily_labels.append(
            day.strftime('%d %b')
        )

        daily_data.append(
            daily_counts.get(day, 0)
        )

    # Application Status Chart

    status_applications = (
    JobApplication.objects
    .values('status')
    .annotate(
        total=Count('id')
    )
    .order_by('status')
)


    status_labels = [
    item['status']
    for item in status_applications
]


    status_data = [
    item['total']
    for item in status_applications
]



    context = {

    'position_labels': json.dumps(position_labels),

    'position_data': json.dumps(position_data),

    'month_labels': json.dumps(month_labels),

    'month_data': json.dumps(month_data),

    'daily_labels': json.dumps(daily_labels),

    'daily_data': json.dumps(daily_data),

    'status_labels': json.dumps(status_labels),

    'status_data': json.dumps(status_data),

}


    return render(
        request,
        'charts.html',
        context
    )
def register_view(request):
    if request.method=="POST":
        username=request.POST['username']
        email=request.POST['email']
        password=request.POST['password']
        firstname=request.POST['fname']
        lastname=request.POST['lname']
        user=User.objects.filter(username=username)
        if user.exists():
            return redirect('/register')
        else:
            usr=User.objects.create_user(username=username,email=email,first_name=firstname,last_name=lastname)
            usr.set_password(password)
            usr.is_superuser=True
            usr.is_staff=True
            usr.save()

            return redirect ('/login')
    else:
        return render(request,'register.html')



def loginview(request):
    if request.method == 'POST':
    
        usr = request.POST.get('username')
        pas = request.POST.get('password')
        usr_auth=authenticate(username=usr,password=pas)
        if usr_auth:
            login(request, usr_auth)
            return redirect('/adminview/')
        else:
            return redirect('/login')
    else:

        return render(request, 'login.html')
    
def logoutview(request):
    logout(request)
    return redirect('/login/')

class LoginRequire(object):
    def dispatch(self,request,*arg,**kwargs):
        if request.user.is_authenticated and request.user.is_staff:
            pass
        else:
            return redirect('/login')
        return super().dispatch(request,*arg,**kwargs)

class AdminView(LoginRequire, View):
    def get(self, request):
        employee = Employee.objects.count()
        company = Company.objects.count()

        apply = JobApplication.objects.filter(
        status='Accepted'
        ).count()

        vacant = Job.objects.filter(
        is_active=True
        ).count()

        recent_applications = JobApplication.objects.select_related(
        'employee',
        'job',
        'job__company'
        ).order_by('applied_date')[:5]


        top_companies = (
    Company.objects
    .annotate(
        jobs_posted=Count('job', distinct=True),
        applications_received=Count('job__jobapplication')
    )
    .order_by('-applications_received')[:5]
)

        context = {
        'employee': employee,
        'company': company,
        'apply': apply,
        'vacant': vacant,
        'recent_applications': recent_applications,
        'top_companies': top_companies,
        
    }

        return render(request, 'admin_index.html', context)
    
def employee_detail(request, id):

    employee = Employee.objects.get(id=id)

    skills = Skill.objects.filter(employee=employee)
    educations = Education.objects.filter(employee=employee)
    experiences = Experience.objects.filter(employee=employee)

    applications = JobApplication.objects.filter(
        employee=employee
    )

    application_count = applications.count()


    try:
        career_result = EmployeeCareerResult.objects.get(
            employee=employee
        )
    except EmployeeCareerResult.DoesNotExist:
        career_result = None
    
    paginator = Paginator(applications, 3) 

    page_number = request.GET.get("page")
    obj = paginator.get_page(page_number)



    context = {

        "employee": employee,

        "skills": skills,

        "educations": educations,

        "experiences": experiences,

        "application_count": application_count,

        "career_result": career_result,
        "obj": obj,

    }


    return render(
        request,
        "employee_detail.html",
        context
    )

def delete_employee(request,id):
    employee=Employee.objects.filter(id=id).delete()
    return redirect('employeelist')

def delete_company(request,id):
    company=Company.objects.filter(id=id).delete()
    return redirect('companylist')



def company_detail(request, id):

    company = Company.objects.get(
        id=id
    )


    # Jobs posted by this company

    jobs = Job.objects.filter(
        company=company
    )



    # Count total jobs

    job_count = jobs.count()
    paginator = Paginator(jobs, 3) 

    page_number = request.GET.get("page")
    obj = paginator.get_page(page_number)


    # Application status counts

    accepted_count = JobApplication.objects.filter(
        job__company=company,
        status="Accepted"
    ).count()



    rejected_count = JobApplication.objects.filter(
        job__company=company,
        status="Rejected"
    ).count()



    pending_count = JobApplication.objects.filter(
        job__company=company,
        status="Pending"
    ).count()



    shortlisted_count = JobApplication.objects.filter(
        job__company=company,
        status="Shortlisted"
    ).count()



    context = {

        "company": company,

        "obj": obj,

        "job_count": job_count,

        "accepted_count": accepted_count,

        "rejected_count": rejected_count,

        "pending_count": pending_count,

        "shortlisted_count": shortlisted_count,

    }


    return render(
        request,
        "company_detail.html",
        context
    )
def company_list_view(request):
    employee_id = request.session.get('employee_id')

    if employee_id:
        employee = Employee.objects.get(id=employee_id)
    company = Company.objects.all()
    paginator = Paginator(company, 3)
    page_number = request.GET.get("page")
    companies = paginator.get_page(page_number)

    context = {
        'companies': companies,
        'employee' :employee,
        'company':company
        
    }

    return render(request, 'company_list_view.html', context)

def applied_job(request):
    employee_id = request.session.get("employee_id")
    

    if not employee_id:
        return redirect("employeelogin")

    employee = Employee.objects.get(id=employee_id)

    applications = JobApplication.objects.filter(employee=employee).order_by('-applied_date')
   
    paginator = Paginator(applications, 3)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "applied_job.html", {
        "applications": applications,
        "employee": employee,
        'page_obj':page_obj
    })

from django.db.models.functions import ExtractMonth

def hiring_analytics(request):

    company_id = request.session.get('company_id')

    company = Company.objects.get(id=company_id)
    # Total jobs posted by company
    total_jobs = Job.objects.filter(
        company=company
    ).count()


    # All applications for company's jobs
    applications = JobApplication.objects.filter(
        job__company=company
    )


    total_applications = applications.count()


    # Change status field according to your model
    hired = applications.filter(
        status="Accepted"
    ).count()


    pending = applications.filter(
        status="Pending"
    ).count()

    short = applications.filter(
        status="Shortlisted"
    ).count()


    reject = applications.filter(
        status="Rejected"
    ).count()


    # Monthly application data
    monthly_applications = (
        applications
        .annotate(month=ExtractMonth('applied_date'))
        .values('month')
        .annotate(total=Count('id'))
        .order_by('month')
    )


    months = []
    totals = []

    for item in monthly_applications:
        months.append(
            item['month']
        )
        totals.append(
            item['total']
        )


    context = {
        'company': company,
        'total_jobs': total_jobs,
        'total_applications': total_applications,
        'hired': hired,
        'pending': pending,
        'months': months,
        'totals': totals,
        'short' : short,
        'reject' :reject,
    }


    return render(
        request,
        'hiring_analytics.html',
        context
    )

def savejob(request, id):
    employee = Employee.objects.get(id=request.session['employee_id'])
    job = Job.objects.get(id=id)

    saved = SaveJob.objects.filter(employee=employee, job=job)

    if saved.exists():
        saved.delete()
        messages.success(request, "Removed from saved jobs")
    else:
        SaveJob.objects.create(employee=employee, job=job)
        messages.success(request, "Saved job successfully!")

    return redirect('jobdetail', id=id)

from django.shortcuts import render, get_object_or_404


def employee_profile_view(request, id):

    # Get employee
    employee = get_object_or_404(Employee, id=id)

    # Get employee profile (OneToOne)
    profile = EmployeeProfile.objects.filter(employee=employee).first()

    # Get all related information
    education = Education.objects.filter(employee=employee)
    experience = Experience.objects.filter(employee=employee)
    skills = Skill.objects.filter(employee=employee)


    context = {
        'employee': employee,
        'profile': profile,
        'education': education,
        'experience': experience,
        'skills': skills,
    }


    return render(
        request,
        'employee_profile_view.html',
        context
    )

def company_candidates(request):

    company_id = request.session.get('company_id')

    company = Company.objects.get(id=company_id)

    job_applications = JobApplication.objects.filter(
        job__company=company
    ).select_related(
        'employee',
        'job'
    )

    return render(
        request,
        'company_candidates.html',
        {
            'company': company,
            'job_applications': job_applications,
        }
    )
