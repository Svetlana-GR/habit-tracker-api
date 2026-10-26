from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from datetime import date, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Habit Tracker API", version="1.0.0")

# В памяти (словарь). Ключ - ID привычки, значение - данные.
habits_db = {}
habit_counter = 1

class HabitCreate(BaseModel):
    name: str

class HabitCheck(BaseModel):
    check_date: date | None = None  # Если дата не передана, возьмем сегодня

def get_next_id():
    global habit_counter
    current = habit_counter
    habit_counter += 1
    return current

@app.get("/")
def read_root():
    return {"message": "Habit Tracker API is running"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/version")
def get_version():
    return {"version": "1.0.0"}

@app.get("/habits")
def list_habits():
    return [habits_db[key] for key in sorted(habits_db.keys())]

@app.post("/habits")
def create_habit(habit: HabitCreate):
    max_habits = int(os.getenv("MAX_DAILY_HABITS", 5))
    if len(habits_db) >= max_habits:
        raise HTTPException(status_code=400, detail="Habit limit reached")
    
    habit_id = get_next_id()
    habits_db[habit_id] = {
        "name": habit.name,
        "streak": 0,
        "last_checked": None
    }
    print(f"[EVENT] Habit '{habit.name}' (ID: {habit_id}) created.")
    return {"id": habit_id, **habits_db[habit_id]}

@app.post("/habits/{habit_id}/check")
def check_habit(habit_id: int, data: HabitCheck):
    if habit_id not in habits_db:
        raise HTTPException(status_code=404, detail="Habit not found")
    
    habit = habits_db[habit_id]
    # Если дата не пришла в запросе, используем сегодняшнюю
    check_date = data.check_date or date.today()
    
    last_date_str = habit["last_checked"]
    
    if last_date_str is None:
        # Первый чек в истории привычки
        new_streak = 1
    else:
        last_date = date.fromisoformat(last_date_str)
        
        if check_date == last_date:
            return {"message": "Already checked for this date", "streak": habit["streak"]}
        elif check_date == last_date + timedelta(days=1):
            new_streak = habit["streak"] + 1
        elif check_date > last_date + timedelta(days=1):
            new_streak = 1  # Сброс серии из-за пропуска
        else:
            raise HTTPException(status_code=400, detail="Cannot check date in the past")
    
    habits_db[habit_id]["streak"] = new_streak
    habits_db[habit_id]["last_checked"] = check_date.isoformat()
    
    print(f"[EVENT] Habit '{habit['name']}' (ID: {habit_id}) checked for {check_date}. Streak: {new_streak}")
    return {"message": "Checked", "streak": new_streak}
