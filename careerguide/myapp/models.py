from django.db import models

# Create your models here.

# Job seeker table
class Employee(models.Model):
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)

    def __str__(self):
        return self.username
    
class EmployeeProfile(models.Model):
    employee = models.OneToOneField(Employee, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=10)
    address = models.TextField()
    summary = models.TextField(blank=True)
    profile_image = models.ImageField(upload_to='profile/', blank=True, null=True)
    def __str__(self):
        return self.full_name



# Company table
class Company(models.Model):
    company_name = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    phone = models.CharField(max_length=15)
    description = models.TextField()
    website = models.URLField(blank=True)
    address = models.TextField()
    profile_image = models.ImageField(upload_to='profile/', blank=True, null=True)
    tagline = models.CharField(max_length=255, blank=True, null=True)
    facebook = models.CharField(max_length=255, blank=True, null=True)
    twitter = models.CharField(max_length=255, blank=True, null=True)
    linkedin = models.CharField(max_length=255, blank=True, null=True)

    def str(self):
        return self.company_name
    
class Education(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    institution = models.CharField(max_length=200)
    degree = models.CharField(max_length=100)
    field_of_study = models.CharField(max_length=100)
    start_year = models.IntegerField()
    end_year = models.IntegerField()
    def __str__(self):
        return self.institution

class Experience(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    company_name = models.CharField(max_length=200)
    position = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.position
    
class Skill(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    skill_name = models.CharField(max_length=100)
    proficiency = models.CharField(
        max_length=20,
        choices=[
            ('Beginner', 'Beginner'),
            ('Intermediate', 'Intermediate'),
            ('Advanced', 'Advanced'),
        ]
    )
    def __str__(self):
        return self.skill_name
    
class Position(models.Model):
    position_name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.position_name
    
class City(models.Model):
    city_name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.city_name
    

    
class Job(models.Model):

    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    JOB_TYPE_CHOICES = [
        ('Full Time', 'Full Time'),
        ('Part Time', 'Part Time'),
        ('Internship', 'Internship'),
        ('Remote', 'Remote'),
    ]
    job_type = models.CharField(
        max_length=20,
        choices=JOB_TYPE_CHOICES
    )
    description = models.TextField()
    vacancy = models.PositiveIntegerField(default=1)
    salary = models.CharField(max_length=100)
    requirements = models.TextField()
    city = models.ForeignKey(City,on_delete=models.PROTECT)
    position = models.ForeignKey(Position, on_delete=models.PROTECT)
    location = models.CharField(max_length=100)
    posted_date = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.company} - {self.job_type} - {self.position}"
    
class JobApplication(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)

    job = models.ForeignKey(Job, on_delete=models.CASCADE)

    cover_letter = models.TextField(blank=True)

    applied_date = models.DateTimeField(auto_now_add=True)

    status = models.CharField(
        max_length=30,
        choices=[
            ('Pending', 'Pending'),
            ('Shortlisted', 'Shortlisted'),
            ('Rejected', 'Rejected'),
            ('Accepted', 'Accepted'),
        ],
        default='Pending'
    )

    def __str__(self):
        return f"{self.employee} - {self.job}"
    



class EmployeeCareerResult(models.Model):

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE
    )

    best_match = models.CharField(
        max_length=100
    )

    similar_matches = models.TextField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )


    def __str__(self):
        return self.best_match
    
class SaveJob(models.Model):
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE
    )
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    def __str__(self):
        return f"{self.employee} - {self.job}"