# Muslimaa Academy - Complete Project Documentation

> **Last Updated:** September 2026
> **Live URL:** https://muslimaaacademy.com
> **GitHub:** https://github.com/metheiram/muslimaa-academy (Private)
> **Owner:** Iram Mukhtar

---

## 1. What Is This Project?

Muslimaa Academy is a **full-stack SaaS web platform** for Islamic education, built specifically for Muslim women and children. It's a complete learning management system where:

- **Students** can browse courses, enroll, attend live classes, submit homework, track attendance, and receive notifications
- **Teachers** can register, manage their own academy (students, classes, homework), pay monthly subscriptions, and run their teaching business through the platform
- **Admin (Superuser)** has full control over everything — students, teachers, courses, enrollments, fees, SaaS subscriptions, and payments

The platform follows a **SaaS (Software as a Service) model** where teachers pay monthly subscription fees (Rs. 5,000 - 10,000) based on how many students they want to manage.

---

## 2. Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend Framework** | Django 4.2+ (Python) |
| **Database** | PostgreSQL (Neon.tech cloud) |
| **Frontend** | HTML5, CSS3, JavaScript (vanilla) |
| **Email Service** | Brevo SMTP (transactional emails) |
| **Hosting** | Vercel (Hobby plan) |
| **Version Control** | Git + GitHub (private repo) |
| **Static Files** | WhiteNoise (compressed manifest storage) |
| **Image Handling** | Pillow (Python imaging library) |
| **REST API** | Django REST Framework (installed, minimal use) |

### Python Dependencies
```
django >=4.2,<7.0
djangorestframework >=3.14
python-dotenv >=1.0
psycopg2-binary >=2.9
pillow >=10.0
whitenoise >=6.5
gunicorn >=21.2
dj-database-url >=2.1
```

---

## 3. Architecture Overview

```
muslimaa-academy/
├── config/                  # Django project settings
│   ├── settings.py          # Main settings (DB, email, security)
│   ├── urls.py              # Root URL configuration
│   └── wsgi.py              # WSGI entry point
│
├── accounts/                # User management + SaaS teacher system
│   ├── models.py            # Profile, TeacherSubscription, SubscriptionPayment
│   ├── views.py             # Login, register, student dashboard, profile
│   ├── teacher_views.py     # Teacher register, login, dashboard, students, subscription
│   ├── student_portal_views.py  # Student portal (SaaS)
│   ├── notification_views.py    # Notification management
│   └── urls.py              # All accounts URLs (namespace: accounts)
│
├── courses/                 # Course management
│   ├── models.py            # Course, Rating
│   ├── enrollment_models.py # Enrollment (with teacher assignment)
│   ├── views.py             # Course list, detail, enrollment
│   ├── enrollment_views.py  # Enrollment management
│   └── urls.py
│
├── dashboard/               # Admin panel
│   ├── views.py             # Admin dashboard, students, teachers, courses, enrollments, fees, SaaS
│   └── urls.py              # Admin URLs (namespace: dashboard)
│
├── classes/                 # Live classes & meetings
│   ├── models.py            # Meeting (with Google Meet/Zoom links)
│   └── views.py
│
├── attendance/              # Attendance tracking
│   ├── models.py            # Schedule, Attendance
│   └── views.py
│
├── homework/                # Homework management
│   ├── models.py            # Homework, HomeworkSubmission
│   └── views.py
│
├── payments/                # Payment tracking
│   ├── models.py            # PaymentMethod, Payment
│   └── views.py
│
├── notifications/           # In-app notifications
│   ├── models.py            # Notification
│   └── management/commands/ # Fee reminder command
│
├── messaging/               # Teacher-student messaging
│   ├── models.py            # Message
│   └── views.py
│
├── workshops/               # Workshop management
│   ├── models.py            # Workshop
│   └── views.py
│
├── announcements/           # Announcements
│   ├── models.py            # Announcement
│   └── views.py
│
├── content/                 # CMS content
│   ├── models.py            # Testimonial, ContactMessage
│   └── views.py
│
├── templates/               # All HTML templates (85+ files)
│   ├── base/                # Base layouts (base.html, base_student.html, base_teacher.html, etc.)
│   ├── accounts/            # Auth pages + dashboards
│   ├── dashboard/           # Admin panel pages
│   ├── courses/             # Course pages
│   ├── classes/             # Meeting pages
│   ├── attendance/          # Attendance pages
│   ├── homework/            # Homework pages
│   ├── payments/            # Payment pages
│   ├── messaging/           # Messaging pages
│   ├── workshops/           # Workshop pages
│   ├── announcements/       # Announcement pages
│   ├── content/             # Content pages (about, contact, FAQ)
│   └── emails/              # Email templates
│
├── static/                  # CSS, JS, images
│   ├── css/app.css          # Global styles (minimal - most CSS is inline)
│   ├── js/app.js            # Global JavaScript
│   └── images/              # Logo, images
│
├── .env                     # Environment variables (secrets)
├── .env.example             # Environment template
├── requirements.txt         # Python dependencies
├── manage.py                # Django management
└── db.sqlite3               # Local SQLite (development)
```

---

## 4. All Database Models (18 total)

### accounts app

**Profile** — Extended user info (auto-created for every user)
| Field | Type | Description |
|-------|------|-------------|
| user | OneToOneField(User) | Link to Django user |
| phone | CharField(20) | Phone/WhatsApp number |
| subject | CharField(200) | Subject or academy name |

**TeacherSubscription** — SaaS subscription for teachers
| Field | Type | Description |
|-------|------|-------------|
| teacher | OneToOneField(User) | One subscription per teacher |
| plan | CharField | basic / standard / premium |
| status | CharField | active / expired / pending / cancelled |
| max_students | IntegerField | 10 / 20 / 50 based on plan |
| current_students | IntegerField | Current enrolled count |
| monthly_price | DecimalField | Rs. 5000 / 6000 / 10000 |
| start_date | DateField | When subscription started |
| end_date | DateField | When subscription expires |

Plan limits:
- **Basic:** 1-10 students, Rs. 5,000/month
- **Standard:** 11-20 students, Rs. 6,000/month
- **Premium:** 21-50 students, Rs. 10,000/month

**SubscriptionPayment** — Payment records for subscriptions
| Field | Type | Description |
|-------|------|-------------|
| teacher | ForeignKey(User) | Who paid |
| subscription | ForeignKey(TeacherSubscription) | Which subscription |
| amount | DecimalField | Payment amount |
| method | CharField | jazzcash / sadapay / easypaisa / bank / cash |
| screenshot | ImageField | Payment proof screenshot |
| transaction_id | CharField | Transaction reference |
| status | CharField | pending / approved / rejected |
| approved_by | ForeignKey(User) | Admin who approved |

### courses app

**Course** — Course catalog
| Field | Type | Description |
|-------|------|-------------|
| title | CharField(200) | Course name |
| slug | SlugField | URL-friendly name |
| description | TextField | Full description |
| category | CharField | quranic / islamic / arabic / personal / kids |
| level | CharField | beginner / intermediate / advanced |
| duration | CharField | e.g., "6 weeks" |
| price | DecimalField | Course fee |
| image | ImageField | Course thumbnail |
| instructor | ForeignKey(User) | Assigned teacher |
| features | TextField | One feature per line |
| curriculum | TextField | One module per line |
| faq | TextField | Q: | A: format |
| is_active | BooleanField | Published or draft |

**Rating** — Student course reviews
| Field | Type | Description |
|-------|------|-------------|
| student | ForeignKey(User) | Reviewer |
| course | ForeignKey(Course) | Course reviewed |
| rating | IntegerField | 1-5 stars |
| review | TextField | Written review |

**Enrollment** — Student-course enrollment (in enrollment_models.py)
| Field | Type | Description |
|-------|------|-------------|
| student | ForeignKey(User) | Enrolled student |
| course | ForeignKey(Course) | Enrolled course |
| teacher | ForeignKey(User) | Assigned teacher |
| status | CharField | pending / approved / rejected |
| payment_screenshot | ImageField | Payment proof |
| approved_at | DateTimeField | When approved |

### payments app

**PaymentMethod** — Available payment methods
| Field | Type | Description |
|-------|------|-------------|
| name | CharField | Method name |
| method | CharField | jazzcash / sadapay / easypaisa / bank |
| account_number | CharField | Account number |
| account_title | CharField | Account holder name |
| instructions | TextField | Payment instructions |

**Payment** — Course payment records
| Field | Type | Description |
|-------|------|-------------|
| enrollment | ForeignKey(Enrollment) | Related enrollment |
| student | ForeignKey(User) | Student who paid |
| course | ForeignKey(Course) | Course paid for |
| amount | DecimalField | Payment amount |
| status | CharField | pending / paid / free / waived |
| method | CharField | Payment method used |

### classes app

**Meeting** — Live class sessions
| Field | Type | Description |
|-------|------|-------------|
| title | CharField | Meeting title |
| course | ForeignKey(Course) | Related course |
| teacher | ForeignKey(User) | Host teacher |
| meet_link | TextField | Google Meet / Zoom URL |
| scheduled_at | DateTimeField | Date and time |
| duration_minutes | IntegerField | Duration (default 60) |
| status | CharField | upcoming / ongoing / completed / cancelled |
| students | ManyToManyField(User) | Assigned students |

### homework app

**Homework** — Assignments
| Field | Type | Description |
|-------|------|-------------|
| title | CharField | Assignment title |
| description | TextField | Instructions |
| course | ForeignKey(Course) | Related course |
| teacher | ForeignKey(User) | Assigned by |
| due_date | DateField | Deadline |

**HomeworkSubmission** — Student submissions
| Field | Type | Description |
|-------|------|-------------|
| homework | ForeignKey(Homework) | Related assignment |
| student | ForeignKey(User) | Submitted by |
| submission_text | TextField | Written submission |
| file | FileField | Uploaded file |
| grade | CharField | A+ / A / B / C / D / F |
| feedback | TextField | Teacher feedback |

### attendance app

**Schedule** — Class timetable
| Field | Type | Description |
|-------|------|-------------|
| course | ForeignKey(Course) | Related course |
| teacher | ForeignKey(User) | Teaching teacher |
| day | CharField | monday - sunday |
| start_time | TimeField | Class start |
| end_time | TimeField | Class end |

**Attendance** — Daily attendance records
| Field | Type | Description |
|-------|------|-------------|
| student | ForeignKey(User) | Student |
| course | ForeignKey(Course) | Course |
| date | DateField | Attendance date |
| status | CharField | present / absent / late / excused |
| marked_by | ForeignKey(User) | Teacher who marked |

### notifications app

**Notification** — In-app notifications
| Field | Type | Description |
|-------|------|-------------|
| user | ForeignKey(User) | Recipient |
| title | CharField | Notification title |
| message | TextField | Notification body |
| is_read | BooleanField | Read status |
| notification_type | CharField | fee_reminder / enrollment / payment / general |

### messaging app

**Message** — Teacher-student messaging
| Field | Type | Description |
|-------|------|-------------|
| sender | ForeignKey(User) | Message sender |
| recipient | ForeignKey(User) | Message recipient |
| subject | CharField | Message subject |
| body | TextField | Message content |
| is_read | BooleanField | Read status |

### workshops app

**Workshop** — Workshop events
| Field | Type | Description |
|-------|------|-------------|
| title | CharField | Workshop name |
| slug | SlugField | URL-friendly name |
| description | TextField | Details |
| date | DateField | Event date |
| time | TimeField | Event time |
| instructor | ForeignKey(User) | Led by |
| price | DecimalField | Fee |

### announcements app

**Announcement** — Platform announcements
| Field | Type | Description |
|-------|------|-------------|
| title | CharField | Announcement title |
| message | TextField | Announcement body |
| target | CharField | all / course specific |
| priority | CharField | normal / important / urgent |
| created_by | ForeignKey(User) | Admin who created |

### content app

**Testimonial** — Student testimonials
| Field | Type | Description |
|-------|------|-------------|
| author | CharField | Student name |
| quote | TextField | Testimonial text |
| is_featured | BooleanField | Show on homepage |

**ContactMessage** — Contact form submissions
| Field | Type | Description |
|-------|------|-------------|
| name | CharField | Sender name |
| email | EmailField | Sender email |
| subject | CharField | courses / support / feedback / partnership / other |
| message | TextField | Message content |
| is_read | BooleanField | Admin read status |

---

## 5. All Features (Complete List)

### Public Pages
| Feature | URL | Description |
|---------|-----|-------------|
| Homepage | `/` | Hero, courses preview, testimonials, FAQ, CTA |
| Course List | `/courses/` | Browse all courses with search/filter |
| Course Detail | `/courses/<slug>/` | Course info, curriculum, FAQ, rating form |
| About | `/content/about/` | Academy story, mission, values |
| Contact | `/content/contact/` | Contact form with validation |
| Workshops | `/workshops/` | Upcoming workshops listing |
| FAQ | `/content/faq/` | Frequently asked questions |
| Testimonials | `/content/testimonials/` | Student reviews |

### Authentication
| Feature | URL | Description |
|---------|-----|-------------|
| Login | `/accounts/login/` | Student/ Admin login with role-based redirect |
| Register | `/accounts/register/` | Unified form with Student/Teacher role selector |
| Teacher Login | `/accounts/teacher/login/` | Dedicated teacher login |
| Student Portal Login | `/accounts/portal/login/` | Dedicated student portal login |
| Forgot Password | `/accounts/password/forgot/` | Password reset request |
| Reset Password | `/accounts/reset/<uid>/<token>/` | Password reset form |

### Student Features
| Feature | URL | Description |
|---------|-----|-------------|
| Dashboard | `/student/dashboard/` or `/accounts/dashboard/` | Stats, courses, payments, meetings |
| My Courses | (in dashboard) | Enrolled courses list |
| Enroll | `/courses/<slug>/enroll/` | Course enrollment with payment screenshot |
| My Enrollments | (in dashboard) | Enrollment status, payment upload |
| Meetings | `/schedule/student/` | Upcoming and past meetings |
| Attendance | `/attendance/student/` | Attendance stats and history |
| Homework | `/homework/student/` | Pending and submitted homework |
| Notifications | `/accounts/notifications/` | In-app notifications with mark-read |
| Profile | `/accounts/profile/` | View profile |
| Edit Profile | `/accounts/profile/edit/` | Update name, email, phone |
| Change Password | `/accounts/password/change/` | Change account password |

### Student Portal (SaaS)
| Feature | URL | Description |
|---------|-----|-------------|
| Portal Login | `/accounts/portal/login/` | Student portal login |
| Portal Dashboard | `/accounts/portal/` | Stats, courses, meetings, homework |
| Portal Courses | `/accounts/portal/courses/` | Enrolled courses |
| Portal Meetings | `/accounts/portal/meetings/` | Meeting schedule |
| Portal Homework | `/accounts/portal/homework/` | Homework list |
| Portal Attendance | `/accounts/portal/attendance/` | Attendance records |
| Portal Notifications | `/accounts/portal/notifications/` | Notifications |

### Teacher Features (SaaS)
| Feature | URL | Description |
|---------|-----|-------------|
| Teacher Register | `/accounts/teacher/register/` | Register with plan selection |
| Teacher Login | `/accounts/teacher/login/` | Teacher login |
| Teacher Dashboard | `/accounts/teacher/dashboard/` | Stats, subscription, students, meetings |
| My Students | `/accounts/teacher/students/` | Student list with search |
| Add Student | `/accounts/teacher/students/add/` | Add new student |
| Edit Student | `/accounts/teacher/students/<id>/edit/` | Edit student details |
| Remove Student | `/accounts/teacher/students/<id>/remove/` | Remove student |
| Subscription | `/accounts/teacher/subscription/` | Plan info, payment form, history |
| Submit Payment | `/accounts/teacher/payment/` | Upload payment proof (screenshot) |
| Profile | `/accounts/profile/` | Teacher profile |
| Edit Profile | `/accounts/profile/edit/` | Update profile |
| Change Password | `/accounts/password/change/` | Change password |

### Admin Dashboard
| Feature | URL | Description |
|---------|-----|-------------|
| Admin Dashboard | `/dashboard/` | Overview stats, charts, messages, notifications |
| Students | `/dashboard/students/` | List, add, edit, delete students |
| Teachers | `/dashboard/teachers/` | List, add, edit, assign teachers |
| Enrollments | `/dashboard/enrollments/` | Approve/reject, assign teacher |
| Fee Tracking | `/dashboard/fees/` | Payment records, reminders |
| Courses | `/dashboard/courses/` | CRUD courses |
| SaaS Teachers | `/dashboard/teachers-saas/` | Teacher subscriptions, approve payments |
| Teacher Detail | `/dashboard/teachers-saas/<id>/` | View teacher, change plan, approve/reject |
| Django Admin | `/admin/` | Full Django admin panel |

### Communication
| Feature | URL | Description |
|---------|-----|-------------|
| In-app Notifications | (integrated) | Fee reminders, enrollment updates, payment alerts |
| Email Notifications | (Brevo SMTP) | Welcome emails, payment confirmations, approvals/rejections |
| Contact Form | `/content/contact/` | Public contact form |
| Messaging | `/messages/` | Teacher-student messaging |

---

## 6. User Roles & Permissions

| Role | Flag | Access |
|------|------|--------|
| **Student** | `is_staff=False, is_superuser=False` | Student dashboard, courses, enrollments, meetings, homework, attendance |
| **Teacher** | `is_staff=True, is_superuser=False` | Teacher dashboard, manage students, subscription, payments |
| **Admin** | `is_superuser=True` | Full admin dashboard, all management pages, SaaS panel |

### Role-Based Redirects
- **Login success:**
  - Superuser → `/dashboard/` (admin)
  - Staff (teacher) → `/accounts/teacher/dashboard/`
  - Regular user (student) → `/student/dashboard/`

---

## 7. Email System (Brevo SMTP)

| Event | Recipient | Subject |
|-------|-----------|---------|
| Teacher registers | Teacher | "Welcome to Muslimaa Academy - Teacher Registration" |
| Teacher submits payment | All admins | "New Subscription Payment - [Teacher Name]" |
| Admin approves payment | Teacher | "Subscription Approved - Muslimaa Academy" |
| Admin rejects payment | Teacher | "Payment Update - Muslimaa Academy" |
| Password reset request | User | "Password Reset - Muslimaa Academy" |
| Fee reminder (automated) | Unpaid students | Fee reminder with payment details |

**SMTP Config:** `smtp-relay.brevo.com:587` (TLS)
**From Address:** `Muslimaa Academy <metheiraam@gmail.com>`

---

## 8. Design System

### Colors
| Token | Hex | Usage |
|-------|-----|-------|
| `--brand-700` | `#471820` | Primary brand (deep maroon) |
| `--brand-800` | `#3d1319` | Darker variant |
| `--accent-gold` | `#d4a574` | Accent, highlights |
| `--text-secondary` | `#5a4a55` | Body text |
| `--text-muted` | `#8a7a85` | Secondary text |
| Background | `#faf6f1` | Page background (cream) |

### Typography
| Font | Usage |
|------|-------|
| Playfair Display | Headings, brand name |
| Inter | Body text, UI elements |

### Responsive Breakpoints
| Breakpoint | Target |
|------------|--------|
| `1024px` | Tablet landscape, sidebar collapse |
| `768px` | Tablet portrait, mobile header |
| `480px` | Small phones |

### UI Components
- Cards with `border-radius: 14px`
- Buttons with hover transitions
- Badges for status indicators
- Modal forms for admin CRUD
- Sidebar navigation with hamburger menu on mobile
- Stats cards with icons
- Data tables with horizontal scroll on mobile

---

## 9. API Endpoints (URL Map)

### Root URLs (`config/urls.py`)
| Pattern | Target |
|---------|--------|
| `/` | Homepage |
| `/admin/` | Django Admin |
| `/student/dashboard/` | Student Dashboard |
| `/courses/` | Course app |
| `/workshops/` | Workshop app |
| `/accounts/` | Accounts app |
| `/content/` | Content app |
| `/dashboard/` | Admin Dashboard |
| `/attendance/` | Attendance app |
| `/schedule/` | Classes app |
| `/announcements/` | Announcements app |
| `/homework/` | Homework app |
| `/messages/` | Messaging app |

### Accounts URLs (`accounts/urls.py` — namespace: `accounts`)
| Pattern | View | Name |
|---------|------|------|
| `login/` | CustomLoginView | `login` |
| `logout/` | custom_logout | `logout` |
| `register/` | register | `register` |
| `profile/` | profile | `profile` |
| `profile/edit/` | edit_profile | `edit_profile` |
| `password/change/` | change_password | `change_password` |
| `password/forgot/` | forgot_password | `forgot_password` |
| `reset/<uid>/<token>/` | reset_password | `reset_password` |
| `dashboard/` | student_dashboard | `student_dashboard` |
| `notifications/` | student_notifications | `student_notifications` |
| `teacher/register/` | teacher_register | `teacher_register` |
| `teacher/login/` | teacher_login | `teacher_login` |
| `teacher/logout/` | teacher_logout | `teacher_logout` |
| `teacher/dashboard/` | teacher_dashboard | `teacher_dashboard` |
| `teacher/subscription/` | teacher_subscription | `teacher_subscription` |
| `teacher/payment/` | teacher_payment_submit | `teacher_payment_submit` |
| `teacher/students/` | teacher_students | `teacher_students` |
| `teacher/students/add/` | teacher_add_student | `teacher_add_student` |
| `teacher/students/<id>/edit/` | teacher_edit_student | `teacher_edit_student` |
| `teacher/students/<id>/remove/` | teacher_remove_student | `teacher_remove_student` |
| `portal/login/` | student_portal_login | `student_portal_login` |
| `portal/` | student_portal_dashboard | `student_portal_dashboard` |
| `portal/courses/` | student_portal_courses | `student_portal_courses` |
| `portal/meetings/` | student_portal_meetings | `student_portal_meetings` |
| `portal/homework/` | student_portal_homework | `student_portal_homework` |
| `portal/attendance/` | student_portal_attendance | `student_portal_attendance` |
| `portal/notifications/` | student_portal_notifications | `student_portal_notifications` |
| `portal/logout/` | student_portal_logout | `student_portal_logout` |

### Dashboard URLs (`dashboard/urls.py` — namespace: `dashboard`)
| Pattern | View | Name |
|---------|------|------|
| `` | admin_dashboard | `admin_dashboard` |
| `students/` | admin_students | `admin_students` |
| `teachers/` | admin_teachers | `admin_teachers` |
| `enrollments/` | admin_enrollments | `admin_enrollments` |
| `fees/` | admin_fees | `admin_fees` |
| `courses/` | admin_courses | `admin_courses` |
| `teachers-saas/` | admin_teachers_saas | `admin_teachers_saas` |
| `teachers-saas/<id>/` | admin_teacher_detail | `admin_teacher_detail` |
| `teachers-saas/<id>/change-plan/` | admin_change_plan | `admin_change_plan` |
| `subscription/<id>/approve/` | admin_approve_subscription | `admin_approve_subscription` |
| `subscription/<id>/reject/` | admin_reject_subscription | `admin_reject_subscription` |

---

## 10. Business Model

```
┌─────────────────────────────────────────────────────┐
│                    MUSLIMAA ACADEMY                  │
│              Islamic Education SaaS Platform         │
├─────────────────────────────────────────────────────┤
│                                                     │
│  STUDENTS          TEACHERS           ADMIN         │
│  (Free)            (Paying)           (Superuser)   │
│                                                     │
│  - Browse courses  - Register         - Full access │
│  - Enroll          - Pay subscription - Approve     │
│  - Attend classes  - Manage students  - Manage all  │
│  - Submit HW       - Create meetings  - SaaS panel  │
│  - Track progress  - Track attendance - Fee tracking│
│  - Get notifs      - Get notifs       - Notifications│
│                                                     │
│  ┌─────────────────────────────────────────────┐    │
│  │         SUBSCRIPTION PLANS                  │    │
│  │                                             │    │
│  │  Basic:     1-10 students  → Rs. 5,000/mo  │    │
│  │  Standard: 11-20 students  → Rs. 6,000/mo  │    │
│  │  Premium:  21-50 students  → Rs. 10,000/mo │    │
│  │                                             │    │
│  │  Payment: JazzCash / SadaPay / EasyPaisa    │    │
│  │  Verification: Screenshot → Admin Approves  │    │
│  └─────────────────────────────────────────────┘    │
│                                                     │
│  REVENUE STREAMS:                                   │
│  1. Monthly teacher subscriptions                   │
│  2. Course enrollment fees (per student)            │
│  3. Workshop fees                                   │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## 11. Deployment

| Component | Service |
|-----------|---------|
| **Hosting** | Vercel (Hobby plan) |
| **Database** | Neon.tech PostgreSQL (cloud) |
| **Email** | Brevo SMTP (transactional) |
| **Domain** | muslimaaacademy.com (Namecheap) |
| **DNS** | Namecheap → Vercel |
| **SSL** | Auto (Vercel) |
| **Static Files** | WhiteNoise (served from Django) |
| **Media Files** | Vercel filesystem (limited on Hobby) |

### Deployment Flow
1. Push to `main` branch on GitHub
2. Vercel auto-deploys
3. Migrations run locally against Neon DB (no Vercel terminal)
4. Static files collected and served by WhiteNoise

---

## 12. Key Credentials (DO NOT SHARE)

| Credential | Location |
|------------|----------|
| Admin Login | `iram_mukhtar` / `iraverse+muslimaa123!` |
| DB URL | `.env` → `DATABASE_URL` |
| Brevo SMTP | `.env` → `EMAIL_HOST_USER` / `EMAIL_HOST_PASSWORD` |
| Admin JazzCash | `03294629629` (Title: Iram) |
| Admin SadaPay | `0318-4439418` (Title: Iram) |
| WhatsApp | `03184439418` (Iram Mukhtar) |

---

## 13. Git History (Recent Commits)

| Hash | Message |
|------|---------|
| `0427592` | Add Brevo email notifications, password visibility toggle, loading states, styled 404/500 pages, focus-visible styles, fix invalid HTML in sidebars |
| `02bb1a7` | Major visual fixes: responsive CSS for all pages, fix auth message bugs, add SaaS sidebar link, fix table overflow, improve UX across 25 templates |
| `0056362` | Fix admin 500 (missing SubscriptionPayment import) + teacher 404 (wrong redirect paths) + approve/reject GET crash |
| `dada363` | Add admin notifications for teacher payments & registrations, pending payments badge on sidebar, alert section on dashboard |
| `5f5cc7e` | QA fixes: Enrollment import, URL namespacing, template base classes, query slicing bug |
| `bee560c` | Fix URL namespacing: all teacher URLs now use accounts: prefix correctly |
| `5bdfa39` | Unified registration: Student/Teacher role selector with plan selection for teachers |
| `abd1ad4` | Add complete Student Portal: login, dashboard, courses, meetings, homework, attendance, notifications |
| `33f7bcd` | Add complete SaaS teacher system: registration, login, dashboard, student management, subscription plans, payment tracking, admin panel |
| `ffbbc1e` | Fix student meetings page: change extra_head to student_extra_head to restore sidebar styles |
| `86d564e` | Add server-side search to all admin management pages (students, teachers, courses, enrollments, fees) |

---

## 14. How to Run Locally

```bash
# 1. Clone the repo
git clone https://github.com/metheiram/muslimaa-academy.git
cd muslimaa-academy

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy environment file
copy .env.example .env  # Windows
# cp .env.example .env  # Mac/Linux

# 5. Run migrations
python manage.py migrate

# 6. Create superuser
python manage.py createsuperuser

# 7. Run development server
python manage.py runserver

# 8. Visit http://localhost:8000
```

---

## 15. Template Architecture

```
base/base.html                    ← Public pages (home, courses, etc.)
    ├── base/navbar.html          ← Navigation bar (included)
    ├── base/footer.html          ← Footer (included)
    └── base/messages.html        ← Django messages (included)

base/base_dashboard.html          ← Dashboard shell (used by all dashboards)

base/base_student.html            ← Student dashboard (extends base_dashboard)
    ├── student_dashboard.html
    ├── student_notifications.html
    ├── edit_profile.html
    ├── change_password.html
    └── my_enrollments.html

base/base_teacher.html            ← Teacher dashboard (extends base_dashboard)
    ├── teacher_dashboard.html
    ├── teacher_subscription.html
    ├── teacher_students.html
    ├── teacher_add_student.html
    ├── teacher_edit_student.html
    ├── edit_profile_teacher.html
    └── change_password_teacher.html

base/base_student_portal.html     ← Student portal (extends base_dashboard)
    ├── student_portal_dashboard.html
    ├── student_portal_courses.html
    ├── student_portal_meetings.html
    ├── student_portal_homework.html
    ├── student_portal_attendance.html
    └── student_portal_notifications.html

(Admin pages extend base_dashboard.html directly with their own sidebar)
    ├── dashboard/admin.html
    ├── dashboard/students.html
    ├── dashboard/teachers.html
    ├── dashboard/courses.html
    ├── dashboard/enrollments.html
    ├── dashboard/fees.html
    ├── dashboard/teachers_saas.html
    └── dashboard/teacher_detail.html
```

---

*This document contains all information about the Muslimaa Academy project. Any AI model or human developer reading this should have a complete understanding of the project's architecture, features, models, and business logic.*
