# PostHog Analytics Setup

This document outlines how to properly configure PostHog analytics for deployment.

## Environment Variables

### Required Variables

Create a `.env` file in the root of your project with the following variables:

```bash
# PostHog Analytics Configuration
VITE_PUBLIC_POSTHOG_KEY=your_posthog_project_api_key_here
VITE_PUBLIC_POSTHOG_HOST=https://us.i.posthog.com
```

### Getting Your PostHog API Key

1. Log in to your PostHog dashboard
2. Go to Project Settings
3. Copy your Project API Key (starts with `phc_`)
4. Replace `your_posthog_project_api_key_here` with your actual key

### For Different Environments

#### Production Deployment
Add these environment variables to your hosting provider:
- **Vercel**: Add to Environment Variables section in project settings
- **Netlify**: Add to Site settings > Environment variables
- **Railway/Heroku**: Add through their CLI or dashboard

#### Development
Copy `.env.example` to `.env` and update with your actual PostHog key:
```bash
cp .env.example .env
```

### Security Notes

- Never commit your actual `.env` file to version control
- The `.env.example` file shows the structure but contains example/placeholder values
- Always use `VITE_PUBLIC_` prefix for client-side environment variables in Vite

## Implemented Tracking Events

The following events are automatically tracked:

### Page Views
- Automatically tracked when users navigate between pages
- Properties: `page_path`, `page_name`

### User Identification
- When users submit the contact form (identified by email)
- Properties: `name`, `email`, `contact_method`, `timestamp`

### Form Interactions
- Contact form submissions (successful and failed)
- Properties: `name`, `email`, `subject`, `has_subject`, `errors`

### Social Media Clicks
- Clicks on social media icons
- Properties: `platform`, `url`

### Press Article Clicks
- Clicks on press articles
- Properties: `outlet`, `title`, `url`

### Newsletter Signups
- Newsletter subscription link clicks
- Properties: `source` (e.g., 'footer_link')

## Usage in Components

```tsx
import { useAnalytics } from '@/hooks/useAnalytics';

function YourComponent() {
  const { track, identify, events } = useAnalytics();

  // Track custom events
  const handleCustomEvent = () => {
    track('custom_event', {
      property1: 'value1',
      property2: 'value2'
    });
  };

  // Identify users
  const handleUserSignIn = (email: string) => {
    identify(email, {
      name: 'User Name',
      signup_date: new Date().toISOString()
    });
  };

  return (
    // Your component JSX
  );
}
```

## Testing

### Development Mode
PostHog debug mode is automatically enabled in development. Check your browser's developer console to see PostHog events being tracked.

### Production Verification
After deployment, verify tracking is working by:
1. Visiting your live site
2. Performing tracked actions (form submission, social clicks, etc.)
3. Checking your PostHog dashboard for the events

## Troubleshooting

### Events Not Appearing
1. Verify your API key is correct
2. Check that environment variables are properly set in your hosting provider
3. Ensure the PostHog host URL is correct
4. Check browser developer console for any PostHog errors

### Debug Mode
Set `debug: true` in PostHog options (already configured for development mode) to see detailed logging in the console.