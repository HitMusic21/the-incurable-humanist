# Deployment Guide - The Incurable Humanist

## Pre-Deployment Checklist

Before deploying to production, ensure you've completed these steps:

### ✅ Required Configuration

- [ ] **Formspree Setup**: Replace `YOUR_FORMSPREE_ID` in `src/components/ContactForm.tsx` with your actual Formspree form ID
- [ ] **Domain Update**: Update all instances of `theincurablehumanist.com` in:
  - `index.html` (meta tags, canonical URL, OG tags)
  - `public/sitemap.xml` (all URL entries)
  - `public/robots.txt` (sitemap URL)
- [ ] **Test Build**: Run `npm run build` locally to ensure no errors
- [ ] **Content Review**: Verify all text in `src/config/site.ts` is correct

### ✅ Optional Enhancements

- [ ] **Custom OG Image**: Replace `public/og-image.svg` with a custom 1200x630px image
- [ ] **Analytics**: Add Google Analytics or Plausible tracking
- [ ] **Founder Photo**: Replace portrait placeholder in About page
- [ ] **Environment Variables**: Set up `.env` file for sensitive data

---

## Deployment Options

### Option 1: Vercel (Recommended - Easiest)

**Why Vercel:**
- Zero-config deployment for Vite apps
- Automatic HTTPS
- Global CDN
- Preview deployments for every commit
- Free tier available

**Steps:**

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Ready for deployment"
   git push origin main
   ```

2. **Deploy to Vercel**
   - Go to [vercel.com](https://vercel.com)
   - Click "Add New Project"
   - Import your GitHub repository
   - Vercel auto-detects Vite settings:
     - Build Command: `npm run build`
     - Output Directory: `dist`
     - Install Command: `npm install`
   - Click "Deploy"

3. **Add Environment Variables** (in Vercel dashboard)
   - Go to Project Settings → Environment Variables
   - Add: `VITE_FORMSPREE_ID` = `your_formspree_id`
   - Redeploy for changes to take effect

4. **Custom Domain** (optional)
   - Go to Project Settings → Domains
   - Add your custom domain
   - Update DNS records as instructed
   - Vercel automatically provisions SSL

**Vercel CLI (Alternative):**
```bash
npm install -g vercel
vercel login
vercel --prod
```

---

### Option 2: Netlify

**Why Netlify:**
- Similar to Vercel
- Great form handling (alternative to Formspree)
- Generous free tier

**Steps:**

1. **Push to GitHub** (same as above)

2. **Deploy to Netlify**
   - Go to [netlify.com](https://netlify.com)
   - Click "Add new site" → "Import an existing project"
   - Connect to GitHub and select repository
   - Build settings:
     - Build command: `npm run build`
     - Publish directory: `dist`
   - Click "Deploy"

3. **Environment Variables**
   - Go to Site Settings → Build & deploy → Environment
   - Add: `VITE_FORMSPREE_ID`

4. **Custom Domain**
   - Go to Domain Settings
   - Add custom domain
   - Configure DNS

**Netlify CLI (Alternative):**
```bash
npm install -g netlify-cli
netlify login
netlify deploy --prod
```

---

### Option 3: Cloudflare Pages

**Why Cloudflare:**
- Fastest global CDN
- Built-in analytics
- Unlimited bandwidth on free tier

**Steps:**

1. **Push to GitHub**

2. **Deploy to Cloudflare Pages**
   - Go to [pages.cloudflare.com](https://pages.cloudflare.com)
   - Click "Create a project"
   - Connect GitHub repository
   - Build settings:
     - Framework preset: Vite
     - Build command: `npm run build`
     - Build output directory: `dist`
   - Environment variables: Add `VITE_FORMSPREE_ID`
   - Deploy

3. **Custom Domain**
   - Go to Custom domains
   - Add your domain
   - Update nameservers if using Cloudflare DNS

---

### Option 4: GitHub Pages

**Limitations:**
- Requires repository to be public
- Custom domain setup is more manual
- No built-in environment variables

**Steps:**

1. **Install gh-pages**
   ```bash
   npm install --save-dev gh-pages
   ```

2. **Update package.json**
   Add homepage and deploy scripts:
   ```json
   {
     "homepage": "https://yourusername.github.io/repository-name",
     "scripts": {
       "predeploy": "npm run build",
       "deploy": "gh-pages -d dist"
     }
   }
   ```

3. **Update vite.config.ts**
   ```typescript
   export default defineConfig({
     base: '/repository-name/', // Your repo name
     plugins: [react()]
   })
   ```

4. **Deploy**
   ```bash
   npm run deploy
   ```

5. **Enable GitHub Pages**
   - Go to repository Settings → Pages
   - Source: Deploy from branch `gh-pages`

---

## Post-Deployment Tasks

### 1. Verify Deployment

**Test all pages:**
- [ ] Home page loads correctly
- [ ] About page displays properly
- [ ] Press page shows all articles
- [ ] Contact form submits successfully
- [ ] Newsletter page opens (redirects to Substack)
- [ ] 404 page appears for invalid URLs

**Test responsive design:**
- [ ] Mobile (375px width)
- [ ] Tablet (768px width)
- [ ] Desktop (1440px width)

**Test social sharing:**
- [ ] Share on Twitter/X - verify OG image appears
- [ ] Share on Facebook - verify title and description
- [ ] Share on LinkedIn - check preview card

### 2. SEO Setup

**Google Search Console:**
1. Go to [search.google.com/search-console](https://search.google.com/search-console)
2. Add your property (domain or URL prefix)
3. Verify ownership (DNS or HTML tag)
4. Submit sitemap: `https://yourdomain.com/sitemap.xml`

**Monitor indexing:**
- Check coverage report after a few days
- Fix any errors reported
- Request indexing for important pages

### 3. Analytics (Optional)

**Google Analytics:**
1. Create GA4 property at [analytics.google.com](https://analytics.google.com)
2. Get measurement ID (G-XXXXXXXXXX)
3. Add to `index.html` before `</head>`:
   ```html
   <script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
   <script>
     window.dataLayer = window.dataLayer || [];
     function gtag(){dataLayer.push(arguments);}
     gtag('js', new Date());
     gtag('config', 'G-XXXXXXXXXX');
   </script>
   ```

**Plausible (Privacy-friendly alternative):**
1. Sign up at [plausible.io](https://plausible.io)
2. Add domain
3. Add script to `index.html`:
   ```html
   <script defer data-domain="yourdomain.com" src="https://plausible.io/js/script.js"></script>
   ```

### 4. Performance Optimization

**Test performance:**
- Run [PageSpeed Insights](https://pagespeed.web.dev/)
- Aim for 90+ score on all metrics
- Fix any critical issues

**Optimize images:**
- Compress OG image if large
- Consider converting SVG favicon to PNG for better browser support
- Add actual founder photo in WebP format

### 5. Security Headers (Optional)

**Vercel/Netlify:** Add `vercel.json` or `netlify.toml`:
```json
{
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        {
          "key": "X-Content-Type-Options",
          "value": "nosniff"
        },
        {
          "key": "X-Frame-Options",
          "value": "DENY"
        },
        {
          "key": "X-XSS-Protection",
          "value": "1; mode=block"
        }
      ]
    }
  ]
}
```

---

## Continuous Deployment

### Automatic Deployments

All recommended platforms (Vercel, Netlify, Cloudflare) automatically deploy when you push to your main branch:

```bash
# Make changes
git add .
git commit -m "Update content"
git push origin main
# Deployment happens automatically!
```

### Preview Deployments

- Every pull request gets its own preview URL
- Test changes before merging to main
- Share with stakeholders for review

---

## Troubleshooting

### Build Failures

**Error: "Cannot find module"**
- Run `npm install` locally
- Check package.json for correct dependencies
- Ensure Node.js version matches (18+)

**Error: "TypeScript errors"**
- Run `npm run build` locally to see errors
- Fix TypeScript issues before pushing

### Form Not Working

**Formspree issues:**
- Verify form ID is correct
- Check Formspree dashboard for submissions
- Ensure email is verified in Formspree

**CORS errors:**
- Formspree handles CORS automatically
- If using custom backend, add CORS headers

### SEO Issues

**Pages not indexing:**
- Verify robots.txt allows crawling
- Submit sitemap in Search Console
- Check for `noindex` meta tags (should not exist)

**OG image not showing:**
- Verify image URL is absolute (not relative)
- Use PNG instead of SVG for better compatibility
- Check image dimensions (1200x630px recommended)

---

## Support & Maintenance

### Regular Updates

**Monthly:**
- Update sitemap lastmod dates
- Review and update press articles
- Check for broken links

**Quarterly:**
- Update dependencies: `npm update`
- Review analytics and adjust strategy
- Update About page content if needed

**Annually:**
- Renew custom domain
- Review and update meta descriptions
- Audit accessibility compliance

---

## Additional Resources

- [Vite Documentation](https://vitejs.dev/guide/)
- [React Router Documentation](https://reactrouter.com/)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [Formspree Documentation](https://help.formspree.io/)
- [Web Vitals](https://web.dev/vitals/)

---

**Questions or Issues?**

Create an issue in the GitHub repository with:
- Detailed description of the problem
- Steps to reproduce
- Browser and device information
- Screenshots if applicable

Good luck with your deployment! 🚀
