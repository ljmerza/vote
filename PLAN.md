# Poll Application Plan

## Overview
A Django web application where users can create polls, share voting links, and view results.

## Features

### 1. Create Poll
- User creates a poll with:
  - Poll question/title
  - Multiple choice answer options (minimum 2)
  - Poll settings:
    - Anonymous voting (yes/no)
    - Show results publicly (yes/no) or only to creator
  - Optional: Poll creator name/identifier
- Generate unique shareable link for voting
- Generate admin link for viewing results

### 2. Vote on Poll (Multiple Choice)
- Anyone with the voting link can:
  - View the poll question
  - See all answer options
  - Select one or multiple choices (configurable)
  - Submit vote(s)
  - Prevent multiple votes (IP-based or cookie-based)
  - View results after voting (if poll is set to public results)

### 3. View Results
- **Poll Creator (Admin Link)**:
  - Always has access via unique admin link
  - Sees all vote data including voter information (if not anonymous)
  
- **Public Results** (if enabled):
  - Voters can see results after voting or via results link
  - Shows aggregated data only
  
- **Anonymous vs. Non-Anonymous**:
  - Anonymous: Only vote counts shown, no voter identification
  - Non-Anonymous: Can show who voted for what (optional display)
  
- **Display Elements**:
  - Poll question
  - All answer options with vote counts
  - Percentage breakdown
  - Total votes
  - Visual charts/graphs
  - Voter names/identifiers (if not anonymous)

## Technical Architecture

### Models
1. **Poll**
   - id (auto)
   - question (CharField)
   - created_at (DateTimeField)
   - admin_token (UUIDField) - for creator access
   - slug (SlugField) - for public voting link
   - is_anonymous (BooleanField, default=True) - hide voter identities
   - public_results (BooleanField, default=False) - allow anyone to view results
   - allow_multiple_choices (BooleanField, default=False) - multiple choice voting

2. **Choice**
   - id (auto)
   - poll (ForeignKey to Poll)
   - choice_text (CharField)
   - votes (IntegerField, default=0)

3. **Vote** (for tracking and non-anonymous polls)
   - poll (ForeignKey)
   - choice (ForeignKey)
   - voter_name (CharField, blank=True, null=True) - for non-anonymous polls
   - ip_address (GenericIPAddressField)
   - voted_at (DateTimeField)

### Views
1. **Create Poll** (`/create/`)
   - Form to create poll with dynamic choice fields
   - Poll settings: anonymous, public results, multiple choice
   - Returns admin link and voting link

2. **Vote Page** (`/poll/<slug>/`)
   - Display poll and choices
   - Show radio buttons (single choice) or checkboxes (multiple choice)
   - Optional: voter name field (if not anonymous)
   - Handle vote submission
   - Show thank you message after voting
   - Redirect to results if public_results enabled

3. **Results Page - Admin** (`/results/<admin_token>/`)
   - Full access to all data
   - Display vote counts and percentages
   - Show voter names if not anonymous
   - Show charts/visualizations

4. **Results Page - Public** (`/poll/<slug>/results/`)
   - Only accessible if public_results enabled
   - Show aggregated vote data only
   - No voter identification even if not anonymous
   - Show charts/visualizations

### URLs Structure
- `/` - Home/Create poll page
- `/create/` - POST endpoint for creating poll
- `/poll/<slug>/` - Public voting page
- `/poll/<slug>/vote/` - POST endpoint for submitting vote
- `/poll/<slug>/results/` - Public results page (if enabled)
- `/admin/<admin_token>/` - Admin results page (creator only)

## UI Design (Bootstrap 5)

### Pages
1. **Home/Create Poll Page**
   - Clean form with Bootstrap styling
   - Question input field
   - Dynamic "Add Choice" button (JavaScript)
   - Minimum 2 choices required
   - Poll settings checkboxes:
     - Allow multiple choice selection
     - Anonymous voting
     - Public results viewing
   - Submit button

2. **Poll Created Success Page**
   - Display both links prominently:
     - Voting link (public)
     - Admin link (private - for creator)
   - Copy-to-clipboard buttons for links
   - QR code (optional)

3. **Voting Page**
   - Poll question as heading
   - Radio buttons (single) or checkboxes (multiple choice)
   - Optional: Voter name input (if not anonymous)
   - Submit vote button
   - Link to public results (if enabled)
   - Clean, mobile-responsive design

4. **Results Page - Public** (if enabled)
   - Poll question
   - Progress bars showing vote percentages
   - Vote counts (aggregated only)
   - Chart visualization (Chart.js or similar)
   - No voter identification

5. **Results Page - Admin** (creator only)
   - Poll question
   - Progress bars showing vote percentages
   - Vote counts
   - Detailed voter list (if not anonymous)
   - Chart visualization (Chart.js or similar)
   - Total votes and timestamp

## Implementation Steps

1. **Setup Models**
   - Create Poll, Choice models
   - Run migrations

2. **Create Poll Form & View**
   - Build form with JavaScript for dynamic choices
   - Handle poll creation
   - Generate unique tokens

3. **Voting View**
   - Display poll choices
   - Handle vote submission
   - Prevent duplicate votes

4. **Results View**
   - Calculate percentages
   - Display with Bootstrap components
   - Add visualization

5. **Bootstrap Integration**
   - Add Bootstrap 5 CDN
   - Style all templates
   - Add responsive design

6. **JavaScript Enhancements**
   - Dynamic choice fields on create form
   - Copy-to-clipboard functionality
   - Form validation

## Security Considerations
- Use Django CSRF protection
- Validate all inputs
- Rate limiting on vote submission
- Secure admin token generation (UUID4)
- Consider vote tampering prevention

## Future Enhancements
- User authentication
- Poll expiration dates
- Edit/delete polls
- Multiple choice polls
- Anonymous vs. named voting
- Export results (CSV, PDF)
