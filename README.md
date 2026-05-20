# ⚡ SyncUp — MVP Prototype

Bantu kelompok belajar mulai sesi dengan arah yang jelas, tanpa perlu ada yang jadi pemimpin duluan.

---

## 🚀 Cara Jalankan

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Jalankan app
```bash
streamlit run app.py
```

App akan terbuka otomatis di browser di `http://localhost:8501`

---

## 📱 Alur Penggunaan

### Ketua Tim
1. Buka app → klik **Buat Sesi Baru**
2. Isi topik sesi (cth: "Revisi laporan final")
3. Copy link/kode sesi → bagikan ke anggota
4. Klik **Isi Input Sebagai Ketua Tim** → isi form
5. Setelah semua anggota mengisi → klik **Lihat Agenda Sesi**
6. Klik **Mulai Timer** untuk memulai sesi dengan countdown

### Anggota
1. Buka app → klik **Gabung Sesi**
2. Masukkan nama + kode sesi dari ketua
3. Isi form: topik, kendala, waktu available, role preference
4. Submit → agenda otomatis terbentuk

---

## 🗂️ Struktur
```
syncup/
├── app.py              # Main Streamlit app
├── requirements.txt    # Dependencies
├── README.md           # This file
└── syncup_sessions.json  # Auto-generated session data
```

---

## ✂️ Fitur yang Sengaja Tidak Dibangun (MVP Scope)
- Login / autentikasi
- Notifikasi / reminder
- Riwayat sesi
- Chat dalam app
- Sinkronisasi timer real-time antar device
- Integrasi kalender
