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



def intro(request):
    jobcount=Job.objects.count()
    companycount=Company.objects.count()
    fillcount=JobApplication.objects.filter(status='Accepted').count()
    employeecount= JobApplication.objects.values('employee').distinct().count()
    context = {
        
        'jobcount':jobcount,
        'companycount':companycount,
        'fillcount':fillcount,
        'employeecount':employeecount
    }

    return render(request, 'intro.html', context)


def homeview(request):
    jobs = Job.objects.filter(is_active=True).order_by('-posted_date')
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
    jobcount = Job.objects.filter(is_active=True).count()   
    companycount=Company.objects.count()
    fillcount=JobApplication.objects.filter(status='Accepted').count()
    employeecount= JobApplication.objects.values('employee').distinct().count()
    popular_positions = (
    Position.objects.annotate(
        total_applications=Count("job__jobapplication")
    )
    .order_by("-total_applications")[:3]   
)

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
        'employeecount':employeecount,
        'popular_positions':popular_positions,
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


    employee = Employee.objects.get(
        id=employee_id
    )



    if request.method == "POST":


        # =========================
        # EMPLOYEE PROFILE
        # =========================

        full_name = request.POST.get('full_name')
        phone = request.POST.get('phone')
        gender = request.POST.get('gender')
        date_of_birth = request.POST.get('date_of_birth')
        address = request.POST.get('address')
        summary = request.POST.get('summary')

        profile_image = request.FILES.get(
            'profile_image'
        )



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





        # =========================
        # EDUCATION MULTIPLE SAVE
        # =========================


        Education.objects.filter(
            employee=employee
        ).delete()



        institutions = request.POST.getlist(
            'institution[]'
        )

        degrees = request.POST.getlist(
            'degree[]'
        )

        fields = request.POST.getlist(
            'field_of_study[]'
        )

        start_years = request.POST.getlist(
            'start_year[]'
        )

        end_years = request.POST.getlist(
            'end_year[]'
        )



        for i in range(len(institutions)):


            if institutions[i].strip():


                Education.objects.create(
                    employee=employee,
                    institution=institutions[i],
                    degree=degrees[i] if i < len(degrees) else "",
                    field_of_study=fields[i] if i < len(fields) else "",
                    start_year=start_years[i] if i < len(start_years) and start_years[i] else None,
                    end_year=end_years[i] if i < len(end_years) and end_years[i] else None,
                )







        # =========================
        # EXPERIENCE MULTIPLE SAVE
        # =========================


        Experience.objects.filter(
            employee=employee
        ).delete()



        company_names = request.POST.getlist(
            'company_name[]'
        )

        positions = request.POST.getlist(
            'position[]'
        )

        start_dates = request.POST.getlist(
            'start_date[]'
        )

        end_dates = request.POST.getlist(
            'end_date[]'
        )

        descriptions = request.POST.getlist(
            'description[]'
        )




        for i in range(len(company_names)):


            if company_names[i].strip():


                Experience.objects.create(
                    employee=employee,

                    company_name=company_names[i],

                    position=positions[i] 
                    if i < len(positions) 
                    else "",

                    start_date=start_dates[i]
                    if i < len(start_dates) and start_dates[i]
                    else None,

                    end_date=end_dates[i]
                    if i < len(end_dates) and end_dates[i]
                    else None,

                    description=descriptions[i]
                    if i < len(descriptions)
                    else "",
                )








        # =========================
        # SKILL MULTIPLE SAVE
        # =========================


        Skill.objects.filter(
            employee=employee
        ).delete()



        skill_names = request.POST.getlist(
            'skill_name[]'
        )


        skill_levels = request.POST.getlist(
            'skill_level[]'
        )




        for i in range(len(skill_names)):


            if skill_names[i].strip():


                Skill.objects.create(

                    employee=employee,

                    skill_name=skill_names[i],

                    proficiency=skill_levels[i]
                    if i < len(skill_levels)
                    else "Beginner"

                )





        # =========================
        # RETURN TO APPLY JOB
        # =========================


        job_id = request.session.pop(
            "apply_job_id",
            None
        )


        if job_id:

            request.session["open_apply_modal"] = True

            return redirect(
                "jobdetail",
                id=job_id
            )



        return redirect(
            'employeeprofile'
        )






    # =========================
    # CHECK EXISTING PROFILE
    # =========================


    try:


        profile = EmployeeProfile.objects.get(
            employee=employee
        )


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
            'employee_profile.html',
            {
                'employee': employee
            }
        )
def applyjob(request, id):

    employee_id = request.session.get("employee_id")

    if not employee_id:
        return redirect("employeelogin")

    employee = Employee.objects.get(id=employee_id)

    if not EmployeeProfile.objects.filter(employee=employee).exists():
        return redirect("employeeprofile")

    job = get_object_or_404(Job, id=id)

    # Prevent applying to closed jobs
    if not job.is_active:
        messages.error(request, "This job is no longer accepting applications.")
        return redirect("jobdetail", id=id)

    if request.method == "POST":

        if JobApplication.objects.filter(
            employee=employee,
            job=job
        ).exists():
            return redirect("jobdetail", id=id)

        cover_letter = request.POST.get("cover_letter")

        JobApplication.objects.create(
            employee=employee,
            job=job,
            cover_letter=cover_letter,
            status="Pending"
        )

    return redirect("jobdetail", id=id)
from django.shortcuts import get_object_or_404

def check_apply(request, id):
    job = get_object_or_404(Job, id=id)

    if not job.is_active:
        messages.error(request, "This job is no longer accepting applications.")
        return redirect("jobdetail", id=job.id)

    employee_id = request.session.get("employee_id")

    if not employee_id:
        return redirect("employeelogin")

    employee = Employee.objects.get(id=employee_id)

    if not EmployeeProfile.objects.filter(employee=employee).exists():
        request.session["apply_job_id"] = id
        return redirect("employeeprofile")

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

    employee = get_object_or_404(Employee, id=id)

    profile = get_object_or_404(
        EmployeeProfile,
        employee=employee
    )


    if request.method == "POST":


        # =========================
        # UPDATE PROFILE
        # =========================

        profile.full_name = request.POST.get('full_name')
        profile.phone = request.POST.get('phone')
        profile.gender = request.POST.get('gender')
        profile.date_of_birth = request.POST.get('date_of_birth')
        profile.address = request.POST.get('address')
        profile.summary = request.POST.get('summary')


        if request.FILES.get('profile_image'):
            profile.profile_image = request.FILES.get('profile_image')


        profile.save()



        # =========================
        # EDUCATION
        # =========================

        Education.objects.filter(
            employee=employee
        ).delete()


        institutions = request.POST.getlist(
            'institution[]'
        )

        degrees = request.POST.getlist(
            'degree[]'
        )

        fields = request.POST.getlist(
            'field_of_study[]'
        )

        start_years = request.POST.getlist(
            'start_year[]'
        )

        end_years = request.POST.getlist(
            'end_year[]'
        )


        for i in range(len(institutions)):

            if institutions[i]:

                Education.objects.create(
                    employee=employee,
                    institution=institutions[i],
                    degree=degrees[i] if i < len(degrees) else "",
                    field_of_study=fields[i] if i < len(fields) else "",
                    start_year=start_years[i] if i < len(start_years) and start_years[i] else None,
                    end_year=end_years[i] if i < len(end_years) and end_years[i] else None,
                )




        # =========================
        # EXPERIENCE
        # =========================

        Experience.objects.filter(
            employee=employee
        ).delete()


        company_names = request.POST.getlist(
            'company_name[]'
        )

        positions = request.POST.getlist(
            'position[]'
        )

        start_dates = request.POST.getlist(
            'start_date[]'
        )

        end_dates = request.POST.getlist(
            'end_date[]'
        )

        descriptions = request.POST.getlist(
            'description[]'
        )


        for i in range(len(company_names)):

            if company_names[i]:

                Experience.objects.create(
                    employee=employee,
                    company_name=company_names[i],
                    position=positions[i] if i < len(positions) else "",
                    start_date=start_dates[i] if i < len(start_dates) and start_dates[i] else None,
                    end_date=end_dates[i] if i < len(end_dates) and end_dates[i] else None,
                    description=descriptions[i] if i < len(descriptions) else "",
                )





        # =========================
        # SKILL
        # =========================

        Skill.objects.filter(
            employee=employee
        ).delete()


        skill_names = request.POST.getlist(
            'skill_name[]'
        )

        skill_levels = request.POST.getlist(
            'skill_level[]'
        )


        for i in range(len(skill_names)):

            if skill_names[i]:

                Skill.objects.create(
                    employee=employee,
                    skill_name=skill_names[i],
                    proficiency=(
                        skill_levels[i]
                        if i < len(skill_levels)
                        else "Beginner"
                    )
                )



        return redirect(
            'employeeprofile'
        )




    # =========================
    # LOAD EXISTING DATA
    # =========================


    educations = Education.objects.filter(
        employee=employee
    )


    experiences = Experience.objects.filter(
        employee=employee
    )


    skills = Skill.objects.filter(
        employee=employee
    )



    return render(
        request,
        'edit_employee_profile.html',
        {
            'employee': employee,
            'profile': profile,
            'educations': educations,
            'experiences': experiences,
            'skills': skills,
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
        return redirect("companypostview",id=company.id)

    return render(request, "company_post.html", {"company": company})
def view_company_detail(request,id):
    

    company = Company.objects.get(id=id)

    context = {
        'company': company,
    }

    return render(request, 'view_company_detail.html', context)

def company_profile(request,id):
    company_id = request.session.get('company_id')
    if not company_id:
                return redirect('companylogin')

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




from django.shortcuts import get_object_or_404, render
from django.core.paginator import Paginator

def company_post_view(request, id):
    company_id = request.session.get('company_id')
    
    if not company_id:
            return redirect('companylogin')
    company = get_object_or_404(Company, id=id)

    # Get all jobs for this company
    jobs = Job.objects.filter(company=company)

    # Filter by status
    status = request.GET.get("status")

    if status == "open":
        jobs = jobs.filter(is_active=True)
    elif status == "closed":
        jobs = jobs.filter(is_active=False)

    jobs = jobs.order_by("-posted_date")   # or "-id"

    paginator = Paginator(jobs, 5)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "company_post_view.html", {
        "company": company,
        "jobs": page_obj,
        "page_obj": page_obj,
        "status": status,
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

def deletepost(request, id):

    job = Job.objects.get(id=id)

    company_id = job.company.id

    job.delete()

    return redirect('companypostview', id=company_id)

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

    employee = None

    employee_id = request.session.get("employee_id")

    if employee_id:
        employee = Employee.objects.filter(id=employee_id).first()


    if request.method == "POST":

        answers = []

        for i in range(1, 26):
            answer = request.POST.get(f"q{i}")
            answers.append(answer)


        result = calculate_match(answers)


        # Save result only if employee is logged in
        if employee_id and employee:

            EmployeeCareerResult.objects.create(
                employee=employee,
                best_match=result["best"],
                similar_matches=", ".join(result["similar"])
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
            "questions": QUESTIONS,
            "employee": employee
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
    employee = None

    employee_id = request.session.get('employee_id')

    if employee_id:
        employee = Employee.objects.filter(id=employee_id).first()

    companies = Company.objects.all()

    paginator = Paginator(companies, 3)
    page_number = request.GET.get("page")
    companies_page = paginator.get_page(page_number)

    context = {
        'companies': companies_page,
        'employee': employee,
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
    if not company_id:
        return redirect('companylogin')

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

    # Get employee profile
    profile = EmployeeProfile.objects.filter(employee=employee).first()

    # Get employee information
    education = Education.objects.filter(employee=employee)
    experience = Experience.objects.filter(employee=employee)
    skills = Skill.objects.filter(employee=employee)

    # Get logged-in company
    company = None
    company_id = request.session.get("company_id")

    if company_id:
        company = Company.objects.filter(id=company_id).first()

    context = {
        "employee": employee,
        "profile": profile,
        "education": education,
        "experience": experience,
        "skills": skills,
        "company": company,
    }

    return render(request, "employee_profile_view.html", context)

def company_candidates(request):
    

    company_id = request.session.get("company_id")
    if not company_id:
                return redirect('companylogin')

    company = get_object_or_404(
        Company,
        id=company_id
    )


    jobs = Job.objects.filter(
    company=company,
    is_active=True
    ).prefetch_related(
    'jobapplication_set__employee'
)


    context = {
        "company": company,
        "jobs": jobs,
    }


    return render(
        request,
        "company_candidates.html",
        context
    )
# views.py

from django.shortcuts import render, get_object_or_404
from .models import Job

def company_job_detail(request, id):

    data = get_object_or_404(Job, id=id)

    company = data.company

    return render(
        request,
        'company_job_detail.html',
        {
            'data': data,
            'company': company
        }
    )

from .models import JobApplication, EmployeeProfile, Education, Experience, Skill


def job_applicants(request, id):

    application = JobApplication.objects.get(id=id)

    employee = application.employee

    profile = EmployeeProfile.objects.get(employee=employee)

    company = application.job.company


    return render(
        request,
        'job_applicants.html',
        {
            'application': application,
            'employee': employee,
            'profile': profile,
            'company': company
        }
    )
from django.shortcuts import get_object_or_404, redirect
from .models import JobApplication

def update_application_status(request, id):
    application = get_object_or_404(JobApplication, id=id)
    job = application.job

    if request.method == "POST":
        new_status = request.POST.get("status")
        old_status = application.status

        # Accepting an applicant
        if old_status != "Accepted" and new_status == "Accepted":
            if job.vacancy > 0:
                job.vacancy -= 1

                if job.vacancy == 0:
                    job.is_active = False

                job.save()

        # Changing from Accepted back to another status
        elif old_status == "Accepted" and new_status != "Accepted":
            job.vacancy += 1
            job.is_active = True
            job.save()

        application.status = new_status
        application.save()

    return redirect("job_applicants", id=application.id)

def saved_jobs(request):

    employee_id = request.session.get("employee_id")

    if not employee_id:
        return redirect("employeelogin")


    employee = get_object_or_404(
        Employee,
        id=employee_id
    )


    saved = SaveJob.objects.filter(
        employee=employee
    ).select_related(
        "job",
        "job__company",
        "job__position"
    ).order_by("-id")


    # Pagination
    paginator = Paginator(saved, 5)

    page_number = request.GET.get("page")

    page_obj = paginator.get_page(page_number)


    return render(
        request,
        "saved_jobs.html",
        {
            "employee": employee,
            "page_obj": page_obj
        }
    )

def show_post(request,id):
    

    company = Company.objects.get(id=id)
    

    jobs = Job.objects.filter(company=company)

    status = request.GET.get("status")

    if status == "open":
        jobs = jobs.filter(is_active=True)
    elif status == "closed":
        jobs = jobs.filter(is_active=False)

    jobs = jobs.order_by("-posted_date")  # or "-id" if you don't have posted_date

    paginator = Paginator(jobs, 5)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "company": company,
        "jobs": page_obj,
        "page_obj": page_obj,
        "status": status,
    }

    return render(request, "show_post.html", context)

from django.core.mail import EmailMessage, get_connection


from django.contrib import messages





def send_application_email(request, id, status):

    application = get_object_or_404(
        JobApplication,
        id=id
    )

    company = application.job.company


    # Check 1: Cannot send email when Pending
    if status == "Pending":

        messages.warning(
            request,
            "Please update the application status before sending an email."
        )

        return redirect(
            "job_applicants",
            id=id
        )


    # Check 2: Check if this status email was already sent
    already_sent = ApplicationEmail.objects.filter(
        application=application,
        status=status
    ).exists()


    if already_sent:

        messages.warning(
            request,
            f"The {status} email has already been sent for this application."
        )

        return redirect(
            "job_applicants",
            id=id
        )


    # Default messages

    if status == "Accepted":

        default_message = f"""
Dear {application.employee.username},

Congratulations!

Your application for 
{application.job.position.position_name}

has been accepted.

Company:
{company.company_name}

We will contact you soon.

Best regards,
{company.company_name}
"""


    elif status == "Shortlisted":

        default_message = f"""
Dear {application.employee.username},

Your application for
{application.job.position.position_name}

has been shortlisted.

We will contact you soon.

Best regards,
{company.company_name}
"""


    elif status == "Rejected":

        default_message = f"""
Dear {application.employee.username},

Thank you for applying.

Your application was not selected.

We wish you success.

Best regards,
{company.company_name}
"""


    else:

        default_message = ""



    # Send email

    if request.method == "POST":


        company_email = request.POST.get("email")

        app_password = request.POST.get("app_password")



        subject = request.POST.get("subject")

        message = request.POST.get("message")



        connection = get_connection(

            host="smtp.gmail.com",

            port=587,

            username=company_email,

            password=app_password,

            use_tls=True

        )



        email = EmailMessage(

            subject,

            message,

            company_email,

            [application.employee.email],

            connection=connection

        )


        # Send email
        email.send()



        # Save company email credentials after successful send
        if not company.email_app_password:

            company.email = company_email

            company.email_app_password = app_password

            company.save()



        # Save email history

        ApplicationEmail.objects.create(

            application=application,

            status=status,

            subject=subject,

            message=message

        )



        messages.success(
            request,
            "Email has been sent successfully!"
        )


        return redirect(
            "job_applicants",
            id=id
        )



    return render(

        request,

        "send_application_email.html",

        {
            "application": application,
            "status": status,
            "default_message": default_message,
            "company": company
        }

    )


