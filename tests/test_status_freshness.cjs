const assert=require('node:assert/strict');
const {calendarGap,snapshotCurrent}=require('../public/r3-status.js');
const now=new Date('2026-10-14T07:00:00Z');
assert.equal(calendarGap('2026-10-13',now),1);
assert.equal(calendarGap('2026-10-12',now),2);
assert.equal(calendarGap('2026-10-15',now),null);
assert.equal(calendarGap('2026-02-30',now),null);
assert.equal(calendarGap('',now),null);
assert.equal(calendarGap('2026-10-13',new Date('2026-10-13T22:30:00Z')),1); // Paris already 14 October
assert.equal(snapshotCurrent('2026-10-13T13:33:58Z',now),true);
assert.equal(snapshotCurrent('2026-10-10T13:33:58Z',now),false);
assert.equal(snapshotCurrent('2026-10-15T13:33:58Z',now),false);
assert.equal(snapshotCurrent('invalid',now),false);
console.log('PASS: status freshness, calendar boundaries, invalid/future dates (10 cases)');
