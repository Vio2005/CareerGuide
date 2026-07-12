from turtle import position
from urllib import request

from django.shortcuts import render,redirect
from .models import *
from django.contrib import messages

# Create your views here.
def homeview(request):
    job=Job.objects.all()
    position = request.GET.get('position')
    city = request.GET.get('city')
    job_type = request.GET.get('job_type')

    if position:
        job = job.filter(
            position__position_name__icontains=position
        )

    if city:
        job = job.filter(
            city__city_name__icontains=city
        )

    if job_type:
        job = job.filter(
            job_type=job_type
        )
    

    context={'job':job, 'position': position,'city': city,'job_type': job_type, }
    return render(request, 'index.html', context)

def jobdetail(request,id):
    data=Job.objects.filter(id=id)
    employee_id = request.session.get('employee_id')

    employee = None

    if employee_id:
        employee = Employee.objects.get(id=employee_id)

    
    context={"data":data, "employee": employee}
    return render(request,'jobdetail.html',context)


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

            messages.warning(request, "You have already applied for this job.")
            return redirect('jobdetail', id=id)

        cover_letter = request.POST.get("cover_letter")

        

        JobApplication.objects.create(
            employee=employee,
            job=job,
            cover_letter=cover_letter,
            status="Pending"
        )

        messages.success(request, "Applied successfully!")

    return redirect('jobdetail', id=id)

def company_register(request):
    if request.method == "POST":
        company_name = request.POST.get("company_name")
        email = request.POST.get("email")
        password = request.POST.get("password")
        phone=request.POST.get("phone")
        description=request.POST.get("description")
        website=request.POST.get("website")
        address=request.POST.get("address")
        profile_image = request.FILES.get('profile_image')


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

            return redirect("companyview")

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
    job_applications = JobApplication.objects.filter(job__company=company)

    context = {
        'company': company,
        'job': job,
        'job_applications': job_applications
    }

    return render(request, 'companyview.html', context)


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
        job_type = request.POST.get("job_type")
        description = request.POST.get("description")
        vacancy = request.POST.get("vacancy")
        salary=request.POST.get("salary")
        requirements=request.POST.get("requirements")
        city=request.POST.get("city")
        position=request.POST.get("position")
        location = request.POST.get('location')
        city_obj, created = City.objects.get_or_create(city_name=city)
        position_obj, created = Position.objects.get_or_create(position_name=position)


        Job.objects.create(
            company=company,
            job_type=job_type,
            description=description,
            vacancy=vacancy,
            salary=salary,
            requirements=requirements,
            location=location,
            city=city_obj,
            position=position_obj
        )
        
        
        messages.success(request, "Applied successfully!")

    return render(request,'company_post.html')

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

def company_post_view(request,id):

    company = Company.objects.get(id=id)
    jobs = Job.objects.filter(company=company)

    context = {
        'company': company,
        'jobs': jobs,
    }

    return render(request, 'company_post_view.html', context)

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



       
    