from django.urls import path
from .views import *

urlpatterns = [
    path('homeview', homeview,name='homeview'),
    path('jobdetail/<int:id>/', jobdetail,name='jobdetail'),
    path('employeeregister', employee_register,name='employeeregister'),
    path('employeelogin', employee_login,name='employeelogin'),
    path('employeelogout', employee_logout,name='employeelogout'),
    path('employeeprofile', employee_profile,name='employeeprofile'),
    path('applyjob/<int:id>/', applyjob, name='applyjob'),
    path('companyregister', company_register,name='companyregister'),
    path('companylogin', company_login,name='companylogin'),
    path('companylogout', company_logout,name='companylogout'),
    path('companyview', companyview,name='companyview'),
    path('editemployeeprofile/<int:id>/', edit_employee_profile, name='edit_employee_profile'),
    path('companypost', post,name='companypost'),
    path('companyprofile/<int:id>/', company_profile,name='companyprofile'),
    path('editcompanyprofile/<int:id>/', edit_company_profile, name='editcompanyprofile'),
    path('companypostview/<int:id>/', company_post_view, name='companypostview'),
    path('editpost/<int:id>/', edit_post, name='editpost'),
    path('deletepost/<int:id>/', deletepost, name='deletepost'),
    path('viewapply/<int:id>/', view_apply, name='viewapply'),


]