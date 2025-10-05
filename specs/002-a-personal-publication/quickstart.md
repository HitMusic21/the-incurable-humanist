# Quickstart Manual Testing Guide

**Feature**: The Incurable Humanist - Personal Publication Platform
**Purpose**: Validate acceptance scenarios through manual testing
**Date**: 2025-10-04

## Prerequisites

- Backend running on `http://localhost:8000`
- Frontend running on `http://localhost:5173`
- Database initialized with migrations
- Test data: Denise's author account created

## Test Scenarios

### Scenario 1: Author - Create and Publish Story

**Given** Denise has written a new story
**When** she accesses her author dashboard
**Then** she can compose, format, categorize, and publish the story

**Steps**:
1. Navigate to `http://localhost:5173/admin/login`
2. Login as Denise (author account)
3. Click "New Story" button
4. Fill in story form:
   - Title: "Finding Home in Grief"
   - Content: Rich text with headings, paragraphs, quotes
   - Themes: Select "grief" and "migration"
   - Optional: Upload cover image
   - Optional: Add content warning
5. Click "Save as Draft"
6. Verify story appears in drafts list
7. Click "Publish" on the draft
8. Verify story moves to published list
9. Open story in new tab (public view)
10. Verify all content displays correctly

**Expected Results**:
- ✅ Story saved as draft with all fields
- ✅ Draft editable before publishing
- ✅ Published story visible on homepage
- ✅ Themes displayed correctly
- ✅ Cover image shown (if uploaded)
- ✅ Content warning displayed (if added)

---

### Scenario 2: Author - Comment Moderation

**Given** Denise has published stories
**When** she reviews reader engagement
**Then** she can see comment activity and moderate comments before they appear publicly

**Steps**:
1. As a reader, submit a comment on a published story
2. Login as Denise to admin dashboard
3. Navigate to "Moderation Queue"
4. Verify pending comment appears with:
   - Reader name and email
   - Comment content
   - Story title
   - Timestamp
5. Click "Approve" on the comment
6. Verify comment moves to approved list
7. Open story in public view
8. Verify approved comment now visible
9. Submit another test comment
10. Reject this comment
11. Verify rejected comment not visible publicly

**Expected Results**:
- ✅ All reader comments pending by default
- ✅ Moderation queue shows all pending comments
- ✅ Approved comments visible on stories
- ✅ Rejected comments hidden from public

---

### Scenario 3: Author - Newsletter Curation

**Given** Denise wants to feature specific stories
**When** she curates content for the newsletter
**Then** she can select stories and schedule newsletter delivery to subscribers

**Steps**:
1. Login to admin dashboard
2. Navigate to "Newsletter" section
3. Click "Create Newsletter"
4. Select 3-5 published stories
5. Preview newsletter template
6. Choose delivery schedule:
   - Daily subscribers: next morning
   - Weekly subscribers: next Monday
   - Monthly subscribers: next month
7. Click "Schedule Send"
8. Verify scheduled newsletter in queue
9. (Optionally) trigger manual send for testing

**Expected Results**:
- ✅ Can select multiple stories
- ✅ Preview shows story excerpts
- ✅ Different frequencies handled correctly
- ✅ Emails sent to appropriate subscriber groups
- ✅ Unsubscribe link present in emails

---

### Scenario 4: Author - Edit Published Story

**Given** Denise published a story with an error
**When** she edits the published story
**Then** changes are saved and reflected immediately without affecting reader bookmarks or comments

**Steps**:
1. Navigate to published stories list
2. Click "Edit" on a published story
3. Make changes:
   - Update title: Add "[Updated]" prefix
   - Fix typo in content
   - Add new theme
4. Click "Save Changes"
5. Verify changes reflected in public view
6. As a reader with bookmark on this story:
   - Navigate to bookmarks
   - Verify story still bookmarked
   - Updated title shown
7. Check comments on story still present

**Expected Results**:
- ✅ Published story editable
- ✅ Changes reflect immediately
- ✅ Bookmarks preserved
- ✅ Comments preserved
- ✅ Updated_at timestamp updated

---

### Scenario 5: Reader - Browse Stories

**Given** a visitor discovers the platform
**When** they browse the homepage
**Then** they see published stories organized by themes (grief, migration, art) without requiring authentication

**Steps**:
1. Open `http://localhost:5173` (not logged in)
2. Verify homepage displays:
   - List of published stories
   - Story cards with: title, excerpt, cover image, themes, read time
   - Sorted by newest first
3. Click "grief" theme filter
4. Verify only grief-tagged stories shown
5. Click "migration" theme filter
6. Verify migration stories (including multi-theme stories)
7. Use search bar: "home"
8. Verify search results match title/content
9. Click on a story card
10. Verify full story loads without login prompt

**Expected Results**:
- ✅ No authentication required for browsing
- ✅ Stories organized by theme
- ✅ Search works across title, content, themes
- ✅ Story details accessible without login
- ✅ Multi-theme stories appear in all relevant filters

---

### Scenario 6: Reader - Engage with Content

**Given** a reader finds a meaningful story
**When** they want to engage
**Then** they can create an account, bookmark the story, and submit a comment for moderation

**Steps**:
1. Find a story (as visitor)
2. Try to bookmark → redirected to login/register
3. Click "Register" and create account:
   - Email: test@example.com
   - Password: SecurePass123
   - Name: Test Reader
4. After registration, automatically logged in
5. Bookmark the story (heart icon)
6. Verify bookmark added
7. Navigate to "My Bookmarks"
8. Verify story appears in list
9. Return to story
10. Submit a comment: "Beautiful story about grief and healing"
11. Verify "awaiting moderation" message shown
12. Comment not visible in public comment list yet

**Expected Results**:
- ✅ Registration flow smooth
- ✅ Bookmark requires authentication
- ✅ Bookmarks accessible in user profile
- ✅ Comment submission successful
- ✅ Pending status shown to comment author
- ✅ Comment not public until moderated

---

### Scenario 7: Reader - Newsletter Subscription

**Given** a reader wants regular updates
**When** they subscribe to the newsletter
**Then** they receive curated story collections and new content notifications based on their indicated interests

**Steps**:
1. Login as reader
2. Navigate to "Newsletter" in profile menu
3. Click "Subscribe"
4. Select frequency: "Weekly"
5. Select preferred themes:
   - ✅ grief
   - ✅ migration
   - ⬜ art
6. Click "Subscribe"
7. Verify subscription confirmation
8. Check email inbox for welcome email
9. Simulate newsletter send (trigger manually or wait for schedule)
10. Verify newsletter received with:
    - Curated stories matching preferences
    - Unsubscribe link at bottom
11. Click "Manage Subscription"
12. Change frequency to "Monthly"
13. Verify update confirmed

**Expected Results**:
- ✅ Subscription flow clear and simple
- ✅ Frequency options: daily, weekly, monthly
- ✅ Theme preferences honored
- ✅ Welcome email sent
- ✅ Newsletters contain relevant stories
- ✅ Unsubscribe link works
- ✅ Subscription editable

---

### Scenario 8: Reader - Reading Progress

**Given** a subscribed reader receives a newsletter
**When** they click a story link
**Then** they land directly on the story with reading progress tracked (if authenticated)

**Steps**:
1. As authenticated reader, open a long story
2. Scroll 50% down the page
3. Navigate away (close tab or go to homepage)
4. Return to story
5. Verify scroll position restored to 50%
6. Continue reading to 80%
7. Navigate to profile → "Continue Reading"
8. Verify story listed with 80% progress
9. Click story from "Continue Reading"
10. Verify lands at 80% position
11. Complete story (100%)
12. Verify marked as "completed" in profile

**Expected Results**:
- ✅ Progress tracked on scroll
- ✅ Position restored on return
- ✅ "Continue Reading" shows in-progress stories
- ✅ Completed stories marked separately
- ✅ Progress persists across sessions

---

## Edge Cases to Test

### Edge Case 1: Story Deletion (Archiving)
**Scenario**: Denise deletes a published story that readers have bookmarked and commented on

**Steps**:
1. As Denise, navigate to published story with bookmarks/comments
2. Click "Archive" (not "Delete")
3. Confirm archiving
4. Verify story removed from public homepage
5. As reader with bookmark:
   - Navigate to bookmarks
   - Try to open archived story
   - Verify appropriate message: "Story no longer available"
6. As Denise in admin:
   - Navigate to archived stories
   - Verify story present with all data
   - Comments and bookmarks preserved
   - Option to "Republish" available

**Expected**: Archive hides from public but preserves all data

---

### Edge Case 2: Unauthorized Story Submission
**Scenario**: Reader attempts to submit a story (should not have this capability)

**Steps**:
1. Login as reader (not author)
2. Try to access `/admin/stories/new` directly
3. Verify 403 Forbidden or redirect to homepage
4. Look for "New Story" button in UI
5. Verify button not present for readers

**Expected**: No story creation access for readers

---

### Edge Case 3: Comment Threading (Author Replies)
**Scenario**: Denise moderates comments and can reply to them

**Steps**:
1. Reader submits comment on story
2. Denise approves comment
3. Denise clicks "Reply" on approved comment
4. Writes reply and submits
5. Verify reply appears nested under original comment
6. Reader returns to story
7. Verify can see both original comment and Denise's reply
8. Reader can reply to Denise's reply (threaded conversation)

**Expected**: Threaded comment structure works

---

### Edge Case 4: Newsletter Delivery Failures
**Scenario**: Handle bounced emails gracefully

**Steps**:
1. Subscribe with invalid email: "fake@invaliddomain.test"
2. Trigger newsletter send
3. Monitor email service logs
4. Verify bounce handling:
   - Subscription marked inactive
   - User notified (if possible)
   - No crash or error on frontend

**Expected**: Graceful handling of email failures

---

### Edge Case 5: Multi-Theme Stories
**Scenario**: Story tagged with all three themes appears in all filters

**Steps**:
1. As Denise, create story tagged: grief + migration + art
2. Publish story
3. As visitor, filter by "grief"
4. Verify story appears
5. Filter by "migration"
6. Verify story appears
7. Filter by "art"
8. Verify story appears
9. Search for term in story
10. Verify appears in search results

**Expected**: Multi-theme stories accessible from all relevant paths

---

### Edge Case 6: Author Dashboard Access Control
**Scenario**: Prevent unauthorized access to admin dashboard

**Steps**:
1. As reader, navigate to `/admin`
2. Verify redirect to login or 403
3. Try accessing `/admin/stories`
4. Verify denied
5. Logout completely
6. Try accessing admin routes
7. Verify all denied without authentication
8. Login as Denise
9. Verify full admin access granted

**Expected**: Admin routes protected, only accessible to author

---

## Performance Testing

### Test: Page Load Time
**Target**: <3 seconds on standard broadband

**Steps**:
1. Clear browser cache
2. Open homepage with network throttling (Fast 3G)
3. Measure load time with DevTools
4. Verify <3 seconds
5. Test story detail page
6. Verify <3 seconds

---

### Test: Concurrent Users
**Target**: Support 500 concurrent readers

**Steps**:
1. Use load testing tool (k6, Locust, or Artillery)
2. Simulate 500 concurrent readers browsing stories
3. Monitor API response times
4. Verify <200ms p95 for API endpoints
5. Check database connection pool
6. Verify no connection errors

---

## Validation Checklist

After completing all scenarios:

- [ ] All 8 acceptance scenarios pass
- [ ] All 6 edge cases handled correctly
- [ ] Performance targets met (<3s load, 500 concurrent)
- [ ] No broken links or 404 errors
- [ ] Responsive on mobile devices
- [ ] HTTPS working in production
- [ ] All forms validated properly
- [ ] Error messages user-friendly
- [ ] Email deliverability verified
- [ ] Database migrations run successfully

---

## Next Steps

After quickstart validation passes:
1. Run automated test suite (pytest + Vitest)
2. Security audit (OWASP checklist)
3. Accessibility audit (WCAG 2.1 AA)
4. Deploy to staging environment
5. UAT with Denise (real author testing)
6. Production deployment
