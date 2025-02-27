from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Score
from users.models import UserProfiles
from django.utils.dateparse import parse_date
import json

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
        return redirect("dashboard")  # Redirect to dashboard or another page

    return render(request, "manual_upload.html")

@login_required(login_url='/login/')
def pdf_uploading(request):
    return render(request, 'pdf_upload.html')

@login_required(login_url='/login/')
def dashboard(request):
    user = request.user

    # Fetch manual scores only for the logged-in user
    manual_scores = Score.objects.filter(user_profile=user).order_by('-date', '-current_time')

    # Get the most recent entry
    last_entry = manual_scores.first()

    # Prepare data for charts
    series_trends = []   # Stores series-wise trends over time
    shot_trends = []     # Stores total shot trends over time
    series_totals = []   # Line chart data for total score trends
    pie_chart_data = {
        "Series 1": 0,
        "Series 2": 0,
        "Series 3": 0,
        "Series 4": 0,
        "Series 5": 0,
        "Series 6": 0
    }

    for score in manual_scores:
        formatted_date = score.date.strftime("%Y-%m-%d")

        # Add series-wise scores to trends
        series_trends.append({
            "date": formatted_date,
            "series_1": score.s1t,
            "series_2": score.s2t,
            "series_3": score.s3t,
            "series_4": score.s4t,
            "series_5": score.s5t if score.match_type == "60-Shots" else None,
            "series_6": score.s6t if score.match_type == "60-Shots" else None,
            "total": score.total
        })

        # Extract shot-wise trends for each series
        total_shots = sum(score.series_1 or []) + sum(score.series_2 or []) + sum(score.series_3 or []) + sum(score.series_4 or [])
        if score.match_type == "60-Shots":
            total_shots += sum(score.series_5 or []) + sum(score.series_6 or [])

        shot_trends.append({
            "date": formatted_date,
            "shots": total_shots
        })

        # Pie chart data (total contribution of each series)
        pie_chart_data["Series 1"] += score.s1t
        pie_chart_data["Series 2"] += score.s2t
        pie_chart_data["Series 3"] += score.s3t
        pie_chart_data["Series 4"] += score.s4t
        if score.match_type == "60-Shots":
            pie_chart_data["Series 5"] += score.s5t
            pie_chart_data["Series 6"] += score.s6t

        # Total score trend over time
        series_totals.append({
            "date": formatted_date,
            "total": score.total
        })

    # Convert data to JSON for the frontend
    context = {
        "last_entry": last_entry,
        "series_trends": json.dumps(series_trends),
        "shot_trends": json.dumps(shot_trends),
        "pie_chart_data": json.dumps(pie_chart_data),
        "series_totals": json.dumps(series_totals),
    }

    return render(request, 'dashboard.html', context)

# Create your views here.
