# Changelog

## Version 2.0 - New Features (2025-11-01)

### Added
- **Poll Descriptions** - Add optional text descriptions to provide context for your polls
- **Edit Polls** - Modify poll question, description, choices, and settings (only before votes are cast)
- **Delete Polls** - Permanently delete polls with confirmation dialog
- **Email Sharing** - Share polls via email with pre-filled subject and body
- **Enhanced Copy** - Improved clipboard functionality with visual feedback and fallbacks

### Changed
- Admin results URL changed from `/admin/<token>/` to `/results/<token>/` to avoid Django admin conflict
- Updated Poll model with `description` and `updated_at` fields
- Improved admin results page with Edit/Delete buttons
- Enhanced email sharing on all relevant pages

### Database Migrations
- Added `description` field to Poll model (TextField, optional)
- Added `updated_at` field to Poll model (auto-updated timestamp)

## Version 1.0 - Initial Release

### Core Features
- Create polls with multiple choice options
- Single or multiple answer selection
- Anonymous/non-anonymous voting
- Public/private results
- Unique voting and admin links
- IP-based duplicate vote prevention
- Real-time charts with Chart.js
- Responsive Bootstrap 5 UI
- Copy to clipboard functionality

### Models
- Poll model with settings
- Choice model with vote tracking
- Vote model for detailed tracking
