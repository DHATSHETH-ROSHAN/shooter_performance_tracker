from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import manualscore
from .models import pdfScore
from users.models import UserProfiles
from django.utils.dateparse import parse_date
import fitz
import re
from datetime import datetime
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
        print(full_text)
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
        latest_score = manualscore.objects.filter(user_profile=user).order_by("-current_time").first()
        print(latest_score)    
    elif source == "pdf":
        latest_score = pdfScore.objects.filter(user_profile=user).order_by("-date").first()
    else:
        latest_score = None
    if not latest_score:
        return JsonResponse({"error": "No scores found"}, status=404)

    return render(request, 'current_analytics.html')

# Create your views here.
