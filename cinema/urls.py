from django.contrib import admin
from django.urls import path
from bookingapp import views
from bookingapp.views import (
    homepage, login_page, signin_page,
    send_otp, verify_otp, main_login_page,
    location_page, do_login
)

urlpatterns = [
    path('admin/', admin.site.urls),

    # Homepage
    path("homepage/<str:city>/", views.homepage, name="homepage_city"),

    # Login + location
    path('', login_page, name='login'),
    path('location/', location_page, name='location'),

    # Sign in + OTP
    path('signin/', signin_page, name='signin'),
    path('send-otp/', send_otp, name='send_otp'),
    path('verify-otp/', verify_otp, name='verify_otp'),
    path("save-password/", views.save_password, name="save_password"),

    path('mainlogin/',   main_login_page, name='mainloginpage'),
    path('do-login/', do_login, name='do_login'),

    # Movie page for 2.0
    path("movie/2-0/", views.movie_2_0, name="movie_2_0"),

    # Coins payment
    path("pay/", views.pay, name="pay"),

    
    path("movies/anbe-sivam/", views.anbesivam, name="anbesivam"),

    path("movies/paruthiveeran/", views.paruthiveeran, name="paruthiveeran"),

    path("movies/o_kadhal_kanmani/", views.o_kadhal_kanmani, name="o_kadhal_kanmani"),

    path("movies/adithya_varma/", views.adithya_varma, name="adithya_varma")
    
]
