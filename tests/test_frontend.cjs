// Safe formatting contract; no browser or real Vertex request required.
const fs=require('fs'),vm=require('vm'),assert=require('node:assert/strict');
const source=fs.readFileSync('app/static/inspection.js','utf8').split('(()=>{')[0];
const env={window:{},esc:s=>String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'",'&#39;')};
vm.runInNewContext(source,env);
const out=env.window.formatAI('## Findings\n- **Check** pressure\n- Inspect flow\n\n1. Review\n<script>alert(1)</script>');
assert(out.includes('<h4>Findings</h4>'));
assert(out.includes('<ul><li><strong>Check</strong> pressure</li>'));
assert(out.includes('<ol><li>Review</li></ol>'));
assert(!out.includes('<script>'));assert(out.includes('&lt;script&gt;'));
assert(!env.window.formatAI('[click](javascript:alert(1))').includes('<a'));
console.log('Frontend formatting and HTML escaping checks passed.');
