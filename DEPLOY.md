# 🚀 Panduan Deploy SyncUp ke Internet

Ikuti langkah ini **satu kali** — setelah itu website kamu live dan bisa dibuka siapa saja.

---

## Bagian 1 — Setup Database (Supabase)

### 1. Buat akun Supabase
Buka [supabase.com](https://supabase.com) → **Start your project** → login pakai GitHub.

### 2. Buat project baru
- Klik **New Project**
- Isi nama (cth: `syncup`) dan password database
- Pilih region terdekat (Singapore)
- Tunggu ~2 menit sampai project siap

### 3. Buat tabel `sessions`
Di sidebar kiri → **SQL Editor** → klik **New query** → paste SQL ini lalu klik **Run**:

```sql
CREATE TABLE sessions (
  code        TEXT PRIMARY KEY,
  topic       TEXT NOT NULL,
  members     JSONB DEFAULT '[]'::jsonb,
  created_at  BIGINT
);

-- Izinkan akses publik (untuk prototype)
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "allow_all" ON sessions
  FOR ALL USING (true) WITH CHECK (true);
```

### 4. Ambil kredensial
Di sidebar → **Project Settings** → **API**:
- Copy **Project URL** → ini `SUPABASE_URL`
- Copy **anon / public key** → ini `SUPABASE_KEY`

---

## Bagian 2 — Upload ke GitHub

### 1. Buat repo baru
Buka [github.com/new](https://github.com/new):
- Nama repo: `syncup`
- Visibility: **Public**
- Klik **Create repository**

### 2. Push kode
Di terminal, masuk ke folder `syncup/`:

```bash
cd syncup
git init
git add app.py requirements.txt .streamlit/config.toml .gitignore README.md
# JANGAN add secrets.toml — sudah ada di .gitignore
git commit -m "first commit"
git branch -M main
git remote add origin https://github.com/USERNAME/syncup.git
git push -u origin main
```

> Ganti `USERNAME` dengan username GitHub kamu.

---

## Bagian 3 — Deploy ke Streamlit Community Cloud

### 1. Buka Streamlit Cloud
Buka [share.streamlit.io](https://share.streamlit.io) → login pakai GitHub.

### 2. Deploy app
- Klik **New app**
- Pilih repo `syncup` dan branch `main`
- Main file path: `app.py`
- Klik **Advanced settings** → tab **Secrets**

### 3. Tambahkan secrets
Paste ini di kolom Secrets (ganti dengan nilai asli dari Supabase):

```toml
SUPABASE_URL = "https://xxxxxxxxxxxx.supabase.co"
SUPABASE_KEY = "eyJxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

### 4. Deploy!
Klik **Deploy** → tunggu ~1-2 menit → website kamu live di URL seperti:
```
https://syncup-namakamu.streamlit.app
```

---

## ✅ Hasil Akhir

- Website live & bisa dibuka dari HP/laptop siapapun
- Data tersimpan di Supabase — tidak hilang saat app restart
- Ketua tim buat sesi → share kode → anggota buka link yang sama dan gabung
- Semua gratis (Supabase free tier + Streamlit Community Cloud free)

---

## 🔄 Update Kode

Kalau kamu edit `app.py` dan mau update website:
```bash
git add app.py
git commit -m "update fitur X"
git push
```
Streamlit Cloud otomatis re-deploy dalam ~1 menit.
