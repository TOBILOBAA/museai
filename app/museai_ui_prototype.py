# import time
# import streamlit as st

# from pathlib import Path

# # ---------------------------------------------------
# # Basic page config
# # ---------------------------------------------------
# st.set_page_config(
#     page_title="MuseAI – Multimodal Museum Companion",
#     page_icon="🎧",
#     layout="wide",
#     initial_sidebar_state="collapsed",
# )

# # ---------- Global dark styling + components ----------
# st.markdown(
#     """
#     <style>
#     /* App background + text */
#     .stApp {
#         background-color: #050608;
#         color: #f5f5f5;
#     }
#     /* Reduce default padding */
#     .block-container {
#         padding-top: 1.8rem;
#     }
#     /* Hide Streamlit's default white header */
#     header {visibility: hidden;}

#     /* Logo pill */
#     .muse-logo-pill {
#         display: inline-flex;
#         align-items: center;
#         justify-content: center;
#         padding: 0.25rem 0.9rem;
#         border-radius: 999px;
#         background: #111318;           /* slightly lighter than bg */
#         border: 1px solid #252834;
#         font-weight: 600;
#         letter-spacing: 0.18em;
#         font-size: 0.65rem;
#         text-transform: uppercase;
#     }

#     /* Hero card */
#     .hero-card {
#         background: radial-gradient(circle at top, #171922 0, #06070a 55%);
#         border-radius: 1.6rem;
#         padding: 3rem 2.8rem 2.4rem;
#         box-shadow: 0 18px 45px rgba(0,0,0,0.75);
#         max-width: 520px;
#         margin: 4rem auto 3rem auto;
#         text-align: center;
#     }
#     .hero-title {
#         font-size: 2.4rem;
#         font-weight: 650;
#         margin-bottom: 0.5rem;
#     }
#     .hero-sub {
#         font-size: 0.95rem;
#         opacity: 0.86;
#         margin-bottom: 2.2rem;
#     }

#     /* Buttons – global style + hover + pressed */
#     .stButton > button {
#         border-radius: 999px;
#         padding: 0.7rem 1.9rem;
#         border: 1px solid #f5f5f5;
#         background: #f5f5f5;
#         color: #050608;
#         font-weight: 600;
#         box-shadow: 0 10px 25px rgba(0,0,0,0.55);
#         transition: all 0.13s ease-out;
#     }
#     .stButton > button:hover {
#         background: #ffffff;
#         border-color: #ffffff;
#         transform: translateY(-1px);
#         box-shadow: 0 14px 32px rgba(0,0,0,0.7);
#     }
#     .stButton > button:active {
#         transform: translateY(1px) scale(0.99);
#         box-shadow: 0 6px 18px rgba(0,0,0,0.55);
#     }

#     /* Language select – shrink width a bit */
#     .lang-select-box .stSelectbox > div > div {
#         max-width: 170px;
#     }

#     /* Section titles + subtitles */
#     .section-title {
#         text-align: center;
#         margin-bottom: 0.1rem;
#     }
#     .section-sub {
#         text-align: center;
#         font-size: 0.86rem;
#         opacity: 0.78;
#         margin-bottom: 1.7rem;
#     }

#     /* Camera frame card */
#     .camera-frame {
#         background: #101219;
#         border-radius: 1.2rem;
#         padding: 1.4rem;
#         box-shadow: 0 12px 30px rgba(0,0,0,0.7);
#     }

#     /* Chat bubbles */
#     .bubble-assistant {
#         background: #181a23;
#         padding: 0.7rem 0.9rem;
#         border-radius: 0.9rem;
#         margin-bottom: 0.45rem;
#         color: #f5f5f5;
#     }
#     .bubble-user {
#         background: #273646;
#         padding: 0.7rem 0.9rem;
#         border-radius: 0.9rem;
#         margin-bottom: 0.45rem;
#         color: #ffffff;
#         text-align: right;
#     }
#     </style>
#     """,
#     unsafe_allow_html=True,
# )

# # ---------------------------------------------------
# # Language & copy system
# # ---------------------------------------------------
# LANG_LABELS = {
#     "en": "English 🇬🇧",
#     "fr": "Français 🇫🇷",
#     "he": "עברית 🇮🇱",
# }
# LABEL_TO_LANG = {v: k for k, v in LANG_LABELS.items()}

# STRINGS = {
#     "en": {
#         "hero_title": "MuseAI",
#         "hero_sub": "A smart museum guide that sees, listens, and explains.",
#         "hero_button": "Start museum tour",
#         "step1_title": "Step 1 – Capture the artifact",
#         "step1_hint": "Take a photo of an artifact to unlock your tour.",
#         "scanning": "Scanning your photo… stand by.",
#         "step2_title": "Step 2 – Talk to MuseAI",
#         "step2_hint": "Tap the mic and ask your question out loud. No typing needed.",
#         "fake_answer": "This is a demo answer explaining your artifact in a friendly way.",
#         "demo_question": "What is this artifact and how was it used?",
#         "error_title": "Something went wrong",
#         "error_body": "This is how a user-friendly error message will appear in the real app.",
#     },
#     "fr": {
#         "hero_title": "MuseAI",
#         "hero_sub": "Votre guide de musée intelligent qui voit, écoute et explique.",
#         "hero_button": "Commencer la visite",
#         "step1_title": "Étape 1 – Photographiez l’objet",
#         "step1_hint": "Prenez une photo d’un objet pour lancer la visite.",
#         "scanning": "Analyse de votre photo… un instant.",
#         "step2_title": "Étape 2 – Parlez à MuseAI",
#         "step2_hint": "Appuyez sur le micro et posez votre question à voix haute.",
#         "fake_answer": "Ceci est une réponse de démonstration qui explique l’objet.",
#         "demo_question": "Quel est cet objet et à quoi servait-il ?",
#         "error_title": "Un problème est survenu",
#         "error_body": "Voici comment un message d’erreur convivial apparaîtra dans l’application.",
#     },
#     "he": {
#         "hero_title": "MuseAI",
#         "hero_sub": "מדריך מוזיאוני חכם שרואה, שומע ומסביר.",
#         "hero_button": "התחל סיור במוזיאון",
#         "step1_title": "שלב 1 – צלמו את הפריט",
#         "step1_hint": "צלמו פריט כדי לפתוח את הסיור.",
#         "scanning": "סורק את התמונה… רגע אחד.",
#         "step2_title": "שלב 2 – דברו עם MuseAI",
#         "step2_hint": "לחצו על המיקרופון ושאלו בקול. אין צורך להקליד.",
#         "fake_answer": "זו תשובת דמו שמסבירה את הפריט בצורה נעימה.",
#         "demo_question": "מהו הפריט הזה וכיצד השתמשו בו?",
#         "error_title": "אירעה שגיאה",
#         "error_body": "כך תיראה הודעת שגיאה ידידותית באפליקציה האמיתית.",
#     },
# }

# # ---------------------------------------------------
# # Session state
# # ---------------------------------------------------
# if "language" not in st.session_state:
#     st.session_state.language = "en"

# if "hero_started" not in st.session_state:
#     st.session_state.hero_started = False

# if "camera_has_photo" not in st.session_state:
#     st.session_state.camera_has_photo = False

# if "is_scanning" not in st.session_state:
#     st.session_state.is_scanning = False

# if "fake_chat" not in st.session_state:
#     st.session_state.fake_chat = []  # list of dicts {role, text}


# def on_change_language():
#     """Update language code when dropdown changes."""
#     label = st.session_state._lang_select_label
#     st.session_state.language = LABEL_TO_LANG[label]


# # ---------------------------------------------------
# # TOP STRIP: logo + language dropdown
# # ---------------------------------------------------
# lang = st.session_state.language
# txt = STRINGS[lang]

# top_left, top_spacer, top_right = st.columns([1.2, 5, 1.4])

# with top_left:
#     st.markdown(
#         "<div class='muse-logo-pill'>MUSEAI</div>",
#         unsafe_allow_html=True,
#     )

# with top_right:
#     current_label = LANG_LABELS[lang]
#     with st.container():
#         st.markdown("<div class='lang-select-box'>", unsafe_allow_html=True)
#         st.selectbox(
#             " ",  # no label
#             options=list(LANG_LABELS.values()),
#             index=list(LANG_LABELS.values()).index(current_label),
#             key="_lang_select_label",
#             on_change=on_change_language,
#             label_visibility="collapsed",
#         )
#         st.markdown("</div>", unsafe_allow_html=True)

# st.markdown("")

# # ---------------------------------------------------
# # HERO / SPLASH SCREEN
# # ---------------------------------------------------
# if not st.session_state.hero_started:
#     st.markdown(
#         f"""
#         <div class="hero-card">
#             <div class="hero-title">{txt['hero_title']}</div>
#             <div class="hero-sub">{txt['hero_sub']}</div>
#         </div>
#         """,
#         unsafe_allow_html=True,
#     )

#     center_col = st.columns([3, 2, 3])[1]
#     with center_col:
#         start_clicked = st.button(txt["hero_button"], use_container_width=True)

#     if start_clicked:
#         st.session_state.hero_started = True
#         st.rerun()

#     # Stop before main tour UI
#     st.stop()

# # ---------------------------------------------------
# # MAIN TOUR PROTOTYPE
# # ---------------------------------------------------

# # Sidebar (this will later mirror your real app)
# with st.sidebar:
#     st.markdown("### MuseAI Tour")
#     st.caption("Your multilingual museum companion.")

#     current_label = LANG_LABELS[st.session_state.language]
#     st.selectbox(
#         "Language",
#         options=list(LANG_LABELS.values()),
#         index=list(LANG_LABELS.values()).index(current_label),
#         key="_sidebar_lang",
#     )
#     # Keep language in sync from sidebar too
#     st.session_state.language = LABEL_TO_LANG[st.session_state._sidebar_lang]
#     txt = STRINGS[st.session_state.language]

#     st.markdown("")
#     st.button("Start new tour", use_container_width=True)

# # STEP 1 – Camera
# st.markdown(
#     f"<h3 class='section-title'>{txt['step1_title']}</h3>",
#     unsafe_allow_html=True,
# )
# st.markdown(
#     f"<p class='section-sub'>{txt['step1_hint']}</p>",
#     unsafe_allow_html=True,
# )

# cam_outer = st.container()
# with cam_outer:
#     cam_col, _ = st.columns([1.4, 1])

#     with cam_col:
#         st.markdown("<div class='camera-frame'>", unsafe_allow_html=True)
#         camera_file = st.camera_input(
#             " ",
#             key="demo_camera",
#             label_visibility="collapsed",
#         )
#         st.markdown("</div>", unsafe_allow_html=True)

#         if camera_file is not None and not st.session_state.is_scanning:
#             st.session_state.camera_has_photo = True
#             st.session_state.is_scanning = True

#     status_col, _ = st.columns([1.4, 1])
#     with status_col:
#         if not st.session_state.camera_has_photo:
#             st.caption("Once the photo is captured, MuseAI will auto-scan it.")
#         else:
#             with st.spinner(txt["scanning"]):
#                 time.sleep(1.3)  # fake delay
#             st.success("✅ Artifact recognized (demo only).")

# st.markdown("---")

# # STEP 2 – Voice conversation demo
# st.markdown(
#     f"<h3 class='section-title'>{txt['step2_title']}</h3>",
#     unsafe_allow_html=True,
# )
# st.markdown(
#     f"<p class='section-sub'>{txt['step2_hint']}</p>",
#     unsafe_allow_html=True,
# )

# voice_col, _ = st.columns([1.2, 1])
# with voice_col:
#     if st.button("🎤 Hold to ask (demo)", key="demo_mic_btn"):
#         # In the real app this is where the mic would record.
#         # For now we just simulate a Q&A.
#         st.session_state.fake_chat.append(
#             {"role": "user", "text": txt["demo_question"]}
#         )
#         st.session_state.fake_chat.append(
#             {"role": "assistant", "text": txt["fake_answer"]}
#         )

# # Chat bubbles
# for msg in st.session_state.fake_chat:
#     if msg["role"] == "assistant":
#         st.markdown(
#             f"<div class='bubble-assistant'>🤖 {msg['text']}</div>",
#             unsafe_allow_html=True,
#         )
#     else:
#         st.markdown(
#             f"<div class='bubble-user'>🧑 {msg['text']}</div>",
#             unsafe_allow_html=True,
#         )

# st.markdown("---")

# # Error-preview area
# with st.expander("Demo: what an error message will look like"):
#     st.error(
#         f"**{txt['error_title']}**\n\n"
#         f"{txt['error_body']}\n\n"
#         "_Technical details will be hidden behind this friendly message._"
#     )




















# import time
# from pathlib import Path

# import streamlit as st

# # ---------------------------------------------------
# # Global page / theming
# # ---------------------------------------------------
# st.set_page_config(
#     page_title="MuseAI – Multimodal Museum Companion",
#     page_icon="🎧",
#     layout="wide",
# )

# # Custom CSS – dark theme, logo pill, hero card, camera styling, sidebar
# st.markdown(
#     """
#     <style>
#     .stApp {
#         background-color: #050608;
#     }

#     /* Remove Streamlit default white header */
#     header, [data-testid="stToolbar"] {
#         background: transparent;
#     }

#     .block-container {
#         padding-top: 2.8rem;
#         max-width: 1100px;
#     }

#     /* Top bar */
#     .muse-topbar {
#         display: flex;
#         justify-content: space-between;
#         align-items: center;
#         margin-bottom: 2.0rem;
#     }

#     .muse-logo-pill {
#         display: inline-flex;
#         align-items: center;
#         justify-content: center;
#         padding: 0.25rem 0.9rem;
#         border-radius: 999px;
#         background: rgba(10,10,13,0.9);
#         border: 1px solid rgba(255,255,255,0.16);
#         box-shadow: 0 8px 20px rgba(0,0,0,0.6);
#         font-size: 0.72rem;
#         letter-spacing: 0.18em;
#         text-transform: uppercase;
#         color: #f8f8f8;
#     }

#     /* Limit width of top language select */
#     .muse-top-lang > div[data-testid="stSelectbox"] {
#         max-width: 170px;
#         margin-left: auto;
#     }

#     /* Hero card */
#     .muse-hero-wrapper {
#         display: flex;
#         justify-content: center;
#         margin-top: 1.0rem;
#         margin-bottom: 3.0rem;
#     }

#     .muse-hero-card {
#         max-width: 480px;
#         width: 100%;
#         padding: 2.4rem 2.7rem;
#         border-radius: 26px;
#         background: radial-gradient(circle at top, #191922, #09090d);
#         box-shadow:
#             0 26px 60px rgba(0,0,0,0.85),
#             0 0 0 1px rgba(255,255,255,0.03);
#         text-align: center;
#     }

#     .muse-hero-title {
#         font-size: 2.4rem;
#         margin-bottom: 0.6rem;
#         color: #ffffff;
#     }

#     .muse-hero-sub {
#         font-size: 1rem;
#         opacity: 0.9;
#         margin-bottom: 1.8rem;
#         color: #f5f5f5;
#     }

#     /* Primary button – light pill, good contrast */
#     .muse-primary-btn button {
#         border-radius: 999px;
#         border: none;
#         background: #f5f5f5;
#         color: #050608;
#         font-weight: 600;
#         padding: 0.7rem 1.8rem;
#         box-shadow: 0 10px 28px rgba(0,0,0,0.55);
#     }
#     .muse-primary-btn button:hover {
#         background: #ffffff;
#     }
#     .muse-primary-btn button:active {
#         transform: scale(0.97);
#     }

#     /* Sidebar (for the main screen) */
#     [data-testid="stSidebar"] {
#         background: #050608;
#         border-right: 1px solid rgba(255,255,255,0.08);
#     }
#     [data-testid="stSidebar"] * {
#         color: #f7f7f7 !important;
#     }

#     /* Step titles */
#     .muse-step-title {
#         font-size: 1.2rem;
#         font-weight: 600;
#         color: #ffffff;
#         margin-bottom: 0.15rem;
#         text-align: left;
#     }
#     .muse-step-sub {
#         font-size: 0.9rem;
#         opacity: 0.82;
#         color: #d7d7d7;
#         margin-bottom: 1.4rem;
#         text-align: left;
#     }

#     /* Style camera area darker */
#     [data-testid="stCameraInput"] > div {
#         background: #121216 !important;
#         border-radius: 22px !important;
#         border: 1px solid rgba(255,255,255,0.08) !important;
#         box-shadow: 0 22px 42px rgba(0,0,0,0.8) !important;
#     }
#     [data-testid="stCameraInput"] button {
#         border-radius: 999px !important;
#     }

#     /* Chat bubbles demo */
#     .muse-assistant {
#         background:#202020;
#         padding:0.7rem 0.9rem;
#         border-radius:0.8rem;
#         margin-bottom:0.4rem;
#         color:#f5f5f5;
#     }
#     .muse-user {
#         background:#2b3b4a;
#         padding:0.7rem 0.9rem;
#         border-radius:0.8rem;
#         margin-bottom:0.4rem;
#         text-align:right;
#         color:#ffffff;
#     }
#     </style>
#     """,
#     unsafe_allow_html=True,
# )

# # ---------------------------------------------------
# # Language system
# # ---------------------------------------------------
# LANG_LABELS = {
#     "en": "English 🇬🇧",
#     "fr": "Français 🇫🇷",
#     "he": "עברית 🇮🇱",
# }
# LABEL_TO_LANG = {v: k for k, v in LANG_LABELS.items()}

# STRINGS = {
#     "en": {
#         "hero_title": "MuseAI",
#         "hero_sub": "A smart museum guide that sees, listens, and explains.",
#         "hero_button": "Start museum tour",
#         "step1_title": "Step 1 – Capture the artifact",
#         "step1_sub": "Take a photo of an artifact to unlock your tour.",
#         "scanning": "Scanning your photo… stand by.",
#         "step2_title": "Step 2 – Talk to MuseAI",
#         "step2_sub": "Use your voice to ask anything about this artifact.",
#         "fake_answer": "This is a demo answer explaining your artifact in a friendly way.",
#         "error_title": "Something went wrong",
#         "error_body": "This is how a user-friendly error message will appear in the real app.",
#         "sidebar_title": "MuseAI Tour",
#         "sidebar_hint": "Aim at an artifact, then speak once MuseAI has identified it.",
#         "sidebar_start": "Start new artifact tour",
#         "demo_question_label": "Type a demo question here:",
#     },
#     "fr": {
#         "hero_title": "MuseAI",
#         "hero_sub": "Un guide de musée intelligent qui voit, écoute et explique.",
#         "hero_button": "Commencer la visite",
#         "step1_title": "Étape 1 – Photographiez l’objet",
#         "step1_sub": "Prenez une photo d’un objet pour lancer votre visite.",
#         "scanning": "Analyse de votre photo… un instant.",
#         "step2_title": "Étape 2 – Parlez à MuseAI",
#         "step2_sub": "Utilisez votre voix pour poser toutes vos questions.",
#         "fake_answer": "Ceci est une réponse de démonstration qui explique l’objet.",
#         "error_title": "Un problème est survenu",
#         "error_body": "Voici comment un message d’erreur convivial apparaîtra dans l’application.",
#         "sidebar_title": "Visite MuseAI",
#         "sidebar_hint": "Visez un objet, puis parlez une fois qu’il est identifié.",
#         "sidebar_start": "Commencer une nouvelle visite",
#         "demo_question_label": "Écrivez une question de démonstration :",
#     },
#     "he": {
#         "hero_title": "MuseAI",
#         "hero_sub": "מדריך מוזיאון חכם שרואה, שומע ומסביר.",
#         "hero_button": "התחלת סיור במוזיאון",
#         "step1_title": "שלב 1 – צלמו את הפריט",
#         "step1_sub": "צלמו פריט כדי לפתוח את הסיור.",
#         "scanning": "הצילום נסרק… רק רגע.",
#         "step2_title": "שלב 2 – דברו עם MuseAI",
#         "step2_sub": "השתמשו בקול כדי לשאול כל שאלה על הפריט.",
#         "fake_answer": "זו תשובת דמו שמסבירה את הפריט בצורה נעימה.",
#         "error_title": "אירעה שגיאה",
#         "error_body": "כך תיראה הודעת שגיאה ידידותית באפליקציה האמיתית.",
#         "sidebar_title": "סיור MuseAI",
#         "sidebar_hint": "כוונו לפריט, ואז דברו אחרי שמזהים אותו.",
#         "sidebar_start": "התחל סיור חדש",
#         "demo_question_label": "הקלידו כאן שאלה לדוגמה:",
#     },
# }

# # ---------------------------------------------------
# # Session state
# # ---------------------------------------------------
# if "language" not in st.session_state:
#     st.session_state.language = "en"
# if "hero_started" not in st.session_state:
#     st.session_state.hero_started = False
# if "camera_has_photo" not in st.session_state:
#     st.session_state.camera_has_photo = False
# if "is_scanning" not in st.session_state:
#     st.session_state.is_scanning = False
# if "fake_chat" not in st.session_state:
#     st.session_state.fake_chat = []


# def language_selector(label: str = "", location: str = "top") -> str:
#     """
#     Reusable language select that updates session_state immediately.
#     location: "top" or "sidebar" – only affects label visibility / CSS wrapper.
#     """
#     lang = st.session_state.language
#     current = LANG_LABELS[lang]
#     options = list(LANG_LABELS.values())
#     index = options.index(current)

#     if location == "top":
#         # no "Language" label, just the box
#         value = st.selectbox(
#             " ",
#             options=options,
#             index=index,
#             label_visibility="collapsed",
#             key=f"lang_{location}",
#         )
#     else:
#         value = st.selectbox(
#             label or "Language",
#             options=options,
#             index=index,
#             key=f"lang_{location}",
#         )

#     st.session_state.language = LABEL_TO_LANG[value]
#     return st.session_state.language


# # ---------------------------------------------------
# # TOP BAR (logo + language) – always visible
# # ---------------------------------------------------
# with st.container():
#     col_logo, col_lang = st.columns([5, 1.4])
#     with col_logo:
#         st.markdown(
#             "<div class='muse-logo-pill'>MUSEAI</div>",
#             unsafe_allow_html=True,
#         )
#     with col_lang:
#         st.markdown("<div class='muse-top-lang'>", unsafe_allow_html=True)
#         language_selector(location="top")
#         st.markdown("</div>", unsafe_allow_html=True)

# st.markdown("")  # small gap

# lang = st.session_state.language
# txt = STRINGS[lang]

# # ---------------------------------------------------
# # HERO (splash) – only before starting
# # ---------------------------------------------------
# if not st.session_state.hero_started:
#     st.markdown(
#         """
#         <div class="muse-hero-wrapper">
#           <div class="muse-hero-card">
#         """,
#         unsafe_allow_html=True,
#     )
#     st.markdown(
#         f"""
#         <div class="muse-hero-title">{txt['hero_title']}</div>
#         <div class="muse-hero-sub">{txt['hero_sub']}</div>
#         """,
#         unsafe_allow_html=True,
#     )
#     center_col = st.columns([1, 1, 1])[1]
#     with center_col:
#         with st.container():
#             st.markdown('<div class="muse-primary-btn">', unsafe_allow_html=True)
#             start_clicked = st.button(txt["hero_button"], use_container_width=True)
#             st.markdown('</div>', unsafe_allow_html=True)

#     st.markdown(
#         """
#           </div>
#         </div>
#         """,
#         unsafe_allow_html=True,
#     )

#     if start_clicked:
#         st.session_state.hero_started = True
#         st.rerun()

#     st.stop()  # do not render the rest until started

# # ---------------------------------------------------
# # MAIN SCREEN (after starting tour) – with sidebar
# # ---------------------------------------------------

# # Sidebar – dark, aligned with theme
# with st.sidebar:
#     st.markdown(f"### {txt['sidebar_title']}")
#     language_selector(label="Language", location="sidebar")
#     st.markdown("---")
#     st.button(txt["sidebar_start"])
#     st.markdown(
#         f"<p style='font-size:0.85rem;opacity:0.75;'>{txt['sidebar_hint']}</p>",
#         unsafe_allow_html=True,
#     )

# # Step 1 – camera
# st.markdown(f"<div class='muse-step-title'>{txt['step1_title']}</div>", unsafe_allow_html=True)
# st.markdown(f"<div class='muse-step-sub'>{txt['step1_sub']}</div>", unsafe_allow_html=True)

# cam_cols = st.columns([1.2, 1.6, 1.2])
# with cam_cols[1]:
#     camera_file = st.camera_input(
#         " ",
#         key="demo_camera",
#         label_visibility="collapsed",
#     )

#     if camera_file is not None and not st.session_state.is_scanning:
#         st.session_state.camera_has_photo = True
#         st.session_state.is_scanning = True

# if st.session_state.camera_has_photo:
#     with st.spinner(txt["scanning"]):
#         time.sleep(1.5)
#     st.success("✅ Artifact recognized (demo)")
#     st.session_state.is_scanning = False

# st.markdown("---")

# # Step 2 – conversation area (still text demo, but copy talks about voice)
# st.markdown(f"<div class='muse-step-title'>{txt['step2_title']}</div>", unsafe_allow_html=True)
# st.markdown(f"<div class='muse-step-sub'>{txt['step2_sub']}</div>", unsafe_allow_html=True)

# # In real app this would be microphone; here we keep simple text to preview bubbles
# user_question = st.text_input(txt["demo_question_label"])

# if user_question:
#     st.session_state.fake_chat.append({"role": "user", "text": user_question})
#     st.session_state.fake_chat.append({"role": "assistant", "text": txt["fake_answer"]})

# for msg in st.session_state.fake_chat:
#     if msg["role"] == "assistant":
#         st.markdown(f"<div class='muse-assistant'>🤖 {msg['text']}</div>", unsafe_allow_html=True)
#     else:
#         st.markdown(f"<div class='muse-user'>🧑 {msg['text']}</div>", unsafe_allow_html=True)

# st.markdown("---")

# with st.expander("Demo: what an error message will look like"):
#     st.error(
#         f"**{txt['error_title']}**\n\n"
#         f"{txt['error_body']}\n\n"
#         "_Technical details will be hidden behind this friendly message._"
#     )








import time
import streamlit as st

from pathlib import Path

# ---------------------------------------------------
# Basic page config
# ---------------------------------------------------
st.set_page_config(
    page_title="MuseAI – Multimodal Museum Companion",
    page_icon="🎧",
    layout="wide",
    initial_sidebar_state="collapsed",
)


st.markdown(
    """
    <style>
    /* App background + text */
    .stApp {
        background-color: #050608;
        color: #f5f5f5;
    }
    /* Reduce default padding */
    .block-container {
        padding-top: 1.8rem;
    }
    /* Hide Streamlit's default white header */
    header {visibility: hidden;}

    /* Logo pill */
    .muse-logo-pill {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        padding: 0.25rem 0.9rem;
        border-radius: 999px;
        background: #111318;           /* slightly lighter than bg */
        border: 1px solid #252834;
        font-weight: 600;
        letter-spacing: 0.18em;
        font-size: 0.65rem;
        text-transform: uppercase;
    }

    /* Keep logo + language on same vertical line */
    .lang-select-box .stSelectbox > div {
        margin-top: 0;          /* remove extra top gap above select */
    }

    /* Hero card */
    .hero-card {
        background: radial-gradient(circle at top, #171922 0, #06070a 55%);
        border-radius: 1.6rem;
        padding: 3rem 2.8rem 2.4rem;
        box-shadow: 0 18px 45px rgba(0,0,0,0.75);
        max-width: 520px;
        margin: 4rem auto 3rem auto;
        text-align: center;
    }
    .hero-title {
        font-size: 2.4rem;
        font-weight: 650;
        margin-bottom: 0.5rem;
    }
    .hero-sub {
        font-size: 0.95rem;
        opacity: 0.86;
        margin-bottom: 2.2rem;
    }

    /* Buttons – global style + hover + pressed */
    .stButton > button {
        border-radius: 999px;
        padding: 0.7rem 1.9rem;
        border: 1px solid #f5f5f5;
        background: #f5f5f5;
        color: #050608;
        font-weight: 600;
        box-shadow: 0 10px 25px rgba(0,0,0,0.55);
        transition: all 0.13s ease-out;
    }
    .stButton > button:hover {
        background: #ffffff;
        border-color: #ffffff;
        transform: translateY(-1px);
        box-shadow: 0 14px 32px rgba(0,0,0,0.7);
    }
    .stButton > button:active {
        transform: translateY(1px) scale(0.99);
        box-shadow: 0 6px 18px rgba(0,0,0,0.55);
    }

    /* Language select – shrink width a bit */
    .lang-select-box .stSelectbox > div > div {
        max-width: 170px;
    }

    /* Section titles + subtitles (center – kept for later if you want) */
    .section-title {
        text-align: center;
        margin-bottom: 0.1rem;
    }
    .section-sub {
        text-align: center;
        font-size: 0.86rem;
        opacity: 0.78;
        margin-bottom: 1.7rem;
    }

    /* LEFT-aligned section titles + subtitles (what you asked for) */
    .section-title-left {
        text-align: left;
        margin-bottom: 0.1rem;
    }
    .section-sub-left {
        text-align: left;
        font-size: 0.86rem;
        opacity: 0.78;
        margin-bottom: 1.7rem;
    }

    /* Make the Take Photo button rounded / nice */
    .camera-frame button {
        border-radius: 999px !important;
        padding: 0.5rem 1.4rem !important;
        font-weight: 600;
        border: 1px solid #f5f5f5;
        background: #f5f5f5;
        color: #050608;
    }

    .camera-frame button:hover {
        background: #ffffff;
        border-color: #ffffff;
    }

    /* Chat bubbles */
    .bubble-assistant {
        background: #181a23;
        padding: 0.7rem 0.9rem;
        border-radius: 0.9rem;
        margin-bottom: 0.45rem;
        color: #f5f5f5;
    }
    .bubble-user {
        background: #273646;
        padding: 0.7rem 0.9rem;
        border-radius: 0.9rem;
        margin-bottom: 0.45rem;
        color: #ffffff;
        text-align: right;
    }
        /* ===== SIDEBAR – make it dark like the main area & nice button ===== */
    [data-testid="stSidebar"] {
        background: #050608; /* same dark base as main area */
        border-right: 1px solid rgba(255,255,255,0.08);
    }

    /* Sidebar text colour + size */
    [data-testid="stSidebar"] * {
        color: #f7f7f7 !important;
        font-size: 0.9rem;
    }

    /* Sidebar language select – darker box, decent contrast */
    [data-testid="stSidebar"] .stSelectbox > div > div {
        background: #111318;
        border-radius: 10px;
        border: 1px solid rgba(255,255,255,0.18);
    }

    /* Sidebar primary button (Start new artifact tour) like Code B */
    [data-testid="stSidebar"] .stButton > button {
        border-radius: 10px;
        border: 1px solid rgba(255,255,255,0.25) !important;
        background: #0b0c10;
        color: #050608;
        font-weight: 600;
        padding: 0.55rem 1.6rem;
        box-shadow: 0 10px 24px rgba(0,0,0,0.65);
        transition: all 0.12s ease-out;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        background: #111317;
        transform: translateY(-1px);
        border-color: rgba(255,255,255,0.35) !important;
        box-shadow: 0 14px 30px rgba(0,0,0,0.75);
    }
    [data-testid="stSidebar"] .stButton > button:active {
        transform: translateY(1px) scale(0.99);
        box-shadow: 0 7px 18px rgba(0,0,0,0.6);
    }

    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------
# Language & copy system
# ---------------------------------------------------
LANG_LABELS = {
    "en": "English 🇬🇧",
    "fr": "Français 🇫🇷",
    "he": "עברית 🇮🇱",
}
LABEL_TO_LANG = {v: k for k, v in LANG_LABELS.items()}

STRINGS = {
    "en": {
        "hero_title": "MuseAI",
        "hero_sub": "A smart museum guide that sees, listens, and explains.",
        "hero_button": "Start museum tour",
        "step1_title": "Step 1 – Capture the artifact",
        "step1_hint": "Take a photo of an artifact to unlock your tour.",
        "scanning": "Scanning your photo… stand by.",
        "step2_title": "Step 2 – Talk to MuseAI",
        "step2_hint": "Tap the mic and ask your question out loud. No typing needed.",
        "fake_answer": "This is a demo answer explaining your artifact in a friendly way.",
        "demo_question": "What is this artifact and how was it used?",
        "error_title": "Something went wrong",
        "error_body": "This is how a user-friendly error message will appear in the real app.",
    },
    "fr": {
        "hero_title": "MuseAI",
        "hero_sub": "Votre guide de musée intelligent qui voit, écoute et explique.",
        "hero_button": "Commencer la visite",
        "step1_title": "Étape 1 – Photographiez l’objet",
        "step1_hint": "Prenez une photo d’un objet pour lancer la visite.",
        "scanning": "Analyse de votre photo… un instant.",
        "step2_title": "Étape 2 – Parlez à MuseAI",
        "step2_hint": "Appuyez sur le micro et posez votre question à voix haute.",
        "fake_answer": "Ceci est une réponse de démonstration qui explique l’objet.",
        "demo_question": "Quel est cet objet et à quoi servait-il ?",
        "error_title": "Un problème est survenu",
        "error_body": "Voici comment un message d’erreur convivial apparaîtra dans l’application.",
    },
    "he": {
        "hero_title": "MuseAI",
        "hero_sub": "מדריך מוזיאוני חכם שרואה, שומע ומסביר.",
        "hero_button": "התחל סיור במוזיאון",
        "step1_title": "שלב 1 – צלמו את הפריט",
        "step1_hint": "צלמו פריט כדי לפתוח את הסיור.",
        "scanning": "סורק את התמונה… רגע אחד.",
        "step2_title": "שלב 2 – דברו עם MuseAI",
        "step2_hint": "לחצו על המיקרופון ושאלו בקול. אין צורך להקליד.",
        "fake_answer": "זו תשובת דמו שמסבירה את הפריט בצורה נעימה.",
        "demo_question": "מהו הפריט הזה וכיצד השתמשו בו?",
        "error_title": "אירעה שגיאה",
        "error_body": "כך תיראה הודעת שגיאה ידידותית באפליקציה האמיתית.",
    },
}

# ---------------------------------------------------
# Session state
# ---------------------------------------------------
if "language" not in st.session_state:
    st.session_state.language = "en"

if "hero_started" not in st.session_state:
    st.session_state.hero_started = False

if "camera_has_photo" not in st.session_state:
    st.session_state.camera_has_photo = False

if "is_scanning" not in st.session_state:
    st.session_state.is_scanning = False

if "fake_chat" not in st.session_state:
    st.session_state.fake_chat = []  # list of dicts {role, text}


def on_change_language():
    """Update language code when top-right dropdown changes."""
    label = st.session_state._lang_select_label
    st.session_state.language = LABEL_TO_LANG[label]


# ---------------------------------------------------
# TOP STRIP: logo + language dropdown (aligned)
# ---------------------------------------------------
lang = st.session_state.language
txt = STRINGS[lang]

top_left, top_spacer, top_right = st.columns([1.2, 5, 1.4])

with top_left:
    st.markdown(
        "<div class='muse-logo-pill'>MUSEAI</div>",
        unsafe_allow_html=True,
    )

with top_right:
    current_label = LANG_LABELS[lang]
    st.markdown("<div class='lang-select-box'>", unsafe_allow_html=True)
    st.selectbox(
        " ",  # no label
        options=list(LANG_LABELS.values()),
        index=list(LANG_LABELS.values()).index(current_label),
        key="_lang_select_label",
        on_change=on_change_language,
        label_visibility="collapsed",
    )
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("")

# ---------------------------------------------------
# HERO / SPLASH SCREEN
# ---------------------------------------------------
if not st.session_state.hero_started:
    st.markdown(
        f"""
        <div class="hero-card">
            <div class="hero-title">{txt['hero_title']}</div>
            <div class="hero-sub">{txt['hero_sub']}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    center_col = st.columns([3, 2, 3])[1]
    with center_col:
        start_clicked = st.button(txt["hero_button"], use_container_width=True)

    if start_clicked:
        st.session_state.hero_started = True
        st.rerun()

    # Stop before main tour UI
    st.stop()

# ---------------------------------------------------
# MAIN TOUR PROTOTYPE
# ---------------------------------------------------

# Sidebar (mirrors real app later)
with st.sidebar:
    st.markdown("### MuseAI Tour")
    st.caption("Your multilingual museum companion.")

    current_label = LANG_LABELS[st.session_state.language]
    sidebar_choice = st.selectbox(
        "Language",
        options=list(LANG_LABELS.values()),
        index=list(LANG_LABELS.values()).index(current_label),
        key="_sidebar_lang",
    )
    # Keep language in sync from sidebar too
    st.session_state.language = LABEL_TO_LANG[sidebar_choice]
    txt = STRINGS[st.session_state.language]

    st.markdown("")
    st.button("Start new artifact tour", use_container_width=True)

    st.caption(
        "Aim at an artifact, then speak once MuseAI has identified it."
    )

# STEP 1 – Camera (titles LEFT aligned as requested)
st.markdown(
    f"<h3 class='section-title-left'>{txt['step1_title']}</h3>",
    unsafe_allow_html=True,
)
st.markdown(
    f"<p class='section-sub-left'>{txt['step1_hint']}</p>",
    unsafe_allow_html=True,
)

cam_outer = st.container()
with cam_outer:
    cam_col, _ = st.columns([1.4, 1])

    with cam_col:
        st.markdown("<div class='camera-frame'>", unsafe_allow_html=True)
        camera_file = st.camera_input(
            " ",
            key="demo_camera",
            label_visibility="collapsed",
        )
        st.markdown("</div>", unsafe_allow_html=True)

        if camera_file is not None and not st.session_state.is_scanning:
            st.session_state.camera_has_photo = True
            st.session_state.is_scanning = True

    status_col, _ = st.columns([1.4, 1])
    with status_col:
        if not st.session_state.camera_has_photo:
            st.caption("Once the photo is captured, MuseAI will auto-scan it.")
        else:
            with st.spinner(txt["scanning"]):
                time.sleep(1.3)  # fake delay
            st.success("✅ Artifact recognized (demo only).")

st.markdown("---")

# STEP 2 – Voice conversation demo (LEFT aligned)
st.markdown(
    f"<h3 class='section-title-left'>{txt['step2_title']}</h3>",
    unsafe_allow_html=True,
)
st.markdown(
    f"<p class='section-sub-left'>{txt['step2_hint']}</p>",
    unsafe_allow_html=True,
)

voice_col, _ = st.columns([1.2, 1])
with voice_col:
    if st.button("🎤 Hold to ask (demo)", key="demo_mic_btn"):
        # In the real app this is where the mic would record.
        # For now we just simulate a Q&A.
        st.session_state.fake_chat.append(
            {"role": "user", "text": txt["demo_question"]}
        )
        st.session_state.fake_chat.append(
            {"role": "assistant", "text": txt["fake_answer"]}
        )

# Chat bubbles
for msg in st.session_state.fake_chat:
    if msg["role"] == "assistant":
        st.markdown(
            f"<div class='bubble-assistant'>🤖 {msg['text']}</div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"<div class='bubble-user'>🧑 {msg['text']}</div>",
            unsafe_allow_html=True,
        )

st.markdown("---")

# Error-preview area
with st.expander("Demo: what an error message will look like"):
    st.error(
        f"**{txt['error_title']}**\n\n"
        f"{txt['error_body']}\n\n"
        "_Technical details will be hidden behind this friendly message._"
    )