# The Incurable Humanist - Setup Guide

## Prerequisites

- Node.js 18+ and npm
- Git

## Local Development Setup

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Configure Contact Form (Required)

The contact form uses [Formspree](https://formspree.io/) to handle submissions.

**Steps:**

1. Go to https://formspree.io/ and create a free account
2. Create a new form and copy your form ID (looks like `xyzabc123`)
3. Open `src/components/ContactForm.tsx`
4. Replace `YOUR_FORMSPREE_ID` on line 6 with your actual form ID:

```typescript
const [state, handleSubmit] = useForm("xyzabc123"); // Your actual ID here
```

**Optional:** You can also use environment variables:

1. Create a `.env` file in the frontend directory:
```bash
cp .env.example .env
```

2. Add your Formspree ID:
```
VITE_FORMSPREE_ID=xyzabc123
```

3. Update ContactForm.tsx to use the environment variable:
```typescript
const [state, handleSubmit] = useForm(import.meta.env.VITE_FORMSPREE_ID);
```

### 3. Start Development Server

```bash
npm run dev
```

The site will be available at `http://localhost:5173`

### 4. Build for Production

```bash
npm run build
```

The built files will be in the `dist` directory.

## Configuration Files

### Site Configuration

Edit `src/config/site.ts` to update:
- Site name and branding
- Navigation links
- Social media URLs
- Contact email
- Press articles

### SEO Meta Tags

Edit `index.html` to customize:
- Page title and description
- Social media sharing images
- Theme colors
- Canonical URL (update to your actual domain)

## Deployment

### Deploy to Vercel (Recommended)

1. Push your code to GitHub
2. Go to [vercel.com](https://vercel.com)
3. Import your repository
4. Add environment variables in Vercel dashboard:
   - `VITE_FORMSPREE_ID` (your Formspree form ID)
5. Deploy!

Vercel will automatically:
- Build your site on every commit
- Provide HTTPS
- Configure custom domains
- Enable automatic preview deployments

### Deploy to Netlify

1. Push your code to GitHub
2. Go to [netlify.com](https://netlify.com)
3. Import your repository
4. Build settings:
   - Build command: `npm run build`
   - Publish directory: `dist`
5. Add environment variables:
   - `VITE_FORMSPREE_ID`
6. Deploy!

### Other Platforms

The site is a standard Vite + React app and can be deployed to:
- GitHub Pages
- Cloudflare Pages
- AWS Amplify
- Any static hosting service

## Important Notes

### Before Deploying

1. ✅ **Update Formspree ID** in ContactForm.tsx
2. ✅ **Update domain** in `index.html` meta tags (replace `theincurablehumanist.com` with your actual domain)
3. ✅ **Update sitemap.xml** URLs with your actual domain
4. ✅ **Test contact form** to ensure emails are being sent
5. ✅ **Review all content** in `src/config/site.ts`

### After Deploying

1. Test all pages on mobile and desktop
2. Verify contact form works
3. Test social media sharing (Twitter, Facebook, LinkedIn)
4. Submit sitemap to Google Search Console
5. Set up analytics (optional)

## Troubleshooting

### Contact form not working
- Verify Formspree ID is correct
- Check browser console for errors
- Ensure form inputs have proper `name` attributes

### Build errors
- Clear node_modules and reinstall: `rm -rf node_modules && npm install`
- Check Node.js version: `node --version` (should be 18+)
- Run `npm run build` and check for TypeScript errors

### Styling issues
- Clear browser cache
- Check Tailwind configuration in `tailwind.config.ts`
- Verify all imports in component files

## Support

For issues or questions:
- Check existing GitHub issues
- Create a new issue with detailed description
- Include browser console errors if applicable

## License

© 2025 Denise Rodriguez Dao. All rights reserved.
