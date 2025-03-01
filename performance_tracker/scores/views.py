from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Score
from .models import pdfScore
from users.models import UserProfiles
from django.utils.dateparse import parse_date


@login_required(login_url='/login/')
def manual_upload(request):
    if request.method == "POST":
        user = request.user  # Get the logged-in user

        # Validate training type
        match_type = request.POST.get("training_type")
        if match_type not in ["40", "60"]:
            messages.error(request, "Invalid training type selected.")
            return redirect("manual_upload")

        # Convert training type into match format (40-Shots or 60-Shots)
        match_type = "40-Shots" if match_type == "40" else "60-Shots"

        date_input = request.POST.get("date")  # Get date input from form
        training_date = parse_date(date_input)  # Convert to Date object

        if not training_date:
            messages.error(request, "Invalid date format.")
            return redirect("manual_upload")

        # Extract day name (Monday, Tuesday, etc.)
        training_day = training_date.strftime("%A")  # Example: "Monday"

        # Extract scores from form input
        series_scores = []
        for i in range(1, 7):  # Loop through 6 possible series
            series_data = []
            for j in range(1, 11):  # Each series has 10 shots
                score = request.POST.get(f"series{i}_shot{j}")
                if score:
                    try:
                        score = int(score)
                        if 0 <= score <= 10:  # Validate range
                            series_data.append(score)
                        else:
                            messages.error(request, f"Invalid score in Series {i}, Shot {j}. Must be between 0 and 10.")
                            return redirect("manual_upload")
                    except ValueError:
                        messages.error(request, f"Invalid score format in Series {i}, Shot {j}.")
                        return redirect("manual_upload")
                else:
                    series_data.append(0)  # Default to 0 if empty

            # Append only if required (40 shots → 4 series, 60 shots → 6 series)
            if i <= 4 or (match_type == "60-Shots" and i > 4):
                series_scores.append(series_data)

        # Extract additional fields
        duration = request.POST.get("duration")
        notes = request.POST.get("notes", "")
        adjustment_made = request.POST.get("adjustment") == "on"  # Checkbox handling
        adjustment_comment = request.POST.get("adjustment_comment", "") if adjustment_made else None

        # Validate duration
        try:
            duration = int(duration)
            if duration <= 0:
                messages.error(request, "Practice duration must be a positive number.")
                return redirect("manual_upload")
        except ValueError:
            messages.error(request, "Invalid duration format.")
            return redirect("manual_upload")

        # Save the score entry
        score_entry = Score.objects.create(
            user_profile=UserProfiles.objects.get(username=user.username),
            match_type=match_type,
            date=training_date,  # Change 'training_date' to 'date'
            day=training_day,  # Change 'training_day' to 'day'
            series_1=series_scores[0] if len(series_scores) > 0 else None,
            series_2=series_scores[1] if len(series_scores) > 1 else None,
            series_3=series_scores[2] if len(series_scores) > 2 else None,
            series_4=series_scores[3] if len(series_scores) > 3 else None,
            series_5=series_scores[4] if len(series_scores) > 4 else None,
            series_6=series_scores[5] if len(series_scores) > 5 else None,
            duration = duration,
            notes=notes,
            adjustment_made=adjustment_made,
            adjustment_comment=adjustment_comment
        )

        messages.success(request, "Training data saved successfully!")
        return redirect("/score/shooter/home/analytics/?source=manual")  # Redirect to dashboard or another page

    return render(request, "manual_upload.html")

@login_required(login_url='/login/')
def pdf_uploading(request):
    if request:
        messages.success(request, "Training data saved successfully!")
        return redirect("/score/shooter/home/analytics/?source=manual") 
    return render(request, 'pdf_upload.html')

@login_required(login_url='/login/')
def dashboard(request):
    if not request.user.is_authenticated:
        messages.warning(request,"You need to login to access this page!!")
        return redirect(request,'/login/')
    return render(request, 'dashboard.html')

@login_required(login_url='/login/')
def analytics(request):
    source = request.GET.get("source", "manual")  # Get source from query params
    request.session["analytics_source"] = source  # Save in session
    user = request.user
    # Get the latest score entry
    if source == "manual":
        latest_score = Score.objects.filter(user_profile=user).order_by("-current_time").first()
        print(latest_score)    
    elif source == "pdf":
        latest_score = pdfScore.objects.filter(user_profile=user).order_by("-date").first()
    else:
        latest_score = None

    context = {
        "source": source,
        "latest_score": latest_score
    }
    print("Analytics Source:", source) 
    return render(request, 'current_analytics.html', context)

# Create your views here.
