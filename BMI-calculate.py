
# ============================================
# ADVANCED BMI CALCULATOR
# Python + SQLite + Matplotlib + GUI
# Google Colab Version
# ============================================

import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import ipywidgets as widgets

from IPython.display import display, clear_output
from datetime import datetime

# ============================================
# 1. DATABASE CONNECTION
# ============================================

DB_NAME = "bmi_database.db"

def connect_db():
    return sqlite3.connect(DB_NAME)

def create_database():
    try:
        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bmi_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                weight REAL NOT NULL,
                height REAL NOT NULL,
                bmi REAL NOT NULL,
                category TEXT NOT NULL,
                date TEXT NOT NULL
            )
        """)

        conn.commit()
        conn.close()

    except sqlite3.Error as e:
        print("Database Error:", e)


create_database()


# ============================================
# 2. BMI CALCULATION
# ============================================

def calculate_bmi(weight, height):

    if weight <= 0 or height <= 0:
        raise ValueError("Weight and height must be positive.")

    bmi = weight / (height ** 2)

    if bmi < 18.5:
        category = "Underweight"
    elif bmi < 25:
        category = "Normal"
    elif bmi < 30:
        category = "Overweight"
    else:
        category = "Obese"

    return round(bmi, 2), category


# ============================================
# 3. SAVE RECORD IN DATABASE
# ============================================

def save_record(username, weight, height, bmi, category):

    try:
        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO bmi_records
            (username, weight, height, bmi, category, date)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            username,
            weight,
            height,
            bmi,
            category,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))

        conn.commit()
        conn.close()

        return True

    except sqlite3.Error as e:
        print("Database Save Error:", e)
        return False


# ============================================
# 4. GET USER HISTORY
# ============================================

def get_history(username):

    try:
        conn = connect_db()

        df = pd.read_sql_query(
            """
            SELECT weight, height, bmi, category, date
            FROM bmi_records
            WHERE username = ?
            ORDER BY date ASC
            """,
            conn,
            params=(username,)
        )

        conn.close()
        return df

    except sqlite3.Error as e:
        print("Database Read Error:", e)
        return pd.DataFrame()


# ============================================
# 5. BMI GRAPH
# ============================================

def show_graph(username):

    df = get_history(username)

    if df.empty:
        print("No history available for this user.")
        return

    plt.figure(figsize=(10, 5))

    plt.plot(
        range(1, len(df) + 1),
        df["bmi"],
        marker="o",
        linewidth=2
    )

    plt.title(f"BMI History - {username}")
    plt.xlabel("Record Number")
    plt.ylabel("BMI")

    plt.xticks(range(1, len(df) + 1))

    plt.grid(True)
    plt.tight_layout()
    plt.show()


# ============================================
# 6. GUI DESIGN
# ============================================

title = widgets.HTML(
    """
    <div style="
        background: linear-gradient(120deg,#172554,#2563eb);
        padding:25px;
        border-radius:15px;
        color:white;
        text-align:center;
    ">
        <h1>⚖️ BMI CALCULATOR</h1>
        <p>Advanced Python Health Calculator</p>
    </div>
    """
)

username_input = widgets.Text(
    placeholder="Enter your name",
    description="Name:",
    layout=widgets.Layout(width="350px")
)

weight_input = widgets.FloatText(
    description="Weight:",
    value=60,
    layout=widgets.Layout(width="350px")
)

height_input = widgets.FloatText(
    description="Height:",
    value=1.70,
    layout=widgets.Layout(width="350px")
)

calculate_button = widgets.Button(
    description="Calculate BMI",
    button_style="success",
    icon="calculator",
    layout=widgets.Layout(width="180px", height="40px")
)

history_button = widgets.Button(
    description="View History",
    button_style="info",
    icon="history"
)

graph_button = widgets.Button(
    description="Show BMI Graph",
    button_style="primary",
    icon="line-chart"
)

output = widgets.Output()


# ============================================
# 7. CALCULATE BUTTON FUNCTION
# ============================================

def calculate_button_clicked(b):

    with output:
        clear_output()

        username = username_input.value.strip()
        weight = weight_input.value
        height = height_input.value

        try:

            if not username:
                print("❌ Please enter your name.")
                return

            if weight <= 0 or height <= 0:
                print("❌ Weight and height must be positive.")
                return

            bmi, category = calculate_bmi(weight, height)

            print("=" * 40)
            print("          BMI CALCULATION")
            print("=" * 40)

            print(f"User: {username}")
            print(f"Weight: {weight} kg")
            print(f"Height: {height} m")
            print(f"BMI: {bmi}")
            print(f"Category: {category}")

            print("=" * 40)

            colors = {
                "Underweight": "#3498db",
                "Normal": "#27ae60",
                "Overweight": "#e67e22",
                "Obese": "#e74c3c"
            }

            display(widgets.HTML(
                f"""
                <div style="
                    background:{colors[category]};
                    padding:20px;
                    border-radius:12px;
                    color:white;
                    text-align:center;
                    margin-top:10px;
                ">
                    <h2>BMI: {bmi}</h2>
                    <h3>{category}</h3>
                </div>
                """
            ))

            if save_record(username, weight, height, bmi, category):
                print("✅ Record saved successfully!")
            else:
                print("⚠️ Could not save record.")

            print(
                "\nNote: BMI is a screening measure, "
                "not a diagnosis. Adult categories are "
                "not appropriate for teenagers."
            )

        except (ValueError, TypeError) as e:
            print("Input Error:", e)

        except Exception as e:
            print("Unexpected Error:", e)


# ============================================
# 8. HISTORY BUTTON FUNCTION
# ============================================

def history_button_clicked(b):

    with output:
        clear_output()

        username = username_input.value.strip()

        if not username:
            print("❌ Enter a username first.")
            return

        df = get_history(username)

        if df.empty:
            print("No records found for", username)

        else:
            print("📋 BMI HISTORY:", username)
            display(df)


# ============================================
# 9. GRAPH BUTTON FUNCTION
# ============================================

def graph_button_clicked(b):

    with output:
        clear_output()

        username = username_input.value.strip()

        if not username:
            print("❌ Enter a username first.")
            return

        show_graph(username)


# ============================================
# 10. CONNECT BUTTON EVENTS
# ============================================

calculate_button.on_click(calculate_button_clicked)
history_button.on_click(history_button_clicked)
graph_button.on_click(graph_button_clicked)


# ============================================
# 11. DISPLAY APPLICATION
# ============================================

app = widgets.VBox([

    title,

    widgets.HTML("<h3>👤 User Information</h3>"),

    username_input,

    widgets.HTML("<h3>📏 Body Measurements</h3>"),

    weight_input,

    height_input,

    calculate_button,

    widgets.HTML("<hr><h3>📊 BMI Dashboard</h3>"),

    widgets.HBox([
        history_button,
        graph_button
    ]),

    output

], layout=widgets.Layout(
    width="100%",
    padding="15px"
))

display(app)

print("✅ BMI Calculator Application Started!")