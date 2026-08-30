# CloudText - Complete Changelog & Architecture Specification (2026 Update)

> Documenting all modifications, feature additions, database schema updates, storage cleanup algorithms, cybersecurity measures, UI design implementations, and test suites across the CloudText codebase.

---

## Ğµ Summary of Changes & Updates

### 1. Database Schema & Persistence (ct/models.py, ct/migrations/0002_*.py)
* **Neon PostgreSQL & SQLite Dual Compatibility:** Added fallback logic in text/settings.py so the app uses local SQLite (db.sqlite3) for offline development and automatically connects to Neon PostgreSQL via DATABASE_URL in production.
* **BYTEA Storage for Ephemeral Disk Environments:** Render free tier app disks reset on every restart/redeploy. Files are stored as raw binary blobs (models.BinaryField) directly inside Neon PostgreSQL, eliminating external paid cloud storage (AWS S3) requirements.
* **Schema Additions (Store Model):**
  * is_file (BooleanField, default=False): Distinguishes binary file uploads from plain text/code pastes.
  * file_data (BinaryField, optional): Holds raw uncompressed image bytes or losslessly compressed zip archives.
  * file_name (CharField, optional): Stores the sanitized original file or zip package name.
  * file_size (BigIntegerField, default=0): Tracks total binary blob size in bytes for accurate DB storage calculations.
  * file_type (CharField, optional): Tracks MIME content-type (image/png, application/zip, etc.).w

---

### 2. DB Storage Management & Conditional 30-Day Cleanup (ct/views.py)
* **Conditional 30-Day File Cleanup (cleanup_expired_files):**
  * **mule:** 30-day-old file records (is_file=True and date <= 30 days ago) are purged **IFF AND ONLY IFF**:
    1. Total DB file storage exceeds **400 MB** (> 400 * 1024 * 1024 bytes), **mMR**
    2. Incoming upload payload is **>= 200 MB** (>= 200 * 1024 * 1024 bytes).
  * **Rule:** If neither condition is met, 30-day-old files are **NOT deleted**.
  * **Rule:** Text-only pastes (is_file=False) are **NEVER deleted** under any circumstance.
* **Total Storage Calculation (get_total_db_storage_bytes):** Uses Django ORM Sum('file_size') aggregation on is_file=True records.

---

### 3. Upload & File Handling Features (ct/views.py, save1.html)
*`*unified Drag & Drop Zone:** Supports pasting raw text/code snippets, dropping single files, dropping multiple files, OR dropping **entire directory folder trees** (webkitdirectory).
* **100% Original Image Quality Preservation:** Image uploads (.png, .jpg, .jpeg, 'gif, .webp, .svg) are stored as raw uncompressed binary streams (BYTEA) without any lossy compression or resbzing.
* **Lossless Zip Compression for Folders & Non-Images:** Directories and non-image files are zipped using zipfile.ZIP_DEFLATED compression to conserve database space.
* **Simultaneous Text & Media Uploads:** Users can paste text notes AND drop files/images at the same time; both are saved together under a single 4-character code.
* **Controlled Downloads (No Auto-Downloading):** File retrieval renders a structured card with preview/metadata and an explicit **"Download Package (.zip)"** button (/download/<id>/).w

---

### 4. ğŸ¡ Built-in Cybersecurity Measures (ct/views.py, text/settings.py)

#### *Measure A: Path Traversal & Zip Slip Guard (sanitize_filename)**
* **Code Location:** ct/views.py
* **Explanation:** Strips dangerous path traversal characters (../, ..\) and invalid symbols using os.path.basename() and Django's get_valid_filename(). Prevents malicious relative path overrides in single/multi-file uploads and zip archives.
* **Code Tag:** # === SECURITY MEASURES 2026: File Name Sanitization & Path Traversal Guard ===

#### *Measure B: IP-Based Rate Limiting (is_rate_limited)**
*`*Code Location:** ct/views.py
* **Explanation:** Enforces an IP sliding window cap of **maximum 7 requests per minute per IP address** (REMOTE_ADDR & X-Forwarded-For) on /save/ and /get/ routes. Protects against automated 4-character code brute-forcing and DoS storage flooding.
* **Code Tag:** # === SECURITY MEASURES 2026: IP-Based Rate Limiter (Max 7 requests/min per IP) ===

#### *Measure C: HTTP Security Headers & Stored XSS Prevention**
*`*Code Location:** text/settings.py & ct/views.py (d½İ¹±½…‘}™¥±”¤(©€©áÁ±…¹…Ñ¥½¸è¨¨½¹™¥ÕÉ•Ì±½‰…°‰É½İÍ•ÈÍ•ÕÉ¥Ñä¡•…‘•ÉÌè(€€¨MUI}	I=]MI}aMM}%1QH€ôQÉÕ”(€€¨MUI}=9Q9Q}QeA}9=M9%€ôQÉÕ”(€€¨a}I5}=AQ%=9L€ô€9dœ€¡±¥­©…­¥¹œÁÉ½Ñ•Ñ¥½¸¤(€€¨½É•½¹Ñ•¹Ğµ¥ÍÁ½Í¥Ñ¥½¸è…ÑÑ…¡µ•¹Ğ…¹`µ½¹Ñ•¹ĞµQåÁ”µ=ÁÑ¥½¹Ìè¹½Í¹¥™˜½¸™¥±”‘½İ¹±½…‘ÌÑ¼ÁÉ•Ù•¹Ğ‰É½İÍ•ÉÌ™É½´•á•ÕÑ¥¹œÕÁ±½…‘•€¹¡Ñµ°½È€¹ÍÙœÍÉ¥ÁÑÌ¥¸Ñ¡”ÕÍ•ÈÌ‰É½İÍ•È½¹Ñ•áĞ¸(©€©½‘”Q…œè¨¨€Œ€ôôôMUI%Qd5MUIL€ÈÀÈØè!QQ@M•ÕÉ¥Ñä!•…‘•ÉÌ€ôôô((´´´((ŒŒŒ€Ô¸U$5½‘•É¹¥é…Ñ¥½¸€˜5½‰¥±”=ÁÑ¥µ¥é…Ñ¥½¸€¡‰…Í”Ä¹¡Ñµ°°Í…Ù”Ä¹¡Ñµ°°É•ÍÕ±ĞÄ¹¡Ñµ°°‰½ÕĞ¹¡Ñµ°¤(©€©=ÁÑ¥½¸€È€¡Y•É•°€¼ÁÁ±”5¥¹¥µ…±¥ÍĞQ¡•µ”¤è¨¨AÕÉ”=‰Í¥‘¥…¸	±…¬€ ŒÀÀÀÀÀÀ¤°…É¬¡…É½…°ÍÕÉ™…•Ì€ ŒÁ„Á„Á„¤°É¥ÍÀ]¡¥Ñ”Ñ•áĞ€ ŒÀÀÀÀÀÀ¤°…¹µ•É…±É••¸…•¹ÑÌ€ ŒÄÁˆäàÄ¤¸(¨€¨©5½‰¥±”µ¥ÉÍĞM•…É •ÍÌè¨¨5½Ù•Ñ¡”€‰M•…É İ¥Ñ ½‘”ˆÉ•ÑÉ¥•Ù”¥¹ÁÕĞ‰…È=UQM%Ñ¡”½±±…ÁÍ¥‰±”¡…µ‰ÕÉ•Èµ•¹Ô¥¸‰…Í”Ä¹¡Ñµ°¸Q¡”É•ÑÉ¥•Ù”Í•…É ‰…ÈÉ•µ…¥¹ÌÁ•Éµ…¹•¹Ñ±äÙ¥Í¥‰±”‘¥É•Ñ±ä¥¸Ñ¡”Ñ½À¡•…‘•È…É½ÍÌ…±°µ½‰¥±”…¹‘•Í­Ñ½ÀÍÉ••¹Ì€ ‰…Ù…¥±…‰±”™É½´¼ˆ¤¸(¨€¨©¹¡…¹•%¹¹•ÈQ•áĞY¥Í¥‰¥±¥Ñäè¨¨(€€¨Q•áÑ…É•„Á±…•¡½±‘•Èè€‰!•±±¼°A…ÍÑ”å½ÕÈÑ•áĞ½½‘”¡•É”ˆ¸(€€¨Q½ÀÉ•ÑÉ¥•Ù”‰…ÈÁ±…•¡½±‘•Èè€‰M•…É İ¥Ñ ½‘”ˆ¸(€€¨MLÉÕ±”è¹™½É•¡¥ µ½¹ÑÉ…ÍĞ€èéÁ±…•¡½±‘•ÈÍÑå±¥¹œ€¡½±½Èè€„Å„Å…„€…¥µÁ½ÉÑ…¹Ğì½Á…¥Ñäè€Ä€…¥µÁ½ÉÑ…¹Ğì¤¸(¨€¨¨Äµ±¥¬½Áä½‘”	ÕÑÑ½¸è¨¨‘‘•€Äµ±¥¬€¨©½Áä½‘”¨¨‰ÕÑÑ½¸Ñ¼…±•ÉĞ‰…¹¹•È…¹É•ÑÉ¥•Ù•Ñ•áĞÍ¹¥ÁÁ•ÑÌ¸(¨€¨©5Õ±Ñ¤µA¥ÑÕÉ”…±±•Éä€˜i¥ÀáÁ±½É•Èè¨¨áÑÉ…ÑÌ‰…Í”ØĞ¥¹±¥¹”¥µ…”Ñ¡Õµ‰¹…¥±Ì™½ÈÁ¥ÑÕÉ”Á…­…•Ì…¹‘¥ÍÁ±…åÌ…¸%µÍÑå±”™¥±”±¥ÍĞ™½Èé¥À…É¡¥Ù•Ì¥¸É•ÍÕ±ĞÄ¹¡Ñµ°¸((´´´((ŒŒŒ€Ø¸ÕÑ½µ…Ñ•U¹¥ĞQ•ÍĞMÕ¥Ñ”€¡Ğ½Ñ•ÍÑÌ¹Áä¤)±°€ÜÕ¹¥ĞÑ•ÍÑÌÁ…ÍÍ•±•…¹±ä€¡ÁåÑ¡½¸µ…¹…”¹ÁäÑ•ÍĞĞ¤è(Ä¸Ñ•ÍÑ}Ñ•áÑ}ÕÁ±½…‘}…¹‘}É•ÑÉ¥•Ù…°èY•É¥™¥•ÌÁ±…¥¸Ñ•áĞ½½‘”Á…ÍÑ”Í…Ù¥¹œ…¹½‘”É•ÑÉ¥•Ù…°¸(È¸Ñ•ÍÑ}™¥±•}ÕÁ±½…‘}…¹‘}‘½İ¹±½…èY•É¥™¥•Ì‰¥¹…Éä™¥±”é¥ÁÁ¥¹œ…¹•áÁ±¥¥Ğ‘½İ¹±½…É½ÕÑ”¸(Ì¸Ñ•ÍÑ}¥µ…•}ÅÕ…±¥Ñå}ÁÉ•Í•ÉÙ…Ñ¥½¸èY•É¥™¥•Ì€ÄÀÀ”‰åÑ”µ™½Èµ‰åÑ”¥µ…”ÅÕ…±¥ÑäÁÉ•Í•ÉÙ…Ñ¥½¸¸(Ğ¸Ñ•ÍÑ|ÌÁ}‘…å}±•…¹ÕÁ}½¹‘¥Ñ¥½¹…±}ÉÕ±•ÌèY•É¥™¥•Ì±•…¹ÕÀÑÉ¥•ÉÌ=91d¥˜€ø€ĞÀÁ5½È¥¹½µ¥¹œ™¥±”€øô€ÈÀÁ5°İ¡¥±”­••Á¥¹œÑ•áĞÁ…ÍÑ•ÌÁ•Éµ…¹•¹Ğ¸(Ô¸Ñ•ÍÑ}¥Á}É…Ñ•}±¥µ¥Ñ¥¹}µ…á|İ}Á•É}µ¥¹ÕÑ”èY•É¥™¥•Ì%@É…Ñ”±¥µ¥Ñ¥¹œ…Ğµ…à€ÜÉ•Ä½µ¥¸Á•È%@¸(Ø¸Ñ•ÍÑ}Á…Ñ¡}ÑÉ…Ù•ÉÍ…±}™¥±•¹…µ•}Í…¹¥Ñ¥é…Ñ¥½¸èY•É¥™¥•ÌÍÑÉ¥ÁÁ¥¹œ½˜€¸¸¼…¹€¸¹pÁ…Ñ ÑÉ…Ù•ÉÍ…°Ù•Ñ½ÉÌ¹ Ä¸Ñ•ÍÑ}Í¥µÕ±Ñ…¹•½ÕÍ}Ñ•áÑ}…¹‘}™¥±•}ÕÁ±½…èY•É¥™¥•ÌÍ¥µÕ±Ñ…¹•½ÕÌÑ•áĞ¹½Ñ•Ì…¹™¥±”½¥µ…”ÕÁ±½…‘ÌÕ¹‘•È€Ä½‘”¸((´´´((ŒŒŒƒ
„½‘”Q…¥¹œ½¹Ù•¹Ñ¥½¸)±°…‘‘¥Ñ¥½¹Ì…¹ÕÁ‘…Ñ•Ì…É½ÍÌµ½‘•±Ì¹Áä°Ù¥•İÌ¹Áä°Í•ÑÑ¥¹Ì¹Áä°ÕÉ±Ì¹Áä°Ñ•ÍÑÌ¹Áä°…¹Ñ•µÁ±…Ñ•Ì…É”ÍÑÉ¥Ñ±äİÉ…ÁÁ•Õ¹‘•Èè( ¡ÑÑÁÌè¼½ÍÑ…¬¹¥¸¤(½‘”è(Œ€ôôô€ÈÀÈØÕÁ‘…Ñ”„€ôôô(¸¸¸(Œ€ôôô€ÈÀÈØÕÁ‘…Ñ”„€ôôô()…¹Í•ÕÉ¥Ñä™Õ¹Ñ¥½¹Ì…É”İÉ…ÁÁ•Õ¹‘•Èè(½‘”è8(Œ€ôôôMUI%Qd5MUIL€ÈÀÈØèm•…ÑÕÉ”9…µ•t€ôôô(ŒáÁ±…¹…Ñ¥½¸èm•Ñ…¥±•É•…Í½¹t(¸¸¸(Œ€ôôôMUI%Qd5MUIL€ÈÀÈØ€ôôô(