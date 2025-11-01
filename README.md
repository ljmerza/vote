# Poll Application

A Django-based web application for creating and sharing polls with real-time results.

## Features

- ✅ **Create Polls** - Easy poll creation with multiple choice options
- ✅ **Poll Descriptions** - Add optional context and details
- ✅ **Multiple Choice** - Support for single or multiple answer selection
- ✅ **Anonymous/Non-Anonymous Voting** - Toggle voter identification
- ✅ **Public/Private Results** - Control who can view results
- ✅ **Unique Links** - Separate voting and admin links
- ✅ **Duplicate Prevention** - IP-based vote tracking
- ✅ **Real-time Charts** - Visual results with Chart.js
- ✅ **Edit Polls** - Modify polls before any votes are cast
- ✅ **Delete Polls** - Remove polls permanently
- ✅ **Email Sharing** - Share via email with pre-filled message
- ✅ **Copy to Clipboard** - Quick link sharing
- ✅ **Bootstrap 5 UI** - Modern, responsive design

## Installation

1. **Clone or navigate to the project directory:**
   ```bash
   cd /media/cubxi/docker/projects/vote
   ```

2. **Activate virtual environment:**
   ```bash
   source venv/bin/activate
   ```

3. **Run migrations (already done):**
   ```bash
   python manage.py migrate
   ```

4. **Start the server:**
   ```bash
   python manage.py runserver 0.0.0.0:6243
   ```

5. **Access the application:**
   - Local: http://localhost:6243/
   - Network: http://YOUR_IP:6243/

## Usage

### Creating a Poll
1. Visit the home page
2. Enter your poll question
3. (Optional) Add a description for context
4. Add 2 or more choices
5. Configure settings:
   - **Allow multiple choices** - Let voters select multiple options
   - **Anonymous voting** - Hide voter names
   - **Public results** - Allow anyone to view results
6. Click "Create Poll"
7. Share the voting link with others
8. Use the admin link to view detailed results

### Managing Your Poll
- **Edit**: Click "Edit" on admin results page (only before votes)
- **Delete**: Click "Delete" to permanently remove poll
- **Share**: Use email button or copy link to clipboard

### Voting
1. Visit the poll link
2. Select your choice(s)
3. Enter your name (if not anonymous)
4. Submit your vote
5. View results (if public)

### Viewing Results
- **Public Results**: Available to everyone if enabled
- **Admin Results**: Accessible only via the unique admin link
  - Shows voter details (if not anonymous)
  - Displays vote timestamps
  - Full analytics

## Project Structure

```
vote/
├── polls/                  # Main app
│   ├── models.py          # Poll, Choice, Vote models
│   ├── views.py           # All view logic
│   ├── urls.py            # URL routing
│   ├── admin.py           # Django admin config
│   ├── templates/         # HTML templates
│   └── static/            # CSS files
├── voteproject/           # Project settings
│   ├── settings.py        # Django settings
│   └── urls.py            # Root URL config
├── manage.py              # Django management
└── db.sqlite3             # Database

```

## Models

### Poll
- question, slug, admin_token
- is_anonymous, public_results, allow_multiple_choices
- created_at timestamp

### Choice
- poll (ForeignKey)
- choice_text
- votes count

### Vote
- poll, choice (ForeignKeys)
- voter_name (optional)
- ip_address, voted_at

## API Endpoints

- `/` - Create poll page
- `/poll/<slug>/` - Voting page
- `/poll/<slug>/vote/` - Submit vote (POST)
- `/poll/<slug>/results/` - Public results (if enabled)
- `/results/<admin_token>/` - Admin results page (creator only)
- `/edit/<admin_token>/` - Edit poll page (before votes)
- `/delete/<admin_token>/` - Delete poll confirmation

## Technologies

- **Backend**: Django 5.2.7
- **Frontend**: Bootstrap 5, Bootstrap Icons
- **Charts**: Chart.js 4.4.0
- **Database**: SQLite

## Security Notes

⚠️ **Development Mode**
- `DEBUG = True` - Should be False in production
- `ALLOWED_HOSTS = ['*']` - Should be specific domains in production
- Secret key should be in environment variables

## Future Enhancements

- User authentication
- Poll expiration dates
- Edit/delete polls
- Export results (CSV, PDF)
- Rate limiting
- Email notifications
- Social media sharing

## License

MIT License
