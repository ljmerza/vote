# Quick Start Guide

## Running the Application

1. **Navigate to project directory:**
   ```bash
   cd /media/cubxi/docker/projects/vote
   ```

2. **Activate virtual environment:**
   ```bash
   source venv/bin/activate
   ```

3. **Start the server:**
   ```bash
   python manage.py runserver 0.0.0.0:6243
   ```

4. **Access the app:**
   - From this machine: http://localhost:6243/
   - From other machines: http://YOUR_IP_ADDRESS:6243/

## Quick Test

1. Open http://localhost:6243/
2. Create a test poll:
   - Question: "What's your favorite color?"
   - Choices: Red, Blue, Green
   - Check "Public results"
3. Copy the voting link
4. Vote on the poll
5. View the results!

## Creating Your First Poll

1. **Enter Poll Question**: Type your question in the main field
2. **Add Choices**: Click "Add Choice" to add more options (minimum 2)
3. **Configure Settings**:
   - ✅ Allow multiple choice selection - Users can pick more than one option
   - ✅ Anonymous voting - Hide who voted for what
   - ✅ Public results - Anyone can view results
4. **Create Poll**: Click the button to generate links
5. **Share**: Copy and share the voting link
6. **Track**: Use admin link to see detailed results

## Admin Panel

To access Django admin:

1. Create superuser:
   ```bash
   python manage.py createsuperuser
   ```

2. Access at: http://localhost:6243/admin/

3. Manage polls, choices, and votes directly

## Troubleshooting

**Server won't start:**
- Check if port 6243 is already in use
- Make sure virtual environment is activated

**Can't access from other machines:**
- Check firewall settings
- Ensure server is running on 0.0.0.0:6243
- Verify ALLOWED_HOSTS in settings.py includes '*'

**Static files not loading:**
```bash
python manage.py collectstatic
```

## Common Commands

```bash
# Run server
python manage.py runserver 0.0.0.0:6243

# Make migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Open Django shell
python manage.py shell
```

## Tips

- **Bookmark your admin link** - You'll need it to view results
- **Test with multiple devices** - Try voting from your phone
- **Share via QR code** - Use a QR generator for easy mobile sharing
- **Export results** - Copy from admin panel or take screenshots

## Next Steps

- Customize the styling in `polls/static/polls/style.css`
- Add more features in `polls/views.py`
- Modify templates in `polls/templates/polls/`
- Check `PLAN.md` for future enhancement ideas
