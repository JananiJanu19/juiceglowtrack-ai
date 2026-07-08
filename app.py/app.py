
import streamlit as st
import pandas as pd
import json
from pathlib import Path
from datetime import date, timedelta
import base64

st.set_page_config(page_title="GlowTrack AI", page_icon="✨", layout="wide")

DATA_DIR = Path("glowtrack_data")
DATA_DIR.mkdir(exist_ok=True)

DAILY_LOG_FILE = DATA_DIR / "daily_log.json"
CHECKPOINT_FILE = DATA_DIR / "checkpoints.json"
IMAGE_DIR = DATA_DIR / "checkpoint_images"
IMAGE_DIR.mkdir(exist_ok=True)

JUICE_OPTIONS = [
    "Carrot Orange Glow Juice",
    "Beetroot Skin Glow Juice",
    "Amla Vitamin C Clarity Juice",
    "Cucumber Hydration Juice",
    "Papaya Skin Repair Smoothie"
]

HYDRATION_OPTIONS = ["", "Dry", "Normal", "Hydrated"]
SKIN_LOOK_OPTIONS = ["", "Dull", "Normal", "Fresh / Glowy"]
BREAKOUT_OPTIONS = ["", "None", "Mild", "Moderate", "Bad"]
DIGESTION_OPTIONS = ["", "Bad", "Okay", "Good"]

CHECKPOINT_DAYS = [1, 15, 30, 60, 90, 120, 180, 270, 365]

AI_GUIDANCE = {
    15: {
        "title": "Day 15",
        "text": """
**What may improve by now**
- Slightly better hydration if your water intake and sleep are not terrible.
- Mild reduction in dryness/dullness if you were previously inconsistent with fruit/veg intake.
- Digestion may feel a bit lighter if the juices replaced junk snacks instead of adding extra sugar on top.

**What probably won’t change much yet**
- Pigmentation
- Acne marks
- Large pore appearance
- Chronic acne if the real trigger is hormones, stress, or bad skincare
"""
    },
    30: {
        "title": "Day 30",
        "text": """
**What may improve by now**
- Skin can look a bit fresher and less tired if you’ve been consistent.
- Puffiness and dehydration-related dullness may reduce slightly.
- If amla/cucumber/papaya are regular and your overall diet is cleaner, your face may look less “flat” and more hydrated.

**Still don’t expect miracles**
- Juice alone is not going to erase pigmentation or acne scars.
- If sunscreen, sleep, and protein are poor, results will plateau fast.
"""
    },
    60: {
        "title": "Day 60",
        "text": """
**What may improve by now**
- Better overall consistency in hydration and digestion.
- Skin may hold moisture better and look less dull day-to-day.
- Some people may notice fewer random breakouts if the rest of the routine improved too.

**Still depends on other variables**
- If you’re using irritating skincare, sleeping badly, or eating inflammatory junk, juice won’t save you.
"""
    },
    90: {
        "title": "Day 90",
        "text": """
**Best-case realistic outcome**
- More consistent brightness and hydration.
- Better habit discipline and a clearer sense of what helps your skin.
- Slight improvement in overall “healthy” look if the rest of your routine is decent.

**Reality check**
- Pigmentation, acne scarring, and texture usually need a lot more than juice.
- This should be treated as a support habit, not the main treatment.
"""
    },
    180: {
        "title": "Day 180",
        "text": """
**Now you’re in the range where long-term habits matter**
- If you were genuinely consistent with nutrition, sleep, sunscreen, and barrier-friendly skincare, this is where more noticeable changes can show.
- Skin tone evenness and baseline hydration may be better than at the start.
"""
    },
    365: {
        "title": "Day 365",
        "text": """
**One year is enough time to judge whether your routine works**
- You should be able to compare baseline vs current skin clearly.
- By now the useful insight is not “which juice is best,” but **which full routine consistently gives you better skin**.
"""
    }
}

def load_json(path, default):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return default
    return default

def save_json(path, data):
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")

def default_daily_log(days=365):
    start = date.today()
    rows = []
    for i in range(days):
        d = start + timedelta(days=i)
        rows.append({
            "day": i + 1,
            "date": str(d),
            "done": False,
            "juice": "",
            "hydration": "",
            "skin_look": "",
            "breakouts": "",
            "digestion": ""
        })
    return rows

def default_checkpoints():
    data = {}
    for day in CHECKPOINT_DAYS:
        data[str(day)] = {
            "front_image": "",
            "left_image": "",
            "right_image": "",
            "manual_analysis": "",
            "overall_brightness": "",
            "pigmentation": "",
            "acne_bumps": "",
            "under_eye": "",
            "texture_pores": "",
            "hydration_look": "",
            "overall_summary": ""
        }
    return data

def ensure_data():
    if not DAILY_LOG_FILE.exists():
        save_json(DAILY_LOG_FILE, default_daily_log())
    if not CHECKPOINT_FILE.exists():
        save_json(CHECKPOINT_FILE, default_checkpoints())

ensure_data()

daily_log = load_json(DAILY_LOG_FILE, default_daily_log())
checkpoint_data = load_json(CHECKPOINT_FILE, default_checkpoints())

def save_daily_log():
    save_json(DAILY_LOG_FILE, daily_log)

def save_checkpoints():
    save_json(CHECKPOINT_FILE, checkpoint_data)

def score_counts(values, good_label):
    if not values:
        return 0
    return sum(1 for v in values if v == good_label)

def current_streak(log):
    streak = 0
    for row in reversed(log):
        if row["done"]:
            streak += 1
        else:
            break
    return streak

def get_completion_stats(log):
    completed = sum(1 for row in log if row["done"])
    total = len(log)
    percent = round((completed / total) * 100, 1) if total else 0
    return completed, total - completed, percent

def image_to_base64(path):
    if not path or not Path(path).exists():
        return None
    data = Path(path).read_bytes()
    encoded = base64.b64encode(data).decode()
    suffix = Path(path).suffix.lower().replace(".", "")
    mime = "jpeg" if suffix in ["jpg", "jpeg"] else suffix
    return f"data:image/{mime};base64,{encoded}"

def save_uploaded_image(uploaded_file, checkpoint_day, view_name):
    if uploaded_file is None:
        return None
    ext = Path(uploaded_file.name).suffix or ".jpg"
    out_path = IMAGE_DIR / f"day_{checkpoint_day}_{view_name}{ext}"
    out_path.write_bytes(uploaded_file.getbuffer())
    return str(out_path)

def average_score_from_option(log, key, positive_values):
    vals = [row[key] for row in log if row[key]]
    if not vals:
        return "No data"
    score = sum(1 for v in vals if v in positive_values)
    return f"{score}/{len(vals)} positive"

st.title("✨ GlowTrack AI")
st.caption("Continuous skin, juice, and checkpoint progress tracker. Built as a real app structure — not a fake one-page challenge.")

tab1, tab2, tab3, tab4 = st.tabs(["Dashboard", "Daily Tracker", "Checkpoint Selfies", "AI Progress Guide"])

with tab1:
    st.subheader("Dashboard")

    completed, remaining, completion_pct = get_completion_stats(daily_log)
    streak = current_streak(daily_log)
    most_used = pd.Series([row["juice"] for row in daily_log if row["juice"]]).value_counts()
    top_juice = most_used.index[0] if not most_used.empty else "No juice logged yet"

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Days completed", completed)
    col2.metric("Remaining entries", remaining)
    col3.metric("Completion %", f"{completion_pct}%")
    col4.metric("Current streak", streak)

    st.markdown("### Quick summary")
    c1, c2 = st.columns(2)
    with c1:
        st.info(f"**Most used juice:** {top_juice}")
        st.write(f"**Hydration trend:** {average_score_from_option(daily_log, 'hydration', ['Hydrated'])}")
        st.write(f"**Skin look trend:** {average_score_from_option(daily_log, 'skin_look', ['Fresh / Glowy'])}")
    with c2:
        st.write(f"**Breakout control trend:** {average_score_from_option(daily_log, 'breakouts', ['None', 'Mild'])}")
        st.write(f"**Digestion trend:** {average_score_from_option(daily_log, 'digestion', ['Good'])}")
        st.warning("This dashboard is only as useful as your honesty in logging. Fake inputs = fake insights.")

    st.markdown("### Checkpoint status")
    checkpoint_rows = []
    for day in CHECKPOINT_DAYS:
        cp = checkpoint_data[str(day)]
        checkpoint_rows.append({
            "Checkpoint Day": day,
            "Front Selfie": "Uploaded" if cp["front_image"] else "Missing",
            "Manual Analysis": "Added" if cp["manual_analysis"] else "Pending",
            "Overall Summary": cp["overall_summary"] or ""
        })
    st.dataframe(pd.DataFrame(checkpoint_rows), use_container_width=True)

with tab2:
    st.subheader("Daily Tracker")
    st.caption("Default build includes 365 days. You can keep using it beyond 90 days. Edit only what you actually did.")

    with st.expander("Bulk actions", expanded=False):
        if st.button("Reset all daily entries"):
            daily_log = default_daily_log()
            save_json(DAILY_LOG_FILE, daily_log)
            st.success("Daily tracker reset. Refresh the page if needed.")

    display_days = st.slider("How many days to show right now", min_value=30, max_value=365, value=120, step=15)

    updated_rows = []
    for row in daily_log[:display_days]:
        with st.container(border=True):
            c1, c2, c3, c4, c5, c6, c7 = st.columns([1.1, 1.2, 2.4, 1.4, 1.6, 1.6, 1.4])
            c1.markdown(f"**Day {row['day']}**")
            done = c2.checkbox("Done", value=row["done"], key=f"done_{row['day']}")
            juice = c3.selectbox("Juice", [""] + JUICE_OPTIONS, index=([""] + JUICE_OPTIONS).index(row["juice"]) if row["juice"] in [""] + JUICE_OPTIONS else 0, key=f"juice_{row['day']}")
            hydration = c4.selectbox("Hydration", HYDRATION_OPTIONS, index=HYDRATION_OPTIONS.index(row["hydration"]) if row["hydration"] in HYDRATION_OPTIONS else 0, key=f"hydration_{row['day']}")
            skin_look = c5.selectbox("Skin look", SKIN_LOOK_OPTIONS, index=SKIN_LOOK_OPTIONS.index(row["skin_look"]) if row["skin_look"] in SKIN_LOOK_OPTIONS else 0, key=f"skin_{row['day']}")
            breakouts = c6.selectbox("Breakouts", BREAKOUT_OPTIONS, index=BREAKOUT_OPTIONS.index(row["breakouts"]) if row["breakouts"] in BREAKOUT_OPTIONS else 0, key=f"breakouts_{row['day']}")
            digestion = c7.selectbox("Digestion", DIGESTION_OPTIONS, index=DIGESTION_OPTIONS.index(row["digestion"]) if row["digestion"] in DIGESTION_OPTIONS else 0, key=f"digestion_{row['day']}")

            updated_rows.append({
                "day": row["day"],
                "date": row["date"],
                "done": done,
                "juice": juice,
                "hydration": hydration,
                "skin_look": skin_look,
                "breakouts": breakouts,
                "digestion": digestion
            })

    if st.button("Save daily tracker"):
        for i in range(display_days):
            daily_log[i] = updated_rows[i]
        save_daily_log()
        st.success("Daily tracker saved.")

with tab3:
    st.subheader("Checkpoint Selfies + Skin Analysis")
    st.caption("Upload clean no-makeup selfies at major checkpoints. The app stores the images and your analysis notes. Real automatic AI analysis would require a vision backend/API later.")

    for day in CHECKPOINT_DAYS:
        cp_key = str(day)
        cp = checkpoint_data[cp_key]

        with st.expander(f"Checkpoint Day {day}", expanded=(day in [1, 15, 30, 90])):
            st.markdown("#### Upload checkpoint selfies")
            col1, col2, col3 = st.columns(3)

            with col1:
                front = st.file_uploader(f"Front selfie – Day {day}", type=["jpg", "jpeg", "png"], key=f"front_{day}")
                if front is not None:
                    path = save_uploaded_image(front, day, "front")
                    checkpoint_data[cp_key]["front_image"] = path
                    save_checkpoints()
                    st.success("Front selfie saved.")
                if checkpoint_data[cp_key]["front_image"]:
                    st.image(checkpoint_data[cp_key]["front_image"], caption=f"Day {day} front", use_container_width=True)

            with col2:
                left = st.file_uploader(f"Left-side selfie – Day {day}", type=["jpg", "jpeg", "png"], key=f"left_{day}")
                if left is not None:
                    path = save_uploaded_image(left, day, "left")
                    checkpoint_data[cp_key]["left_image"] = path
                    save_checkpoints()
                    st.success("Left selfie saved.")
                if checkpoint_data[cp_key]["left_image"]:
                    st.image(checkpoint_data[cp_key]["left_image"], caption=f"Day {day} left", use_container_width=True)

            with col3:
                right = st.file_uploader(f"Right-side selfie – Day {day}", type=["jpg", "jpeg", "png"], key=f"right_{day}")
                if right is not None:
                    path = save_uploaded_image(right, day, "right")
                    checkpoint_data[cp_key]["right_image"] = path
                    save_checkpoints()
                    st.success("Right selfie saved.")
                if checkpoint_data[cp_key]["right_image"]:
                    st.image(checkpoint_data[cp_key]["right_image"], caption=f"Day {day} right", use_container_width=True)

            st.markdown("#### Skin analysis fields")
            c1, c2 = st.columns(2)
            with c1:
                brightness = st.text_input("Overall brightness / dullness", value=cp["overall_brightness"], key=f"brightness_{day}")
                pigmentation = st.text_input("Pigmentation areas / uneven tone", value=cp["pigmentation"], key=f"pigment_{day}")
                acne = st.text_input("Active acne / bumps / congestion", value=cp["acne_bumps"], key=f"acne_{day}")
            with c2:
                under_eye = st.text_input("Under-eye darkness", value=cp["under_eye"], key=f"undereye_{day}")
                texture = st.text_input("Texture / pores", value=cp["texture_pores"], key=f"texture_{day}")
                hydration_look = st.text_input("Hydration / oiliness appearance", value=cp["hydration_look"], key=f"hydrationlook_{day}")

            manual_analysis = st.text_area(
                "Manual AI analysis / comparison notes",
                value=cp["manual_analysis"],
                key=f"manual_{day}",
                height=140,
                placeholder="This is where a real AI skin analysis result can be pasted or stored. Example: Mild improvement in brightness vs baseline, but pigmentation around mouth still prominent."
            )

            overall_summary = st.text_area(
                "Checkpoint summary",
                value=cp["overall_summary"],
                key=f"summary_{day}",
                height=100,
                placeholder="Example: Skin looks less dull than baseline. Breakouts slightly calmer. Pigmentation unchanged."
            )

            if st.button(f"Save checkpoint Day {day}", key=f"save_cp_{day}"):
                checkpoint_data[cp_key].update({
                    "overall_brightness": brightness,
                    "pigmentation": pigmentation,
                    "acne_bumps": acne,
                    "under_eye": under_eye,
                    "texture_pores": texture,
                    "hydration_look": hydration_look,
                    "manual_analysis": manual_analysis,
                    "overall_summary": overall_summary
                })
                save_checkpoints()
                st.success(f"Checkpoint Day {day} saved.")

with tab4:
    st.subheader("AI Progress Guide")
    st.caption("This is the realistic expectation section. It’s not pretending juice alone transforms skin.")

    milestone_cols = st.columns(3)
    ordered_days = [15, 30, 60, 90, 180, 365]
    for idx, day in enumerate(ordered_days):
        with milestone_cols[idx % 3]:
            st.markdown(f"### {AI_GUIDANCE[day]['title']}")
            st.markdown(AI_GUIDANCE[day]["text"])

    st.markdown("---")
    st.markdown("## How to actually use the selfie analysis with me")
    st.info(
        "If you upload your no-makeup checkpoint selfies in chat, I can analyze them and you can paste the result into the 'Manual AI analysis' field for that checkpoint. "
        "That gives you a real human/AI review trail instead of fake autogenerated nonsense."
    )

st.markdown("---")
st.caption("GlowTrack AI • Continuous Skin & Juice Tracker • Streamlit MVP")
