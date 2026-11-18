"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
import base64
import hashlib
import hmac
import json
import os
from pathlib import Path
import time

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

SESSION_COOKIE_NAME = "teacher_session"
SESSION_DURATION_SECONDS = 8 * 60 * 60


class LoginRequest(BaseModel):
    username: str
    password: str


def _auth_settings():
    credentials_value = os.getenv("TEACHER_CREDENTIALS")
    session_secret = os.getenv("SESSION_SECRET")

    if not credentials_value or not session_secret:
        return None
    if len(session_secret) < 32:
        raise HTTPException(
            status_code=503,
            detail="Teacher authentication is misconfigured"
        )

    try:
        credentials = json.loads(credentials_value)
    except json.JSONDecodeError as error:
        raise HTTPException(
            status_code=503,
            detail="Teacher authentication is misconfigured"
        ) from error

    if (
        not isinstance(credentials, dict)
        or not credentials
        or not all(
            isinstance(username, str)
            and username
            and isinstance(password, str)
            and password
            for username, password in credentials.items()
        )
    ):
        raise HTTPException(
            status_code=503,
            detail="Teacher authentication is misconfigured"
        )

    return credentials, session_secret


def _session_token(username: str, expires_at: int, session_secret: str) -> str:
    payload = base64.urlsafe_b64encode(
        f"{username}:{expires_at}".encode()
    ).rstrip(b"=").decode()
    signature = hmac.new(
        session_secret.encode(), payload.encode(), hashlib.sha256
    ).hexdigest()
    return f"{payload}.{signature}"


def _session_username(request: Request, session_secret: str):
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token:
        return None

    try:
        payload, signature = token.split(".", 1)
        expected_signature = hmac.new(
            session_secret.encode(), payload.encode(), hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(signature, expected_signature):
            return None

        encoded_payload = payload + "=" * (-len(payload) % 4)
        username, expires_at = base64.urlsafe_b64decode(
            encoded_payload
        ).decode().rsplit(":", 1)
        if int(expires_at) <= int(time.time()):
            return None
        return username
    except (ValueError, UnicodeDecodeError):
        return None


def require_teacher(request: Request):
    settings = _auth_settings()
    if settings is None:
        raise HTTPException(
            status_code=503,
            detail="Teacher authentication is not configured"
        )

    credentials, session_secret = settings
    username = _session_username(request, session_secret)
    if username not in credentials:
        raise HTTPException(status_code=401, detail="Teacher login required")
    return username


# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

# In-memory activity database
activities = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"]
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"]
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"]
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"]
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"]
    }
}


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    return activities


@app.post("/auth/login")
def login(login_request: LoginRequest, request: Request, response: Response):
    settings = _auth_settings()
    if settings is None:
        raise HTTPException(
            status_code=503,
            detail="Teacher authentication is not configured"
        )

    credentials, session_secret = settings
    expected_password = credentials.get(login_request.username)
    if (
        expected_password is None
        or not hmac.compare_digest(
            login_request.password.encode(), expected_password.encode()
        )
    ):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    expires_at = int(time.time()) + SESSION_DURATION_SECONDS
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=_session_token(login_request.username, expires_at, session_secret),
        max_age=SESSION_DURATION_SECONDS,
        httponly=True,
        secure=request.url.scheme == "https",
        samesite="strict",
        path="/",
    )
    return {"message": "Logged in"}


@app.post("/auth/logout")
def logout(response: Response):
    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        httponly=True,
        samesite="strict",
        path="/",
    )
    return {"message": "Logged out"}


@app.get("/auth/session")
def get_session(request: Request):
    settings = _auth_settings()
    if settings is None:
        raise HTTPException(
            status_code=503,
            detail="Teacher authentication is not configured"
        )

    credentials, session_secret = settings
    username = _session_username(request, session_secret)
    return {"authenticated": username in credentials}


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(
    activity_name: str, email: str, _teacher: str = Depends(require_teacher)
):
    """Sign up a student for an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is not already signed up
    if email in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is already signed up"
        )

    # Add student
    activity["participants"].append(email)
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(
    activity_name: str, email: str, _teacher: str = Depends(require_teacher)
):
    """Unregister a student from an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is signed up
    if email not in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is not signed up for this activity"
        )

    # Remove student
    activity["participants"].remove(email)
    return {"message": f"Unregistered {email} from {activity_name}"}
