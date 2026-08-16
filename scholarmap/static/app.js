const sections={
  top_conference:'Top Conference',
  strong_labs:'Strong Labs / Companies',
  most_cited:'Most Cited',
  surveys:'Surveys',
  classics:'Classics',
  open_source:'Open Source'
};

const checks=document.getElementById('checks');
for(const [k,v] of Object.entries(sections)){
  checks.insertAdjacentHTML('beforeend',`<label class="chip"><input type="checkbox" value="${k}" checked>${v}</label>`);
}

const esc=s=>String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));

function authorMarkup(p){
  const details=(p.author_details&&p.author_details.length)
    ? p.author_details
    : (p.authors||[]).map(name=>({name,id:null,institutions:[]}));
  return details.slice(0,8).map(a=>
    `<button type="button" class="author-link" data-author-id="${esc(a.id||'')}" data-author-name="${esc(a.name)}">${esc(a.name)}</button>`
  ).join('<span class="author-sep">, </span>');
}

function paperCard(p,{compact=false}={}){
  const links=Object.entries(p.links||{}).map(([k,v])=>
    `<a target="_blank" rel="noreferrer" href="${esc(v)}">${esc(k)}</a>`
  ).join('');
  const tags=(p.tags||[]).map(x=>`<span class="tag">${esc(x)}</span>`).join('');
  const inst=(p.institutions||[]).slice(0,3).join(' · ');
  const repo=(p.repositories||[])[0];
  return `<article class="paper${compact?' compact':''}">
    <h3>${esc(p.title)}</h3>
    <div class="meta author-row">${authorMarkup(p)}</div>
    <div class="meta">${inst?esc(inst)+'<br>':''}${esc(p.venue||'arXiv / Other')} · ${esc(p.publication_date||'')}</div>
    <div class="tags">${tags}</div>
    <div class="metrics">
      <b>${Number(p.citations||0).toLocaleString()} citations</b>
      ${p.impact_percentile!=null?`<span>${Number(p.impact_percentile).toFixed(1)}% topic-age percentile</span>`:''}
      ${repo?`<span>${repo.stars==null?'—':Number(repo.stars).toLocaleString()} ★</span>`:''}
    </div>
    <div class="why"><b>Why it matters.</b> ${esc(p.why_it_matters)}</div>
    ${compact?'':`<details><summary>Abstract</summary><div class="abstract">${esc(p.abstract)}</div></details>`}
    <div class="links">${links}</div>
  </article>`;
}

async function buildLandscape(){
  const btn=document.getElementById('search');
  btn.disabled=true;
  document.getElementById('status').textContent='Building research landscape…';
  document.getElementById('results').innerHTML='';
  const payload={
    topic:document.getElementById('topic').value,
    date_from:document.getElementById('from').value,
    date_to:document.getElementById('to').value,
    sections:[...checks.querySelectorAll('input:checked')].map(x=>x.value),
    sort:document.getElementById('sort').value,
    papers_per_section:+document.getElementById('count').value,
    live:document.getElementById('live').checked
  };
  try{
    const r=await fetch('/api/search',{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify(payload)
    });
    if(!r.ok) throw new Error(await r.text());
    const data=await r.json();
    document.getElementById('status').textContent=`${data.candidate_count} candidate papers · ${data.date_from} → ${data.date_to}`;
    let html=(data.warnings||[]).map(w=>`<div class="warning">${esc(w)}</div>`).join('');
    for(const s of data.sections){
      html+=`<section class="section"><div class="section-heading"><h2>${esc(s.title)}</h2><span>${s.papers.length}</span></div>${s.papers.map(p=>paperCard(p)).join('')}</section>`;
    }
    document.getElementById('results').innerHTML=html;
  }catch(e){
    document.getElementById('status').textContent='Search failed';
    document.getElementById('results').innerHTML=`<div class="warning">${esc(e.message)}</div>`;
  }finally{
    btn.disabled=false;
  }
}

async function openAuthor(authorId,authorName){
  const overlay=document.getElementById('authorOverlay');
  const topic=document.getElementById('topic').value;
  overlay.classList.add('open');
  overlay.setAttribute('aria-hidden','false');
  document.body.classList.add('modal-open');
  document.getElementById('authorTitle').textContent=authorName;
  document.getElementById('authorSubtitle').textContent=`All-time papers by this author related to “${topic}”`;
  document.getElementById('authorStatus').textContent='Loading author research map…';
  document.getElementById('authorPapers').innerHTML='';
  try{
    const r=await fetch('/api/authors/papers',{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({
        author_id:authorId||null,
        author_name:authorName,
        topic,
        live:document.getElementById('live').checked,
        limit:1000
      })
    });
    if(!r.ok) throw new Error(await r.text());
    const data=await r.json();
    document.getElementById('authorTitle').textContent=data.author.name;
    document.getElementById('authorSubtitle').textContent=`${data.paper_count} topic-relevant papers · all-time · ranked for “${data.topic}”`;
    const warnings=(data.warnings||[]).map(w=>`<div class="warning">${esc(w)}</div>`).join('');
    document.getElementById('authorStatus').innerHTML=warnings;
    document.getElementById('authorPapers').innerHTML=data.papers.length
      ? data.papers.map(p=>paperCard(p,{compact:true})).join('')
      : '<div class="empty">No topic-matching papers were found for this author.</div>';
  }catch(e){
    document.getElementById('authorStatus').innerHTML=`<div class="warning">${esc(e.message)}</div>`;
  }
}

function closeAuthor(){
  const overlay=document.getElementById('authorOverlay');
  overlay.classList.remove('open');
  overlay.setAttribute('aria-hidden','true');
  document.body.classList.remove('modal-open');
}

document.getElementById('search').addEventListener('click',buildLandscape);
document.getElementById('closeAuthor').addEventListener('click',closeAuthor);
document.getElementById('authorOverlay').addEventListener('click',e=>{if(e.target.id==='authorOverlay')closeAuthor();});
document.addEventListener('keydown',e=>{if(e.key==='Escape')closeAuthor();});
document.addEventListener('click',e=>{
  const link=e.target.closest('.author-link');
  if(!link) return;
  openAuthor(link.dataset.authorId||'',link.dataset.authorName||link.textContent.trim());
});

buildLandscape();
