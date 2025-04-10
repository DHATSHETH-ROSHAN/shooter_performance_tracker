import fitz
import re
import json
import statistics
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import manualscore
from .models import pdfScore, activities
from users.models import UserProfiles
from django.http import JsonResponse
from django.utils.dateparse import parse_date
from datetime import datetime,timedelta
from django.http import JsonResponse


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
        score_entry = manualscore.objects.create(
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
        request.session["last_manual_upload"] = {
            "match_type": match_type,
            "date": training_date.strftime("%Y-%m-%d"),
            "day": training_day,
            "series_scores": series_scores,
            "duration": duration,
            "notes": notes,
            "adjustment_made": adjustment_made,
            "adjustment_comment": adjustment_comment
        }
        messages.success(request, "Training data saved successfully!")
        return redirect("/score/shooter/home/analytics/?source=manual")  # Redirect to dashboard or another page

    return render(request, "manual_upload.html")

@login_required(login_url='/login/')
def pdf_uploading(request):
    if request.method == "POST":
        user = request.user  # Get logged-in user
        # Get or create user profile (Fix for "User Profile Not Found" issue)
        try:
            user_profile = UserProfiles.objects.get(username=user.username)
        except UserProfiles.DoesNotExist:
            messages.error(request, "User profile not found.")
            return redirect("upload_pdf")
        
        uploaded_file = request.FILES.get("pdf_file")  # Get uploaded file
        if not uploaded_file:
            messages.error(request, "No file selected.")
            return redirect("upload_pdf")
        if not uploaded_file.name.endswith(".pdf"):
            messages.error(request, "Only PDF files are allowed.")
            return redirect("upload_pdf") 
        # Extract PDF data
        extracted_data = []
        try:
            doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
            for page in doc:
                text = page.get_text("text")
                extracted_data.append(text.strip())
        except Exception as e:
            messages.error(request, f'Error Processing PDF: {str(e)}')
            return redirect("upload_pdf")
        
        full_text = "\n".join(extracted_data)
        structured_data = pdf_extractor(full_text)
        # Ensure valid match type
        match_type = "60-Shots" if structured_data["match_type"] == "Air Rifle 60" else "40-Shots"
        total = structured_data["total"]
        inner_tens = structured_data["inner_tens"]

        if inner_tens > total:
            total = structured_data["inner_tens"]
            inner_tens = structured_data["total"]
        #series values
        series_totals = structured_data["series_totals"]
        if len(series_totals) >= 4:  # Ensures at least 4 values exist
            s1t = series_totals[0]
            s2t = series_totals[1]
            s3t = series_totals[2]
            s4t = series_totals[3]
            
            if len(series_totals) == 6:  # Only for 60-shots match
                s5t = series_totals[4]
                s6t = series_totals[5]
            else:
                s5t = None
                s6t = None
        else:
            s1t = s2t = s3t = s4t = s5t = s6t = None  # Handle missing values
        # saving the values of each series for list
        series_1 = structured_data["series_1"]
        series_2 = structured_data["series_2"]
        series_3 = structured_data["series_3"]
        series_4 = structured_data["series_4"]
        series_5 = structured_data["series_5"]
        series_6 = structured_data["series_6"]

        #group sizes
        gps = structured_data["gps"]
        gps1 = structured_data["gps1"]
        gps2 = structured_data["gps2"]
        gps3 = structured_data["gps3"]
        gps4 = structured_data["gps4"]
        gps5 = structured_data["gps5"]
        gps6 = structured_data["gps6"]
        # for mpi values
        fmpi = structured_data["fmpi"]
        s1mpi = structured_data["mpi1"]
        s2mpi = structured_data["mpi2"]
        s3mpi = structured_data["mpi3"]
        s4mpi = structured_data["mpi4"]
        s5mpi = structured_data["mpi5"]
        s6mpi = structured_data["mpi6"]
        #extracting date and day
        date = datetime.strptime(structured_data["date"], "%d-%m-%Y %H:%M:%S") 
        # Validate duration
        duration = request.POST.get("duration")
        if duration is not None:
            try:
                duration = int(duration)
                if duration < 0 or duration > 240:
                    messages.error(request, "Practice duration must be between 0 and 240 minutes.")
                    return redirect("upload_pdf")
            except ValueError:
                messages.error(request, "Invalid duration format.")
                return redirect("upload_pdf")

        # Save extracted data into the database
        pdfScore.objects.create(
            user_profile=user_profile,
            match_type=match_type,
            duration=duration,
            adjustment_made=request.POST.get("adjustment") == "on",
            adjustment_comment=request.POST.get("adjustment_comment", ""),
            notes=request.POST.get("notes", ""),
            total = total,
            inner_tens = inner_tens,
            series_1 = series_1,
            series_2 = series_2,
            series_3 = series_3,
            series_4 = series_4,
            series_5 = series_5,
            series_6 = series_6,
            s1t = s1t,
            s2t = s2t,
            s3t = s3t,
            s4t = s4t,
            s5t = s5t,
            s6t = s6t,
            date = date,
            gps = gps,
            gps1 = gps1,
            gps2 = gps2,
            gps3 = gps3,
            gps4 = gps4,
            gps5 = gps5,
            gps6 = gps6,
            fmpi = fmpi,
            s1mpi = s1mpi,
            s2mpi = s2mpi,
            s3mpi = s3mpi,
            s4mpi = s4mpi,
            s5mpi = s5mpi,
            s6mpi = s6mpi,
        )
        messages.success(request, "Training data saved successfully!")
        return redirect("/score/shooter/home/analytics/?source=pdf")

    return render(request, "pdf_upload.html")


def pdf_extractor(text):
    data = {}
    patterns = {
        "date_time": re.search(r"(\d{2}[-/]\d{2}[-/]\d{4} \d{2}:\d{2}:\d{2})", text),
        "match_type": re.search(r"Results\n(.+)", text),
        "start_number": re.search(r"Start number:\s*(.+)", text),
        "name": re.search(r"Name:\s*(.+)", text),
        "total": re.search(r"Total:\s*(.+)", text),
        "inner_tens": re.search(r"Inner tens:\s*(.+)",text),
        "group_sizes": re.findall(r"Ø:\s*([\d\.]+)",text),
    }
    data = {
        "match_type": patterns["match_type"].group(1).strip() if patterns["match_type"] else None,
        "start_number": patterns["start_number"].group(1).strip() if patterns["start_number"] else None,
        "name": patterns["name"].group(1).strip() if patterns["name"] else None,
        "total" : patterns["total"].group(1).strip() if patterns["total"] else None,
        "inner_tens" :patterns["inner_tens"].group(1).strip() if patterns["inner_tens"] else None,   
    }
    if patterns["date_time"]:
        raw_date = patterns["date_time"].group(1)
        # List of possible date formats
        possible_formats = ["%d-%m-%Y %H:%M:%S", "%d/%m/%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S"]
        for fmt in possible_formats:
            try:
                # Try parsing with each format
                parsed_date =datetime.strptime(raw_date, fmt)
                # Convert to standard format (YYYY-MM-DD HH:MM:SS)
                data["date"] = parsed_date.strftime("%d-%m-%Y %H:%M:%S")
                break  # Stop checking after the first valid format
            except ValueError:
                continue  # Try the next format
        # If no format matched, set date to None
        if "date" not in data:
            data["date"] = None
    else:
        data["date"] = None


    match_type = data["match_type"]
    if match_type:
        if "40" in match_type:
            series_pattern = r"Series totals:\s*((?:\d+\.\d+\s*){4})"
        elif "60" in match_type:
            series_pattern = r"Series totals:\s*((?:\d+\.\d+\s*){6})"
        else:
            series_pattern = None
    # Extract series totals
    if series_pattern:
        series_match = re.search(series_pattern, text)
        if series_match:
            data["series_totals"] = list(map(float, series_match.group(1).split()))
        else:
            data["series_totals"] = None

    group_sizes = patterns["group_sizes"]
    data["gps"] = float(group_sizes[0]) if len(group_sizes) > 0 else None
    data["gps1"] = float(group_sizes[1]) if len(group_sizes) > 1 else None
    data["gps2"] = float(group_sizes[2]) if len(group_sizes) > 2 else None
    data["gps3"] = float(group_sizes[3]) if len(group_sizes) > 3 else None
    data["gps4"] = float(group_sizes[4]) if len(group_sizes) > 4 else None
    data["gps5"] = float(group_sizes[5]) if len(group_sizes) > 5 else None
    data["gps6"] = float(group_sizes[6]) if len(group_sizes) > 6 else None
    #mpi vvalues and patterns
    # Extract MPI (Mean Point of Impact) values
    mpi_pattern = re.findall(r"(?:MPI:\s*)?X:\s*([-+]?\d+\.\d+)\s*mm;\s*Y:\s*([-+]?\d+\.\d+)\s*mm", text)
    if mpi_pattern:
        # Store all MPI values as a list of [X, Y]
        data["mpi"] = [[float(x), float(y)] for x, y in mpi_pattern]
        # Store specific MPI values in separate keys
        data["fmpi"] = [float(mpi_pattern[0][0]), float(mpi_pattern[0][1])] if len(mpi_pattern) > 0 else None
        data["mpi1"] = [float(mpi_pattern[1][0]), float(mpi_pattern[1][1])] if len(mpi_pattern) > 1 else None
        data["mpi2"] = [float(mpi_pattern[2][0]), float(mpi_pattern[2][1])] if len(mpi_pattern) > 2 else None
        data["mpi3"] = [float(mpi_pattern[3][0]), float(mpi_pattern[3][1])] if len(mpi_pattern) > 3 else None
        data["mpi4"] = [float(mpi_pattern[4][0]), float(mpi_pattern[4][1])] if len(mpi_pattern) > 4 else None
        data["mpi5"] = [float(mpi_pattern[5][0]), float(mpi_pattern[5][1])] if len(mpi_pattern) > 5 else None
        data["mpi6"] = [float(mpi_pattern[6][0]), float(mpi_pattern[6][1])] if len(mpi_pattern) > 6 else None
    # series 1 scores
    def extract_series(text, series_number):
        pattern = rf"((?:\d+\.\d+\s*){{10}})Series {series_number}:"
        match = re.search(pattern, text)
        if match:
            series_scores = list(map(float, re.findall(r"\d+\.\d+", match.group(1))))
            return series_scores
        return None
    data["series_1"] = extract_series(text, 1)
    data["series_2"] = extract_series(text, 2)
    data["series_3"] = extract_series(text, 3)
    data["series_4"] = extract_series(text, 4)
    data["series_5"] = extract_series(text, 5)
    data["series_6"] = extract_series(text, 6)
    return data

@login_required(login_url='/login/')
def history(request):
    user = request.user
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            toggle_state = data.get("toggle_state")  # Get the sent toggle value

            # Fetch the appropriate scores based on toggle state
            if toggle_state == "manual":
                scores = list(manualscore.objects.all().values())  # Fetch manual scores
            elif toggle_state == "est":
                scores = list(pdfScore.objects.all().values())  # Fetch EST scores
            else:
                return JsonResponse({"error": "Invalid toggle state"}, status=400)

            return JsonResponse({"toggle_state": toggle_state, "scores": scores})
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format"}, status=400)

    # 🔹 Handle GET requests correctly by rendering the HTML template
    manual_scores = manualscore.objects.all()  # Fetch manual scores
    est_scores = pdfScore.objects.all()  # Fetch EST scores
    return render(request, 'shooter_history.html', {"manual_scores": manual_scores, "est_scores": est_scores})

@login_required(login_url='/login/')
def analytics(request):
    source = request.GET.get("source", "manual")  # Get source from query params
    request.session["analytics_source"] = source  # Save in session
    user = request.user
    last_manual_upload = request.session.get("last_manual_upload", None)
    # Get the latest score entry
    if source == "manual":
        latest_score = manualscore.objects.filter(user_profile=user).order_by("-current_time").first()   
    elif source == "pdf":
        latest_score = pdfScore.objects.filter(user_profile=user).order_by("-date").first()
    else:
        latest_score = None
    return render(request, 'current_analytics.html', {"latest_score": latest_score, "uploaded_data": last_manual_upload})

@login_required
def user_activities(request):
    if not request.user.is_authenticated:
        messages.warning(request, "You need to login to access this page!!")
        return redirect('login')
    
    recent_activities = activities.objects.filter(user=request.user).order_by("-date")
    
    if request.method == 'POST':
        activity_category = request.POST.get('category')
        activity_name = request.POST.get('name')
        duration = request.POST.get('duration')
        notes = request.POST.get('notes')
        
        if all([activity_category, activity_name, duration]):
            new_activity = activities(
                user=request.user,
                activity_category=activity_category,
                activity_name=activity_name,
                duration=duration,
                notes=notes
            )
            new_activity.save()
            messages.success(request, 'Activity added successfully!')
        else:
            messages.error(request, 'All fields are required!')
    
    context = {
        'recent_activities': recent_activities
    }
    
    return render(request, 'activities.html', context)

@login_required(login_url='/login/')
def dashboard(request):
    user = request.user
    user_profile = UserProfiles.objects.get(username=user.username)
    # fetch all scores for the logged-in user
    manual_scores = manualscore.objects.filter(user_profile=user_profile)
    pdf_scores = pdfScore.objects.filter(user_profile=user_profile)

    practice_dates_man = manual_scores.values_list('date', flat=True).distinct()
    streak_count_man = 0
    current_streak_man = 0
    previous_date_man = None
 
    for date in sorted(practice_dates_man, reverse=True):
        if previous_date_man is None or previous_date_man - date == timedelta(days=1):
            current_streak_man += 1
        else:
            break
        previous_date_man = date
    streak_count_man = current_streak_man

    # calculate the total number of scores
    duration_40_man = list(manual_scores.filter(match_type="40-Shots").values_list('duration', flat=True))
    duration_60_man = list(manual_scores.filter(match_type="60-Shots").values_list('duration', flat=True))
    score_40_man = list(manual_scores.filter(match_type="40-Shots").values_list('total', flat=True))
    score_60_man = list(manual_scores.filter(match_type="60-Shots").values_list('total', flat=True))
    # manual calculations    
    total_manual_scores = manual_scores.count()
    # calculate tht total 40 shots matches in manual scores
    total_man_40_shots = manual_scores.filter(match_type="40-Shots").count()
    # calculate the total 60 shots matches in manual scores
    total_man_60_shots = manual_scores.filter(match_type="60-Shots").count()
    best_man_40_shots = max([score.total for score in manual_scores.filter(match_type="40-Shots") if score.total is not None],default=0)
    best_man_60_shots = max([score.total for score in manual_scores.filter(match_type="60-Shots") if score.total is not None],default=0)
    last_30_avg_40_man = round(sum(score.total for score in manual_scores.filter(match_type="40-Shots").order_by('-date')[:30]) / count_40, 2) if (count_40 := manual_scores.filter(match_type="40-Shots").order_by('-date')[:30].count()) > 0 else 0   
    last_30_avg_60_man = round(sum(score.total for score in manual_scores.filter(match_type="60-Shots").order_by('-date')[:30]) / count_60, 2) if (count_60 := manual_scores.filter(match_type="60-Shots").order_by('-date')[:30].count()) > 0 else 0
    # 40 shots series average
    avg_s1_40 = round(sum(score.s1t for score in manual_scores.filter(match_type="40-Shots")) / total_man_40_shots, 1) if (total_man_40_shots := manual_scores.filter(match_type="40-Shots").count()) > 0 else 0
    avg_s2_40 = round(sum(score.s2t for score in manual_scores.filter(match_type="40-Shots")) / total_man_40_shots, 1) if total_man_40_shots > 0 else 0
    avg_s3_40 = round(sum(score.s3t for score in manual_scores.filter(match_type="40-Shots")) / total_man_40_shots, 1) if total_man_40_shots > 0 else 0
    avg_s4_40 = round(sum(score.s4t for score in manual_scores.filter(match_type="40-Shots")) / total_man_40_shots, 1) if total_man_40_shots > 0 else 0
    # 60-Shots series average
    avg_s1_60 = round(sum(score.s1t for score in manual_scores.filter(match_type="60-Shots")) / total_man_60_shots, 1) if (total_man_60_shots := manual_scores.filter(match_type="60-Shots").count()) > 0 else 0
    avg_s2_60 = round(sum(score.s2t for score in manual_scores.filter(match_type="60-Shots")) / total_man_60_shots, 1) if total_man_60_shots > 0 else 0
    avg_s3_60 = round(sum(score.s3t for score in manual_scores.filter(match_type="60-Shots")) / total_man_60_shots, 1) if total_man_60_shots > 0 else 0
    avg_s4_60 = round(sum(score.s4t for score in manual_scores.filter(match_type="60-Shots")) / total_man_60_shots, 1) if total_man_60_shots > 0 else 0
    avg_s5_60 = round(sum(score.s5t for score in manual_scores.filter(match_type="60-Shots")) / total_man_60_shots, 1) if total_man_60_shots > 0 else 0
    avg_s6_60 = round(sum(score.s6t for score in manual_scores.filter(match_type="60-Shots")) / total_man_60_shots, 1) if total_man_60_shots > 0 else 0
    # other things 
    shot_avg_man_40 = round(statistics.mean([score.average for score in manual_scores.filter(match_type="40-Shots")]) ,1) if manual_scores.filter(match_type="40-Shots").exists() else 0
    shot_avg_man_60 = round(statistics.mean([score.average for score in manual_scores.filter(match_type="60-Shots")]) ,1) if manual_scores.filter(match_type="60-Shots").exists() else 0
    shot_avg_man_40_lst = list(manual_scores.filter(match_type="40-Shots").values_list("average", flat=True))
    shot_avg_man_60_lst = list(manual_scores.filter(match_type="60-Shots").values_list("average", flat=True))
    shot_avg_man = round(statistics.mean([score.average for score in manual_scores]),1)
    avg_man_duration = round(statistics.mean([score.duration for score in manual_scores]),1)
    date_man_40 = list(manual_scores.filter(match_type="40-Shots").values_list("date", flat=True))
    date_man_40 = [date.strftime("%Y-%m-%d") for date in date_man_40]  # Convert to string
    date_man_60 = list(manual_scores.filter(match_type="60-Shots").values_list("date", flat=True))
    date_man_60 = [date.strftime("%Y-%m-%d") for date in date_man_60] # pdf calculations
    practice_dates_est = manual_scores.values_list('date', flat=True).distinct()
    streak_count_est = 0
    current_streak_est = 0
    previous_date_est = None

    for date in sorted(practice_dates_est, reverse=True):
        if previous_date_est is None or previous_date_est - date == timedelta(days=1):
            current_streak_est += 1
        else:
            break
        previous_date_est = date
    streak_count_est = current_streak_est
    total_pdf_scores = pdf_scores.count()
    # calculate the total 40 shots matches in pdf scores
    total_pdf_40_shots = pdf_scores.filter(match_type="40-Shots").count()
    last_30_avg_40_est = round(sum([score.total for score in pdf_scores.filter(match_type="40-Shots").order_by('-date')[:30] if score.total is not None]) / min(30, pdf_scores.filter(match_type="40-Shots").count()), 1) if pdf_scores.filter(match_type="40-Shots").count() > 0 else 0
    best_pdf_40_shots = max([score.total for score in pdf_scores.filter(match_type="40-Shots") if score.total is not None],default=0)
    # 40 shots series average
    avg_s1_40_est = round(sum([score.s1t for score in pdf_scores.filter(match_type = "40-Shots")]) / max(1, pdf_scores.filter(match_type = "40-Shots").count()), 1)
    avg_s2_40_est = round(sum([score.s2t for score in pdf_scores.filter(match_type = "40-Shots")]) / max(1, pdf_scores.filter(match_type = "40-Shots").count()), 1)
    avg_s3_40_est = round(sum([score.s3t for score in pdf_scores.filter(match_type = "40-Shots")]) / max(1, pdf_scores.filter(match_type = "40-Shots").count()), 1)
    avg_s4_40_est = round(sum([score.s4t for score in pdf_scores.filter(match_type = "40-Shots")]) / max(1, pdf_scores.filter(match_type = "40-Shots").count()), 1)
    # other things
    est_tot_40_avg = round(statistics.mean(scores), 1) if (scores := [s.total for s in pdf_scores.filter(match_type="40-Shots") if s.total is not None]) else 0
    est_ser_40_avg = round(statistics.mean(scores), 1) if (scores := [s.average_series_score for s in pdf_scores.filter(match_type="40-Shots") if s.average_series_score is not None]) else 0
    est_shot_40_avg = round(statistics.mean(scores), 1) if (scores := [s.average_shot_score for s in pdf_scores.filter(match_type="40-Shots") if s.average_shot_score is not None]) else 0
    # calculate the total 60 shots matches in pdf scores
    total_pdf_60_shots = pdf_scores.filter(match_type="60-Shots").count()
    best_pdf_60_shots = max([score.total for score in pdf_scores.filter(match_type="60-Shots") if score.total is not None],default=0)
    last_30_avg_60_est = round(sum([score.total for score in pdf_scores.filter(match_type="60-Shots").order_by('-date')[:30] if score.total is not None]) / min(30, pdf_scores.filter(match_type="60-Shots").count()), 1) if pdf_scores.filter(match_type="60-Shots").count() > 0 else 0
    duration_40_est = list(pdf_scores.filter(match_type="40-Shots").values_list('duration', flat=True))
    duration_60_est = list(pdf_scores.filter(match_type="60-Shots").values_list('duration', flat=True))
    score_40_est = json.dumps([float(score) for score in pdf_scores.filter(match_type="40-Shots").values_list('total', flat=True)])
    score_60_est = json.dumps([float(score) for score in pdf_scores.filter(match_type="60-Shots").values_list('total', flat=True)])
    date_est_40 = list(pdf_scores.filter(match_type="40-Shots").values_list("date", flat=True))
    date_est_40 = [date.strftime("%Y-%m-%d") for date in date_est_40]  # Convert to string
    date_est_60 = list(pdf_scores.filter(match_type="60-Shots").values_list("date", flat=True))
    date_est_60 = [date.strftime("%Y-%m-%d") for date in date_est_60] # pdf calculations
    avg_group_size_40 = round(statistics.mean([score.gps for score in pdf_scores.filter(match_type="40-Shots")]), 1) if pdf_scores.filter(match_type="40-Shots").exists() else 0
    avg_group_size_60 = round(statistics.mean([score.gps for score in pdf_scores.filter(match_type="60-Shots")]), 1) if pdf_scores.filter(match_type="60-Shots").exists() else 0
    avg_in10_40_est = round(statistics.mean([score.inner_tens for score in pdf_scores.filter(match_type="40-Shots")]), 1) if pdf_scores.filter(match_type="40-Shots").exists() else 0
    avg_in10_60_est = round(statistics.mean([score.inner_tens for score in pdf_scores.filter(match_type="60-Shots")]), 1) if pdf_scores.filter(match_type="60-Shots").exists() else 0
    in10_40_est_lst = list(pdf_scores.filter(match_type="40-Shots").values_list("inner_tens", flat=True))
    in10_60_est_lst = list(pdf_scores.filter(match_type="60-Shots").values_list("inner_tens", flat=True))
    # 60 shots series average
    avg_s1_60_est = round(statistics.mean([score.s1t for score in pdf_scores.filter(match_type = "60-Shots") if score.s1t is not None]), 1) if pdf_scores.filter(match_type = "60-Shots").exists() else None
    avg_s2_60_est = round(statistics.mean([score.s2t for score in pdf_scores.filter(match_type = "60-Shots") if score.s2t is not None]),1) if pdf_scores.filter(match_type = "60-Shots").exists() else None
    avg_s3_60_est = round(statistics.mean([score.s3t for score in pdf_scores.filter(match_type = "60-Shots") if score.s3t is not None]),1) if pdf_scores.filter(match_type = "60-Shots").exists() else None
    avg_s4_60_est = round(statistics.mean([score.s4t for score in pdf_scores.filter(match_type = "60-Shots") if score.s4t is not None]),1) if pdf_scores.filter(match_type = "60-Shots").exists() else None
    avg_s5_60_est = round(statistics.mean([score.s5t for score in pdf_scores.filter(match_type = "60-Shots") if score.s5t is not None]),1) if pdf_scores.filter(match_type = "60-Shots").exists() else None
    avg_s6_60_est = round(statistics.mean([score.s6t for score in pdf_scores.filter(match_type = "60-Shots") if score.s6t is not None]),1) if pdf_scores.filter(match_type = "60-Shots").exists() else None
    # group sizes to list
    # for 60 shots
    filt_est_40 = pdf_scores.filter(match_type="40-Shots")
    filt_est_60 = pdf_scores.filter(match_type="60-Shots")
    avg_gps1_40 = round(sum([score.gps1 for score in filt_est_40 ])/ max(1, filt_est_40.count()), 1) if len(filt_est_40) > 0 else 0
    avg_gps2_40 = round(sum([score.gps2 for score in filt_est_40 ])/ max(1, filt_est_40.count()), 1) if len(filt_est_40) > 0 else 0
    avg_gps3_40 = round(sum([score.gps3 for score in filt_est_40 ])/ max(1, filt_est_40.count()), 1) if len(filt_est_40) > 0 else 0
    avg_gps4_40 = round(sum([score.gps4 for score in filt_est_40 ])/ max(1, filt_est_40.count()), 1) if len(filt_est_40) > 0 else 0
    avg_gps1_60 = round(sum([score.gps1 for score in filt_est_60 ])/ max(1, filt_est_60.count()), 1) if len(filt_est_60) > 0 else 0
    avg_gps2_60 = round(sum([score.gps2 for score in filt_est_60 ])/ max(1, filt_est_60.count()), 1) if len(filt_est_60) > 0 else 0
    avg_gps3_60 = round(sum([score.gps3 for score in filt_est_60 ])/ max(1, filt_est_60.count()), 1) if len(filt_est_60) > 0 else 0
    avg_gps4_60 = round(sum([score.gps4 for score in filt_est_60 ])/ max(1, filt_est_60.count()), 1) if len(filt_est_60) > 0 else 0
    avg_gps5_60 = round(sum([score.gps5 for score in filt_est_60 ])/ max(1, filt_est_60.count()), 1) if len(filt_est_60) > 0 else 0
    avg_gps6_60 = round(sum([score.gps6 for score in filt_est_60 ])/ max(1, filt_est_60.count()), 1) if len(filt_est_60) > 0 else 0

# other things
    est_tot_60_avg = round(statistics.mean([score.total for score in pdf_scores.filter(match_type = "60-Shots")]),1)
    est_ser_60_avg = round(statistics.mean([score.average_series_score for score in pdf_scores.filter(match_type="60-Shots")]),1)
    est_shot_60_avg = round(statistics.mean([score.average_shot_score for score in pdf_scores.filter(match_type="60-Shots")]),1)
    shot_avg_est_40_lst = list(pdf_scores.filter(match_type="40-Shots").values_list("average_shot_score", flat=True))
    shot_avg_est_60_lst = list(pdf_scores.filter(match_type="60-Shots").values_list("average_shot_score", flat=True))
    
    # total calculations
    total_scores = total_manual_scores + total_pdf_scores
    # calculate total 40 shots matches
    total_40_shots = total_man_40_shots + total_pdf_40_shots
    # calculate total 60 shots matches
    total_60_shots = total_man_60_shots + total_pdf_60_shots
    context = {
        'streak_count_man': streak_count_man,
        'total_manual_scores': total_manual_scores,
        'total_man_40_shots': total_man_40_shots,
        'total_man_60_shots': total_man_60_shots,
        'best_man_40_shots': best_man_40_shots,
        'best_man_60_shots': best_man_60_shots,
        'last_30_avg_40_man': last_30_avg_40_man,
        'last_30_avg_60_man': last_30_avg_60_man,
        'duration_40_man': json.dumps([float(d) for d in duration_40_man]),
        'duration_60_man': json.dumps([float(d) for d in duration_60_man]),
    # 40 shots series average
        'avg_s1_40': avg_s1_40,
        'avg_s2_40': avg_s2_40,
        'avg_s3_40': avg_s3_40,
        'avg_s4_40': avg_s4_40,
        'score_40_man': json.dumps([float(s) for s in score_40_man]),
    # 60 shots series average
        'avg_s1_60': avg_s1_60,
        'avg_s2_60': avg_s2_60,
        'avg_s3_60': avg_s3_60,
        'avg_s4_60': avg_s4_60,
        'avg_s5_60': avg_s5_60,
        'avg_s6_60': avg_s6_60,
        'score_60_man': json.dumps([float(s) for s in score_60_man]),
        'shot_avg_man_40': shot_avg_man_40,
        'shot_avg_man_60': shot_avg_man_60,
        'shot_avg_man_40_lst': json.dumps([float(s) for s in shot_avg_man_40_lst]),
        'shot_avg_man_60_lst': json.dumps([float(s) for s in shot_avg_man_60_lst]),
        'date_man_40': json.dumps(date_man_40),
        'date_man_60': json.dumps(date_man_60),
        'shot_avg_man': shot_avg_man,
        'avg_man_duration': avg_man_duration,
        'streak_count_est': streak_count_est,

        'total_pdf_scores': total_pdf_scores,

        'total_pdf_40_shots': total_pdf_40_shots,
        'total_pdf_60_shots': total_pdf_60_shots,
        'best_pdf_40_shots': best_pdf_40_shots,
        'best_pdf_60_shots': best_pdf_60_shots,
        'last_30_avg_40_est': last_30_avg_40_est,
        'last_30_avg_60_est': last_30_avg_60_est,
        'est_tot_40_avg': est_tot_40_avg,
        'est_ser_40_avg': est_ser_40_avg,
        'est_shot_40_avg': est_shot_40_avg,
        'avg_group_size_40': avg_group_size_40,
        'avg_group_size_60': avg_group_size_60,
        'avg_in10_40_est': avg_in10_40_est,
        'avg_in10_60_est': avg_in10_60_est,
        'in10_40_est_lst': json.dumps([float(i) for i in in10_40_est_lst]),
        'in10_60_est_lst': json.dumps([float(i) for i in in10_60_est_lst]),
        'duration_40_est': json.dumps([float(d) for d in duration_40_est]),
        'duration_60_est': json.dumps([float(d) for d in duration_60_est]),
        'shot_avg_est_40_lst': json.dumps([float(s) for s in shot_avg_est_40_lst]),
        'shot_avg_est_60_lst': json.dumps([float(s) for s in shot_avg_est_60_lst]),
        'avg_s1_40_est': avg_s1_40_est,
        'avg_s2_40_est': avg_s2_40_est,
        'avg_s3_40_est': avg_s3_40_est,
        'avg_s4_40_est': avg_s4_40_est,
        'est_tot_60_avg': est_tot_60_avg,
        'est_ser_60_avg': est_ser_60_avg,
        'est_shot_60_avg': est_shot_60_avg,
        'avg_s1_60_est': avg_s1_60_est,
        'avg_s2_60_est': avg_s2_60_est,
        'avg_s3_60_est': avg_s3_60_est,
        'avg_s4_60_est': avg_s4_60_est,
        'avg_s5_60_est': avg_s5_60_est,
        'avg_s6_60_est': avg_s6_60_est,
        'avg_gps1_40': avg_gps1_40,
        'avg_gps2_40': avg_gps2_40,
        'avg_gps3_40': avg_gps3_40,
        'avg_gps4_40': avg_gps4_40,
        'avg_gps1_60': avg_gps1_60,
        'avg_gps2_60': avg_gps2_60,
        'avg_gps3_60': avg_gps3_60,
        'avg_gps4_60': avg_gps4_60,
        'avg_gps5_60': avg_gps5_60,
        'avg_gps6_60': avg_gps6_60,
        'score_40_est': score_40_est,
        'score_60_est': score_60_est,
        'date_est_40': json.dumps(date_est_40),
        'date_est_60': json.dumps(date_est_60),
        'total_scores': total_scores,
        'total_40_shots': total_40_shots,
        'total_60_shots': total_60_shots,
    }
    return render(request, 'dashboard.html', context)

# inspection view
@login_required(login_url='/login/')
def inspect(request, id):
    user_profile = get_object_or_404(UserProfiles, id=id)
    username = user_profile.username
    # fetch all scores for the logged-in user
    manual_scores = manualscore.objects.filter(user_profile=user_profile)
    pdf_scores = pdfScore.objects.filter(user_profile=user_profile)

    
    streak_count_man = 0
    current_streak_man = 0
    previous_date_man = None
    try:
        practice_dates_man = manual_scores.values_list('date', flat=True).distinct()
        for date in sorted(practice_dates_man, reverse=True):
            if previous_date_man is None or previous_date_man - date == timedelta(days=1):
                current_streak_man += 1
            else:
                break
            previous_date_man = date
        streak_count_man = current_streak_man
    except Exception:
        streak_count_man = 0

    # calculate the total number of scores
    duration_40_man = list(manual_scores.filter(match_type="40-Shots").values_list('duration', flat=True))
    duration_60_man = list(manual_scores.filter(match_type="60-Shots").values_list('duration', flat=True))
    score_40_man = list(manual_scores.filter(match_type="40-Shots").values_list('total', flat=True))
    score_60_man = list(manual_scores.filter(match_type="60-Shots").values_list('total', flat=True))
    # manual calculations    
    total_manual_scores = manual_scores.count()
    # calculate tht total 40 shots matches in manual scores
    total_man_40_shots = manual_scores.filter(match_type="40-Shots").count()
    # calculate the total 60 shots matches in manual scores
    total_man_60_shots = manual_scores.filter(match_type="60-Shots").count()
    best_man_40_shots = max([score.total for score in manual_scores.filter(match_type="40-Shots") if score.total is not None],default=0)
    best_man_60_shots = max([score.total for score in manual_scores.filter(match_type="60-Shots") if score.total is not None],default=0)
    last_30_avg_40_man = round(sum(score.total for score in manual_scores.filter(match_type="40-Shots").order_by('-date')[:30]) / count_40, 2) if (count_40 := manual_scores.filter(match_type="40-Shots").order_by('-date')[:30].count()) > 0 else 0   
    last_30_avg_60_man = round(sum(score.total for score in manual_scores.filter(match_type="60-Shots").order_by('-date')[:30]) / count_60, 2) if (count_60 := manual_scores.filter(match_type="60-Shots").order_by('-date')[:30].count()) > 0 else 0
    # 40 shots series average
    avg_s1_40 = round(sum(score.s1t for score in manual_scores.filter(match_type="40-Shots")) / total_man_40_shots, 1) if (total_man_40_shots := manual_scores.filter(match_type="40-Shots").count()) > 0 else 0
    avg_s2_40 = round(sum(score.s2t for score in manual_scores.filter(match_type="40-Shots")) / total_man_40_shots, 1) if total_man_40_shots > 0 else 0
    avg_s3_40 = round(sum(score.s3t for score in manual_scores.filter(match_type="40-Shots")) / total_man_40_shots, 1) if total_man_40_shots > 0 else 0
    avg_s4_40 = round(sum(score.s4t for score in manual_scores.filter(match_type="40-Shots")) / total_man_40_shots, 1) if total_man_40_shots > 0 else 0
    # 60-Shots series average
    avg_s1_60 = round(sum(score.s1t for score in manual_scores.filter(match_type="60-Shots")) / total_man_60_shots, 1) if (total_man_60_shots := manual_scores.filter(match_type="60-Shots").count()) > 0 else 0
    avg_s2_60 = round(sum(score.s2t for score in manual_scores.filter(match_type="60-Shots")) / total_man_60_shots, 1) if total_man_60_shots > 0 else 0
    avg_s3_60 = round(sum(score.s3t for score in manual_scores.filter(match_type="60-Shots")) / total_man_60_shots, 1) if total_man_60_shots > 0 else 0
    avg_s4_60 = round(sum(score.s4t for score in manual_scores.filter(match_type="60-Shots")) / total_man_60_shots, 1) if total_man_60_shots > 0 else 0
    avg_s5_60 = round(sum(score.s5t for score in manual_scores.filter(match_type="60-Shots")) / total_man_60_shots, 1) if total_man_60_shots > 0 else 0
    avg_s6_60 = round(sum(score.s6t for score in manual_scores.filter(match_type="60-Shots")) / total_man_60_shots, 1) if total_man_60_shots > 0 else 0
    # other things 
    shot_avg_man_40 = round(statistics.mean([score.average for score in manual_scores.filter(match_type="40-Shots")]) ,1) if manual_scores.filter(match_type="40-Shots").exists() else 0
    shot_avg_man_60 = round(statistics.mean([score.average for score in manual_scores.filter(match_type="60-Shots")]) ,1) if manual_scores.filter(match_type="60-Shots").exists() else 0
    shot_avg_man_40_lst = list(manual_scores.filter(match_type="40-Shots").values_list("average", flat=True))
    shot_avg_man_60_lst = list(manual_scores.filter(match_type="60-Shots").values_list("average", flat=True))
    # shot_avg_man = round(statistics.mean([score.average for score in manual_scores]),1)
    # avg_man_duration = round(statistics.mean([score.duration for score in manual_scores]),1)
    if manual_scores:
        shot_avg_man = round(statistics.mean([score.average for score in manual_scores]), 1)
        avg_man_duration = round(statistics.mean([score.duration for score in manual_scores]), 1)
    else:
        shot_avg_man = 0.0  # or None, or "-"
        avg_man_duration = 0.0
    date_man_40 = list(manual_scores.filter(match_type="40-Shots").values_list("date", flat=True))
    date_man_40 = [date.strftime("%Y-%m-%d") for date in date_man_40]  # Convert to string
    date_man_60 = list(manual_scores.filter(match_type="60-Shots").values_list("date", flat=True))
    date_man_60 = [date.strftime("%Y-%m-%d") for date in date_man_60] # pdf calculations
    practice_dates_est = manual_scores.values_list('date', flat=True).distinct()
    streak_count_est = 0
    current_streak_est = 0
    previous_date_est = None

    for date in sorted(practice_dates_est, reverse=True):
        if previous_date_est is None or previous_date_est - date == timedelta(days=1):
            current_streak_est += 1
        else:
            break
        previous_date_est = date
    streak_count_est = current_streak_est
    total_pdf_scores = pdf_scores.count()
    # calculate the total 40 shots matches in pdf scores
    total_pdf_40_shots = pdf_scores.filter(match_type="40-Shots").count()
    last_30_avg_40_est = round(sum([score.total for score in pdf_scores.filter(match_type="40-Shots").order_by('-date')[:30] if score.total is not None]) / min(30, pdf_scores.filter(match_type="40-Shots").count()), 1) if pdf_scores.filter(match_type="40-Shots").count() > 0 else 0
    best_pdf_40_shots = max([score.total for score in pdf_scores.filter(match_type="40-Shots") if score.total is not None],default=0)
    # 40 shots series average
    avg_s1_40_est = round(sum([score.s1t for score in pdf_scores.filter(match_type = "40-Shots")]) / max(1, pdf_scores.filter(match_type = "40-Shots").count()), 1)
    avg_s2_40_est = round(sum([score.s2t for score in pdf_scores.filter(match_type = "40-Shots")]) / max(1, pdf_scores.filter(match_type = "40-Shots").count()), 1)
    avg_s3_40_est = round(sum([score.s3t for score in pdf_scores.filter(match_type = "40-Shots")]) / max(1, pdf_scores.filter(match_type = "40-Shots").count()), 1)
    avg_s4_40_est = round(sum([score.s4t for score in pdf_scores.filter(match_type = "40-Shots")]) / max(1, pdf_scores.filter(match_type = "40-Shots").count()), 1)
    # other things
    est_tot_40_avg = round(statistics.mean(scores), 1) if (scores := [s.total for s in pdf_scores.filter(match_type="40-Shots") if s.total is not None]) else 0
    est_ser_40_avg = round(statistics.mean(scores), 1) if (scores := [s.average_series_score for s in pdf_scores.filter(match_type="40-Shots") if s.average_series_score is not None]) else 0
    est_shot_40_avg = round(statistics.mean(scores), 1) if (scores := [s.average_shot_score for s in pdf_scores.filter(match_type="40-Shots") if s.average_shot_score is not None]) else 0
    # calculate the total 60 shots matches in pdf scores
    total_pdf_60_shots = pdf_scores.filter(match_type="60-Shots").count()
    best_pdf_60_shots = max([score.total for score in pdf_scores.filter(match_type="60-Shots") if score.total is not None],default=0)
    last_30_avg_60_est = round(sum([score.total for score in pdf_scores.filter(match_type="60-Shots").order_by('-date')[:30] if score.total is not None]) / min(30, pdf_scores.filter(match_type="60-Shots").count()), 1) if pdf_scores.filter(match_type="60-Shots").count() > 0 else 0
    duration_40_est = list(pdf_scores.filter(match_type="40-Shots").values_list('duration', flat=True))
    duration_60_est = list(pdf_scores.filter(match_type="60-Shots").values_list('duration', flat=True))
    score_40_est = json.dumps([float(score) for score in pdf_scores.filter(match_type="40-Shots").values_list('total', flat=True)])
    score_60_est = json.dumps([float(score) for score in pdf_scores.filter(match_type="60-Shots").values_list('total', flat=True)])
    date_est_40 = list(pdf_scores.filter(match_type="40-Shots").values_list("date", flat=True))
    date_est_40 = [date.strftime("%Y-%m-%d") for date in date_est_40]  # Convert to string
    date_est_60 = list(pdf_scores.filter(match_type="60-Shots").values_list("date", flat=True))
    date_est_60 = [date.strftime("%Y-%m-%d") for date in date_est_60] # pdf calculations
    avg_group_size_40 = round(statistics.mean([score.gps for score in pdf_scores.filter(match_type="40-Shots")]), 1) if pdf_scores.filter(match_type="40-Shots").exists() else 0
    avg_group_size_60 = round(statistics.mean([score.gps for score in pdf_scores.filter(match_type="60-Shots")]), 1) if pdf_scores.filter(match_type="60-Shots").exists() else 0
    avg_in10_40_est = round(statistics.mean([score.inner_tens for score in pdf_scores.filter(match_type="40-Shots")]), 1) if pdf_scores.filter(match_type="40-Shots").exists() else 0
    avg_in10_60_est = round(statistics.mean([score.inner_tens for score in pdf_scores.filter(match_type="60-Shots")]), 1) if pdf_scores.filter(match_type="60-Shots").exists() else 0
    in10_40_est_lst = list(pdf_scores.filter(match_type="40-Shots").values_list("inner_tens", flat=True))
    in10_60_est_lst = list(pdf_scores.filter(match_type="60-Shots").values_list("inner_tens", flat=True))
    # 60 shots series average
    avg_s1_60_est = round(statistics.mean([score.s1t for score in pdf_scores.filter(match_type = "60-Shots") if score.s1t is not None]), 1) if pdf_scores.filter(match_type = "60-Shots").exists() else None
    avg_s2_60_est = round(statistics.mean([score.s2t for score in pdf_scores.filter(match_type = "60-Shots") if score.s2t is not None]),1) if pdf_scores.filter(match_type = "60-Shots").exists() else None
    avg_s3_60_est = round(statistics.mean([score.s3t for score in pdf_scores.filter(match_type = "60-Shots") if score.s3t is not None]),1) if pdf_scores.filter(match_type = "60-Shots").exists() else None
    avg_s4_60_est = round(statistics.mean([score.s4t for score in pdf_scores.filter(match_type = "60-Shots") if score.s4t is not None]),1) if pdf_scores.filter(match_type = "60-Shots").exists() else None
    avg_s5_60_est = round(statistics.mean([score.s5t for score in pdf_scores.filter(match_type = "60-Shots") if score.s5t is not None]),1) if pdf_scores.filter(match_type = "60-Shots").exists() else None
    avg_s6_60_est = round(statistics.mean([score.s6t for score in pdf_scores.filter(match_type = "60-Shots") if score.s6t is not None]),1) if pdf_scores.filter(match_type = "60-Shots").exists() else None
    # group sizes to list
    # for 60 shots
    filt_est_40 = pdf_scores.filter(match_type="40-Shots")
    filt_est_60 = pdf_scores.filter(match_type="60-Shots")
    avg_gps1_40 = round(sum([score.gps1 for score in filt_est_40 ])/ max(1, filt_est_40.count()), 1) if len(filt_est_40) > 0 else 0
    avg_gps2_40 = round(sum([score.gps2 for score in filt_est_40 ])/ max(1, filt_est_40.count()), 1) if len(filt_est_40) > 0 else 0
    avg_gps3_40 = round(sum([score.gps3 for score in filt_est_40 ])/ max(1, filt_est_40.count()), 1) if len(filt_est_40) > 0 else 0
    avg_gps4_40 = round(sum([score.gps4 for score in filt_est_40 ])/ max(1, filt_est_40.count()), 1) if len(filt_est_40) > 0 else 0
    avg_gps1_60 = round(sum([score.gps1 for score in filt_est_60 ])/ max(1, filt_est_60.count()), 1) if len(filt_est_60) > 0 else 0
    avg_gps2_60 = round(sum([score.gps2 for score in filt_est_60 ])/ max(1, filt_est_60.count()), 1) if len(filt_est_60) > 0 else 0
    avg_gps3_60 = round(sum([score.gps3 for score in filt_est_60 ])/ max(1, filt_est_60.count()), 1) if len(filt_est_60) > 0 else 0
    avg_gps4_60 = round(sum([score.gps4 for score in filt_est_60 ])/ max(1, filt_est_60.count()), 1) if len(filt_est_60) > 0 else 0
    avg_gps5_60 = round(sum([score.gps5 for score in filt_est_60 ])/ max(1, filt_est_60.count()), 1) if len(filt_est_60) > 0 else 0
    avg_gps6_60 = round(sum([score.gps6 for score in filt_est_60 ])/ max(1, filt_est_60.count()), 1) if len(filt_est_60) > 0 else 0

# other things
    est_tot_60_avg = round(statistics.mean([score.total for score in pdf_scores.filter(match_type = "60-Shots")]),1) if pdf_scores.filter(match_type = "60-Shots").exists() else 0
    est_ser_60_avg = round(statistics.mean([score.average_series_score for score in pdf_scores.filter(match_type="60-Shots")]),1) if pdf_scores.filter(match_type="60-Shots").exists() else 0
    est_shot_60_avg = round(statistics.mean([score.average_shot_score for score in pdf_scores.filter(match_type="60-Shots")]),1) if pdf_scores.filter(match_type="60-Shots").exists() else 0
    shot_avg_est_40_lst = list(pdf_scores.filter(match_type="40-Shots").values_list("average_shot_score", flat=True))
    shot_avg_est_60_lst = list(pdf_scores.filter(match_type="60-Shots").values_list("average_shot_score", flat=True))
    
    # total calculations
    total_scores = total_manual_scores + total_pdf_scores
    # calculate total 40 shots matches
    total_40_shots = total_man_40_shots + total_pdf_40_shots
    # calculate total 60 shots matches
    total_60_shots = total_man_60_shots + total_pdf_60_shots
    context = {
        'username': username,
        'streak_count_man': streak_count_man,
        'total_manual_scores': total_manual_scores,
        'total_man_40_shots': total_man_40_shots,
        'total_man_60_shots': total_man_60_shots,
        'best_man_40_shots': best_man_40_shots,
        'best_man_60_shots': best_man_60_shots,
        'last_30_avg_40_man': last_30_avg_40_man,
        'last_30_avg_60_man': last_30_avg_60_man,
        'duration_40_man': json.dumps([float(d) for d in duration_40_man]),
        'duration_60_man': json.dumps([float(d) for d in duration_60_man]),
    # 40 shots series average
        'avg_s1_40': avg_s1_40,
        'avg_s2_40': avg_s2_40,
        'avg_s3_40': avg_s3_40,
        'avg_s4_40': avg_s4_40,
        'score_40_man': json.dumps([float(s) for s in score_40_man]),
    # 60 shots series average
        'avg_s1_60': avg_s1_60,
        'avg_s2_60': avg_s2_60,
        'avg_s3_60': avg_s3_60,
        'avg_s4_60': avg_s4_60,
        'avg_s5_60': avg_s5_60,
        'avg_s6_60': avg_s6_60,
        'score_60_man': json.dumps([float(s) for s in score_60_man]),
        'shot_avg_man_40': shot_avg_man_40,
        'shot_avg_man_60': shot_avg_man_60,
        'shot_avg_man_40_lst': json.dumps([float(s) for s in shot_avg_man_40_lst]),
        'shot_avg_man_60_lst': json.dumps([float(s) for s in shot_avg_man_60_lst]),
        'date_man_40': json.dumps(date_man_40),
        'date_man_60': json.dumps(date_man_60),
        'shot_avg_man': shot_avg_man,
        'avg_man_duration': avg_man_duration,
        'streak_count_est': streak_count_est,

        'total_pdf_scores': total_pdf_scores,

        'total_pdf_40_shots': total_pdf_40_shots,
        'total_pdf_60_shots': total_pdf_60_shots,
        'best_pdf_40_shots': best_pdf_40_shots,
        'best_pdf_60_shots': best_pdf_60_shots,
        'last_30_avg_40_est': last_30_avg_40_est,
        'last_30_avg_60_est': last_30_avg_60_est,
        'est_tot_40_avg': est_tot_40_avg,
        'est_ser_40_avg': est_ser_40_avg,
        'est_shot_40_avg': est_shot_40_avg,
        'avg_group_size_40': avg_group_size_40,
        'avg_group_size_60': avg_group_size_60,
        'avg_in10_40_est': avg_in10_40_est,
        'avg_in10_60_est': avg_in10_60_est,
        'in10_40_est_lst': json.dumps([float(i) for i in in10_40_est_lst]),
        'in10_60_est_lst': json.dumps([float(i) for i in in10_60_est_lst]),
        'duration_40_est': json.dumps([float(d) for d in duration_40_est]),
        'duration_60_est': json.dumps([float(d) for d in duration_60_est]),
        'shot_avg_est_40_lst': json.dumps([float(s) for s in shot_avg_est_40_lst]),
        'shot_avg_est_60_lst': json.dumps([float(s) for s in shot_avg_est_60_lst]),
        'avg_s1_40_est': avg_s1_40_est,
        'avg_s2_40_est': avg_s2_40_est,
        'avg_s3_40_est': avg_s3_40_est,
        'avg_s4_40_est': avg_s4_40_est,
        'est_tot_60_avg': est_tot_60_avg,
        'est_ser_60_avg': est_ser_60_avg,
        'est_shot_60_avg': est_shot_60_avg,
        'avg_s1_60_est': avg_s1_60_est,
        'avg_s2_60_est': avg_s2_60_est,
        'avg_s3_60_est': avg_s3_60_est,
        'avg_s4_60_est': avg_s4_60_est,
        'avg_s5_60_est': avg_s5_60_est,
        'avg_s6_60_est': avg_s6_60_est,
        'avg_gps1_40': avg_gps1_40,
        'avg_gps2_40': avg_gps2_40,
        'avg_gps3_40': avg_gps3_40,
        'avg_gps4_40': avg_gps4_40,
        'avg_gps1_60': avg_gps1_60,
        'avg_gps2_60': avg_gps2_60,
        'avg_gps3_60': avg_gps3_60,
        'avg_gps4_60': avg_gps4_60,
        'avg_gps5_60': avg_gps5_60,
        'avg_gps6_60': avg_gps6_60,
        'score_40_est': score_40_est,
        'score_60_est': score_60_est,
        'date_est_40': json.dumps(date_est_40),
        'date_est_60': json.dumps(date_est_60),
        'total_scores': total_scores,
        'total_40_shots': total_40_shots,
        'total_60_shots': total_60_shots,
    }
    return render(request, 'inspect.html', context)
# Create your views here.