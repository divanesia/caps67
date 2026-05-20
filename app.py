import streamlit as st
import json
import random
import string
import time

# ── Config ──────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SyncUp",
    page_icon="⚡",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── Supabase client (cached) ─────────────────────────────────────────────────
@st.cache_resource
def get_sb():
    from supabase import create_client
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"],
    )

# ── Data layer ───────────────────────────────────────────────────────────────

def load_session(code: str):
    """Return session dict or None."""
    try:
        r = get_sb().table("sessions").select("*").eq("code", code).execute()
        if r.data:
            row = r.data[0]
            return {"topic": row["topic"], "members": row["members"] or []}
    except Exception as e:
        st.error(f"DB error: {e}")
    return None


def create_session(code: str, topic: str):
    try:
        get_sb().table("sessions").insert({
            "code": code,
            "topic": topic,
            "members": [],
            "created_at": int(time.time()),
        }).execute()
        return True
    except Exception as e:
        st.error(f"DB error: {e}")
        return False


def add_member(code: str, member: dict):
    """Add / replace member entry (upsert by nama)."""
    try:
        sess = load_session(code)
        if not sess:
            return False
        members = [m for m in sess["members"] if m.get("nama") != member["nama"]]
        members.append(member)
        get_sb().table("sessions").update({"members": members}).eq("code", code).execute()
        return True
    except Exception as e:
        st.error(f"DB error: {e}")
        return False


def gen_code():
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=6))


# ── Agenda generator ─────────────────────────────────────────────────────────

def build_agenda(sess):
    members   = sess.get("members", [])
    prioritas, kendala, roles = [], [], {}
    max_waktu = 60

    for m in members:
        if m.get("bahas"):   prioritas.append(m["bahas"])
        if m.get("kendala"): kendala.append(m["kendala"])
        if m.get("nama") and m.get("role"):
            roles[m["nama"]] = m["role"]
        try:
            max_waktu = max(max_waktu, int(m.get("waktu", 60)))
        except Exception:
            pass

    prioritas = list(dict.fromkeys(prioritas))
    kendala   = list(dict.fromkeys(kendala))

    if max_waktu >= 90:
        alur = [
            {"label": "Pembagian tugas & orientasi", "menit": 10},
            {"label": "Pengerjaan / diskusi inti",   "menit": max_waktu - 25},
            {"label": "Review hasil & wrap-up",       "menit": 15},
        ]
    elif max_waktu >= 60:
        alur = [
            {"label": "Pembagian tugas",   "menit": 10},
            {"label": "Pengerjaan bareng", "menit": max_waktu - 20},
            {"label": "Review hasil",      "menit": 10},
        ]
    else:
        alur = [
            {"label": "Orientasi cepat", "menit": 5},
            {"label": "Diskusi inti",    "menit": max_waktu - 10},
            {"label": "Wrap-up",         "menit": 5},
        ]

    return {"prioritas": prioritas, "kendala": kendala, "alur": alur, "roles": roles}


# ── Design helpers ───────────────────────────────────────────────────────────

CSS = """
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
#MainMenu,footer,header,[data-testid="stToolbar"],
[data-testid="stDecoration"],[data-testid="stStatusWidget"]{display:none!important}
html,body,[data-testid="stAppViewContainer"],[data-testid="stMain"],section.main{background:#09090f!important}
[data-testid="block-container"]{max-width:460px!important;padding:24px 16px 80px!important;margin:0 auto!important}
*,*::before,*::after{font-family:'Plus Jakarta Sans',sans-serif!important;box-sizing:border-box}
.stTextInput input,.stNumberInput input{background:#13131f!important;border:1.5px solid #25253a!important;
  border-radius:12px!important;color:#f0f0ff!important;font-size:14px!important;padding:12px 16px!important;transition:border-color .2s!important}
.stTextInput input:focus,.stNumberInput input:focus{border-color:#ff6b35!important;box-shadow:0 0 0 3px rgba(255,107,53,.15)!important}
.stTextInput label,.stNumberInput label{color:#8888aa!important;font-size:12px!important;font-weight:600!important;letter-spacing:.4px!important;text-transform:uppercase!important}
.stRadio>label{color:#8888aa!important;font-size:12px!important;font-weight:600!important;letter-spacing:.4px!important;text-transform:uppercase!important}
[data-testid="stRadio"]>div{gap:8px!important;flex-direction:column!important}
[data-testid="stRadio"]>div>label{background:#13131f!important;border:1.5px solid #25253a!important;border-radius:12px!important;
  padding:11px 16px!important;color:#c0c0d8!important;font-size:14px!important;font-weight:500!important;width:100%!important;margin:0!important;transition:all .15s!important;cursor:pointer!important}
[data-testid="stRadio"]>div>label:has(input:checked){border-color:#ff6b35!important;background:rgba(255,107,53,.1)!important;color:#ff6b35!important}
.stButton>button{background:linear-gradient(135deg,#ff6b35,#e85420)!important;color:#fff!important;border:none!important;
  border-radius:14px!important;padding:14px 24px!important;font-size:15px!important;font-weight:700!important;width:100%!important;
  letter-spacing:.2px!important;transition:all .2s!important;box-shadow:0 4px 20px rgba(255,107,53,.25)!important}
.stButton>button:hover{opacity:.9!important;transform:translateY(-1px)!important}
.ghost .stButton>button{background:#13131f!important;border:1.5px solid #25253a!important;color:#8888aa!important;box-shadow:none!important}
.stNumberInput button{background:#13131f!important;border:1.5px solid #25253a!important;border-radius:8px!important;color:#c0c0d8!important}
.stProgress>div>div>div>div{background:#ff6b35!important;border-radius:99px!important}
.stProgress>div>div>div{background:#1e1e30!important;border-radius:99px!important}
[data-testid="stAlert"]{background:rgba(255,107,53,.08)!important;border:1px solid rgba(255,107,53,.2)!important;border-radius:12px!important;color:#f0f0ff!important}
[data-testid="stCode"] pre{background:#13131f!important;border:1.5px dashed #25253a!important;border-radius:12px!important;color:#8888aa!important;font-size:13px!important;padding:12px 16px!important}
hr{border-color:#1e1e30!important;margin:20px 0!important}
[data-testid="column"]{padding:0 4px!important}
</style>
"""

def chip(t):
    return f'<div style="display:inline-block;background:rgba(255,107,53,.12);color:#ff6b35;border-radius:99px;padding:4px 14px;font-size:11px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:16px;">{t}</div>'

def h1(t, size="28px"):
    return f'<h1 style="font-size:{size};font-weight:800;color:#f0f0ff;line-height:1.2;margin:0 0 8px;">{t}</h1>'

def sub(t):
    return f'<p style="color:#8888aa;font-size:14px;line-height:1.7;margin:0 0 28px;">{t}</p>'

def sec(t):
    return f'<p style="font-size:11px;font-weight:700;color:#ff6b35;letter-spacing:1.5px;text-transform:uppercase;margin:0 0 10px;">{t}</p>'

def card(content, bg="#13131f", border="#25253a", pad="20px 18px"):
    return f'<div style="background:{bg};border:1.5px solid {border};border-radius:14px;padding:{pad};margin-bottom:8px;">{content}</div>'

def badge(t):
    return f'<span style="background:rgba(255,107,53,.12);color:#ff6b35;border-radius:6px;padding:3px 10px;font-size:12px;font-weight:600;">{t}</span>'

def pill(t):
    return f'<div style="display:inline-block;background:#1e1e30;border-radius:99px;padding:5px 14px;font-size:12px;font-weight:700;color:#8888aa;margin-bottom:16px;">{t}</div>'


# ── Navigation ───────────────────────────────────────────────────────────────

def nav(page):
    st.session_state.page = page
    st.rerun()


# ── Timer helpers ────────────────────────────────────────────────────────────

def timer_start(seconds):
    st.session_state.timer_start_ts          = time.time()
    st.session_state.timer_remaining_at_start = seconds
    st.session_state.timer_paused             = False
    st.session_state.timer_paused_remaining   = seconds

def timer_pause():
    st.session_state.timer_paused_remaining = get_remaining()
    st.session_state.timer_paused = True

def timer_resume():
    st.session_state.timer_start_ts           = time.time()
    st.session_state.timer_remaining_at_start = st.session_state.get("timer_paused_remaining", 0)
    st.session_state.timer_paused             = False

def get_remaining():
    if st.session_state.get("timer_paused"):
        return st.session_state.get("timer_paused_remaining", 0)
    elapsed = time.time() - st.session_state.get("timer_start_ts", time.time())
    return max(0, int(st.session_state.get("timer_remaining_at_start", 0) - elapsed))


# ── Pages ────────────────────────────────────────────────────────────────────

def page_landing():
    st.markdown("""
    <div style="text-align:center;padding:48px 0 32px;">
        <div style="font-size:52px;margin-bottom:12px;">⚡</div>
        <div style="font-size:36px;font-weight:800;color:#f0f0ff;letter-spacing:-1px;">
            Sync<span style="color:#ff6b35;">Up</span>
        </div>
        <p style="color:#8888aa;font-size:14px;margin:10px 0 0;line-height:1.7;">
            Bantu kelompokmu mulai sesi<br>dengan arah yang jelas.
        </p>
    </div>
    """, unsafe_allow_html=True)

    if st.button("⚡  Buat Sesi Baru"):
        nav("buat_step1")
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    with st.container():
        st.markdown('<div class="ghost">', unsafe_allow_html=True)
        if st.button("🔗  Gabung Sesi"):
            nav("gabung")
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown('<div style="text-align:center;margin-top:48px;color:#2e2e44;font-size:12px;">Tidak ada yang jadi pemimpin. Semua berkontribusi.</div>', unsafe_allow_html=True)


def page_buat_step1():
    st.markdown(chip("Langkah 1 / 2"), unsafe_allow_html=True)
    st.markdown(h1("Siapkan Sesi Bareng"), unsafe_allow_html=True)
    st.markdown(sub("Semua anggota akan mengisi fokus masing-masing sebelum sesi dimulai"), unsafe_allow_html=True)

    topic = st.text_input("HARI INI MAU BAHAS ATAU KERJAIN APA?",
                          placeholder="contoh: Latihan statistik / Revisi proposal",
                          key="input_topic")
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    if st.button("Lanjut dan Buat Link →"):
        if topic.strip():
            code = gen_code()
            if create_session(code, topic.strip()):
                st.session_state.session_code  = code
                st.session_state.session_topic = topic.strip()
                nav("buat_step2")
        else:
            st.error("Isi topik sesi dulu ya!")

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    with st.container():
        st.markdown('<div class="ghost">', unsafe_allow_html=True)
        if st.button("← Kembali", key="back_b1"): nav("landing")
        st.markdown("</div>", unsafe_allow_html=True)


def page_buat_step2():
    code  = st.session_state.get("session_code", "")
    topic = st.session_state.get("session_topic", "")
    link  = f"sesi.id/join/{code}"          # display only

    st.markdown(chip("Langkah 2 / 2"), unsafe_allow_html=True)
    st.markdown(h1("Ajak Teman Masuk"), unsafe_allow_html=True)
    st.markdown(sub("Bagikan link ini ke anggota kelompokmu"), unsafe_allow_html=True)

    st.markdown(sec("Topik sesi"), unsafe_allow_html=True)
    st.markdown(card(f'<span style="color:#f0f0ff;font-size:14px;font-weight:600;">{topic}</span>',
                     bg="rgba(255,107,53,.07)", border="rgba(255,107,53,.18)"), unsafe_allow_html=True)

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    st.markdown(sec("Kode Sesi (bagikan ini)"), unsafe_allow_html=True)
    st.code(code.upper())
    st.info(f"💡 Anggota cukup ketik kode **{code.upper()}** waktu gabung sesi.")

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # Reload fresh member count
    sess = load_session(code)
    n    = len(sess["members"]) if sess else 0
    if n:
        st.markdown(pill(f"👥 {n} anggota sudah mengisi"), unsafe_allow_html=True)

    if st.button("✍️  Isi Input Sebagai Ketua Tim"):
        st.session_state.member_nama      = "Ketua Tim"
        st.session_state.joining_as_ketua = True
        nav("gabung_form")

    if n:
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        if st.button("🎯  Lihat Agenda Sesi"):
            st.session_state.agenda     = build_agenda(sess)
            st.session_state.alur_index = 0
            nav("agenda")

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    with st.container():
        st.markdown('<div class="ghost">', unsafe_allow_html=True)
        if st.button("← Kembali", key="back_b2"): nav("buat_step1")
        st.markdown("</div>", unsafe_allow_html=True)


def page_gabung():
    st.markdown(h1("Gabung Sesi"), unsafe_allow_html=True)
    st.markdown(sub("Masuk dulu sebelum ikut menyusun agenda sesi bareng"), unsafe_allow_html=True)

    nama = st.text_input("NAMA", placeholder="contoh: Aby", key="g_nama")
    kode = st.text_input("KODE SESI", placeholder="contoh: abc123", key="g_kode")
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    if st.button("Selanjutnya →"):
        if nama.strip() and kode.strip():
            raw  = kode.strip().split("/")[-1].lower().strip()
            sess = load_session(raw)
            if sess:
                st.session_state.session_code     = raw
                st.session_state.member_nama      = nama.strip()
                st.session_state.session_topic    = sess["topic"]
                st.session_state.joining_as_ketua = False
                nav("gabung_form")
            else:
                st.error("Kode sesi tidak ditemukan. Cek lagi ya!")
        else:
            st.error("Isi nama dan kode sesi dulu!")

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    with st.container():
        st.markdown('<div class="ghost">', unsafe_allow_html=True)
        if st.button("← Kembali", key="back_g"): nav("landing")
        st.markdown("</div>", unsafe_allow_html=True)


def page_gabung_form():
    code  = st.session_state.get("session_code", "")
    topic = st.session_state.get("session_topic", "")
    nama  = st.session_state.get("member_nama", "Anggota")

    sess = load_session(code)
    n    = len(sess["members"]) if sess else 0

    st.markdown(pill(f"✍️  {nama}  ·  {n} sudah mengisi"), unsafe_allow_html=True)
    st.markdown(h1(topic, size="22px"), unsafe_allow_html=True)
    st.markdown(sub("Semua jawaban anggota akan digabung otomatis menjadi agenda sesi bareng"), unsafe_allow_html=True)

    bahas   = st.text_input("HAL APA YANG MENURUTMU PERLU DIBAHAS DULU?",
                             placeholder="contoh: pembagian tugas presentasi", key="f_bahas")
    kendala = st.text_input("ADA KENDALA ATAU HAL YANG PERLU DIKLARIFIKASI?",
                             placeholder="contoh: belum bagi role / deadline mepet", key="f_kendala")
    waktu   = st.number_input("HARI INI KAMU AVAILABLE BERAPA LAMA? (MENIT)",
                               min_value=15, max_value=300, value=60, step=15, key="f_waktu")
    role    = st.radio("KAMU NYAMAN BANTU DI BAGIAN...",
                       ["Catet poin penting", "Timer", "Jelasin ide", "Flexible", "Lainnya"],
                       key="f_role")

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    if st.button("Susun Agenda →"):
        if bahas.strip():
            ok = add_member(code, {
                "nama":    nama,
                "bahas":   bahas.strip(),
                "kendala": kendala.strip(),
                "waktu":   int(waktu),
                "role":    role,
            })
            if ok:
                sess = load_session(code)
                st.session_state.agenda     = build_agenda(sess)
                st.session_state.alur_index = 0
                nav("agenda")
        else:
            st.error("Isi minimal satu topik yang ingin dibahas!")

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    with st.container():
        st.markdown('<div class="ghost">', unsafe_allow_html=True)
        if st.button("← Kembali", key="back_f"):
            nav("buat_step2" if st.session_state.get("joining_as_ketua") else "gabung")
        st.markdown("</div>", unsafe_allow_html=True)


def page_agenda():
    code    = st.session_state.get("session_code", "")
    agenda  = st.session_state.get("agenda", {})

    sess      = load_session(code)
    n_members = len(sess["members"]) if sess else 0

    st.markdown(pill(f"👥  {n_members} ANGGOTA"), unsafe_allow_html=True)
    st.markdown(h1("Agenda sesi hari ini"), unsafe_allow_html=True)
    st.markdown(sub("Disusun otomatis dari jawaban semua anggota"), unsafe_allow_html=True)

    # Prioritas
    st.markdown(sec("🔥  Prioritas Pembahasan"), unsafe_allow_html=True)
    for item in (agenda.get("prioritas") or ["—"]):
        st.markdown(card(f'<span style="color:#f0f0ff;font-size:14px;font-weight:500;">{item}</span>',
                         bg="rgba(255,107,53,.07)", border="rgba(255,107,53,.18)"), unsafe_allow_html=True)

    kendala = agenda.get("kendala", [])
    if kendala:
        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
        st.markdown(sec("⚠️  Hal yang Perlu Diperjelas"), unsafe_allow_html=True)
        for item in kendala:
            st.markdown(card(f'<span style="color:#f0f0ff;font-size:14px;">{item}</span>',
                             bg="rgba(255,193,7,.06)", border="rgba(255,193,7,.18)"), unsafe_allow_html=True)

    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
    st.markdown(sec("⏱️  Saran Alur Sesi"), unsafe_allow_html=True)
    alur     = agenda.get("alur", [])
    alur_rows = "".join([
        f'<div style="display:flex;justify-content:space-between;padding:9px 0;border-bottom:1px solid #1e1e30;font-size:13px;">'
        f'<span style="color:#c0c0d8;">{a["label"]}</span>'
        f'<span style="color:#ff6b35;font-weight:700;">{a["menit"]}m</span></div>'
        for a in alur
    ])
    st.markdown(card(alur_rows, pad="4px 16px"), unsafe_allow_html=True)

    roles = agenda.get("roles", {})
    if roles:
        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
        st.markdown(sec("👤  Saran Peran Anggota"), unsafe_allow_html=True)
        for nama, role in roles.items():
            st.markdown(card(
                f'<div style="display:flex;align-items:center;gap:12px;">'
                f'<span style="font-weight:700;font-size:14px;color:#f0f0ff;min-width:80px;">{nama}</span>'
                f'{badge(role)}</div>'
            ), unsafe_allow_html=True)

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    if st.button("▶  Mulai Timer"):
        if alur:
            timer_start(alur[0]["menit"] * 60)
            st.session_state.alur_index = 0
        nav("timer")

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    with st.container():
        st.markdown('<div class="ghost">', unsafe_allow_html=True)
        if st.button("← Kembali ke Beranda", key="back_a"): nav("landing")
        st.markdown("</div>", unsafe_allow_html=True)


def page_timer():
    import streamlit.components.v1 as components

    agenda = st.session_state.get("agenda", {})
    alur   = agenda.get("alur", [])
    idx    = st.session_state.get("alur_index", 0)
    code   = st.session_state.get("session_code", "")

    if not alur or idx >= len(alur):
        st.markdown("""
        <div style="text-align:center;padding:60px 0 20px;">
            <div style="font-size:56px;margin-bottom:16px;">🎉</div>
            <h1 style="font-size:26px;font-weight:800;color:#f0f0ff;">Sesi Selesai!</h1>
            <p style="color:#8888aa;font-size:14px;margin-top:8px;">Kerja bagus semuanya!</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("← Kembali ke Agenda"): nav("agenda")
        return

    current   = alur[idx]
    paused    = st.session_state.get("timer_paused", False)
    remaining = get_remaining()
    total_sec = current["menit"] * 60
    progress  = 1.0 - (remaining / total_sec) if total_sec else 1.0

    sess      = load_session(code)
    n_members = len(sess["members"]) if sess else 0

    st.markdown(pill(f"👥  {n_members} ANGGOTA"), unsafe_allow_html=True)
    st.markdown(h1("Agenda sesi hari ini"), unsafe_allow_html=True)
    st.markdown(sub("Disusun otomatis dari jawaban semua anggota"), unsafe_allow_html=True)

    alur_rows = ""
    for i, a in enumerate(alur):
        if   i < idx: color, weight, prefix = "#3a3a50", "500", "✓"
        elif i == idx: color, weight, prefix = "#f0f0ff", "700", "▶"
        else:          color, weight, prefix = "#8888aa", "400", "○"
        alur_rows += (
            f'<div style="display:flex;justify-content:space-between;padding:10px 0;border-bottom:1px solid #1e1e30;font-size:13px;">'
            f'<span style="color:{color};font-weight:{weight};">{prefix}  {a["label"]}</span>'
            f'<span style="color:{"#ff6b35" if i==idx else color};font-weight:700;">{a["menit"]}m</span></div>'
        )
    st.markdown(card(alur_rows, pad="4px 16px"), unsafe_allow_html=True)
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    mins_d = remaining // 60
    secs_d = remaining % 60

    components.html(f"""
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@800&display=swap" rel="stylesheet">
    <div style="text-align:center;padding:28px 24px;background:rgba(255,107,53,.07);
         border:1.5px solid rgba(255,107,53,.22);border-radius:16px;">
        <div style="font-size:11px;font-weight:700;color:#ff6b35;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:10px;">{current['label']}</div>
        <div id="t" style="font-size:68px;font-weight:800;color:#f0f0ff;font-family:'Plus Jakarta Sans',sans-serif;
             letter-spacing:-3px;line-height:1;font-variant-numeric:tabular-nums;">{mins_d:02d}:{secs_d:02d}</div>
        <div id="st" style="font-size:12px;color:#8888aa;margin-top:10px;">{"⏸  Dijeda" if paused else "▶  Berjalan"}</div>
    </div>
    <script>
        var rem={remaining},paused={'true' if paused else 'false'};
        function fmt(n){{return String(Math.floor(n/60)).padStart(2,'0')+':'+String(n%60).padStart(2,'0');}}
        document.getElementById('t').textContent=fmt(rem);
        if(!paused){{var iv=setInterval(function(){{
            if(rem>0){{rem--;document.getElementById('t').textContent=fmt(rem);}}
            else{{clearInterval(iv);document.getElementById('st').textContent='⏰ Waktu habis';}}
        }},1000);}}
    </script>
    """, height=175)

    st.progress(min(progress, 1.0))
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        with st.container():
            st.markdown('<div class="ghost">', unsafe_allow_html=True)
            if st.button("▶  Lanjutkan" if paused else "⏸  Pause", key="btn_pause"):
                timer_resume() if paused else timer_pause()
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
    with col2:
        if st.button("Selesai ✓" if idx >= len(alur)-1 else "Next →", key="btn_next"):
            nxt = idx + 1
            st.session_state.alur_index = nxt
            if nxt < len(alur):
                timer_start(alur[nxt]["menit"] * 60)
            st.rerun()


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    st.markdown(CSS, unsafe_allow_html=True)
    if "page" not in st.session_state:
        st.session_state.page = "landing"

    {
        "landing":     page_landing,
        "buat_step1":  page_buat_step1,
        "buat_step2":  page_buat_step2,
        "gabung":      page_gabung,
        "gabung_form": page_gabung_form,
        "agenda":      page_agenda,
        "timer":       page_timer,
    }.get(st.session_state.page, page_landing)()

main()
