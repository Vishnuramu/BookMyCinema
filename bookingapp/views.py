from django.shortcuts import render
from django.http import JsonResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.core.mail import send_mail

from datetime import date, timedelta, datetime
import random
import time
import json

from .models import UserAccount, SeatBooking


# -------------------------------------------------------------------
# HELPER: GET COINS FOR CURRENT USER
# -------------------------------------------------------------------
def _get_user_coins(request):
    user_email = request.session.get("user_email")
    coins = 0
    if user_email:
        user = UserAccount.objects.filter(email=user_email).first()
        if user:
            coins = user.bonus_bitcoins
    return coins


# -------------------------------------------------------------------
# HOMEPAGE + STATIC PAGES
# -------------------------------------------------------------------
from django.shortcuts import render
from django.http import Http404

def homepage(request, city=None):
    coins = _get_user_coins(request)

    # If a city was provided in URL, normalize and save to session
    if city:
        city = city.lower()
        request.session['city'] = city
    else:
        # no city in URL, try to use session value
        city = request.session.get('city')

    # Use a friendly display name (capitalized) or a fallback
    city_display = city.capitalize() if city else "Select Location"

    # Map for city-specific templates (lowercase keys)
    city_templates = {
        "chennai": "homepage/chennai.html",
        "dindigul": "homepage/dindigul.html",
        "madurai": "homepage/madurai.html",
        "coimbatore": "homepage/coimbature.html",
        "tiruchi": "homepage/tiruchi.html",
    }

    # If a known city is present, render its template (with city in context)
    if city:
        template_name = city_templates.get(city)
        if not template_name:
            # Unknown city requested in URL — you can choose to 404 or fallback
            raise Http404("Unknown city")

        return render(
            request,
            template_name,
            {
                "city": city_display,     # used in header
                "city_name": city_display, # keep for backward compatibility if used elsewhere
                "coins": coins,
            },
        )

    # No city selected anywhere — render generic homepage and still pass `city`
    return render(
        request,
        "homepage.html",
        {
            "city": city_display,   # will be "Select Location" by default
            "coins": coins,
        },
    )



def login_page(request):
    return render(request, "loginpage.html")


def signin_page(request):
    return render(request, "signinpage.html")


def main_login_page(request):
    return render(request, "mainloginpage.html")


def location_page(request):
    return render(request, "location.html")

# -------------------------------------------------------------------
# GENERIC MOVIE PAGE (ALL SEAT-BOOKING MOVIES)
# -------------------------------------------------------------------
def _movie_page(request, movie_name, template_name):
    coins = _get_user_coins(request)

    # 🔥 Get city from session
    city = request.session.get("city", "Select Location")

    today = date.today()

    selected_date_str = request.GET.get("d")
    if selected_date_str:
        try:
            selected_date = datetime.strptime(selected_date_str, "%Y-%m-%d").date()
        except ValueError:
            selected_date = today
    else:
        selected_date = today

    if selected_date < today or selected_date > today + timedelta(days=2):
        selected_date = today

    days = []
    for i in range(3):
        d = today + timedelta(days=i)
        days.append(
            {
                "weekday": d.strftime("%a").upper(),
                "day": d.strftime("%d"),
                "month": d.strftime("%b").upper(),
                "label": d.strftime("%a %d %b"),
                "iso": d.isoformat(),
                "is_active": (d == selected_date),
            }
        )

    selected_label = next(
        (d["label"] for d in days if d["is_active"]), days[0]["label"]
    )

    disabled_qs = SeatBooking.objects.filter(
        show_date=selected_date,
        movie_name=movie_name,
    ).values_list("seat_label", flat=True)
    disabled_seats = list(disabled_qs)
    disabled_seats_json = json.dumps(disabled_seats)

    context = {
        "city": city.capitalize(),   # 🔥 FIX
        "days": days,
        "selected_date": selected_date,
        "selected_label": selected_label,
        "disabled_seats_json": disabled_seats_json,
        "coins": coins,
    }

    return render(request, template_name, context)




def movie_2_0(request):
    return _movie_page(request, "2.0", "templatesformovie/twopoint_0.html")


def anbesivam(request):
    return _movie_page(request, "anbesivam", "templatesformovie/anbesivam.html")


def paruthiveeran(request):
    return _movie_page(request, "paruthiveeran", "templatesformovie/paruthiveeran.html")


def o_kadhal_kanmani(request):
    return _movie_page(request, "o_kadhal_kanmani", "templatesformovie/o_kadhal_kanmani.html")


def adithya_varma(request):
    return _movie_page(request, "adithya_varma", "templatesformovie/adithya_varma.html")








# -------------------------------------------------------------------
# OTP / SIGNUP FLOW
# -------------------------------------------------------------------
@csrf_exempt
def send_otp(request):
    if request.method != "POST":
        return JsonResponse(
            {"status": "error", "message": "Invalid request method"}, status=400
        )

    email = request.POST.get("email")
    if not email:
        return JsonResponse(
            {"status": "error", "message": "Email is required"}, status=400
        )

    if UserAccount.objects.filter(email=email).exists():
        return JsonResponse(
            {
                "status": "exists",
                "message": "You are already a user. Please log in.",
            }
        )

    otp = random.randint(100000, 999999)

    # save OTP and time in session
    request.session["otp_email"] = email
    request.session["otp_code"] = str(otp)
    request.session["otp_time"] = time.time()

    subject = "Your BookMyCinema OTP"
    body = f"Your OTP code is: {otp}\nThis code is valid for 5 minutes."
    from_email = settings.DEFAULT_FROM_EMAIL

    try:
        send_mail(subject, body, from_email, [email])
    except Exception:
        return JsonResponse(
            {"status": "error", "message": "Failed to send OTP. Check email settings."}
        )

    return JsonResponse({"status": "ok", "message": f"OTP sent to {email}"})


@csrf_exempt
def verify_otp(request):
    if request.method != "POST":
        return JsonResponse(
            {"status": "error", "message": "Invalid request method"}, status=400
        )

    entered_otp = request.POST.get("otp")
    session_otp = request.session.get("otp_code")
    session_time = request.session.get("otp_time")

    if not session_otp or not session_time:
        return JsonResponse(
            {
                "status": "error",
                "message": "No OTP found. Please request a new one.",
            }
        )

    current_time = time.time()
    if current_time - session_time > 300:
        request.session.pop("otp_code", None)
        request.session.pop("otp_time", None)
        return JsonResponse(
            {"status": "error", "message": "OTP expired. Please request a new one."}
        )

    if entered_otp == session_otp:
        request.session.pop("otp_code", None)
        request.session.pop("otp_time", None)
        return JsonResponse(
            {"status": "ok", "message": "OTP verified successfully!"}
        )

    return JsonResponse(
        {"status": "error", "message": "Invalid OTP. Please try again."}
    )


# -------------------------------------------------------------------
# SAVE PASSWORD (SIGNUP FINAL STEP)
# -------------------------------------------------------------------
@csrf_exempt
def save_password(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "").strip()

        if not email or not password:
            return JsonResponse(
                {"status": "error", "message": "Email and password required"}
            )

        user, created = UserAccount.objects.get_or_create(
            email=email,
            defaults={
                "password": password,
                "bonus_bitcoins": 120,  # first time bonus
            },
        )

        if not created:
            return JsonResponse(
                {
                    "status": "exists",
                    "message": "User already exists. Please log in.",
                }
            )

        request.session["user_email"] = user.email
        request.session["user_bonus"] = user.bonus_bitcoins

        return JsonResponse(
            {
                "status": "ok",
                "message": "User saved successfully",
                "bonus_awarded": user.bonus_bitcoins,
            }
        )

    return JsonResponse({"status": "error", "message": "Invalid request"})


# -------------------------------------------------------------------
# LOGIN
# -------------------------------------------------------------------
@csrf_exempt
def do_login(request):
    if request.method != "POST":
        return JsonResponse(
            {"status": "error", "message": "Invalid request method"}, status=400
        )

    email = request.POST.get("email", "").strip()
    password = request.POST.get("password", "")

    if not email:
        return JsonResponse(
            {"status": "error", "message": "Email required"}, status=400
        )

    user = UserAccount.objects.filter(email=email).first()
    if not user:
        return JsonResponse(
            {"status": "email_not_found", "message": "Email not registered"}
        )

    if user.password != password:
        return JsonResponse(
            {"status": "wrong_password", "message": "Incorrect password"}
        )

    request.session["user_email"] = user.email
    return JsonResponse({"status": "ok"})


# -------------------------------------------------------------------
# PAY – DEDUCT COINS + SAVE SEATS
# -------------------------------------------------------------------
@csrf_exempt
def pay(request):
    movie_name = request.POST.get("movie_name")
    if request.method != "POST":
        return JsonResponse({"ok": False, "msg": "Invalid method"}, status=400)

    # amount
    try:
        amount = int(request.POST.get("amount", 0))
    except ValueError:
        amount = 0

    seats_str = request.POST.get("seats", "")
    show_date_str = request.POST.get("show_date")

    if amount <= 0 or not seats_str or not show_date_str:
        return JsonResponse({"ok": False, "msg": "Invalid data"}, status=400)

    # date
    try:
        show_date = datetime.strptime(show_date_str, "%Y-%m-%d").date()
    except ValueError:
        return JsonResponse({"ok": False, "msg": "Invalid date"}, status=400)

    # seat labels like "A1,B3"
    seat_labels = [s.strip() for s in seats_str.split(",") if s.strip()]

    # current user
    user_email = request.session.get("user_email")
    if not user_email:
        return JsonResponse({"ok": False, "msg": "Please log in first"}, status=401)

    user = UserAccount.objects.filter(email=user_email).first()
    if not user:
        return JsonResponse({"ok": False, "msg": "User not found"}, status=404)

    if user.bonus_bitcoins < amount:
        return JsonResponse({"ok": False, "msg": "Not enough coins"}, status=400)

    # deduct coins
    user.bonus_bitcoins -= amount
    user.save()

    # save each seat booking for that date
    for seat in seat_labels:
        SeatBooking.objects.get_or_create(
            seat_label=seat,
            show_date=show_date,
            movie_name=movie_name,
        )

    return JsonResponse({"ok": True})
