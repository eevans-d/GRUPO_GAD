# ✅ User Acceptance Testing (UAT) Plan - v1.3.0
**Date**: October 21, 2025  
**Release**: v1.3.0 (Sprint 2 - 100% Complete)  
**Duration**: 45 minutes  
**Participants**: QA Team, Product Owner, 2-3 Testers

---

## 🎯 UAT Objectives

1. ✅ Verify all features work as specified
2. ✅ Validate UI/UX meets user expectations
3. ✅ Confirm performance is acceptable
4. ✅ Identify any critical issues before production
5. ✅ Obtain stakeholder sign-off

---

## 📋 Test Environment Setup

### Pre-requisites
```bash
✅ v1.3.0 deployed to staging environment
✅ Test database with sample data
✅ Redis cache enabled
✅ All services running (API, DB, WebSocket)
✅ Admin user credentials ready
✅ Multiple browsers ready for testing (Chrome, Firefox, Safari)
✅ Mobile device for responsive testing
```

### Test Data
```
Users in system: 5-10 test usuarios
Tasks: 10-15 test tareas
Telegram bot: Connected and ready
Time: ~45 minutes
```

---

## 🧪 Test Cases

### Domain 1: User Management (ME4)

#### TC-001: User List Display
**Pre-condition**: Logged in as admin user  
**Status**: NOT STARTED

| Step | Action | Expected Result | Result | Notes |
|------|--------|-----------------|--------|-------|
| 1 | Navigate to Admin Dashboard | Dashboard loads | ⏳ | |
| 2 | Click "Users" tab | Users list displays | ⏳ | |
| 3 | Verify table columns | See: ID, Telegram ID, Nombre, Nivel | ⏳ | |
| 4 | Verify pagination controls | See: Previous/Next buttons, page info | ⏳ | |
| 5 | Verify search box | Can filter by name/telegram_id | ⏳ | |
| 6 | Check load time | Page loads in <2 seconds | ⏳ | |

**Pass Criteria**: ✅ All rows completed successfully

---

#### TC-002: Create New User
**Pre-condition**: On Users management page  
**Status**: NOT STARTED

| Step | Action | Expected Result | Result | Notes |
|------|--------|-----------------|--------|-------|
| 1 | Click "Create User" button | Modal dialog opens | ⏳ | |
| 2 | Verify modal title | Shows "Create New User" | ⏳ | |
| 3 | Verify form fields | See: Telegram ID, Nombre, Nivel | ⏳ | |
| 4 | Fill Telegram ID | Input accepts integer | ⏳ | |
| 5 | Fill Nombre | Input accepts text | ⏳ | |
| 6 | Select Nivel | Dropdown shows 1, 2, 3 options | ⏳ | |
| 7 | Click "Save" | Form submits | ⏳ | |
| 8 | Verify success message | Toast/notification appears | ⏳ | |
| 9 | Verify user in table | New user appears in list | ⏳ | |
| 10 | Verify data correctness | Fields match what was entered | ⏳ | |

**Pass Criteria**: ✅ All rows completed, user visible in table

**Error Cases**:
- Duplicate telegram_id → 400 error (graceful handling)
- Empty fields → Validation error
- Invalid nivel → Error message

---

#### TC-003: Edit User
**Pre-condition**: User exists in table  
**Status**: NOT STARTED

| Step | Action | Expected Result | Result | Notes |
|------|--------|-----------------|--------|-------|
| 1 | Click on a user row | User highlighted/selected | ⏳ | |
| 2 | Click "Edit" button or pencil icon | Edit modal opens | ⏳ | |
| 3 | Verify current values | Modal shows existing data | ⏳ | |
| 4 | Change Nombre | Can edit field | ⏳ | |
| 5 | Change Nivel to different value | Can update level | ⏳ | |
| 6 | Click "Update" | Form submits | ⏳ | |
| 7 | Verify success message | Notification shows "User updated" | ⏳ | |
| 8 | Verify changes in table | Table reflects updates | ⏳ | |

**Pass Criteria**: ✅ All changes reflected in real-time

---

#### TC-004: Delete User
**Pre-condition**: Multiple users in table  
**Status**: NOT STARTED

| Step | Action | Expected Result | Result | Notes |
|------|--------|-----------------|--------|-------|
| 1 | Click "Delete" button on user | Confirmation modal appears | ⏳ | |
| 2 | Verify warning message | Shows "Are you sure?" | ⏳ | |
| 3 | Click "Cancel" | Modal closes, no deletion | ⏳ | |
| 4 | Click "Delete" again | Confirmation modal opens | ⏳ | |
| 5 | Click "Confirm Delete" | User is deleted | ⏳ | |
| 6 | Verify user removed | User no longer in table | ⏳ | |
| 7 | Verify success message | Notification shows "User deleted" | ⏳ | |

**Pass Criteria**: ✅ User successfully removed from system

---

#### TC-005: Search/Filter Users
**Pre-condition**: Multiple users in table (10+)  
**Status**: NOT STARTED

| Step | Action | Expected Result | Result | Notes |
|------|--------|-----------------|--------|-------|
| 1 | Type in search box | Results filter in real-time | ⏳ | |
| 2 | Search by name | Shows matching users | ⏳ | |
| 3 | Search by telegram_id | Shows matching users | ⏳ | |
| 4 | Search with partial match | Shows all matches | ⏳ | |
| 5 | Clear search | All users display again | ⏳ | |
| 6 | Search with no results | Shows "No users found" | ⏳ | |

**Pass Criteria**: ✅ All search scenarios working correctly

---

### Domain 2: Performance & Cache (ME5)

#### TC-006: Cache Performance Validation
**Pre-condition**: API is running, Redis is connected  
**Status**: NOT STARTED

| Step | Action | Expected Result | Result | Notes |
|------|--------|-----------------|--------|-------|
| 1 | Open browser DevTools (Network tab) | Ready to monitor requests | ⏳ | |
| 2 | Refresh Users page (first load) | Response time ~100-150ms | ⏳ | |
| 3 | Refresh again immediately | Response time ~10-20ms | ⏳ | |
| 4 | Refresh 5-10 more times | Consistent ~10-20ms times | ⏳ | |
| 5 | Verify cache hit in headers | See X-Cache: HIT header | ⏳ | |
| 6 | Create new user (POST) | Cache invalidates | ⏳ | |
| 7 | Refresh page after create | Response time ~100-150ms again | ⏳ | |
| 8 | Subsequent refreshes | Back to ~10-20ms (cache rebuilt) | ⏳ | |

**Pass Criteria**: 
- ✅ First load: <150ms
- ✅ Cached loads: <20ms
- ✅ Cache invalidation works after POST/PUT/DELETE

**Performance Metrics to Record**:
```
First load: ___ ms
Cached loads (avg): ___ ms
Improvement ratio: ___ x
Cache hit ratio: ___ %
```

---

#### TC-007: Response Time Under Load
**Pre-condition**: Admin page open  
**Status**: NOT STARTED

| Step | Action | Expected Result | Result | Notes |
|------|--------|-----------------|--------|-------|
| 1 | Rapid click "Create User" button | Modal opens quickly | ⏳ | |
| 2 | Fill and save multiple users | Each save <1 second | ⏳ | |
| 3 | Rapid page refresh | No lag or delays | ⏳ | |
| 4 | Multiple edits in succession | System remains responsive | ⏳ | |
| 5 | Search while others editing | UI remains smooth | ⏳ | |

**Pass Criteria**: ✅ No perceivable lag under typical user load

---

### Domain 3: Real-time Notifications (ME3)

#### TC-008: WebSocket Notifications
**Pre-condition**: Two browser windows open (Admin A, Admin B)  
**Status**: NOT STARTED

| Step | Action | Expected Result | Result | Notes |
|------|--------|-----------------|--------|-------|
| 1 | In Browser A, create new user | Immediate notification to B | ⏳ | |
| 2 | In Browser B, verify notification | Toast/popup appears | ⏳ | |
| 3 | Check notification content | Shows user details | ⏳ | |
| 4 | Verify notification timestamp | Correct time displayed | ⏳ | |
| 5 | Test edit notification | Same flow for updates | ⏳ | |
| 6 | Test delete notification | Same flow for deletions | ⏳ | |
| 7 | Check notification persistence | Can see history | ⏳ | |

**Pass Criteria**: ✅ All admins see real-time notifications

---

#### TC-009: Telegram Integration
**Pre-condition**: Telegram bot connected, admin telegram_id registered  
**Status**: NOT STARTED

| Step | Action | Expected Result | Result | Notes |
|------|--------|-----------------|--------|-------|
| 1 | Send /start to bot | Bot responds with welcome | ⏳ | |
| 2 | Send /task_list | Bot lists tasks for user | ⏳ | |
| 3 | Send /help | Bot shows available commands | ⏳ | |
| 4 | Check response time | Bot responds <3 seconds | ⏳ | |
| 5 | Create task in API | Verify in Telegram | ⏳ | |

**Pass Criteria**: ✅ All bot commands functional

---

### Domain 4: UI/UX & Responsiveness

#### TC-010: Responsive Design - Desktop
**Pre-condition**: Desktop browser (1920x1080+)  
**Status**: NOT STARTED

| Step | Action | Expected Result | Result | Notes |
|------|--------|-----------------|--------|-------|
| 1 | View Admin Dashboard | Layout optimal for desktop | ⏳ | |
| 2 | View Users table | All columns visible | ⏳ | |
| 3 | View modals | Modals centered and readable | ⏳ | |
| 4 | Verify scrolling | No horizontal scroll needed | ⏳ | |
| 5 | Check button sizes | Easy to click targets | ⏳ | |
| 6 | Verify colors | Dark and light mode both clear | ⏳ | |

**Pass Criteria**: ✅ Desktop experience optimal

---

#### TC-011: Responsive Design - Mobile
**Pre-condition**: Mobile device or responsive mode (375x667)  
**Status**: NOT STARTED

| Step | Action | Expected Result | Result | Notes |
|------|--------|-----------------|--------|-------|
| 1 | View Dashboard | Layout stacks vertically | ⏳ | |
| 2 | Open Users tab | Single column layout | ⏳ | |
| 3 | Tap user row | Expands to show details | ⏳ | |
| 4 | Open create modal | Full screen or large modal | ⏳ | |
| 5 | Fill form fields | Touch-friendly input sizes | ⏳ | |
| 6 | Tap buttons | Easy to hit with touch | ⏳ | |
| 7 | Test dark mode | Readable on mobile | ⏳ | |

**Pass Criteria**: ✅ Mobile experience comfortable to use

---

#### TC-012: Accessibility
**Pre-condition**: Keyboard and screen reader ready  
**Status**: NOT STARTED

| Step | Action | Expected Result | Result | Notes |
|------|--------|-----------------|--------|-------|
| 1 | Navigate with Tab key | Focus order logical | ⏳ | |
| 2 | Use arrow keys | Can navigate table rows | ⏳ | |
| 3 | Press Enter | Modals open/activate buttons | ⏳ | |
| 4 | Test screen reader | Can read all content | ⏳ | |
| 5 | Verify alt text | Images have descriptions | ⏳ | |
| 6 | Check contrast | Text readable (WCAG AA) | ⏳ | |

**Pass Criteria**: ✅ Meets accessibility standards

---

### Domain 5: Error Handling

#### TC-013: Graceful Error Handling
**Pre-condition**: Running in staging environment  
**Status**: NOT STARTED

| Step | Action | Expected Result | Result | Notes |
|------|--------|-----------------|--------|-------|
| 1 | Try duplicate telegram_id | 400 error, clear message | ⏳ | |
| 2 | Try empty required field | Validation error shown | ⏳ | |
| 3 | Try invalid nivel value | Input rejected with feedback | ⏳ | |
| 4 | Try edit non-existent user | 404 error handled gracefully | ⏳ | |
| 5 | Temporarily stop Redis | API continues (degraded mode) | ⏳ | |
| 6 | Resume Redis | Cache starts working again | ⏳ | |
| 7 | Check error messages | All messages are user-friendly | ⏳ | |

**Pass Criteria**: ✅ No crashes, all errors handled gracefully

---

### Domain 6: Security

#### TC-014: Basic Security Checks
**Pre-condition**: Admin user logged in  
**Status**: NOT STARTED

| Step | Action | Expected Result | Result | Notes |
|------|--------|-----------------|--------|-------|
| 1 | Try to access without login | Redirected to login page | ⏳ | |
| 2 | Verify JWT token in headers | Authorization header present | ⏳ | |
| 3 | Try XSS in user name field | Input sanitized/escaped | ⏳ | |
| 4 | View page source | No sensitive data in HTML | ⏳ | |
| 5 | Check browser console | No XSS vulnerabilities | ⏳ | |

**Pass Criteria**: ✅ No security issues detected

---

## 📊 UAT Results Summary

### Test Execution

| Domain | Test Case | Status | Duration | Notes |
|--------|-----------|--------|----------|-------|
| User Mgmt | TC-001 | ⏳ | -- | |
| User Mgmt | TC-002 | ⏳ | -- | |
| User Mgmt | TC-003 | ⏳ | -- | |
| User Mgmt | TC-004 | ⏳ | -- | |
| User Mgmt | TC-005 | ⏳ | -- | |
| Performance | TC-006 | ⏳ | -- | |
| Performance | TC-007 | ⏳ | -- | |
| Real-time | TC-008 | ⏳ | -- | |
| Integration | TC-009 | ⏳ | -- | |
| Responsive | TC-010 | ⏳ | -- | |
| Responsive | TC-011 | ⏳ | -- | |
| Accessibility | TC-012 | ⏳ | -- | |
| Error Handling | TC-013 | ⏳ | -- | |
| Security | TC-014 | ⏳ | -- | |

**Total**: 14 test cases

---

## ✅ UAT Sign-off Checklist

### Functionality
- [ ] All CRUD operations work correctly
- [ ] Search/filter functionality working
- [ ] Pagination working
- [ ] Real-time notifications working
- [ ] Telegram integration operational
- [ ] Error messages clear and helpful
- [ ] No critical bugs found

### Performance
- [ ] Cache hit ratio >80%
- [ ] Response times acceptable (<100ms without cache, <20ms with)
- [ ] Page loads quickly (<2 sec)
- [ ] No perceivable lag under normal use
- [ ] Performance meets SLAs

### UI/UX
- [ ] Desktop layout looks good
- [ ] Mobile layout responsive
- [ ] Dark mode working properly
- [ ] Colors and fonts consistent
- [ ] Buttons easily clickable
- [ ] Forms intuitive and clear

### Accessibility & Security
- [ ] Keyboard navigation works
- [ ] Screen reader compatible
- [ ] WCAG 2.1 AA compliant
- [ ] No XSS vulnerabilities
- [ ] Authentication/authorization working
- [ ] No hardcoded secrets exposed

### Documentation
- [ ] User guide clear
- [ ] Error messages helpful
- [ ] Feature descriptions accurate
- [ ] Known limitations documented

---

## 🎯 Approval & Sign-Off

### Tester 1: ________________
- Name: ____________________
- Date: ____________________
- Signature: ________________
- Overall Assessment: [ ] PASS  [ ] FAIL  [ ] CONDITIONAL

### Tester 2: ________________
- Name: ____________________
- Date: ____________________
- Signature: ________________
- Overall Assessment: [ ] PASS  [ ] FAIL  [ ] CONDITIONAL

### Product Owner: ____________
- Name: ____________________
- Date: ____________________
- Signature: ________________
- Overall Assessment: [ ] APPROVED  [ ] NEEDS FIXES  [ ] REJECTED

---

## 🚀 Next Steps (If UAT Passes)

1. **Document all findings** in issue tracker
2. **Create hotfixes** for any issues found (if any)
3. **Schedule production deployment** for Oct 22
4. **Prepare rollback plan** (if needed)
5. **Notify stakeholders** of deployment schedule
6. **Update release notes** with final UAT results

---

## 📞 Support During UAT

**Issues Found**: Report to Senior Dev Lead  
**Questions**: Ask Product Owner  
**Technical Issues**: Contact DevOps Lead  

---

**Generated**: October 21, 2025  
**Version**: v1.3.0  
**Environment**: Staging  
**Status**: ⏳ READY FOR EXECUTION
